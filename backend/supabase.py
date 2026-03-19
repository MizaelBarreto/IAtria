import logging

import httpx

from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


def salvar_metricas_supabase(data: dict, settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    url = f"{active_settings.supabase_url.rstrip('/')}/rest/v1/lead_metrics"
    headers = {
        "apikey": active_settings.supabase_key,
        "Authorization": f"Bearer {active_settings.supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=data,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info(
            "supabase_metric_saved",
            extra={"context": {"email": data.get("email"), "intent": data.get("intent")}},
        )
    except httpx.HTTPError as exc:
        logger.exception(
            "supabase_metric_save_failed",
            extra={
                "context": {
                    "email": data.get("email"),
                    "detail": str(exc),
                }
            },
        )
