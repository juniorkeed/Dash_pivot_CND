-- ============================================================
-- 0005 — RPC do pivô de vendas (GROUP BY dinâmico com whitelist)
--
-- Recebe os eixos (dims) e medidas escolhidos no front e devolve o agregado
-- em formato LONGO (cada linha = um objeto jsonb {dim1:.., medida1:..}).
-- O react-pivottable transpõe/totaliza esse resultado já pequeno no cliente.
--
-- Anti-injection: dims/medidas são validadas contra uma WHITELIST e passadas
-- por quote_ident/%I; as datas por %L. SECURITY INVOKER → respeita a RLS.
-- ============================================================

create or replace function pivot_vendas(
    p_dims     text[],
    p_measures text[],
    p_dt_ini   date,
    p_dt_fim   date
) returns setof jsonb
language plpgsql
stable
security invoker
as $$
declare
    allowed_dims constant text[] := array[
        'ano','mes','ano_mes','trimestre',
        'filial','vendedor','cliente','cidade','uf',
        'produto','marca','fornecedor','departamento','secao','categoria'
    ];
    allowed_meas constant text[] := array[
        'qt','vl_total','vl_custo_total','lucro_bruto'
    ];
    dim_list  text;
    meas_list text;
    q         text;
begin
    if p_dt_ini is null or p_dt_fim is null then
        raise exception 'periodo obrigatorio (p_dt_ini, p_dt_fim)';
    end if;
    if array_length(p_measures, 1) is null then
        raise exception 'informe ao menos uma medida';
    end if;
    if exists (select 1 from unnest(p_dims) d where d <> all(allowed_dims)) then
        raise exception 'dimensao nao permitida';
    end if;
    if exists (select 1 from unnest(p_measures) m where m <> all(allowed_meas)) then
        raise exception 'medida nao permitida';
    end if;

    select string_agg(quote_ident(d), ', ') into dim_list from unnest(p_dims) d;
    select string_agg(format('sum(%I) as %I', m, m), ', ') into meas_list
      from unnest(p_measures) m;

    if dim_list is null then
        -- sem dimensões: uma linha com o total geral
        q := format(
            'select to_jsonb(t) from (select %s from vw_vendas_flat '
            'where data between %L and %L) t',
            meas_list, p_dt_ini, p_dt_fim);
    else
        q := format(
            'select to_jsonb(t) from (select %s, %s from vw_vendas_flat '
            'where data between %L and %L group by %s) t',
            dim_list, meas_list, p_dt_ini, p_dt_fim, dim_list);
    end if;

    return query execute q;
end;
$$;
