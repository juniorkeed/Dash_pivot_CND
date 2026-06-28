-- ============================================================
-- 0003 — Índices para acelerar o GROUP BY do pivô por dimensão
-- (a PK composta já cobre prefixos iniciados por `data`)
-- ============================================================

create index if not exists ix_fvd_produto  on fato_vendas_diario (cod_produto);
create index if not exists ix_fvd_filial   on fato_vendas_diario (cod_filial, data);
create index if not exists ix_fvd_vendedor on fato_vendas_diario (cod_vendedor, data);
create index if not exists ix_fvd_cliente  on fato_vendas_diario (cod_cliente);
create index if not exists ix_fvd_data     on fato_vendas_diario (data);

create index if not exists ix_fpd_data     on fato_pedido_diario (data);
create index if not exists ix_fpd_vendedor on fato_pedido_diario (cod_vendedor, data);
create index if not exists ix_fpd_cliente  on fato_pedido_diario (cod_cliente);

analyze dim_produto;
analyze dim_cliente;
analyze fato_vendas_diario;
analyze fato_pedido_diario;
