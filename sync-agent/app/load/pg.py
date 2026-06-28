"""
Carga no Postgres (Supabase) via psycopg3 `COPY`, idempotente por janela.

Estratégia:
- Fatos: staging em TEMP TABLE via COPY → DELETE da janela → INSERT (1 transação).
  Rodar N vezes converge para o mesmo estado (idempotente).
- Dimensões: staging via COPY → INSERT ... ON CONFLICT (pk) DO UPDATE.

Conectar ao pooler do Supabase em transaction mode (porta 6543).
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import psycopg

from app.config import settings
from app.logging_conf import get_logger

logger = get_logger(__name__)


def get_pg_connection() -> psycopg.Connection:
    """Abre uma conexão com o Postgres do Supabase."""
    if not settings.supabase_db_url:
        raise RuntimeError(
            "SUPABASE_DB_URL não configurada. Defina a string de conexão do "
            "pooler do Supabase (porta 6543) no .env."
        )
    return psycopg.connect(settings.supabase_db_url)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara o DataFrame para o COPY:
    - colunas float que são inteiras (códigos com NaN viram float no pandas) são
      convertidas para Int64 nullable, evitando o COPY enviar '123.0' a colunas integer;
    - NaN/NaT viram None (NULL no Postgres).
    """
    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_float_dtype(s):
            nn = s.dropna()
            if len(nn) and bool((nn % 1 == 0).all()):
                out[col] = s.astype("Int64")
    return out.astype(object).where(pd.notna(out), None)


def _copy_into(cur: psycopg.Cursor, table: str, df: pd.DataFrame, columns: list[str]) -> None:
    """COPY de um DataFrame (já com colunas em `columns`) para `table` via STDIN."""
    cols_sql = ", ".join(columns)
    with cur.copy(f"COPY {table} ({cols_sql}) FROM STDIN") as copy:
        for row in df[columns].itertuples(index=False, name=None):
            copy.write_row(row)


def replace_window_fact(
    table: str, df: pd.DataFrame, columns: list[str], dt_ini: date, dt_fim: date
) -> int:
    """Substitui (idempotente) as linhas do fato no intervalo [dt_ini, dt_fim]."""
    df = _clean(df)
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE TEMP TABLE _stg (LIKE {table} INCLUDING DEFAULTS) ON COMMIT DROP")
            _copy_into(cur, "_stg", df, columns)
            cur.execute(f"DELETE FROM {table} WHERE data >= %s AND data <= %s", (dt_ini, dt_fim))
            cur.execute(f"INSERT INTO {table} ({', '.join(columns)}) SELECT {', '.join(columns)} FROM _stg")
        conn.commit()
    logger.info("replace_window_fact: %s linhas em %s [%s..%s]", len(df), table, dt_ini, dt_fim)
    return len(df)


def upsert_dimension(table: str, df: pd.DataFrame, columns: list[str], pk: str) -> int:
    """Upsert de dimensão via staging + ON CONFLICT (pk) DO UPDATE."""
    if df.empty:
        return 0
    df = _clean(df)
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != pk)
    cols_sql = ", ".join(columns)
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE TEMP TABLE _stg (LIKE {table} INCLUDING DEFAULTS) ON COMMIT DROP")
            _copy_into(cur, "_stg", df, columns)
            cur.execute(
                f"INSERT INTO {table} ({cols_sql}) SELECT {cols_sql} FROM _stg "
                f"ON CONFLICT ({pk}) DO UPDATE SET {set_clause}"
            )
        conn.commit()
    logger.info("upsert_dimension: %s linhas em %s", len(df), table)
    return len(df)
