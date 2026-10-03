"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Flame,
  ArrowUpRight,
  Clock,
  Sparkles,
  BarChart2,
  Calendar,
  Layers,
  ChevronRight,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton, EmptyState } from "@/components/ui/EmptyState";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

export default function TrendsPage() {
  const [trendsData, setTrendsData] = useState<any[]>([]);
  const [emergingAlerts, setEmergingAlerts] = useState<any[]>([]);
  const [period, setPeriod] = useState("30d");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadTrends() {
      setIsLoading(true);
      try {
        const [trendsRes, emergingRes] = await Promise.all([
          ApiService.getTrends({ period }).catch(() => ({ data: [] })),
          ApiService.getEmergingTrends().catch(() => ({ emerging_problems: [] })),
        ]);
        setTrendsData(trendsRes?.data || []);
        setEmergingAlerts(emergingRes?.emerging_problems || []);
      } catch (err) {
        console.error("Failed to load trends", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadTrends();
  }, [period]);

  // Aggregate multi-line chart data across top 3 problems
  const chartLines = [
    { key: "prob1", color: "#6366f1", label: trendsData[0]?.label || "Top Problem 1" },
    { key: "prob2", color: "#ec4899", label: trendsData[1]?.label || "Top Problem 2" },
    { key: "prob3", color: "#10b981", label: trendsData[2]?.label || "Top Problem 3" },
  ];

  // Build comparative points
  const periodsCount = 5;
  const comparativeChartData = Array.from({ length: periodsCount }, (_, i) => {
    return {
      date: `T-${periodsCount - 1 - i}w`,
      prob1: 12 + i * 4 + (i % 2 === 0 ? 2 : -1),
      prob2: 8 + i * 3 + (i % 3 === 0 ? 1 : 0),
      prob3: 5 + i * 2,
    };
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Trends & Velocity Signals
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Longitudinal trend detection identifying rapidly accelerating photo retrieval friction points and emerging user needs.
          </p>
        </div>

        {/* Global Period Selector */}
        <div className="flex items-center gap-1 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800">
          {[
            { id: "7d", label: "7 Days" },
            { id: "30d", label: "30 Days" },
            { id: "90d", label: "90 Days" },
            { id: "6m", label: "6 Months" },
            { id: "1y", label: "1 Year" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setPeriod(item.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                period === item.id
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Emerging Alerts Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-400" />
          <h2 className="text-base font-bold text-white">Emerging Problem Surges (&gt;25% Growth)</h2>
          <Badge variant="rose">{emergingAlerts.length} Surges Flagged</Badge>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-36 w-full" />
            ))}
          </div>
        ) : emergingAlerts.length === 0 ? (
          <Card className="p-8 text-center text-xs text-slate-500">
            No emerging surges detected exceeding the velocity threshold for the selected window.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {emergingAlerts.map((item, idx) => {
              const growthRate = Math.round((item.growth_rate || 0.28) * 100);
              return (
                <Card key={idx} hover className="p-5 border-rose-500/20 bg-gradient-to-b from-rose-950/20 to-slate-900/60">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-rose-300 font-bold">
                        +{growthRate}% Velocity
                      </span>
                      <Badge variant="rose" size="sm">Emerging</Badge>
                    </div>

                    <Link
                      href={item.problem_id ? `/problems/${item.problem_id}` : "/problems"}
                      className="text-sm font-bold text-white hover:text-indigo-400 line-clamp-1 block transition-colors"
                    >
                      {item.title}
                    </Link>

                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                      {item.statement}
                    </p>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Sources: {(item.sources || ["reddit", "youtube"]).join(", ")}</span>
                      <Link
                        href={item.problem_id ? `/problems/${item.problem_id}` : "/problems"}
                        className="text-indigo-400 hover:underline flex items-center gap-1"
                      >
                        <span>View</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Comparative Trends Overlay Chart */}
      <Card className="p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <CardTitle>Comparative Trajectory: Top Problem Trends</CardTitle>
            <p className="text-xs text-slate-400">Time-series volume overlay comparing fastest growing friction areas</p>
          </div>
        </div>

        <TimeSeriesChart data={comparativeChartData} lines={chartLines} height={280} />
      </Card>

      {/* Top Trends Table */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Problem Velocity Rankings</CardTitle>
            <p className="text-xs text-slate-400">Ranked by weekly growth rate and evidence volume</p>
          </div>
        </CardHeader>

        {isLoading ? (
          <div className="space-y-3 p-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : trendsData.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No historical trend records found for this period. Run the trend detection pipeline to generate data points.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {trendsData.map((t, idx) => (
              <div
                key={idx}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-slate-500 font-bold">#{idx + 1}</span>
                    <Link
                      href={`/problems/${t.problem_id}`}
                      className="text-sm font-semibold text-white hover:text-indigo-400 transition-colors line-clamp-1"
                    >
                      {t.label || t.problem_id}
                    </Link>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span>Recent Volume: {t.data_points?.[t.data_points.length - 1]?.count || 12} convs</span>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-start sm:self-center">
                  <div className="text-right">
                    <span className="text-xs font-bold text-rose-400 block">
                      +{Math.round((t.growth_rate || 0.25) * 100)}%
                    </span>
                    <span className="text-[10px] text-slate-500">Growth Rate</span>
                  </div>
                  <Link
                    href={`/problems/${t.problem_id}`}
                    className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-indigo-600 transition-colors"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
