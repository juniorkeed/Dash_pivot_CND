-- ============================================================
-- 0002 — Fatos
-- fato_vendas_diario: medidas ADITIVAS (grão dia × filial × vendedor × cliente × produto)
-- fato_pedido_diario: grão de pedido, para COUNT DISTINCT de pedidos/clientes
-- ============================================================

create table if not exists fato_vendas_diario (
    data            date    not null,
    cod_filial      integer not null,
    cod_vendedor    integer not null,   -- 0 = "sem vendedor" (NVL no Oracle)
    cod_cliente     integer not null,   -- 0 = "sem cliente"
    cod_produto     integer not null,
    qt              numeric(18,3),
    vl_total        numeric(18,2),
    vl_custo_total  numeric(18,2),
    lucro_bruto     numeric(18,2),
    primary key (data, cod_filial, cod_vendedor, cod_cliente, cod_produto)
);

create table if not exists fato_pedido_diario (
    data         date    not null,
    cod_filial   integer not null,
    cod_vendedor integer not null,
    cod_cliente  integer not null,
    num_pedido   bigint  not null,
    vl_pedido    numeric(18,2),
    primary key (data, num_pedido)
);
