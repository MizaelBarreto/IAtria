import logging

from langgraph.graph import END, START, StateGraph

from backend.llm import APITimeoutError, GroqLeadClassifier
from backend.models import GraphState, TriagemOutput

logger = logging.getLogger(__name__)


def build_triagem_graph(classifier: GroqLeadClassifier):
    graph = StateGraph(GraphState)

    def classificar_intencao(state: GraphState) -> GraphState:
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
