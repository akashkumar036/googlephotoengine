"use client";
import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";

interface BarDataPoint {
  mode: string;
  count: number;
}

interface BarChartComponentProps {
  data: BarDataPoint[];
  height?: number;
}

const COLORS = ["#6366f1", "#8b5cf6", "#ec4899", "#f43f5e", "#f59e0b", "#10b981"];

export function BarChartComponent({ data, height = 260 }: BarChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No failure data available
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
          <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis
            type="category"
            dataKey="mode"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={110}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.75rem",
              fontSize: "12px",
            }}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
