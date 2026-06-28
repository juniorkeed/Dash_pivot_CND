"""
Configuração de logging para o sync-agent (porta de config/logging.py do projeto
Streamlit, sem dependência de Streamlit). Loga em stdout — adequado para Docker.
"""
import logging
import sys

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado para escrever em stdout."""
    _configure()
    return logging.getLogger(name)
