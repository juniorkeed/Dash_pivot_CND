"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import "react-pivottable/pivottable.css";
import { aggregatorTemplates, numberFormat } from "react-pivottable/Utilities";
import TableRenderers from "react-pivottable/TableRenderers";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
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

  return (
    <div style={{ padding: 20 }}>
      <header style={cab}>
        <h1 style={{ fontSize: 20, margin: 0 }}>📊 Matriz de Vendas</h1>
        <div style={{ fontSize: 13, color: "#666", display: "flex", gap: 12, alignItems: "center" }}>
          <span>{userEmail}</span>
          <button onClick={sair} style={btnSair}>Sair</button>
        </div>
      </header>

      <section style={painel}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
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
            <select style={inp} value={medida} onChange={(e) => setMedida(e.target.value as MeasureKey)}>
              {MEDIDAS.map((m) => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
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

        <label style={{ ...lbl, marginTop: 10 }}>Colunas</label>
        <div style={grupoChips}>
          {DIMENSOES.map((d) => (
            <button key={d.key} onClick={() => porColuna(d.key)} style={chip(colunas.includes(d.key), "#0d9488")}>
              {d.label}
            </button>
          ))}
        </div>
      </section>

      {erro && <p style={{ color: "#c0392b" }}>Erro: {erro}</p>}
      {carregando && <p style={{ color: "#666" }}>Carregando…</p>}
      {dims.length === 0 && <p style={{ color: "#666" }}>Selecione ao menos uma dimensão.</p>}

      <div style={{ background: "#fff", padding: 12, borderRadius: 8, overflow: "auto" }}>
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
  );
}

const cab: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 };
const painel: React.CSSProperties = { background: "#fff", padding: 16, borderRadius: 8, marginBottom: 16 };
const lbl: React.CSSProperties = { display: "block", fontSize: 12, color: "#555", marginBottom: 4 };
const inp: React.CSSProperties = { padding: "7px 9px", border: "1px solid #ccc", borderRadius: 6, fontSize: 14 };
const grupoChips: React.CSSProperties = { display: "flex", flexWrap: "wrap", gap: 6 };
const btnSair: React.CSSProperties = { padding: "4px 10px", border: "1px solid #ccc", background: "#fff", borderRadius: 6, fontSize: 12, cursor: "pointer" };
const chip = (on: boolean, cor = "#2563eb"): React.CSSProperties => ({
  padding: "5px 10px",
  border: "1px solid",
  borderColor: on ? cor : "#ccc",
  background: on ? cor : "#fff",
  color: on ? "#fff" : "#333",
  borderRadius: 16,
  fontSize: 13,
  cursor: "pointer",
});
