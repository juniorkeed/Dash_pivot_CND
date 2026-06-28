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
    <main style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
      <form onSubmit={entrar} style={card}>
        <h1 style={{ marginTop: 0, fontSize: 20 }}>📊 Dash Pivot CND</h1>
        <p style={{ color: "#666", marginTop: 0, fontSize: 14 }}>Entre para ver o painel</p>
        <label style={lbl}>E-mail</label>
        <input style={inp} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label style={lbl}>Senha</label>
        <input style={inp} type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required />
        {erro && <p style={{ color: "#c0392b", fontSize: 13 }}>{erro}</p>}
        <button style={btn} disabled={carregando}>
          {carregando ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}

const card: React.CSSProperties = {
  background: "#fff",
  padding: 32,
  borderRadius: 12,
  width: 340,
  boxShadow: "0 1px 3px rgba(0,0,0,.1)",
};
const lbl: React.CSSProperties = { display: "block", fontSize: 13, marginTop: 12, marginBottom: 4, color: "#333" };
const inp: React.CSSProperties = { width: "100%", padding: "8px 10px", border: "1px solid #ccc", borderRadius: 6, fontSize: 14 };
const btn: React.CSSProperties = { width: "100%", marginTop: 20, padding: 10, background: "#2563eb", color: "#fff", border: 0, borderRadius: 6, fontSize: 15, cursor: "pointer" };
