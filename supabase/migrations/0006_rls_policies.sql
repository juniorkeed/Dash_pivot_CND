-- ============================================================
-- 0006 — Row Level Security + grants
-- Dados sensíveis (faturamento/margem) só para usuários autenticados.
-- O sync-agent grava via service_role (BYPASSRLS) — não precisa de policy.
-- ============================================================

alter table fato_vendas_diario enable row level security;
alter table fato_pedido_diario enable row level security;
alter table dim_filial   enable row level security;
alter table dim_vendedor enable row level security;
alter table dim_cliente  enable row level security;
alter table dim_produto  enable row level security;
alter table dim_data     enable row level security;

-- Leitura liberada apenas para 'authenticated'
create policy auth_read_fvd  on fato_vendas_diario for select to authenticated using (true);
create policy auth_read_fpd  on fato_pedido_diario for select to authenticated using (true);
create policy auth_read_dfil on dim_filial   for select to authenticated using (true);
create policy auth_read_dven on dim_vendedor for select to authenticated using (true);
create policy auth_read_dcli on dim_cliente  for select to authenticated using (true);
create policy auth_read_dpro on dim_produto  for select to authenticated using (true);
create policy auth_read_ddat on dim_data     for select to authenticated using (true);

-- A função do pivô só pode ser executada por usuários autenticados
revoke execute on function pivot_vendas(text[], text[], date, date) from anon, public;
grant  execute on function pivot_vendas(text[], text[], date, date) to authenticated;
