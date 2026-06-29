"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import "react-pivottable/pivottable.css";
import "./pivot-theme.css";
import { aggregatorTemplates, numberFormat } from "react-pivottable/Utilities";
import TableRenderers from "react-pivottable/TableRenderers";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { formatarMoeda, formatarNumero } from "@/lib/format";
import { DIMENSOES, MEDIDAS, type DimKey, type MeasureKey } from "@/lib/pivotConfig";

// Só o renderer (sem o painel de arrastar) — controlamos eixos via seletores.
const PivotTable = dynamic(() => import("react-pivottable/PivotTable"), { ssr: false });

const keyToLabel: Record<string, string> = {};
DIMENSOES.forEach((d) => (keyToLabel[d.key] = d.label));
MEDIDAS.forEach((m) => (keyToLabel[m.key] = m.label));

// Agregadores com formatação pt-BR
const fmtMoeda = numberFormat({ digitsAfterDecimal: 2, thousandsSep: ".", decimalSep: ",", prefix: "R$ " });
const fmtNum = numberFormat({ digitsAfterDecimal: 0, thousandsSep: ".", decimalSep: "," });
const aggregators = {
  "Soma (R$)": aggregatorTemplates.sum(fmtMoeda),
  "Soma (qtd)": aggregatorTemplates.sum(fmtNum),
};

export default function PivotBoard({ userEmail }: { userEmail: string }) {
  const router = useRouter();
  const [dtIni, setDtIni] = useState("2025-02-01");
  const [dtFim, setDtFim] = useState("2026-06-28");
  const [linhas, setLinhas] = useState<DimKey[]>(["marca"]);
  const [colunas, setColunas] = useState<DimKey[]>(["ano_mes"]);
  const [medida, setMedida] = useState<MeasureKey>("vl_total");
  const [dados, setDados] = useState<Record<string, unknown>[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const dims = useMemo(
    () => Array.from(new Set<DimKey>([...linhas, ...colunas])),
    [linhas, colunas],
  );

  const buscar = useCallback(async () => {
    if (dims.length === 0) {
      setDados([]);
      return;
    }
    setCarregando(true);
    setErro(null);
    const supabase = createClient();
    const { data, error } = await supabase.rpc("pivot_vendas", {
      p_dims: dims,
      p_measures: [medida],
      p_dt_ini: dtIni,
      p_dt_fim: dtFim,
    });
    if (error) {
      setErro(error.message);
      setDados([]);
      setCarregando(false);
      return;
    }
    const linhasDados = (data ?? []).map((row: Record<string, unknown>) => {
      const obj: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(row)) obj[keyToLabel[k] ?? k] = v;
      return obj;
    });
    setDados(linhasDados);
    setCarregando(false);
  }, [dims, medida, dtIni, dtFim]);

  useEffect(() => {
    buscar();
  }, [buscar]);

  async function sair() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  function porLinha(key: DimKey) {
    setColunas((prev) => prev.filter((k) => k !== key));
    setLinhas((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }
  function porColuna(key: DimKey) {
    setLinhas((prev) => prev.filter((k) => k !== key));
    setColunas((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

  const medidaInfo = MEDIDAS.find((m) => m.key === medida)!;
  const aggName = medidaInfo.format === "currency" ? "Soma (R$)" : "Soma (qtd)";
  const medidaLabel = keyToLabel[medida];

  // KPIs calculados a partir dos dados realmente carregados
  const totalGeral = useMemo(
    () => dados.reduce((s, r) => s + Number(r[medidaLabel] ?? 0), 0),
    [dados, medidaLabel],
  );
  const registros = dados.length;
  const media = registros ? totalGeral / registros : 0;
  const fmtMedida = (v: number) =>
    medidaInfo.format === "currency" ? formatarMoeda(v) : formatarNumero(v);

  const kpis = [
    { label: `${medidaInfo.label} (total)`, value: fmtMedida(totalGeral) },
    { label: "Combinações", value: formatarNumero(registros) },
    { label: "Média por combinação", value: fmtMedida(media) },
  ];

  return (
    <div style={pagina}>
      {/* ---------- Topbar ---------- */}
      <header style={topbar}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {/* coloque LOGO.png em /public */}
          <img src="/LOGO.png" alt="CND" style={{ height: 26, width: "auto", display: "block" }} />
          <span style={{ width: 1, height: 24, background: "var(--border)" }} />
          <span style={{ font: "600 16px var(--font-display), sans-serif", color: "var(--text)", letterSpacing: "-.01em" }}>
            Matriz de Vendas
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>{userEmail}</span>
          <button onClick={sair} style={btnSair}>Sair</button>
          <span style={avatar}>{(userEmail[0] ?? "U").toUpperCase()}</span>
        </div>
      </header>

      <main style={{ padding: "20px 24px 32px", maxWidth: 1320, margin: "0 auto" }}>
        {/* ---------- KPIs ---------- */}
        <div style={{ display: "flex", gap: 12, marginBottom: 18 }}>
          {kpis.map((k) => (
            <div key={k.label} style={kpiCard}>
              <div style={kpiLabel}>{k.label}</div>
              <div style={kpiValue}>{carregando ? "—" : k.value}</div>
            </div>
          ))}
        </div>

        {/* ---------- Painel de controles ---------- */}
        <section style={painel}>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
            <div>
              <label style={lbl}>De</label>
              <input style={inp} type="date" value={dtIni} onChange={(e) => setDtIni(e.target.value)} />
            </div>
            <div>
              <label style={lbl}>Até</label>
              <input style={inp} type="date" value={dtFim} onChange={(e) => setDtFim(e.target.value)} />
            </div>
            <div>
              <label style={lbl}>Medida</label>
              <div style={segWrap}>
                {MEDIDAS.map((m) => (
                  <button key={m.key} onClick={() => setMedida(m.key)} style={seg(m.key === medida)}>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <label style={lbl}>Linhas</label>
          <div style={grupoChips}>
            {DIMENSOES.map((d) => (
              <button key={d.key} onClick={() => porLinha(d.key)} style={chip(linhas.includes(d.key))}>
                {d.label}
              </button>
            ))}
          </div>

          <label style={{ ...lbl, marginTop: 12 }}>Colunas</label>
          <div style={grupoChips}>
            {DIMENSOES.map((d) => (
              <button key={d.key} onClick={() => porColuna(d.key)} style={chip(colunas.includes(d.key))}>
                {d.label}
              </button>
            ))}
          </div>
        </section>

        {/* ---------- Estados ---------- */}
        {erro && <p style={aviso("#c0392b")}>Erro: {erro}</p>}
        {dims.length === 0 && <p style={aviso("var(--muted)")}>Selecione ao menos uma dimensão.</p>}

        {/* ---------- Matriz ---------- */}
        <div style={{ position: "relative" }}>
          <div style={matrizHead}>
            <span style={{ font: "600 13px var(--font-display), sans-serif", color: "var(--text)" }}>
              {linhas.map((k) => keyToLabel[k]).join(" · ") || "—"}{" "}
              <span style={{ color: "#c4beb4" }}>×</span>{" "}
              {colunas.map((k) => keyToLabel[k]).join(" · ") || "—"}
            </span>
            <span style={{ font: "500 11px var(--font-mono), monospace", color: "var(--muted-2)" }}>
              {carregando ? "carregando…" : `${registros} combinações · ${medidaInfo.label}`}
            </span>
          </div>
          <div className="pivot-surface">
            <PivotTable
              data={dados}
              rows={linhas.map((k) => keyToLabel[k])}
              cols={colunas.map((k) => keyToLabel[k])}
              vals={[keyToLabel[medida]]}
              aggregatorName={aggName}
              aggregators={aggregators}
              renderers={TableRenderers}
              rendererName="Table"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

/* ===================== estilos (Opção A) ===================== */
const pagina: React.CSSProperties = { minHeight: "100vh", background: "var(--bg)" };
const topbar: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "16px 24px",
  background: "var(--surface)",
  borderBottom: "1px solid var(--border)",
};
const avatar: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: "50%",
  background: "var(--text)",
  color: "#fff",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  font: "600 12px var(--font-display), sans-serif",
};
const btnSair: React.CSSProperties = {
  padding: "6px 12px",
  border: "1px solid var(--border)",
  background: "var(--surface)",
  borderRadius: 8,
  fontSize: 12.5,
  color: "var(--text)",
  cursor: "pointer",
};
const kpiCard: React.CSSProperties = {
  flex: 1,
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 13,
  padding: "14px 16px",
};
const kpiLabel: React.CSSProperties = {
  font: "600 10.5px var(--font-sans), sans-serif",
  letterSpacing: ".06em",
  textTransform: "uppercase",
  color: "var(--muted-2)",
};
const kpiValue: React.CSSProperties = {
  font: "600 23px/1.1 var(--font-display), sans-serif",
  color: "var(--text)",
  marginTop: 10,
  fontVariantNumeric: "tabular-nums",
  letterSpacing: "-.01em",
};
const painel: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  padding: 16,
  borderRadius: 13,
  marginBottom: 18,
};
const lbl: React.CSSProperties = {
  display: "block",
  font: "600 10.5px var(--font-sans), sans-serif",
  letterSpacing: ".06em",
  textTransform: "uppercase",
  color: "var(--muted-2)",
  marginBottom: 7,
};
const inp: React.CSSProperties = {
  padding: "8px 11px",
  border: "1px solid #dcd8cf",
  borderRadius: 9,
  fontSize: 14,
  fontFamily: "var(--font-sans), sans-serif",
  color: "var(--text)",
  background: "var(--surface)",
};
const segWrap: React.CSSProperties = {
  display: "inline-flex",
  background: "#f4f2ed",
  border: "1px solid var(--border)",
  borderRadius: 9,
  padding: 3,
  gap: 2,
};
const seg = (on: boolean): React.CSSProperties => ({
  font: "600 12.5px var(--font-sans), sans-serif",
  color: on ? "#fff" : "var(--muted)",
  background: on ? "var(--accent)" : "transparent",
  padding: "6px 13px",
  borderRadius: 7,
  border: 0,
  cursor: "pointer",
});
const grupoChips: React.CSSProperties = { display: "flex", flexWrap: "wrap", gap: 6 };
const chip = (on: boolean): React.CSSProperties => ({
  font: "600 12.5px var(--font-sans), sans-serif",
  padding: "5px 11px",
  border: "1px solid",
  borderColor: on ? "var(--accent)" : "var(--border)",
  background: on ? "var(--accent)" : "var(--surface)",
  color: on ? "#fff" : "var(--muted)",
  borderRadius: 8,
  cursor: "pointer",
});
const matrizHead: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 4px 10px",
};
const aviso = (cor: string): React.CSSProperties => ({ color: cor, fontSize: 13.5, margin: "4px 0 14px" });
