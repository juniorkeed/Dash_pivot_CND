"""
Registro de execuções de sync na tabela `sync_log` do Postgres.
Tolerante a falhas: se o log falhar, apenas avisa (não derruba o sync).
"""
from __future__ import annotations

from datetime import date

from app.load.pg import get_pg_connection
from app.logging_conf import get_logger

logger = get_logger(__name__)


def log_sync(
    entidade: str,
    janela_ini: date | None,
    janela_fim: date | None,
    status: str,
    linhas: int = 0,
    duracao_seg: float | None = None,
    erro: str | None = None,
) -> None:
    """Insere uma linha em sync_log. Status: running | ok | error."""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sync_log "
                    "(entidade, janela_ini, janela_fim, status, linhas, duracao_seg, erro) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (entidade, janela_ini, janela_fim, status, linhas, duracao_seg, erro),
                )
            conn.commit()
    except Exception as exc:  # noqa: BLE001 — log nunca deve derrubar o pipeline
        logger.warning("Falha ao gravar sync_log (%s): %s", entidade, exc)
