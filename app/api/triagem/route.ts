import { NextResponse } from "next/server";

function resolveBackendBaseUrl(requestUrl: string): string {
  const configuredUrl = process.env.TRIAGEM_API_BASE_URL?.trim();
  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, "");
  }

  if (process.env.VERCEL) {
    const { origin } = new URL(requestUrl);
    return `${origin}/backend`;
  }

  return "http://127.0.0.1:8000";
}

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const backendBaseUrl = resolveBackendBaseUrl(request.url);

    const response = await fetch(`${backendBaseUrl}/triagem`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const contentType = response.headers.get("content-type") ?? "application/json";
    const body = await response.text();

    return new NextResponse(body, {
      status: response.status,
      headers: {
        "Content-Type": contentType,
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Não foi possível alcançar a API Python.",
      },
      { status: 502 },
    );
  }
}
