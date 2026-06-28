const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const NUM0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

export const formatarMoeda = (v: number | null | undefined) => BRL.format(Number(v ?? 0));
export const formatarNumero = (v: number | null | undefined) => NUM0.format(Number(v ?? 0));
