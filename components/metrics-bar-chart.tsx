"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS_BY_INTENT: Record<string, string> = {
  vendas: "#1d6f5f",
  suporte: "#bfa236",
  spam: "#d85f3d",
};

type Props = {
  data: Array<{ intent: string; total: number }>;
};

export default function MetricsBarChart({ data }: Props) {
  return (
    <div className="chart-wrapper">
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(25, 31, 42, 0.12)" />
          <XAxis dataKey="intent" tickLine={false} axisLine={false} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
          <Tooltip
            cursor={{ fill: "rgba(216, 95, 61, 0.08)" }}
            contentStyle={{
              borderRadius: 16,
              border: "1px solid rgba(25, 31, 42, 0.08)",
              backgroundColor: "#fffaf3",
            }}
          />
          <Bar dataKey="total" radius={[14, 14, 6, 6]}>
            {data.map((entry, index) => (
              <Cell key={`${entry.intent}-${index}`} fill={COLORS_BY_INTENT[entry.intent] ?? "#1b2631"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
