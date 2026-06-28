/** Espelha a whitelist da RPC pivot_vendas (Supabase). */

export type DimKey =
  | "ano"
  | "mes"
  | "ano_mes"
  | "trimestre"
  | "filial"
  | "vendedor"
  | "cliente"
  | "cidade"
  | "uf"
  | "produto"
  | "marca"
  | "fornecedor"
  | "departamento"
  | "secao"
  | "categoria";

export type MeasureKey = "qt" | "vl_total" | "vl_custo_total" | "lucro_bruto";

export const DIMENSOES: { key: DimKey; label: string }[] = [
  { key: "ano_mes", label: "Ano-Mês" },
  { key: "ano", label: "Ano" },
  { key: "mes", label: "Mês" },
  { key: "trimestre", label: "Trimestre" },
  { key: "marca", label: "Marca" },
  { key: "fornecedor", label: "Fornecedor" },
  { key: "departamento", label: "Departamento" },
  { key: "secao", label: "Seção" },
  { key: "categoria", label: "Categoria" },
  { key: "produto", label: "Produto" },
  { key: "vendedor", label: "Vendedor" },
  { key: "cliente", label: "Cliente" },
  { key: "cidade", label: "Cidade" },
  { key: "uf", label: "UF" },
  { key: "filial", label: "Filial" },
];

export const MEDIDAS: { key: MeasureKey; label: string; format: "currency" | "number" }[] = [
  { key: "vl_total", label: "Valor Total", format: "currency" },
  { key: "lucro_bruto", label: "Lucro Bruto", format: "currency" },
  { key: "vl_custo_total", label: "Custo", format: "currency" },
  { key: "qt", label: "Quantidade", format: "number" },
];
