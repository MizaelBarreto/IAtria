import logging

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.graph import build_triagem_graph
from backend.llm import GroqLeadClassifier
from backend.logging_config import configure_logging
from backend.models import LeadInput, LeadMetricRecord, TriagemOutput
from backend.supabase import salvar_metricas_supabase

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
    return {"status": "ok"}


@app.post("/triagem", response_model=TriagemOutput)
@app.post("/backend/triagem", response_model=TriagemOutput, include_in_schema=False)
async def triagem(payload: LeadInput) -> TriagemOutput:
    logger.info(
        "triagem_requested",
        extra={"context": {"email": payload.email, "nome": payload.nome}},
    )

    try:
        state = await run_in_threadpool(
            triagem_graph.invoke,
            {"lead": payload, "fallback": False},
        )
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
