# IAtria

Projeto de triagem inteligente de leads com FastAPI, LangGraph, Groq, Supabase, n8n e dashboard em Next.js.

## Link do diagrama

Draw.io: http://bit.ly/3N9jX9p

## Entrega principal

- `README.md`: explica o projeto, os arquivos principais, como rodar e como a solucao foi montada.
- `requirements.txt`: dependencias Python do backend.
- `agente_triagem.py`: backend completo em um unico arquivo. Contem configuracao, modelos, cliente Groq, grafo LangGraph, persistencia de metricas no Supabase e rotas FastAPI.
- `workflow_leads.json`: workflow do n8n com webhook, chamada HTTP para o backend, roteamento por intencao, HubSpot mock e insercao no Supabase.
- `payloads_teste.json`: exemplos de leads para testar o fluxo.

## Arquivos de apoio

- `sql/create_lead_metrics.sql`: cria as tabelas `lead_records` e `lead_metrics` no Supabase.
- `app/` e `components/`: dashboard em Next.js com polling e grafico.
- `vercel.json`: configuracao do deploy no Vercel para publicar frontend e API.
- `.env.example`: modelo de variaveis de ambiente.

## Como a solucao foi desenvolvida

O projeto foi ajustado para manter a entrega simples sem perder o escopo pedido:

1. O backend foi consolidado em `agente_triagem.py` para evitar excesso de arquivos Python.
2. O agente usa LangGraph com tres etapas: classificar intencao, analisar sentimento e estruturar a resposta final.
3. A IA usa Groq em modo compativel com OpenAI SDK.
4. O backend grava metricas de toda triagem em `lead_metrics`.
5. O n8n grava apenas `vendas` e `suporte` em `lead_records` e simula HubSpot quando a intencao for `vendas`.
6. O dashboard consulta `lead_metrics` para mostrar o volume de classificacoes.

## Variaveis de ambiente

Crie um arquivo `.env` baseado em `.env.example`:

```env
SUPABASE_URL=https://fzejfxcdgvlemsclqrku.supabase.co
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
TRIAGEM_API_BASE_URL=http://127.0.0.1:8000
```

## Banco de dados

Execute o arquivo `sql/create_lead_metrics.sql` no Supabase. Ele cria:

- `lead_records`: tabela operacional para leads classificados como `vendas` ou `suporte`
- `lead_metrics`: tabela de metricas da IA, usada pelo dashboard

## O que o backend faz

O `agente_triagem.py` expoe:

- `GET /health`
- `POST /triagem`
- `GET /backend/health`
- `POST /backend/triagem`

Fluxo interno do agente:

1. Recebe `nome`, `email` e `mensagem`
2. Classifica a intencao em `vendas`, `suporte` ou `spam`
3. Analisa o sentimento em `positivo`, `neutro` ou `negativo`
4. Aplica fallback para `suporte` + `neutro` se houver falha ou timeout
5. Salva a metrica no Supabase
6. Retorna um JSON simples para o n8n

Exemplo de resposta:

```json
{
  "intent": "vendas",
  "sentiment": "positivo",
  "fallback": false
}
```

## O que o workflow do n8n faz

O arquivo `workflow_leads.json` contem:

1. Webhook de entrada
2. Normalizacao do payload
3. Requisicao HTTP para a API de triagem
4. Switch por intencao
5. HubSpot mock para `vendas`
6. Insercao em `lead_records` para `vendas` e `suporte`
7. Ignora `spam` no banco operacional

Variavel recomendada no n8n:

```text
TRIAGEM_API_URL=https://iatria.vercel.app/backend/triagem
```

## Como rodar localmente

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python agente_triagem.py
```

Frontend:

```powershell
npm install
npm run dev
```

URLs locais:

- API: `http://127.0.0.1:8000/triagem`
- Docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://localhost:3000/dashboard`

## Como testar

1. Use os exemplos de `payloads_teste.json` no webhook do n8n ou em chamadas diretas para a API.
2. Verifique se `vendas` aciona o HubSpot mock.
3. Verifique se apenas `vendas` e `suporte` entram em `lead_records`.
4. Verifique se todas as triagens entram em `lead_metrics`.
5. Acompanhe o resumo das metricas pelo dashboard.

## Deploy

O projeto esta pronto para Vercel com:

- frontend em `/`
- dashboard em `/dashboard`
- API FastAPI em `/backend`

Se frontend e API estiverem no mesmo projeto, nao e necessario alterar codigo apos o deploy. Se a API ficar em outro dominio, ajuste apenas:

- `TRIAGEM_API_BASE_URL=https://sua-api.vercel.app/backend`
- `TRIAGEM_API_URL=https://sua-api.vercel.app/backend/triagem`
