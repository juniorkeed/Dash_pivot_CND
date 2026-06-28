"""
Executor genérico de queries Oracle.
Fornece funções utilitárias: fetch_df, fetch_one, fetch_all, execute, fetch_scalar.

Cópia de db/runner.py do projeto Streamlit (lógica idêntica) — apenas os imports
mudam para a nova estrutura de pacotes. Mantém o retry exponencial em erros
transitórios do Oracle (rede, timeout de listener etc.). Mutations (`execute`)
NÃO têm retry — idempotência não é garantida.
"""
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import oracledb
import pandas as pd

from app.logging_conf import get_logger
from app.oracle.connection import get_connection

logger = get_logger(__name__)

T = TypeVar("T")

# Códigos Oracle tipicamente transitórios (rede/listener/pool)
_TRANSIENT_ERROR_CODES = frozenset({
    3113,   # end-of-file on communication channel
    3114,   # not connected to ORACLE
    12170,  # TNS:Connect timeout occurred
    12528,  # TNS:listener: all appropriate instances are blocking new connections
    12537,  # TNS:connection closed
    12541,  # TNS:no listener
    12571,  # TNS:packet writer failure
})


def _is_transient(exc: Exception) -> bool:
    if not isinstance(exc, oracledb.DatabaseError):
        return False
    args = exc.args
    if not args:
        return False
    err = args[0]
    code = getattr(err, "code", None)
    return code in _TRANSIENT_ERROR_CODES


def _with_retry(
    max_attempts: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: retry exponencial em erros transitórios do Oracle."""
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    if attempt >= max_attempts or not _is_transient(exc):
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Erro transitório em %s (tentativa %d/%d): %s. Retry em %.1fs",
                        fn.__name__, attempt, max_attempts, exc, delay,
                    )
                    time.sleep(delay)
        return wrapper
    return decorator


@_with_retry()
def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Executa uma query e retorna os resultados como DataFrame."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or {})
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows, columns=columns)


@_with_retry()
def fetch_one(sql: str, params: dict | None = None) -> tuple | None:
    """Executa uma query e retorna apenas a primeira linha."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or {})
        result = cursor.fetchone()
        cursor.close()
        return result


@_with_retry()
def fetch_all(sql: str, params: dict | None = None) -> list[tuple]:
    """Executa uma query e retorna todas as linhas como lista de tuplas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or {})
        results = cursor.fetchall()
        cursor.close()
        return results


def execute(sql: str, params: dict | None = None, commit: bool = True) -> int:
    """Executa INSERT/UPDATE/DELETE. Sem retry para evitar execução dupla."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or {})
        rowcount = cursor.rowcount
        if commit:
            conn.commit()
        cursor.close()
        return rowcount


def fetch_scalar(sql: str, params: dict | None = None) -> Any:
    """Retorna o primeiro valor da primeira linha. Útil para COUNT/SUM/etc."""
    result = fetch_one(sql, params)
    return result[0] if result else None
