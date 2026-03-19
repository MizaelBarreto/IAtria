import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


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


def load_payload(sample_index: int) -> dict[str, Any]:
    payloads = json.loads(Path("payloads_teste.json").read_text(encoding="utf-8"))
    if sample_index < 0 or sample_index >= len(payloads):
        raise IndexError(f"sample_index fora do intervalo: 0..{len(payloads) - 1}")
    return payloads[sample_index]


def fetch_latest_record(
    client: httpx.Client,
    supabase_url: str,
    headers: dict[str, str],
    table_name: str,
    email: str,
) -> dict[str, Any] | None:
    query_url = (
        f"{supabase_url}/rest/v1/{table_name}"
        "?select=nome,email,mensagem,intent,sentiment,fallback,created_at"
        f"&email=eq.{email}"
        "&order=created_at.desc"
        "&limit=1"
    )
    response = client.get(query_url, headers=headers)
    if not response.is_success:
        raise RuntimeError(f"Falha ao consultar {table_name}: {response.status_code} {response.text}")
    rows = response.json()
    return rows[0] if rows else None


def call_local_triagem(api_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=30.0) as client:
            triagem_response = client.post(f"{api_url}/triagem", json=payload)
            triagem_response.raise_for_status()
            return triagem_response.json()
    except httpx.HTTPError:
        from backend.main import app

        test_client = TestClient(app)
        triagem_response = test_client.post("/triagem", json=payload)
        triagem_response.raise_for_status()
        return triagem_response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simula o fluxo do n8n e valida os registros no Supabase.")
    parser.add_argument("--sample-index", type=int, default=0, help="Indice do payload em payloads_teste.json")
    args = parser.parse_args()

    load_dotenv()

    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    supabase_key = os.environ["SUPABASE_KEY"]
    api_url = os.environ.get("TRIAGEM_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    payload = load_payload(args.sample_index)

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    result = call_local_triagem(api_url, payload)

    with httpx.Client(timeout=30.0) as client:
        hubspot_status: str | None = None
        lead_record: dict[str, Any] | None = None

        if result["intent"] == "vendas":
            hubspot_response = client.post(
                "https://httpbin.org/post",
                json={**payload, **result, "pipeline": "hubspot-mock"},
            )
            hubspot_response.raise_for_status()
            hubspot_status = "hubspot_mock_ok"

        if result["intent"] != "spam":
            lead_record_payload = {
                "nome": payload["nome"],
                "email": payload["email"],
                "mensagem": payload["mensagem"],
                "intent": result["intent"],
                "sentiment": result["sentiment"],
                "fallback": result["fallback"],
            }
            insert_response = client.post(
                f"{supabase_url}/rest/v1/lead_records",
                headers={**headers, "Prefer": "return=minimal"},
                json=lead_record_payload,
            )
            if not insert_response.is_success:
                raise RuntimeError(
                    f"Falha ao inserir em lead_records: {insert_response.status_code} {insert_response.text}"
                )

        lead_record = fetch_latest_record(client, supabase_url, headers, "lead_records", payload["email"])
        metric_record = fetch_latest_record(client, supabase_url, headers, "lead_metrics", payload["email"])

    if result["intent"] != "spam" and not lead_record:
        raise RuntimeError("Nenhum registro encontrado em lead_records para o payload de teste.")
    if not metric_record:
        raise RuntimeError("Nenhum registro encontrado em lead_metrics para o payload de teste.")

    print("Payload utilizado:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("Triagem:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if hubspot_status:
        print("HubSpot mock:")
        print(hubspot_status)
    print("Lead record:")
    print(json.dumps(lead_record, ensure_ascii=False, indent=2))
    print("Metric record:")
    print(json.dumps(metric_record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
