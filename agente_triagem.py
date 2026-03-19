"""Serviço de triagem de leads com FastAPI, LangGraph, Groq e Supabase."""

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Literal

import httpx
import uvicorn
from fastapi import FastAPI
from langgraph.graph import END, START, StateGraph
from openai import APIError, APITimeoutError, OpenAI
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.concurrency import run_in_threadpool
from typing_extensions import TypedDict

Intent = Literal["vendas", "suporte", "spam"]
Sentiment = Literal["positivo", "neutro", "negativo"]

# Prompts e tipos aceitos pelo agente.
INTENT_PROMPT = """
Voce classifica leads recebidos por uma empresa de software medico.
Analise a mensagem e responda APENAS JSON valido no formato:
{"intent":"vendas|suporte|spam","sentiment":"neutro"}

Regras de classificacao:
- vendas: intencao comercial, orcamento, contratacao, demonstracao, parceria comercial
- suporte: duvida, problema, erro, pedido de ajuda, solicitacao operacional
- spam: propaganda irrelevante, oferta generica, mensagem sem relacao com o negocio

Nao escreva explicacoes. Nao use markdown. Nao escreva texto fora do JSON.
""".strip()

SENTIMENT_PROMPT = """
Voce analisa o sentimento de mensagens recebidas por uma empresa de software medico.
Analise a mensagem e responda APENAS JSON valido no formato:
{"intent":"suporte","sentiment":"positivo|neutro|negativo"}

Regras de sentimento:
- positivo: tom satisfeito, interessado, cordial ou otimista
- neutro: tom informativo, objetivo ou sem emocao clara
- negativo: tom irritado, frustrado, agressivo ou com reclamacao

Nao escreva explicacoes. Nao use markdown. Nao escreva texto fora do JSON.
""".strip()

VALID_INTENTS = {"vendas", "suporte", "spam"}
VALID_SENTIMENTS = {"positivo", "neutro", "negativo"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """Serializa o log em JSON para facilitar observabilidade."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload["context"] = context

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Configura o logger raiz apenas uma vez para evitar duplicidade."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_model: str = Field("llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_base_url: str = Field("https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    llm_timeout_seconds: float = Field(15.0, alias="LLM_TIMEOUT_SECONDS")
    app_name: str = "IAtria Lead Triage"


@lru_cache
def get_settings() -> Settings:
    """Carrega e mantém em cache as variáveis de ambiente da aplicação."""
    return Settings()


class LeadInput(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    mensagem: str = Field(..., min_length=1, max_length=5000)


class TriagemOutput(BaseModel):
    intent: Intent
    sentiment: Sentiment
    fallback: bool = False


class LeadMetricRecord(BaseModel):
    nome: str
    email: EmailStr
    mensagem: str
    intent: Intent
    sentiment: Sentiment
    fallback: bool


class GraphState(TypedDict, total=False):
    lead: LeadInput
    intent: Intent
    sentiment: Sentiment
    fallback: bool
    raw_intent_response: str
    raw_sentiment_response: str
    error: str


class GroqLeadClassifier:
    """Encapsula as chamadas para o modelo e normaliza a saída da IA."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    def classify_intent(self, lead: LeadInput) -> tuple[Intent, str]:
        """Solicita ao modelo a intenção do lead e valida o valor recebido."""
        payload = self._invoke_json(INTENT_PROMPT, lead)
        intent = self._normalize_intent(payload.get("intent"))
        return intent, json.dumps(payload, ensure_ascii=False)

    def classify_sentiment(self, lead: LeadInput) -> tuple[Sentiment, str]:
        """Solicita ao modelo o sentimento predominante da mensagem."""
        payload = self._invoke_json(SENTIMENT_PROMPT, lead)
        sentiment = self._normalize_sentiment(payload.get("sentiment"))
        return sentiment, json.dumps(payload, ensure_ascii=False)

    def _invoke_json(self, system_prompt: str, lead: LeadInput) -> dict[str, Any]:
        """Tenta obter JSON estrito e recua para uma chamada simples se necessário."""
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(lead.model_dump(mode="json"), ensure_ascii=False),
            },
        ]

        try:
            content = self._create_completion(messages, enforce_json=True)
        except APIError as exc:
            logging.getLogger(__name__).warning(
                "groq_json_mode_failed",
                extra={"context": {"detail": str(exc)}},
            )
            content = self._create_completion(messages, enforce_json=False)

        parsed = self._parse_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("Model response is not a JSON object.")
        return parsed

    def _create_completion(self, messages: list[dict[str, str]], enforce_json: bool) -> str:
        """Envia a requisição ao modelo com ou sem `response_format`."""
        kwargs: dict[str, Any] = {
            "model": self.settings.groq_model,
            "temperature": 0,
            "messages": messages,
        }
        if enforce_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ValueError("Empty response from model.")
        return content

    def _parse_json(self, content: str) -> dict[str, Any]:
        """Extrai o JSON mesmo quando a resposta vem envolvida por markdown."""
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.replace("```json", "").replace("```", "").strip()
        start = normalized.find("{")
        end = normalized.rfind("}")
        if start != -1 and end != -1:
            normalized = normalized[start : end + 1]
        return json.loads(normalized)

    def _normalize_intent(self, value: Any) -> Intent:
        normalized = str(value).strip().lower()
        if normalized in VALID_INTENTS:
            return normalized  # type: ignore[return-value]
        raise ValueError(f"Invalid intent received: {value}")

    def _normalize_sentiment(self, value: Any) -> Sentiment:
        normalized = str(value).strip().lower()
        if normalized in VALID_SENTIMENTS:
            return normalized  # type: ignore[return-value]
        raise ValueError(f"Invalid sentiment received: {value}")


def build_triagem_graph(classifier: GroqLeadClassifier):
    """Monta o fluxo LangGraph com intenção, sentimento e resposta final."""
    logger = logging.getLogger(__name__)
    graph = StateGraph(GraphState)

    def classificar_intencao(state: GraphState) -> GraphState:
        """Executa o primeiro nó do grafo e faz fallback em caso de falha."""
        lead = state["lead"]
        try:
            intent, raw = classifier.classify_intent(lead)
            return {"intent": intent, "raw_intent_response": raw, "fallback": state.get("fallback", False)}
        except (APITimeoutError, Exception) as exc:
            logger.exception(
                "intent_classification_failed",
                extra={"context": {"email": lead.email, "detail": str(exc)}},
            )
            return {
                "intent": "suporte",
                "raw_intent_response": "{}",
                "fallback": True,
                "error": f"intent:{exc}",
            }

    def analisar_sentimento(state: GraphState) -> GraphState:
        """Executa o segundo nó do grafo e preserva o fallback quando necessário."""
        lead = state["lead"]
        try:
            sentiment, raw = classifier.classify_sentiment(lead)
            return {
                "sentiment": sentiment,
                "raw_sentiment_response": raw,
                "fallback": state.get("fallback", False),
            }
        except (APITimeoutError, Exception) as exc:
            logger.exception(
                "sentiment_analysis_failed",
                extra={"context": {"email": lead.email, "detail": str(exc)}},
            )
            return {
                "sentiment": "neutro",
                "raw_sentiment_response": "{}",
                "fallback": True,
                "error": f"{state.get('error', '')};sentiment:{exc}".strip(";"),
            }

    def estruturar_resposta(state: GraphState) -> GraphState:
        """Normaliza o estado final do grafo no formato de saída da API."""
        response = TriagemOutput(
            intent=state.get("intent", "suporte"),
            sentiment=state.get("sentiment", "neutro"),
            fallback=state.get("fallback", False),
        )
        return response.model_dump()

    graph.add_node("classificar_intencao", classificar_intencao)
    graph.add_node("analisar_sentimento", analisar_sentimento)
    graph.add_node("estruturar_resposta", estruturar_resposta)

    graph.add_edge(START, "classificar_intencao")
    graph.add_edge("classificar_intencao", "analisar_sentimento")
    graph.add_edge("analisar_sentimento", "estruturar_resposta")
    graph.add_edge("estruturar_resposta", END)

    return graph.compile()


def salvar_metricas_supabase(data: dict, settings: Settings | None = None) -> None:
    """Persiste métricas da triagem sem interromper a resposta da API."""
    active_settings = settings or get_settings()
    logger = logging.getLogger(__name__)
    url = f"{active_settings.supabase_url.rstrip('/')}/rest/v1/lead_metrics"
    headers = {
        "apikey": active_settings.supabase_key,
        "Authorization": f"Bearer {active_settings.supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=10.0)
        response.raise_for_status()
        logger.info(
            "supabase_metric_saved",
            extra={"context": {"email": data.get("email"), "intent": data.get("intent")}},
        )
    except httpx.HTTPError as exc:
        logger.exception(
            "supabase_metric_save_failed",
            extra={"context": {"email": data.get("email"), "detail": str(exc)}},
        )


# Inicialização das dependências principais da aplicação.
configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)
classifier = GroqLeadClassifier(settings)
triagem_graph = build_triagem_graph(classifier)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API de triagem inteligente de leads com LangGraph, Groq e Supabase.",
)


@app.get("/health")
@app.get("/backend/health", include_in_schema=False)
def health() -> dict[str, str]:
    """Retorna um status simples para monitoramento e smoke tests."""
    return {"status": "ok"}


@app.post("/triagem", response_model=TriagemOutput)
@app.post("/backend/triagem", response_model=TriagemOutput, include_in_schema=False)
async def triagem(payload: LeadInput) -> TriagemOutput:
    """Executa a triagem completa, aplica fallback global e salva a métrica."""
    logger.info(
        "triagem_requested",
        extra={"context": {"email": payload.email, "nome": payload.nome}},
    )

    try:
        state = await run_in_threadpool(triagem_graph.invoke, {"lead": payload, "fallback": False})
        result = TriagemOutput(
            intent=state.get("intent", "suporte"),
            sentiment=state.get("sentiment", "neutro"),
            fallback=state.get("fallback", False),
        )
    except Exception as exc:
        logger.exception(
            "triagem_failed",
            extra={"context": {"email": payload.email, "detail": str(exc)}},
        )
        result = TriagemOutput(intent="suporte", sentiment="neutro", fallback=True)

    metric_record = LeadMetricRecord(
        nome=payload.nome,
        email=payload.email,
        mensagem=payload.mensagem,
        intent=result.intent,
        sentiment=result.sentiment,
        fallback=result.fallback,
    )
    await run_in_threadpool(salvar_metricas_supabase, metric_record.model_dump(mode="json"), settings)

    logger.info(
        "triagem_completed",
        extra={
            "context": {
                "email": payload.email,
                "intent": result.intent,
                "sentiment": result.sentiment,
                "fallback": result.fallback,
            }
        },
    )
    return result


if __name__ == "__main__":
    uvicorn.run("agente_triagem:app", host="0.0.0.0", port=8000, reload=True)
