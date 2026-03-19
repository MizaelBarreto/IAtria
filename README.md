# IAtria

Sistema de triagem inteligente de leads com:

- FastAPI + LangGraph no backend
- Groq como provedor de IA
- Supabase para persistencia de leads e metricas
- n8n para orquestracao
- Next.js + Recharts para dashboard

## Estrutura

- [agente_triagem.py](/c:/Users/mizae/Documents/IAtria/agente_triagem.py): entrypoint do backend
- [backend/main.py](/c:/Users/mizae/Documents/IAtria/backend/main.py): API FastAPI
- [backend/graph.py](/c:/Users/mizae/Documents/IAtria/backend/graph.py): grafo LangGraph
- [backend/llm.py](/c:/Users/mizae/Documents/IAtria/backend/llm.py): integracao com Groq
- [backend/supabase.py](/c:/Users/mizae/Documents/IAtria/backend/supabase.py): persistencia de metricas no Supabase
- [sql/create_lead_metrics.sql](/c:/Users/mizae/Documents/IAtria/sql/create_lead_metrics.sql): SQL das tabelas `lead_records` e `lead_metrics`
- [n8n/workflow_leads.json](/c:/Users/mizae/Documents/IAtria/n8n/workflow_leads.json): workflow principal do n8n
- [n8n/workflow_triagem_leads.json](/c:/Users/mizae/Documents/IAtria/n8n/workflow_triagem_leads.json): copia equivalente do workflow
- [payloads_teste.json](/c:/Users/mizae/Documents/IAtria/payloads_teste.json): 5 payloads de teste
- [scripts/verify_supabase_insert.py](/c:/Users/mizae/Documents/IAtria/scripts/verify_supabase_insert.py): simulacao local do fluxo do n8n
- [app/dashboard/page.tsx](/c:/Users/mizae/Documents/IAtria/app/dashboard/page.tsx): dashboard
- [app/api/metrics/route.ts](/c:/Users/mizae/Documents/IAtria/app/api/metrics/route.ts): agregacao das metricas para o dashboard
- [vercel.json](/c:/Users/mizae/Documents/IAtria/vercel.json): configuracao do deploy no Vercel

## Variaveis de ambiente

Baseie [`.env`](/c:/Users/mizae/Documents/IAtria/.env) em [`.env.example`](/c:/Users/mizae/Documents/IAtria/.env.example):

```env
SUPABASE_URL=https://fzejfxcdgvlemsclqrku.supabase.co
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
TRIAGEM_API_BASE_URL=http://127.0.0.1:8000
```

## Banco de dados

Execute [sql/create_lead_metrics.sql](/c:/Users/mizae/Documents/IAtria/sql/create_lead_metrics.sql) no Supabase. Esse arquivo cria:

- `lead_records`: registros de leads classificados como `vendas` ou `suporte`
- `lead_metrics`: metricas de toda triagem, inclusive `spam`, usadas pelo dashboard

Se ocorrer `403 permission denied`, reaplique o bloco final de grants do mesmo arquivo para o `service_role`.

## Backend

Suba a API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python agente_triagem.py
```

Rotas principais:

- `GET /health`
- `POST /triagem`
- `POST /backend/triagem` para deploy no Vercel

Exemplo de request:

```json
{
  "nome": "Carla Mendes",
  "email": "carla.mendes@clinicaviva.com",
  "mensagem": "Ola, quero entender precos e agendar uma demonstracao da plataforma para minha clinica."
}
```

Exemplo de response:

```json
{
  "intent": "vendas",
  "sentiment": "positivo",
  "fallback": false
}
```

## LangGraph

O grafo do agente contem:

1. Classificacao de intencao
2. Analise de sentimento
3. Estruturacao da resposta

Ha tratamento basico de erro e fallback automatico para `suporte` + `neutro`.

## n8n

Importe [n8n/workflow_leads.json](/c:/Users/mizae/Documents/IAtria/n8n/workflow_leads.json).

Fluxo:

1. Webhook recebe `nome`, `email` e `mensagem`
2. HTTP Request chama `POST /triagem`
3. Switch separa `vendas`, `suporte` e `spam`
4. `vendas` vai para HubSpot mock e tambem para `lead_records`
5. `suporte` vai para `lead_records`
6. `spam` nao vai para `lead_records`
7. As metricas da IA sao salvas pelo backend em `lead_metrics`

Para trocar `localhost` pelo endpoint publicado, configure no n8n:

```text
TRIAGEM_API_URL=https://seu-projeto.vercel.app/backend/triagem
```

## Frontend

Suba o dashboard:

```powershell
npm install
npm run dev
```

Acesse:

- `http://localhost:3000/dashboard`

Em ambiente local, o dashboard usa [payloads_teste.json](/c:/Users/mizae/Documents/IAtria/payloads_teste.json) para disparar testes reais contra a API.

## Verificacao local

Para simular o comportamento do n8n sem abrir o n8n:

```powershell
.\.venv\Scripts\python scripts\verify_supabase_insert.py --sample-index 0
```

Esse script:

1. Chama a API local de triagem
2. Se `vendas`, simula o envio ao HubSpot mock
3. Se `vendas` ou `suporte`, insere em `lead_records`
4. Valida o registro em `lead_records`
5. Valida a metrica correspondente em `lead_metrics`

## Vercel

O deploy esta preparado para:

- frontend em `/`
- dashboard em `/dashboard`
- API FastAPI em `/backend`

Se frontend e API ficarem no mesmo projeto do Vercel, nao e necessario alterar codigo depois de obter a URL final.

Se a API ficar em outro projeto, ajuste apenas as variaveis:

- `TRIAGEM_API_BASE_URL=https://sua-api.vercel.app/backend`
- `TRIAGEM_API_URL=https://sua-api.vercel.app/backend/triagem`
