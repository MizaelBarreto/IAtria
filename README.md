# IAtria

Plataforma de triagem inteligente de leads com FastAPI, LangGraph, Groq, Supabase, n8n e dashboard em Next.js.

## Links públicos

- Home: https://iatria.vercel.app
- Dashboard: https://iatria.vercel.app/dashboard
- Documentação da API: https://iatria.vercel.app/backend/docs
- Diagrama: http://bit.ly/3N9jX9p

## Teste rápido

1. Importe `workflow_leads.json` no n8n.
2. Ative o workflow.
3. Envie um payload de `payloads_teste.json` para o webhook.
4. Verifique a execução no n8n.
5. Acompanhe a atualização do dashboard em `https://iatria.vercel.app/dashboard`.

Observação:
- As chaves expostas no `workflow_leads.json` foram mantidas apenas por se tratar de um teste fictício de aplicação, para avaliação interna do fluxo.
- Em um cenário real, essas credenciais deveriam ficar em variáveis de ambiente ou credenciais seguras do n8n.

## Entregáveis

- `agente_triagem.py`: backend principal com FastAPI, LangGraph, Groq, fallback e persistência de métricas.
- `workflow_leads.json`: workflow do n8n com webhook, triagem, switch por intenção, HubSpot mock e inserção no Supabase.
- `payloads_teste.json`: exemplos de teste para `vendas`, `suporte` e `spam`.
- `requirements.txt`: dependências Python.
- `sql/create_lead_metrics.sql`: criação de `lead_records` e `lead_metrics`.
- `app/` e `components/`: dashboard em Next.js.
- `vercel.json`: configuração do deploy no Vercel.

## Fluxo da solução

1. O lead entra pelo webhook do n8n.
2. O n8n chama a API de triagem.
3. O agente classifica intenção e sentimento.
4. O backend grava métricas em `lead_metrics`.
5. O n8n envia `vendas` para um HubSpot mock.
6. O n8n grava `vendas` e `suporte` em `lead_records`.
7. O dashboard consulta o Supabase e exibe a distribuição das classificações.

## Execução local

Crie um `.env` com:

```env
SUPABASE_URL=https://fzejfxcdgvlemsclqrku.supabase.co
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
TRIAGEM_API_BASE_URL=http://127.0.0.1:8000
```

Backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python agente_triagem.py
```

Frontend:

```bash
npm install
npm run dev
```

URLs locais:

- API: http://127.0.0.1:8000/triagem
- Docs: http://127.0.0.1:8000/docs
- Dashboard: http://localhost:3000/dashboard

## Banco de dados

Execute `sql/create_lead_metrics.sql` no Supabase.

Tabelas:

- `lead_records`: armazena leads operacionais classificados como `vendas` ou `suporte`
- `lead_metrics`: armazena métricas de todas as triagens, incluindo `spam`

## API e agente

Rotas principais:

- `GET /health`
- `POST /triagem`
- `GET /backend/health`
- `POST /backend/triagem`

Etapas do agente:

1. Classificação de intenção
2. Análise de sentimento
3. Estruturação da resposta

Fallback padrão em caso de falha:

```json
{
  "intent": "suporte",
  "sentiment": "neutro",
  "fallback": true
}
```

## Workflow n8n

O `workflow_leads.json` inclui:

1. Webhook de entrada
2. Normalização do payload
3. Requisição HTTP para a API de triagem
4. Switch por intenção
5. HubSpot mock para `vendas`
6. Inserção em `lead_records` para `vendas` e `suporte`
7. Descarte operacional de `spam`

## Teste técnico

Para validar a API sem o n8n, envie um `POST` para:

https://iatria.vercel.app/backend/triagem

Exemplo:

```json
{
  "nome": "Teste Suporte",
  "email": "teste.suporte@iatria.dev",
  "mensagem": "O sistema está travando na tela de login e preciso de ajuda urgente."
}
```

Validações esperadas:

1. Retorno de `intent`, `sentiment` e `fallback`
2. Registro de todas as triagens em `lead_metrics`
3. Persistência apenas de `vendas` e `suporte` em `lead_records`
4. Processamento de `vendas` via HubSpot mock
5. Atualização do dashboard por polling

## Deploy

Estrutura preparada para Vercel:

- Frontend: `/`
- Dashboard: `/dashboard`
- API: `/backend`

Se frontend e API estiverem no mesmo projeto, não é necessário alterar código após o deploy. Se a API estiver em outro domínio, ajuste:

- `TRIAGEM_API_BASE_URL=https://sua-api.vercel.app/backend`
- `TRIAGEM_API_URL=https://sua-api.vercel.app/backend/triagem`
