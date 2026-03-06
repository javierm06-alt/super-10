// ============================================================
// fix_bugs_tienda.js — Corrige bugs conocidos del workflow Tienda
//
// Bug 1: Nodo "Traer Historial" — URL empieza con = en vez de ={{ }}
//        Causa: el script create_workflow.js interpoló ${SUPABASE_URL}
//        en un template literal, resultando en =https://... (inválido)
//        Fix: convertir a expresión n8n completa ={{ '...' + $(...) }}
//
// Bug 2: app.js userId — YA ESTABA CORREGIDO (demo_user_01 ✅)
// ============================================================

const http = require('http');
const fs   = require('fs');
const path = require('path');

const N8N_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NmEwNWU3Mi1lYTcwLTQxNWItODkzZS1iZTdkZmRmNDZmZjQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiZGJiY2MzODYtODYxOS00NGI3LTg4NmItODYyNDRmNjFhYjQzIiwiaWF0IjoxNzcxMzQ4NTI3fQ.xSixlqjqIWFnNZ67Q-4FczSjQymKjMOlicg2mZZnKzQ';
const WF_ID = '7ZBpMV18Foo9MrYu';

// URL correcta como expresión n8n (sin = suelto al inicio)
// ={{ 'base_url' + $('Webhook').item.json.body.user_id }}
const SUPABASE_BASE = 'https://dqrhqzdfzhkqpgawgjga.supabase.co';
const URL_HISTORIAL_CORRECTA =
  "={{ '" +
  SUPABASE_BASE +
  "/rest/v1/historial_compras?select=producto_id,cantidad,fecha_compra&user_id=eq.' + $('Webhook').item.json.body.user_id }}";

function apiGet(path) {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: 'localhost', port: 5678,
      path: '/api/v1' + path, method: 'GET',
      headers: { 'X-N8N-API-KEY': N8N_KEY }
    }, res => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => { try { resolve({ s: res.statusCode, b: JSON.parse(d) }); } catch(e) { resolve({ s: res.statusCode, b: d }); } });
    });
    req.on('error', reject); req.end();
  });
}

function apiPut(path, body) {
  const bodyStr = JSON.stringify(body);
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: 'localhost', port: 5678,
      path: '/api/v1' + path, method: 'PUT',
      headers: { 'X-N8N-API-KEY': N8N_KEY, 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(bodyStr) }
    }, res => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => { try { resolve({ s: res.statusCode, b: JSON.parse(d) }); } catch(e) { resolve({ s: res.statusCode, b: d }); } });
    });
    req.on('error', reject); req.write(bodyStr); req.end();
  });
}

async function main() {
  // ── BUG 2: verificar app.js ──────────────────────────────
  const appJsPath = path.join(__dirname, '..', 'app.js');
  const appJs = fs.readFileSync(appJsPath, 'utf8');
  const userId = (appJs.match(/userId:\s*"([^"]+)"/) || [])[1];
  console.log('=== BUG 2: app.js userId ===');
  console.log('  userId actual:', userId);
  if (userId === 'demo_user_01') {
    console.log('  OK — ya estaba corregido, no se toca.');
  } else {
    // Por si acaso corregirlo
    const fixed = appJs.replace(/userId:\s*"[^"]+"/, 'userId: "demo_user_01"');
    fs.writeFileSync(appJsPath, fixed, 'utf8');
    console.log('  CORREGIDO: cambiado a demo_user_01');
  }

  // ── BUG 1: URL del nodo Traer Historial ──────────────────
  console.log('\n=== BUG 1: Traer Historial URL (n8n API) ===');
  const { s: getS, b: wf } = await apiGet('/workflows/' + WF_ID);
  if (getS !== 200) { console.error('  GET falló HTTP', getS); return; }
  console.log('  GET ok —', wf.nodes.length, 'nodos | nombre:', wf.name);

  const nd = wf.nodes.find(x => x.name === 'Traer Historial');
  if (!nd) { console.error('  ERROR: nodo Traer Historial no encontrado'); return; }

  const urlAntes = nd.parameters.url;
  console.log('  URL antes:  ', urlAntes);

  if (!urlAntes.startsWith('=') || urlAntes.startsWith('={{')) {
    console.log('  OK — URL ya está en formato correcto, no se toca.');
  } else {
    nd.parameters.url = URL_HISTORIAL_CORRECTA;
    console.log('  URL después:', nd.parameters.url);

    const { s: putS, b: putR } = await apiPut('/workflows/' + WF_ID, {
      name: wf.name,
      nodes: wf.nodes,
      connections: wf.connections,
      settings: { executionOrder: 'v1' }
    });

    console.log('  PUT HTTP', putS);
    if (putS === 200 || putS === 201) {
      console.log('  PUT exitoso.');
    } else {
      console.error('  PUT falló:', JSON.stringify(putR).substring(0, 400));
      return;
    }
  }

  // ── VERIFICACIÓN FINAL ───────────────────────────────────
  console.log('\n=== VERIFICACIÓN FINAL (GET independiente) ===');
  const { s: vS, b: vWf } = await apiGet('/workflows/' + WF_ID);
  if (vS !== 200) { console.error('  GET verificación falló'); return; }

  const ndV = vWf.nodes.find(x => x.name === 'Traer Historial');
  const urlFinal = ndV && ndV.parameters && ndV.parameters.url;
  const bug1Ok = urlFinal && urlFinal.startsWith('={{');

  const appJsFinal = fs.readFileSync(appJsPath, 'utf8');
  const userIdFinal = (appJsFinal.match(/userId:\s*"([^"]+)"/) || [])[1];
  const bug2Ok = userIdFinal === 'demo_user_01';

  console.log('  Bug 1 — URL Traer Historial: ' + (bug1Ok ? 'OK' : 'FALLO'));
  console.log('    ' + urlFinal);
  console.log('  Bug 2 — app.js userId:       ' + (bug2Ok ? 'OK (' + userIdFinal + ')' : 'FALLO (' + userIdFinal + ')'));
  console.log('\n' + (bug1Ok && bug2Ok ? 'Ambos bugs corregidos.' : 'REVISAR — alguno falló.'));
}

main().catch(e => console.error('FATAL:', e.message));
