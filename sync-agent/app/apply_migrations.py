"""
Aplica as migrations SQL do Supabase na ordem dos nomes de arquivo.
Cada arquivo roda em sua própria transação (rollback se falhar).

Uso: python -m app.apply_migrations
"""
import sys
from pathlib import Path

import psycopg

from app.config import settings
from app.logging_conf import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def main() -> int:
    if not settings.supabase_db_url:
        print("ERRO: SUPABASE_DB_URL não configurada no .env")
        return 1

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"Nenhuma migration encontrada em {MIGRATIONS_DIR}")
        return 1

    with psycopg.connect(settings.supabase_db_url) as conn:
        for f in files:
            sql = f.read_text(encoding="utf-8")
            print(f"Aplicando {f.name} ...", end=" ", flush=True)
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                print("OK")
            except Exception as e:  # noqa: BLE001
                conn.rollback()
                print("ERRO")
                logger.error("Falha em %s: %s", f.name, e)
                return 1

    print("Todas as migrations aplicadas com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
