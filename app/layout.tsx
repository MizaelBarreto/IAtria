import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IAtria Dashboard",
  description: "Triagem inteligente de leads com FastAPI, LangGraph, Supabase e n8n.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
