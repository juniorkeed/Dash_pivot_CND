"""
Configurações centralizadas do sync-agent.

Porta de config/settings.py do projeto Streamlit, agora com pydantic-settings
(validação + leitura de .env) e com as chaves do Postgres/Supabase.

As variáveis de ambiente são lidas de forma case-insensitive, então o mesmo
.env do app Streamlit (ORACLE_HOST, ORACLE_PORT, ...) continua compatível.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Oracle (WinThor) — mesmas chaves do app Streamlit ---
    oracle_host: str = "192.168.1.10"
    oracle_port: int = 1521
    oracle_service_name: str = "WINT"
    oracle_user: str = "CONSULTA"
    oracle_password: str = ""
    oracle_client_dir: str | None = None

    # --- Pool de conexões Oracle ---
    pool_min: int = 1
    pool_max: int = 5
    pool_increment: int = 1

    # --- Postgres / Supabase ---
    # String de conexão do "Session pooler" do Supabase (porta 5432, IPv4):
    # postgresql://postgres.<ref>:<senha>@aws-0-<regiao>.pooler.supabase.com:5432/postgres
    supabase_db_url: str = ""

    # --- Sincronização ---
    # Token simples exigido no header x-sync-token do endpoint POST /sync.
    sync_token: str = ""
    # Janela padrão (dias para trás) quando /sync é chamado sem datas explícitas.
    sync_default_days: int = 30


settings = Settings()
