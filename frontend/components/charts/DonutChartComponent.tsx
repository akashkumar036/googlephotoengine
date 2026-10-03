"use client";
import React from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

interface DonutDataPoint {
  source: string;
  count: number;
}

interface DonutChartComponentProps {
  data: DonutDataPoint[];
  height?: number;
}

const DONUT_COLORS = ["#6366f1", "#ec4899", "#f59e0b", "#10b981", "#06b6d4", "#8b5cf6"];

export function DonutChartComponent({ data, height = 260 }: DonutChartComponentProps) {
  if (!data || data.length === 0 || data.every((d) => d.count === 0)) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No platform source breakdown available
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <Pie
            data={data}
            dataKey="count"
            nameKey="source"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={4}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.75rem",
              fontSize: "12px",
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            formatter={(value) => <span className="text-xs text-slate-400">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
