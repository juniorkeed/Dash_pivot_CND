-- ============================================================
-- 0004 — View "flat" (fato + dimensões) — base do pivô de vendas
-- ============================================================

create or replace view vw_vendas_flat
with (security_invoker = on)
as
select
    f.data,
    d.ano,
    d.mes,
    d.ano_mes,
    d.trimestre,
    f.cod_filial,    fi.filial,
    f.cod_vendedor,  ve.vendedor,
    f.cod_cliente,   cl.cliente,  cl.cidade,  cl.uf,
    f.cod_produto,   pr.produto,  pr.marca,   pr.fornecedor,
                     pr.departamento, pr.secao, pr.categoria,
    f.qt,
    f.vl_total,
    f.vl_custo_total,
    f.lucro_bruto
from fato_vendas_diario f
join      dim_data     d  on d.data         = f.data
left join dim_filial   fi on fi.cod_filial   = f.cod_filial
left join dim_vendedor ve on ve.cod_vendedor = f.cod_vendedor
left join dim_cliente  cl on cl.cod_cliente  = f.cod_cliente
left join dim_produto  pr on pr.cod_produto  = f.cod_produto;
