# IAtria

Sistema completo de triagem inteligente de leads com:

- FastAPI + LangGraph no backend
- Groq como provedor de IA
- Supabase para persistência de métricas
- n8n para automação
- Next.js + Recharts para dashboard

## Estrutura

- [agente_triagem.py](/c:/Users/mizae/Documents/IAtria/agente_triagem.py): entrypoint do backend
- [backend/main.py](/c:/Users/mizae/Documents/IAtria/backend/main.py): API FastAPI
- [backend/graph.py](/c:/Users/mizae/Documents/IAtria/backend/graph.py): grafo LangGraph
- [backend/llm.py](/c:/Users/mizae/Documents/IAtria/backend/llm.py): integração com Groq
- [backend/supabase.py](/c:/Users/mizae/Documents/IAtria/backend/supabase.py): persistência no Supabase
- [sql/create_lead_metrics.sql](/c:/Users/mizae/Documents/IAtria/sql/create_lead_metrics.sql): SQL da tabela
- [n8n/workflow_triagem_leads.json](/c:/Users/mizae/Documents/IAtria/n8n/workflow_triagem_leads.json): workflow do n8n
- [app/dashboard/page.tsx](/c:/Users/mizae/Documents/IAtria/app/dashboard/page.tsx): dashboard
- [app/api/metrics/route.ts](/c:/Users/mizae/Documents/IAtria/app/api/metrics/route.ts): leitura agregada do Supabase
- [next.config.mjs](/c:/Users/mizae/Documents/IAtria/next.config.mjs): configuração do Next.js

## Variáveis de ambiente

Arquivo [`.env`](/c:/Users/mizae/Documents/IAtria/.env) baseado em [`.env.example`](/c:/Users/mizae/Documents/IAtria/.env.example):

```env
SUPABASE_URL=https://fzejfxcdgvlemsclqrku.supabase.co
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
TRIAGEM_API_BASE_URL=http://127.0.0.1:8000
```

## Banco de dados

Execute o SQL de [sql/create_lead_metrics.sql](/c:/Users/mizae/Documents/IAtria/sql/create_lead_metrics.sql) no Supabase para criar a tabela `lead_metrics`.

Se a tabela já existir e a API retornar `403 permission denied for table lead_metrics`, reaplique o bloco final de permissões do mesmo arquivo para conceder acesso ao `service_role` usado pelo backend e pelo dashboard server-side.

## Como rodar o backend

1. Crie o ambiente virtual:

```powershell
python -m venv .venv
```

2. Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

4. Inicie a API:

```powershell
python agente_triagem.py
```

5. Acesse:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

## Como rodar o frontend

1. Instale as dependências:

```powershell
npm install
```

2. Inicie o Next.js:

```powershell
npm run dev
```

3. Acesse:

- Home: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`
- Proxy local de triagem: `http://localhost:3000/api/triagem`

## Testes locais com IA

O dashboard em [app/dashboard/page.tsx](/c:/Users/mizae/Documents/IAtria/app/dashboard/page.tsx) exibe um painel de testes em desenvolvimento usando [payloads_teste.json](/c:/Users/mizae/Documents/IAtria/payloads_teste.json).

Fluxo:

1. Preencha [`.env`](/c:/Users/mizae/Documents/IAtria/.env) com as chaves reais.
2. Suba o backend com `python agente_triagem.py`.
3. Suba o frontend com `npm run dev`.
4. Abra `http://localhost:3000/dashboard`.
5. Use `Testar IA` ou `Executar todos`.

Cada teste chama a rota Next `/api/triagem`, que faz proxy para a API Python e depois atualiza os cards e o gráfico.

## Vercel

Arquivos preparados para deploy:

- [vercel.json](/c:/Users/mizae/Documents/IAtria/vercel.json): configuração de serviços
- [.python-version](/c:/Users/mizae/Documents/IAtria/.python-version): versão Python para deploy

Estratégia de deploy:

1. Serviço `web` com Next.js na raiz `/`
2. Serviço `api` com FastAPI na raiz `/backend`
3. Dashboard público em `/dashboard`
4. API pública em `/backend/triagem`

Passos:

1. No Vercel, configure o projeto com framework `Services`.
2. Defina as variáveis `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`, `LLM_TIMEOUT_SECONDS`.
3. Se quiser sobrescrever o proxy, defina `TRIAGEM_API_BASE_URL`.
4. Rode localmente com `npm run dev:vercel` ou publique com `npx vercel --prod`.

## Endpoint de triagem

`POST /triagem`

Payload:

```json
{
  "nome": "Carla Mendes",
  "email": "carla.mendes@clinicaviva.com",
  "mensagem": "Olá, quero entender preços e agendar uma demonstração da plataforma para minha clínica."
}
```

Resposta:

```json
{
  "intent": "vendas",
  "sentiment": "positivo",
  "fallback": false
}
```

## Resiliência

- Timeout configurável via `LLM_TIMEOUT_SECONDS`
- `try/except` no fluxo de intenção e sentimento
- Fallback automático para `intent="suporte"` e `sentiment="neutro"`
- Persistência no Supabase mesmo quando houver fallback

## n8n

Importe [n8n/workflow_triagem_leads.json](/c:/Users/mizae/Documents/IAtria/n8n/workflow_triagem_leads.json) no n8n.

Fluxo do workflow:

1. Webhook recebe o lead.
2. O lead é normalizado.
3. O n8n chama `POST /triagem`.
4. O `Switch` separa por intenção.
5. Leads de vendas seguem para um HubSpot mock.
6. Todos os leads são persistidos no Supabase.

Para trocar de `localhost` para o endpoint publicado, configure a variável `TRIAGEM_API_URL` no n8n. Exemplo em produção:

```text
https://seu-projeto.vercel.app/backend/triagem
```

## Arquivos auxiliares

- [payloads_teste.json](/c:/Users/mizae/Documents/IAtria/payloads_teste.json): exemplos para testar a API
- [package.json](/c:/Users/mizae/Documents/IAtria/package.json): dependências do frontend
- [requirements.txt](/c:/Users/mizae/Documents/IAtria/requirements.txt): dependências do backend
- [scripts/verify_supabase_insert.py](/c:/Users/mizae/Documents/IAtria/scripts/verify_supabase_insert.py): valida inserção real no Supabase após a triagem
