import json
import os
from pathlib import Path

import httpx


def load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_dotenv()

    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    supabase_key = os.environ["SUPABASE_KEY"]
    api_url = os.environ.get("TRIAGEM_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

    payload = {
        "nome": "Teste Integracao Supabase",
        "email": "teste-integracao-supabase@example.com",
        "mensagem": "Quero uma demonstracao comercial da plataforma para minha clinica.",
    }

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        triagem_response = client.post(f"{api_url}/triagem", json=payload)
        triagem_response.raise_for_status()

        result = triagem_response.json()
        query_url = (
            f"{supabase_url}/rest/v1/lead_metrics"
            "?select=nome,email,mensagem,intent,sentiment,fallback,created_at"
            f"&email=eq.{payload['email']}"
            "&order=created_at.desc"
            "&limit=1"
        )
        db_response = client.get(query_url, headers=headers)
        db_response.raise_for_status()
        rows = db_response.json()

    if not rows:
        raise RuntimeError("Nenhum registro encontrado em lead_metrics para o payload de teste.")

    latest = rows[0]
    print("Triagem:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("Registro encontrado:")
    print(json.dumps(latest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
