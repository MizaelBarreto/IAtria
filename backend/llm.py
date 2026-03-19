import json
import logging
from typing import Any

from openai import APIError, APITimeoutError, OpenAI

from backend.config import Settings
from backend.models import Intent, LeadInput, Sentiment

logger = logging.getLogger(__name__)

INTENT_PROMPT = """
Você classifica leads recebidos por uma empresa de software médico.
Analise a mensagem e responda APENAS JSON válido no formato:
{"intent":"vendas|suporte|spam","sentiment":"neutro"}

Regras de classificação:
- vendas: intenção comercial, orçamento, contratação, demonstração, parceria comercial
- suporte: dúvida, problema, erro, pedido de ajuda, solicitação operacional
- spam: propaganda irrelevante, oferta genérica, mensagem sem relação com o negócio

Não escreva explicações. Não use markdown. Não escreva texto fora do JSON.
""".strip()

SENTIMENT_PROMPT = """
Você analisa o sentimento de mensagens recebidas por uma empresa de software médico.
Analise a mensagem e responda APENAS JSON válido no formato:
{"intent":"suporte","sentiment":"positivo|neutro|negativo"}

Regras de sentimento:
- positivo: tom satisfeito, interessado, cordial ou otimista
- neutro: tom informativo, objetivo ou sem emoção clara
- negativo: tom irritado, frustrado, agressivo ou com reclamação

Não escreva explicações. Não use markdown. Não escreva texto fora do JSON.
""".strip()

VALID_INTENTS = {"vendas", "suporte", "spam"}
VALID_SENTIMENTS = {"positivo", "neutro", "negativo"}


class GroqLeadClassifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    def classify_intent(self, lead: LeadInput) -> tuple[Intent, str]:
        payload = self._invoke_json(INTENT_PROMPT, lead)
        intent = self._normalize_intent(payload.get("intent"))
        return intent, json.dumps(payload, ensure_ascii=False)

    def classify_sentiment(self, lead: LeadInput) -> tuple[Sentiment, str]:
        payload = self._invoke_json(SENTIMENT_PROMPT, lead)
        sentiment = self._normalize_sentiment(payload.get("sentiment"))
        return sentiment, json.dumps(payload, ensure_ascii=False)

    def _invoke_json(self, system_prompt: str, lead: LeadInput) -> dict[str, Any]:
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
            logger.warning(
                "groq_json_mode_failed",
                extra={"context": {"detail": str(exc)}},
            )
            content = self._create_completion(messages, enforce_json=False)

        parsed = self._parse_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("Model response is not a JSON object.")
        return parsed

    def _create_completion(self, messages: list[dict[str, str]], enforce_json: bool) -> str:
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


__all__ = ["GroqLeadClassifier", "APITimeoutError"]
