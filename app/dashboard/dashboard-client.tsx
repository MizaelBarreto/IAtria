"use client";

import Link from "next/link";
import { startTransition, useDeferredValue, useEffect, useState } from "react";

import MetricsBarChart from "@/components/metrics-bar-chart";
import testPayloads from "@/payloads_teste.json";

type Intent = "vendas" | "suporte" | "spam";
type Sentiment = "positivo" | "neutro" | "negativo";

type LeadPayload = {
  nome: string;
  email: string;
  mensagem: string;
};

type MetricsResponse = {
  totals: Array<{ intent: Intent; total: number }>;
  records: number;
  updatedAt: string;
};

type TriagemResponse = {
  intent: Intent;
  sentiment: Sentiment;
  fallback: boolean;
};

const EMPTY_TOTALS: MetricsResponse["totals"] = [
  { intent: "vendas", total: 0 },
  { intent: "suporte", total: 0 },
  { intent: "spam", total: 0 },
];

const SAMPLE_PAYLOADS = testPayloads as LeadPayload[];
const SHOW_LOCAL_TESTS = process.env.NODE_ENV !== "production";

export default function DashboardClient() {
  const [data, setData] = useState<MetricsResponse>({
    totals: EMPTY_TOTALS,
    records: 0,
    updatedAt: new Date(0).toISOString(),
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningKey, setRunningKey] = useState<string | null>(null);
  const [runningBatch, setRunningBatch] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TriagemResponse>>({});

  const deferredTotals = useDeferredValue(data.totals);

  async function fetchMetrics(mounted = true) {
    try {
      const response = await fetch("/api/metrics", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Falha ao carregar métricas.");
      }

      const payload = (await response.json()) as MetricsResponse;
      if (!mounted) {
        return;
      }

      startTransition(() => {
        setData(payload);
        setError(null);
      });
    } catch (fetchError) {
      if (!mounted) {
        return;
      }
      setError(fetchError instanceof Error ? fetchError.message : "Erro inesperado.");
    } finally {
      if (mounted) {
        setLoading(false);
      }
    }
  }

  async function executeSample(sample: LeadPayload) {
    const response = await fetch("/api/triagem", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(sample),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Falha ao executar o teste de triagem.");
    }

    const result = (await response.json()) as TriagemResponse;
    startTransition(() => {
      setTestResults((current) => ({
        ...current,
        [sample.email]: result,
      }));
    });
    return result;
  }

  async function runSingleSample(sample: LeadPayload) {
    setRunningKey(sample.email);
    setTestError(null);
    try {
      await executeSample(sample);
      await fetchMetrics();
    } catch (sampleError) {
      setTestError(sampleError instanceof Error ? sampleError.message : "Erro inesperado ao testar a IA.");
    } finally {
      setRunningKey(null);
    }
  }

  async function runAllSamples() {
    setRunningBatch(true);
    setTestError(null);
    try {
      for (const sample of SAMPLE_PAYLOADS) {
        setRunningKey(sample.email);
        await executeSample(sample);
      }
      await fetchMetrics();
    } catch (sampleError) {
      setTestError(sampleError instanceof Error ? sampleError.message : "Erro inesperado ao rodar o lote.");
    } finally {
      setRunningKey(null);
      setRunningBatch(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    fetchMetrics();
    const interval = window.setInterval(() => {
      void fetchMetrics(mounted);
    }, 5000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <main className="dashboard-shell">
      <section className="dashboard-header">
        <div>
          <p className="eyebrow">Monitoramento</p>
          <h1>Dashboard de triagem de leads</h1>
          <p className="hero-copy">
            Atualização automática a cada 5 segundos com dados consolidados do Supabase.
          </p>
        </div>
        <Link className="secondary-link" href="/">
          Voltar
        </Link>
      </section>

      <section className="stats-grid">
        {data.totals.map((item) => (
          <article key={item.intent} className="stat-card">
            <span className="stat-label">{item.intent}</span>
            <strong className="stat-value">{item.total}</strong>
          </article>
        ))}
        <article className="stat-card accent-card">
          <span className="stat-label">registros</span>
          <strong className="stat-value">{data.records}</strong>
        </article>
      </section>

      <section className="chart-panel">
        <div className="panel-heading">
          <h2>Distribuição por intenção</h2>
          <span>
            {loading ? "Carregando..." : `Última atualização: ${new Date(data.updatedAt).toLocaleTimeString("pt-BR")}`}
          </span>
        </div>
        {error ? <p className="error-banner">{error}</p> : <MetricsBarChart data={deferredTotals} />}
      </section>

      {SHOW_LOCAL_TESTS ? (
        <section className="test-panel">
          <div className="panel-heading">
            <div>
              <h2>Teste local da IA</h2>
              <span>Os payloads de teste são enviados para a API Python e atualizam o Supabase após cada execução.</span>
            </div>
            <button className="primary-button" onClick={runAllSamples} disabled={runningBatch}>
              {runningBatch ? "Executando lote..." : "Executar todos"}
            </button>
          </div>
          {testError ? <p className="error-banner">{testError}</p> : null}
          <div className="sample-grid">
            {SAMPLE_PAYLOADS.map((sample) => {
              const result = testResults[sample.email];
              const isRunning = runningKey === sample.email;

              return (
                <article key={sample.email} className="sample-card">
                  <div className="sample-head">
                    <div>
                      <strong>{sample.nome}</strong>
                      <span>{sample.email}</span>
                    </div>
                    <button className="secondary-button" onClick={() => void runSingleSample(sample)} disabled={isRunning || runningBatch}>
                      {isRunning ? "Testando..." : "Testar IA"}
                    </button>
                  </div>
                  <p className="sample-message">{sample.mensagem}</p>
                  {result ? (
                    <div className="result-row">
                      <span className="result-chip">{result.intent}</span>
                      <span className="result-chip">{result.sentiment}</span>
                      <span className={`result-chip ${result.fallback ? "fallback-chip" : "success-chip"}`}>
                        {result.fallback ? "fallback" : "ok"}
                      </span>
                    </div>
                  ) : (
                    <p className="sample-placeholder">Nenhum teste executado ainda para este payload.</p>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      ) : null}
    </main>
  );
}
