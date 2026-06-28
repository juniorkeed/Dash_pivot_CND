"""
Conexão com Oracle usando oracledb (Thick Mode), com pool de conexões.

Porta de db/connection.py do projeto Streamlit. A ÚNICA mudança real é a remoção
do acoplamento com Streamlit: o `@st.cache_resource` (que garantia 1 pool por
processo) vira um **singleton puro Python thread-safe** com double-checked locking.
A API pública (`get_connection`, `test_connection`) é preservada.
"""
import threading

import oracledb

from app.config import settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

# Tempo máximo (ms) que acquire() aguarda por uma conexão livre antes de falhar.
_POOL_WAIT_TIMEOUT_MS = 30_000

_pool = None
_pool_lock = threading.Lock()
_client_initialized = False


def init_oracle_client() -> None:
    """Inicializa o Oracle Instant Client (Thick Mode) uma única vez."""
    global _client_initialized
    if _client_initialized:
        return
    try:
        if settings.oracle_client_dir:
            oracledb.init_oracle_client(lib_dir=settings.oracle_client_dir)
        else:
            oracledb.init_oracle_client()
    except oracledb.ProgrammingError:
        # Cliente já inicializado neste processo.
        pass
    _client_initialized = True


def get_dsn() -> str:
    """Retorna o DSN formatado para conexão."""
    return oracledb.makedsn(
        host=settings.oracle_host,
        port=settings.oracle_port,
        service_name=settings.oracle_service_name,
    )


def get_connection_pool():
    """
    Cria (uma vez) e retorna o pool de conexões Oracle.

    Singleton thread-safe: substitui o @st.cache_resource do Streamlit, que
    cumpria o mesmo papel de manter um único pool por processo.
    """
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                init_oracle_client()
                _pool = oracledb.create_pool(
                    user=settings.oracle_user,
                    password=settings.oracle_password,
                    dsn=get_dsn(),
                    min=settings.pool_min,
                    max=settings.pool_max,
                    increment=settings.pool_increment,
                    getmode=oracledb.POOL_GETMODE_TIMEDWAIT,
                    wait_timeout=_POOL_WAIT_TIMEOUT_MS,
                )
    return _pool


def get_connection():
    """
    Obtém uma conexão do pool.
    Uso: with get_connection() as conn:
    """
    return get_connection_pool().acquire()


def test_connection() -> tuple[bool, str]:
    """
    Testa a conexão com o banco.
    Retorna (sucesso, mensagem).
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SYSDATE, USER FROM DUAL")
            dt, user = cursor.fetchone()
            cursor.close()
            return True, f"Conectado como {user} em {dt}"
    except Exception:
        logger.exception("Falha ao testar conexão com Oracle")
        return False, "Não foi possível conectar ao banco. Veja os logs para detalhes."
