-- ============================================================
-- 0001 — Dimensões (star schema) + dim_data + controle de sync
-- Snapshot do ERP WinThor. Códigos = chaves do ERP.
-- ============================================================

create table if not exists dim_filial (
    cod_filial   integer primary key,
    filial       text
);

create table if not exists dim_vendedor (
    cod_vendedor integer primary key,
    vendedor     text
);

create table if not exists dim_cliente (
    cod_cliente  integer primary key,
    cliente      text,
    fantasia     text,
    cidade       text,
    uf           text,
    cod_praca    integer
);

create table if not exists dim_produto (
    cod_produto    integer primary key,
    produto        text,
    embalagem      text,
    unidade        text,
    cod_fabricante text,   -- CODFAB: alfanumérico, pode ter zeros à esquerda
    cod_barras     text,   -- CODAUXILIAR: alfanumérico
    codepto        integer,
    departamento   text,
    codsec         integer,
    secao          text,
    codcategoria   integer,
    categoria      text,
    codmarca       integer,
    marca          text,
    codfornec      integer,
    fornecedor     text
);

-- Dimensão calendário (materializada)
create table if not exists dim_data (
    data        date primary key,
    ano         integer not null,
    mes         integer not null,
    dia         integer not null,
    ano_mes     text    not null,   -- 'YYYY-MM'
    trimestre   integer not null,
    dia_semana  integer not null    -- 0=domingo ... 6=sábado
);

-- Popula 2023-01-01 .. 2027-12-31 (ajuste conforme a janela de histórico).
insert into dim_data (data, ano, mes, dia, ano_mes, trimestre, dia_semana)
select
    d::date,
    extract(year    from d)::int,
    extract(month   from d)::int,
    extract(day     from d)::int,
    to_char(d, 'YYYY-MM'),
    extract(quarter from d)::int,
    extract(dow     from d)::int
from generate_series(date '2023-01-01', date '2027-12-31', interval '1 day') as g(d)
on conflict (data) do nothing;

-- Controle/log de execuções do sync-agent
create table if not exists sync_log (
    id          bigint generated always as identity primary key,
    entidade    text not null,
    janela_ini  date,
    janela_fim  date,
    status      text not null,        -- running | ok | error
    linhas      integer default 0,
    duracao_seg numeric,
    erro        text,
    criado_em   timestamptz not null default now()
);
