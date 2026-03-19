# IAtria

Plataforma de triagem inteligente de leads, desenvolvida com FastAPI, LangGraph, Groq, Supabase, n8n e dashboard em Next.js. O sistema realiza classificação automatizada de intenções e sentimentos, roteamento operacional e monitoramento em tempo real.

---

## 🔗 Links públicos

* **Home:** [https://iatria.vercel.app](https://iatria.vercel.app)
* **Dashboard:** [https://iatria.vercel.app/dashboard](https://iatria.vercel.app/dashboard)
* **Documentação da API:** [https://iatria.vercel.app/backend/docs](https://iatria.vercel.app/backend/docs)
* **Diagrama da arquitetura:** [http://bit.ly/3N9jX9p](http://bit.ly/3N9jX9p)

---

## ⚡ Teste rápido

1. Importe o arquivo `workflow_leads.json` no n8n.
2. Configure a variável:

   ```
   TRIAGEM_API_URL=https://iatria.vercel.app/backend/triagem
   ```
3. Envie um payload de `payloads_teste.json` para o webhook.
4. Verifique a execução no n8n.
5. Acompanhe a atualização no dashboard.

---

## 🚀 Visão geral do fluxo

O sistema executa automaticamente as seguintes etapas:

* Recebimento do lead via webhook
* Classificação de intenção e sentimento via API
* Roteamento baseado na intenção
* Persistência de dados no Supabase
* Atualização do dashboard via polling

---

## 📦 Entregáveis

* **Backend:** `agente_triagem.py`
  Implementação central com FastAPI, LangGraph, integração com Groq, fallback e persistência de métricas.

* **Automação (n8n):** `workflow_leads.json`
  Workflow completo de ingestão, processamento e roteamento.

* **Testes:** `payloads_teste.json`
  Exemplos cobrindo cenários de vendas, suporte e spam.

* **Dependências:** `requirements.txt`

* **Banco de dados:** `sql/create_lead_metrics.sql`
  Script para criação das tabelas `lead_records` e `lead_metrics`.

* **Frontend:** diretórios `app/` e `components/`
  Dashboard em Next.js com atualização contínua.

* **Deploy:** `vercel.json`

---

## 🧠 Arquitetura da solução

1. O lead é recebido via webhook do n8n.
2. O n8n aciona a API de triagem.
3. O agente classifica:

   * `intent` (intenção)
   * `sentiment` (sentimento)
4. As métricas são armazenadas em `lead_metrics`.
5. Leads de vendas são encaminhados para um HubSpot mock.
6. Leads relevantes (`vendas` e `suporte`) são armazenados em `lead_records`.
7. O dashboard consome os dados e exibe as classificações em tempo real.

---

## 💻 Execução local

### Variáveis de ambiente

Crie um arquivo `.env`:

```env
SUPABASE_URL=https://fzejfxcdgvlemsclqrku.supabase.co
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
TRIAGEM_API_BASE_URL=http://127.0.0.1:8000
```

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python agente_triagem.py
```

### Frontend

```bash
npm install
npm run dev
```

### Endpoints locais

* API: [http://127.0.0.1:8000/triagem](http://127.0.0.1:8000/triagem)
* Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Dashboard: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

---

## 🗄️ Banco de dados

Execute o script `sql/create_lead_metrics.sql` no Supabase.

Estruturas criadas:

* `lead_records`: armazena leads operacionais (`vendas` e `suporte`)
* `lead_metrics`: armazena métricas de todas as triagens, incluindo spam

---

## 🔌 API e agente

### Rotas principais

* `GET /health`
* `POST /triagem`
* `GET /backend/health`
* `POST /backend/triagem`

### Pipeline do agente

O processamento é dividido em três etapas:

1. Classificação de intenção
2. Análise de sentimento
3. Estruturação da resposta

### Fallback

Em caso de falha ou timeout:

```json
{
  "intent": "suporte",
  "sentiment": "neutro",
  "fallback": true
}
```

---

## ⚙️ Workflow n8n

O arquivo `workflow_leads.json` inclui:

1. Webhook de entrada
2. Normalização do payload
3. Requisição HTTP para a API
4. Roteamento por intenção
5. Integração com HubSpot (mock) para vendas
6. Persistência em banco (`lead_records`)
7. Descarte de spam

### Variável recomendada

```
TRIAGEM_API_URL=https://iatria.vercel.app/backend/triagem
```

---

## 🧪 Teste da API

Envie uma requisição `POST` para:

[https://iatria.vercel.app/backend/triagem](https://iatria.vercel.app/backend/triagem)

Exemplo:

```json
{
  "nome": "Teste Suporte",
  "email": "teste.suporte@iatria.dev",
  "mensagem": "O sistema está travando na tela de login e preciso de ajuda urgente."
}
```

### Validações esperadas

* Retorno de `intent`, `sentiment` e `fallback`
* Registro de todas as triagens em `lead_metrics`
* Persistência seletiva em `lead_records`
* Processamento de vendas via HubSpot mock
* Atualização do dashboard em tempo real

---

## 🧩 Decisões de implementação

A solução foi desenvolvida com foco em:

* Robustez operacional
* Observabilidade
* Facilidade de deploy

O backend foi consolidado em um único arquivo para simplificar avaliação e execução, mantendo apenas os componentes essenciais do fluxo.

---

## ☁️ Deploy

Estrutura preparada para Vercel:

* Frontend: `/`
* Dashboard: `/dashboard`
* API: `/backend`

### Observações

* Não é necessário alterar código se frontend e API estiverem no mesmo projeto.
* Caso a API esteja em outro domínio, ajuste:

```
TRIAGEM_API_BASE_URL=https://sua-api.vercel.app/backend
TRIAGEM_API_URL=https://sua-api.vercel.app/backend/triagem
```

---

## 📌 Considerações finais

O IAtria demonstra uma arquitetura completa de triagem automatizada, integrando IA, automação e visualização de dados em um
