from typing import Literal

from pydantic import BaseModel, EmailStr, Field
from typing_extensions import TypedDict

Intent = Literal["vendas", "suporte", "spam"]
QualifiedLeadIntent = Literal["vendas", "suporte"]
Sentiment = Literal["positivo", "neutro", "negativo"]


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


class LeadRecord(BaseModel):
    nome: str
    email: EmailStr
    mensagem: str
    intent: QualifiedLeadIntent
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
