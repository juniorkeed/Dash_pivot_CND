"""Imprime as contagens das tabelas do Supabase. Uso: python -m app.db_counts"""
import psycopg

from app.config import settings

TABLES = ["dim_filial", "dim_vendedor", "dim_cliente", "dim_produto",
          "fato_vendas_diario", "fato_pedido_diario", "sync_log"]


def main() -> int:
    with psycopg.connect(settings.supabase_db_url) as conn, conn.cursor() as cur:
        for t in TABLES:
            cur.execute(f"select count(*) from {t}")
            print(f"{t}: {cur.fetchone()[0]}")
    return 0


if __name__ == "__main__":
    main()
