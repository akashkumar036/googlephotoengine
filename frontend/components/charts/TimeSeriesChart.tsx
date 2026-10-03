"use client";
import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface DataPoint {
  date: string;
  [key: string]: any;
}

interface TimeSeriesChartProps {
  data: DataPoint[];
  lines?: { key: string; color: string; label: string }[];
  height?: number;
}

export function TimeSeriesChart({
  data,
  lines = [{ key: "count", color: "#6366f1", label: "Volume" }],
  height = 260,
}: TimeSeriesChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No time-series points available
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: "#334155" }}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.75rem",
              fontSize: "12px",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
            }}
            labelStyle={{ color: "#94a3b8", fontWeight: 600, marginBottom: "4px" }}
          />
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.label}
              stroke={line.color}
              strokeWidth={2.5}
              dot={{ r: 3, fill: line.color, strokeWidth: 0 }}
              activeDot={{ r: 6, fill: line.color, stroke: "#0f172a", strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
