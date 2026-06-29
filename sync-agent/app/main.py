"""
API do Sync Agent (FastAPI).

Endpoints:
- GET  /         -> página simples com botões para atualizar os dados
- GET  /health   -> testa a conexão Oracle
- POST /sync     -> dispara a carga Oracle -> Supabase (protegido por x-sync-token)

Roda on-premise, com bind em 127.0.0.1 (ver docker-compose). Sem agendador:
a atualização é sempre manual (botão na página ou chamada ao /sync).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import Body, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from app.config import settings
from app.logging_conf import get_logger
from app.oracle.connection import test_connection
from app.pipeline import sync_window

logger = get_logger(__name__)
app = FastAPI(title="Sync Agent — Central Norte", docs_url="/api-docs")

# Início do histórico disponível no ERP (vendas faturadas).
HISTORICO_INICIO = date(2025, 2, 1)


def _parse(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


@app.get("/health")
def health():
    ok, msg = test_connection()
    return {"oracle_ok": ok, "mensagem": msg}


@app.post("/sync")
def sync(payload: dict = Body(default={}), x_sync_token: str = Header(default="")):
    if settings.sync_token and x_sync_token != settings.sync_token:
        raise HTTPException(status_code=401, detail="Token inválido.")

    hoje = date.today()
    dt_to = _parse(payload["to"]) if payload.get("to") else hoje
    if payload.get("from"):
        dt_from = _parse(payload["from"])
    elif payload.get("full"):
        dt_from = HISTORICO_INICIO
    else:
        dt_from = dt_to - timedelta(days=settings.sync_default_days)

    logger.info("POST /sync solicitado: %s a %s", dt_from, dt_to)
    try:
        resultado = sync_window(dt_from, dt_to)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao sincronizar")
        raise HTTPException(status_code=500, detail=str(exc))

    return {"ok": True, "de": str(dt_from), "ate": str(dt_to), "resultado": resultado}


@app.get("/", response_class=HTMLResponse)
def home():
    return _PAGINA.replace("__TOKEN__", settings.sync_token or "")


_PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atualização de Dados — Central Norte</title>
<style>
  body { font-family: system-ui, "Segoe UI", Roboto, sans-serif; background:#f6f7f9; color:#1a1a1a; display:grid; place-items:center; min-height:100vh; margin:0; }
  .card { background:#fff; padding:32px; border-radius:14px; box-shadow:0 1px 4px rgba(0,0,0,.1); width:460px; max-width:92vw; }
  h1 { font-size:20px; margin:0 0 6px; }
  p.sub { color:#666; margin:0 0 20px; font-size:14px; }
  button { width:100%; padding:12px; margin:6px 0; border:0; border-radius:8px; font-size:15px; cursor:pointer; }
  .primary { background:#2563eb; color:#fff; }
  .ghost { background:#fff; color:#2563eb; border:1px solid #2563eb; }
  button:disabled { opacity:.5; cursor:default; }
  pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; font-size:12px; white-space:pre-wrap; max-height:240px; overflow:auto; margin-top:16px; }
  .ok { color:#16a34a; } .err { color:#dc2626; }
</style>
</head>
<body>
  <div class="card">
    <h1>🔄 Atualização de Dados</h1>
    <p class="sub">Puxa as vendas do Oracle e envia para o painel online (Supabase). Pode levar alguns segundos.</p>
    <button class="primary" id="b1" onclick="sync(false)">Atualizar últimos dias (rápido)</button>
    <button class="ghost"  id="b2" onclick="sync(true)">Atualizar histórico completo</button>
    <pre id="status" style="display:none"></pre>
  </div>
<script>
  const TOKEN = "__TOKEN__";
  async function sync(full) {
    const s = document.getElementById('status');
    const btns = document.querySelectorAll('button');
    btns.forEach(b => b.disabled = true);
    s.style.display = 'block';
    s.className = '';
    s.textContent = 'Atualizando... aguarde.';
    const t0 = Date.now();
    try {
      const r = await fetch('/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-sync-token': TOKEN },
        body: JSON.stringify(full ? { full: true } : {})
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
      const seg = ((Date.now() - t0) / 1000).toFixed(1);
      s.className = 'ok';
      s.textContent = 'Concluído em ' + seg + 's  (período ' + j.de + ' a ' + j.ate + ')\\n\\n'
                    + JSON.stringify(j.resultado, null, 2);
    } catch (e) {
      s.className = 'err';
      s.textContent = 'Erro: ' + e.message;
    } finally {
      btns.forEach(b => b.disabled = false);
    }
  }
</script>
</body>
</html>"""
