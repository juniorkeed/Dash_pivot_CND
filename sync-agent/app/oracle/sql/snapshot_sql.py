"""
Queries de SNAPSHOT — derivadas de SQL_VENDAS_COMPLETA (db/sql/vendas_sql.py do
projeto Streamlit).

Princípio central: o GROUP BY pesado roda NO ORACLE (lugar mais barato) e só o
agregado trafega para a nuvem. Não copiamos venda item-a-item.

Convenção de nomes: colunas já saem com os nomes finais do Postgres (em maiúsculo
do Oracle; o load passa para minúsculo). Todas as queries de fato usam as bind
variables :DTINICIAL e :DTFINAL (intervalo [DTINICIAL, DTFINAL] inclusivo no dia).

NVL(C.CODUSUR, 0)/NVL(C.CODCLI, 0): vendedor e cliente entram na PK do fato no
Postgres, que não aceita NULL — então normalizamos nulos para 0 ("sem vendedor/
sem cliente"). O front usa LEFT JOIN nas dimensões.

Regra de negócio preservada do app atual: vendas faturadas e não canceladas
(C.DTCANCEL IS NULL AND C.POSICAO = 'F').
"""

# ============================================================
# FATO DIÁRIO (medidas ADITIVAS)
# Grão: DATA × FILIAL × VENDEDOR × CLIENTE × PRODUTO
# ============================================================
SQL_SNAPSHOT_FATO_DIARIO = """
SELECT
    TRUNC(C.DTFAT)                                    AS DATA,
    C.CODFILIAL                                       AS COD_FILIAL,
    NVL(C.CODUSUR, 0)                                 AS COD_VENDEDOR,
    NVL(C.CODCLI, 0)                                  AS COD_CLIENTE,
    I.CODPROD                                         AS COD_PRODUTO,
    SUM(I.QT)                                         AS QT,
    SUM(I.QT * I.PVENDA)                              AS VL_TOTAL,
    SUM(I.QT * I.VLCUSTOREAL)                         AS VL_CUSTO_TOTAL,
    SUM((I.QT * I.PVENDA) - (I.QT * I.VLCUSTOREAL))   AS LUCRO_BRUTO
FROM PCPEDI I
INNER JOIN PCPEDC C ON C.NUMPED = I.NUMPED
WHERE C.DTCANCEL IS NULL
  AND C.POSICAO = 'F'
  AND C.DTFAT >= :DTINICIAL
  AND C.DTFAT < :DTFINAL + 1
GROUP BY
    TRUNC(C.DTFAT), C.CODFILIAL, NVL(C.CODUSUR, 0), NVL(C.CODCLI, 0), I.CODPROD
"""

# ============================================================
# FATO PEDIDO (para medidas NÃO ADITIVAS: COUNT DISTINCT pedidos/clientes)
# Grão: DATA × FILIAL × VENDEDOR × CLIENTE × NUM_PEDIDO  (1 linha por pedido-dia)
# ============================================================
SQL_SNAPSHOT_FATO_PEDIDO = """
SELECT
    TRUNC(C.DTFAT)        AS DATA,
    C.CODFILIAL           AS COD_FILIAL,
    NVL(C.CODUSUR, 0)     AS COD_VENDEDOR,
    NVL(C.CODCLI, 0)      AS COD_CLIENTE,
    C.NUMPED              AS NUM_PEDIDO,
    SUM(I.QT * I.PVENDA)  AS VL_PEDIDO
FROM PCPEDI I
INNER JOIN PCPEDC C ON C.NUMPED = I.NUMPED
WHERE C.DTCANCEL IS NULL
  AND C.POSICAO = 'F'
  AND C.DTFAT >= :DTINICIAL
  AND C.DTFAT < :DTFINAL + 1
GROUP BY
    TRUNC(C.DTFAT), C.CODFILIAL, NVL(C.CODUSUR, 0), NVL(C.CODCLI, 0), C.NUMPED
"""

# ============================================================
# DIMENSÕES
# Filial e Vendedor são pequenas → carregamos todas.
# Cliente e Produto podem ser grandes → carregamos só os presentes no período
# sincronizado (o upsert por PK acumula no Postgres ao longo dos syncs).
# ============================================================

SQL_DIM_FILIAL = """
SELECT
    CODIGO        AS COD_FILIAL,
    RAZAOSOCIAL   AS FILIAL
FROM PCFILIAL
WHERE DTEXCLUSAO IS NULL
"""

SQL_DIM_VENDEDOR = """
SELECT
    CODUSUR   AS COD_VENDEDOR,
    NOME      AS VENDEDOR
FROM PCUSUARI
"""

SQL_DIM_CLIENTE_PERIODO = """
SELECT
    CL.CODCLI      AS COD_CLIENTE,
    CL.CLIENTE,
    CL.FANTASIA,
    CL.MUNICENT    AS CIDADE,
    CL.ESTENT      AS UF,
    CL.CODPRACA    AS COD_PRACA
FROM PCCLIENT CL
WHERE CL.CODCLI IN (
    SELECT DISTINCT C.CODCLI
    FROM PCPEDC C
    WHERE C.DTCANCEL IS NULL
      AND C.POSICAO = 'F'
      AND C.DTFAT >= :DTINICIAL
      AND C.DTFAT < :DTFINAL + 1
)
"""

SQL_DIM_PRODUTO_PERIODO = """
SELECT
    PR.CODPROD       AS COD_PRODUTO,
    PR.DESCRICAO     AS PRODUTO,
    PR.EMBALAGEM,
    PR.UNIDADE,
    PR.CODFAB        AS COD_FABRICANTE,
    PR.CODAUXILIAR   AS COD_BARRAS,
    PR.CODEPTO,
    D.DESCRICAO      AS DEPARTAMENTO,
    PR.CODSEC,
    S.DESCRICAO      AS SECAO,
    PR.CODCATEGORIA,
    CAT.CATEGORIA,
    PR.CODMARCA,
    M.MARCA,
    PR.CODFORNEC,
    F.FORNECEDOR
FROM PCPRODUT PR
LEFT JOIN PCDEPTO D ON D.CODEPTO = PR.CODEPTO
LEFT JOIN PCSECAO S ON S.CODSEC = PR.CODSEC
LEFT JOIN PCCATEGORIA CAT ON CAT.CODSEC = PR.CODSEC AND CAT.CODCATEGORIA = PR.CODCATEGORIA
LEFT JOIN PCMARCA M ON M.CODMARCA = PR.CODMARCA
LEFT JOIN PCFORNEC F ON F.CODFORNEC = PR.CODFORNEC
WHERE PR.CODPROD IN (
    SELECT DISTINCT I.CODPROD
    FROM PCPEDI I
    INNER JOIN PCPEDC C ON C.NUMPED = I.NUMPED
    WHERE C.DTCANCEL IS NULL
      AND C.POSICAO = 'F'
      AND C.DTFAT >= :DTINICIAL
      AND C.DTFAT < :DTFINAL + 1
)
"""

# ============================================================
# CONTAGEM DE VALIDAÇÃO — nº de linhas do fato diário no período.
# Usada na "prova de volume" (Fase 1) antes de carregar tudo.
# ============================================================
SQL_COUNT_FATO_DIARIO = """
SELECT COUNT(*) FROM (
""" + SQL_SNAPSHOT_FATO_DIARIO + """
)
"""
