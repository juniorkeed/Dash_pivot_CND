"""
Pipeline de sincronização Oracle → Postgres (Supabase).

Uso (CLI):
    python -m app.pipeline --from 2026-05-01 --to 2026-05-31           # sincroniza a janela
    python -m app.pipeline --from 2026-05-01 --to 2026-05-31 --count-only  # só mede volume
    python -m app.pipeline --smoke                                     # testa conexão Oracle

A flag --count-only NÃO toca no Postgres: serve à "prova de volume" da Fase 1
(quantas linhas o fato diário gera num mês e quanto isso pesa) para decidir a
janela de histórico que cabe no Supabase Free (500 MB).
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta

import pandas as pd

from app.logging_conf import get_logger
from app.oracle.runner import fetch_df, fetch_scalar
from app.oracle.sql import snapshot_sql as q

logger = get_logger(__name__)

# Estimativa grosseira de bytes/linha no Postgres (heap + índices) para o fato diário.
_BYTES_POR_LINHA_FATO = 190

# Mapeamento das colunas de cada tabela (nomes finais, minúsculos, do Postgres).
COLS_FATO_VENDAS = ["data", "cod_filial", "cod_vendedor", "cod_cliente", "cod_produto",
                    "qt", "vl_total", "vl_custo_total", "lucro_bruto"]
COLS_FATO_PEDIDO = ["data", "cod_filial", "cod_vendedor", "cod_cliente", "num_pedido", "vl_pedido"]
COLS_DIM_FILIAL = ["cod_filial", "filial"]
COLS_DIM_VENDEDOR = ["cod_vendedor", "vendedor"]
COLS_DIM_CLIENTE = ["cod_cliente", "cliente", "fantasia", "cidade", "uf", "cod_praca"]
COLS_DIM_PRODUTO = ["cod_produto", "produto", "embalagem", "unidade", "cod_fabricante",
                    "cod_barras", "codepto", "departamento", "codsec", "secao",
                    "codcategoria", "categoria", "codmarca", "marca", "codfornec", "fornecedor"]


def _norm(df):
    """Colunas do Oracle (MAIÚSCULAS) → minúsculas, como no Postgres."""
    df.columns = [c.lower() for c in df.columns]
    return df


def _params(dt_ini: date, dt_fim: date) -> dict:
    return {"DTINICIAL": dt_ini, "DTFINAL": dt_fim}


# ---------------------------------------------------------------- prova de volume

def medir_volume(dt_ini: date, dt_fim: date) -> dict:
    """Extrai o fato diário do período e mede nº de linhas + tamanho estimado."""
    t0 = time.perf_counter()
    df = _norm(fetch_df(q.SQL_SNAPSHOT_FATO_DIARIO, _params(dt_ini, dt_fim)))
    elapsed = time.perf_counter() - t0
    linhas = len(df)
    mb_mem = df.memory_usage(deep=True).sum() / 1e6
    mb_pg = linhas * _BYTES_POR_LINHA_FATO / 1e6
    return {
        "linhas": linhas,
        "mb_pandas": round(mb_mem, 1),
        "mb_pg_estimado": round(mb_pg, 1),
        "segundos_extracao": round(elapsed, 1),
        "dias": (dt_fim - dt_ini).days + 1,
    }


# ---------------------------------------------------------------- sync

def sync_window(dt_ini: date, dt_fim: date) -> dict:
    """Sincroniza dimensões (upsert) e fatos (replace por janela) no Postgres."""
    from app.load import control, pg  # import tardio: só quando há Postgres configurado

    resultado = {}
    t0 = time.perf_counter()
    control.log_sync("vendas", dt_ini, dt_fim, "running")

    # Dimensões (upsert) — filial/vendedor inteiras; cliente/produto do período.
    resultado["dim_filial"] = pg.upsert_dimension(
        "dim_filial", _norm(fetch_df(q.SQL_DIM_FILIAL)), COLS_DIM_FILIAL, "cod_filial")
    resultado["dim_vendedor"] = pg.upsert_dimension(
        "dim_vendedor", _norm(fetch_df(q.SQL_DIM_VENDEDOR)), COLS_DIM_VENDEDOR, "cod_vendedor")
    resultado["dim_cliente"] = pg.upsert_dimension(
        "dim_cliente", _norm(fetch_df(q.SQL_DIM_CLIENTE_PERIODO, _params(dt_ini, dt_fim))),
        COLS_DIM_CLIENTE, "cod_cliente")
    resultado["dim_produto"] = pg.upsert_dimension(
        "dim_produto", _norm(fetch_df(q.SQL_DIM_PRODUTO_PERIODO, _params(dt_ini, dt_fim))),
        COLS_DIM_PRODUTO, "cod_produto")

    # Fatos (replace por janela).
    fato_vendas = _norm(fetch_df(q.SQL_SNAPSHOT_FATO_DIARIO, _params(dt_ini, dt_fim)))
    fato_vendas["data"] = pd.to_datetime(fato_vendas["data"]).dt.date
    resultado["fato_vendas_diario"] = pg.replace_window_fact(
        "fato_vendas_diario", fato_vendas, COLS_FATO_VENDAS, dt_ini, dt_fim)

    fato_pedido = _norm(fetch_df(q.SQL_SNAPSHOT_FATO_PEDIDO, _params(dt_ini, dt_fim)))
    fato_pedido["data"] = pd.to_datetime(fato_pedido["data"]).dt.date
    resultado["fato_pedido_diario"] = pg.replace_window_fact(
        "fato_pedido_diario", fato_pedido, COLS_FATO_PEDIDO, dt_ini, dt_fim)

    dur = round(time.perf_counter() - t0, 1)
    total = resultado["fato_vendas_diario"]
    control.log_sync("vendas", dt_ini, dt_fim, "ok", linhas=total, duracao_seg=dur)
    logger.info("sync_window concluído em %ss: %s", dur, resultado)
    return resultado


# ---------------------------------------------------------------- CLI

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Oracle → Postgres (Supabase)")
    parser.add_argument("--from", dest="dt_from", help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="dt_to", help="Data final YYYY-MM-DD")
    parser.add_argument("--count-only", action="store_true", help="Só medir volume (não grava no Postgres)")
    parser.add_argument("--smoke", action="store_true", help="Testar conexão Oracle e sair")
    args = parser.parse_args(argv)

    if args.smoke:
        from app.oracle.connection import test_connection
        ok, msg = test_connection()
        print(("OK  " if ok else "ERRO ") + msg)
        return 0 if ok else 1

    if not args.dt_from or not args.dt_to:
        parser.error("informe --from e --to (YYYY-MM-DD)")
    dt_ini, dt_fim = _parse_date(args.dt_from), _parse_date(args.dt_to)

    if args.count_only:
        info = medir_volume(dt_ini, dt_fim)
        print(
            f"[PROVA DE VOLUME] {info['dias']} dias ({dt_ini}..{dt_fim})\n"
            f"  fato_vendas_diario: {info['linhas']:,} linhas\n"
            f"  extração Oracle:    {info['segundos_extracao']}s\n"
            f"  ~tamanho no Postgres: {info['mb_pg_estimado']} MB (estimado)\n"
            f"  (pandas em memória:  {info['mb_pandas']} MB)"
        )
        # Projeção para 6 / 12 meses, assumindo o mês como base.
        if info["dias"] > 0:
            por_dia = info["linhas"] / info["dias"]
            for meses in (3, 6, 12):
                linhas_proj = por_dia * 30 * meses
                mb_proj = linhas_proj * _BYTES_POR_LINHA_FATO / 1e6
                print(f"  projeção {meses:>2} meses: ~{linhas_proj:,.0f} linhas, ~{mb_proj:,.0f} MB")
        return 0

    resultado = sync_window(dt_ini, dt_fim)
    print("Sync concluído:", resultado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
