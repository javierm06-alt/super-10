/**
 * Script para crear el workflow "Tienda Inteligente - API Catalogo" en n8n
 * Ejecutar: node create_workflow.js
 */

const API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NmEwNWU3Mi1lYTcwLTQxNWItODkzZS1iZTdkZmRmNDZmZjQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiZGJiY2MzODYtODYxOS00NGI3LTg4NmItODYyNDRmNjFhYjQzIiwiaWF0IjoxNzcxMzQ4NTI3fQ.xSixlqjqIWFnNZ67Q-4FczSjQymKjMOlicg2mZZnKzQ";
const BASE_URL = "http://localhost:5678";

const SUPABASE_URL = "https://dqrhqzdfzhkqpgawgjga.supabase.co";
const SUPABASE_KEY = "sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ";

const workflow = {
    name: "Tienda Inteligente - API Catalogo",
    nodes: [
        {
            parameters: {
                path: "tienda-catalogo",
                httpMethod: "POST",
                responseMode: "responseNode",
                options: {}
            },
            type: "n8n-nodes-base.webhook",
            typeVersion: 2.1,
            position: [-600, 0],
            name: "Webhook",
            webhookId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        },
        {
            parameters: {
                url: `${SUPABASE_URL}/rest/v1/catalogo_productos?select=*`,
                sendHeaders: true,
                headerParameters: {
                    parameters: [
                        { name: "apikey", value: SUPABASE_KEY },
                        { name: "Authorization", value: `Bearer ${SUPABASE_KEY}` }
                    ]
                },
                options: {}
            },
            type: "n8n-nodes-base.httpRequest",
            typeVersion: 4.4,
            position: [-350, 0],
            name: "Traer Catalogo"
        },
        {
            parameters: {
                url: `=${SUPABASE_URL}/rest/v1/historial_compras?select=producto_id,cantidad,fecha_compra&user_id=eq.{{ $('Webhook').item.json.body.user_id }}`,
                sendHeaders: true,
                headerParameters: {
                    parameters: [
                        { name: "apikey", value: SUPABASE_KEY },
                        { name: "Authorization", value: `Bearer ${SUPABASE_KEY}` }
                    ]
                },
                options: {}
            },
            type: "n8n-nodes-base.httpRequest",
            typeVersion: 4.4,
            position: [-100, 0],
            name: "Traer Historial"
        },
        {
            parameters: {
                jsCode: `// ================================================================
// PERSONALIZAR: Divide catálogo en Favoritos vs Explorar
// ================================================================
const catalogoItems = $('Traer Catalogo').all();
const historialItems = $('Traer Historial').all();

const catalogo = catalogoItems.map(i => i.json);
const historial = historialItems.map(i => i.json);

// Deduplicar por ID
const seen = new Set();
const catalogoLimpio = catalogo.filter(p => {
  if (!p.id || seen.has(p.id)) return false;
  seen.add(p.id);
  return true;
});

// Map de productos comprados
const compradosMap = new Map();
for (const h of historial) {
  if (h.producto_id) compradosMap.set(h.producto_id, h.fecha_compra || '');
}

// Dividir
const favoritos = [];
const explorar = [];

for (const prod of catalogoLimpio) {
  if (compradosMap.has(prod.id)) {
    favoritos.push({ ...prod, ultima_compra: compradosMap.get(prod.id), es_favorito: true });
  } else {
    explorar.push({ ...prod, es_favorito: false });
  }
}

// Saludo proactivo
let saludo = 'Bienvenido a tu tienda. Descubre productos seleccionados para ti.';
if (favoritos.length > 0) {
  saludo = 'Veo que te toca surtir ' + favoritos[0].nombre + ', la agregamos de una vez?';
}

return [{ json: { saludo, favoritos, explorar, total_favoritos: favoritos.length, total_explorar: explorar.length } }];`
            },
            type: "n8n-nodes-base.code",
            typeVersion: 2,
            position: [150, 0],
            name: "Personalizar Catalogo"
        },
        {
            parameters: {
                respondWith: "json",
                responseBody: "={{ JSON.stringify($json) }}",
                options: {}
            },
            type: "n8n-nodes-base.respondToWebhook",
            typeVersion: 1.1,
            position: [400, 0],
            name: "Responder"
        }
    ],
    connections: {
        "Webhook": { main: [[{ node: "Traer Catalogo", type: "main", index: 0 }]] },
        "Traer Catalogo": { main: [[{ node: "Traer Historial", type: "main", index: 0 }]] },
        "Traer Historial": { main: [[{ node: "Personalizar Catalogo", type: "main", index: 0 }]] },
        "Personalizar Catalogo": { main: [[{ node: "Responder", type: "main", index: 0 }]] }
    },
    settings: {
        executionOrder: "v1"
    }
};

async function main() {
    try {
        const response = await fetch(`${BASE_URL}/api/v1/workflows`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-N8N-API-KEY": API_KEY
            },
            body: JSON.stringify(workflow)
        });

        const text = await response.text();
        console.log(`Status: ${response.status}`);

        if (!response.ok) {
            console.log("ERROR BODY:", text);
        } else {
            const data = JSON.parse(text);
            console.log("Workflow created! ID:", data.id);
            console.log("Name:", data.name);

            // Activar el workflow
            const activateRes = await fetch(`${BASE_URL}/api/v1/workflows/${data.id}/activate`, {
                method: "POST",
                headers: { "X-N8N-API-KEY": API_KEY }
            });
            if (activateRes.ok) {
                console.log("Workflow ACTIVADO!");
                console.log(`Webhook URL: ${BASE_URL}/webhook/tienda-catalogo`);
            } else {
                console.log("Error al activar:", await activateRes.text());
            }
        }
    } catch (e) {
        console.error("Error:", e.message);
    }
}

main();
