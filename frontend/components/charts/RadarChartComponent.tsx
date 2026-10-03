"use client";
import React from "react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  Tooltip,
} from "recharts";

interface RadarDataPoint {
  dimension: string;
  count: number;
}

interface RadarChartComponentProps {
  data: RadarDataPoint[];
  height?: number;
}

export function RadarChartComponent({ data, height = 260 }: RadarChartComponentProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No dimension data available
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis
            dataKey="dimension"
            stroke="#94a3b8"
            fontSize={11}
            tick={{ fill: "#94a3b8" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.75rem",
              fontSize: "12px",
            }}
          />
          <Radar
            name="Evidence Count"
            dataKey="count"
            stroke="#818cf8"
            fill="#6366f1"
            fillOpacity={0.4}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
