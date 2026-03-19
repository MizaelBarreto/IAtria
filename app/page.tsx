import Link from "next/link";

export default function HomePage() {
  return (
    <main className="landing-shell">
      <section className="hero-card">
        <p className="eyebrow">IAtria</p>
        <h1>Esteira de triagem inteligente para leads com IA e automação.</h1>
        <p className="hero-copy">
          Backend FastAPI com LangGraph e Groq, integração com Supabase, workflow n8n e dashboard em tempo real.
        </p>
        <div className="hero-actions">
          <Link className="primary-link" href="/dashboard">
            Abrir dashboard
          </Link>
          <a className="secondary-link" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </div>
      </section>
    </main>
  );
}
