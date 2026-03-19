import { NextResponse } from "next/server";

type Intent = "vendas" | "suporte" | "spam";

type MetricRow = {
  intent: Intent;
  created_at: string;
};

export async function GET() {
  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return NextResponse.json(
        { error: "Variáveis SUPABASE_URL e SUPABASE_KEY não configuradas." },
        { status: 500 },
      );
    }

    const response = await fetch(
      `${supabaseUrl}/rest/v1/lead_metrics?select=intent,created_at&order=created_at.desc&limit=500`,
      {
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
        },
        cache: "no-store",
      },
    );

    if (!response.ok) {
      const detail = await response.text();
      return NextResponse.json({ error: `Falha ao consultar Supabase: ${detail}` }, { status: 502 });
    }

    const rows = (await response.json()) as MetricRow[];
    const grouped: Record<Intent, number> = {
      vendas: 0,
      suporte: 0,
      spam: 0,
    };

    for (const row of rows) {
      if (row.intent in grouped) {
        grouped[row.intent] += 1;
      }
    }

    return NextResponse.json({
      totals: Object.entries(grouped).map(([intent, total]) => ({
        intent,
        total,
      })),
      records: rows.length,
      updatedAt: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Não foi possível consultar o Supabase.",
      },
      { status: 502 },
    );
  }
}
