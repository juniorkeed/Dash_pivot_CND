"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setCarregando(true);
    setErro(null);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password: senha });
    if (error) {
      setErro("E-mail ou senha inválidos.");
      setCarregando(false);
      return;
    }
    router.push("/pivot");
    router.refresh();
  }

  return (
    <main style={{ display: "grid", placeItems: "center", minHeight: "100vh", background: "var(--bg)" }}>
      <form onSubmit={entrar} style={card}>
        <div style={faixa} />
        <div style={{ padding: "38px 40px 40px" }}>
          {/* coloque LOGO.png em /public */}
          <img src="/LOGO.png" alt="CND" style={{ height: 34, width: "auto", display: "block", marginBottom: 24 }} />

          <h1 style={titulo}>Bem-vindo de volta</h1>
          <p style={sub}>Entre para acessar a matriz de vendas</p>

          <label style={lbl}>E-mail</label>
          <input
            style={inp}
            type="email"
            placeholder="nome@empresa.com.br"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label style={{ ...lbl, marginTop: 16 }}>Senha</label>
          <input
            style={inp}
            type="password"
            placeholder="••••••••••"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />

          {erro && <p style={{ color: "#c0392b", fontSize: 13, marginTop: 14 }}>{erro}</p>}

          <button style={btn} disabled={carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </button>
          <p style={link}>Esqueceu a senha?</p>
        </div>
      </form>
    </main>
  );
}

const card: React.CSSProperties = {
  background: "var(--surface-2)",
  border: "1px solid var(--border)",
  borderRadius: 16,
  width: 420,
  overflow: "hidden",
  boxShadow: "0 12px 40px -24px rgba(0,0,0,.22)",
};
const faixa: React.CSSProperties = { height: 5, background: "var(--accent)" };
const titulo: React.CSSProperties = {
  margin: 0,
  font: "600 22px var(--font-display), sans-serif",
  color: "var(--text)",
  letterSpacing: "-.02em",
};
const sub: React.CSSProperties = {
  margin: "6px 0 0",
  font: "400 14px var(--font-sans), sans-serif",
  color: "var(--muted)",
};
const lbl: React.CSSProperties = {
  display: "block",
  font: "600 11px var(--font-sans), sans-serif",
  letterSpacing: ".05em",
  textTransform: "uppercase",
  color: "var(--muted-2)",
  margin: "26px 0 7px",
};
const inp: React.CSSProperties = {
  width: "100%",
  height: 44,
  padding: "0 14px",
  background: "var(--surface)",
  border: "1px solid #dcd8cf",
  borderRadius: 10,
  fontSize: 14,
  fontFamily: "var(--font-sans), sans-serif",
  color: "var(--text)",
};
const btn: React.CSSProperties = {
  width: "100%",
  height: 46,
  marginTop: 24,
  background: "var(--accent)",
  color: "#fff",
  border: 0,
  borderRadius: 11,
  font: "600 14.5px var(--font-sans), sans-serif",
  cursor: "pointer",
};
const link: React.CSSProperties = {
  textAlign: "center",
  font: "500 12.5px var(--font-sans), sans-serif",
  color: "var(--muted-2)",
  marginTop: 16,
  marginBottom: 0,
};
