"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Layers,
  AlertTriangle,
  Flame,
  Database,
  ArrowUpRight,
  Sparkles,
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Clock,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/EmptyState";
import { RadarChartComponent } from "@/components/charts/RadarChartComponent";
import { BarChartComponent } from "@/components/charts/BarChartComponent";
import { DonutChartComponent } from "@/components/charts/DonutChartComponent";
import { ResearchBriefModal } from "@/components/ResearchBriefModal";

export default function OverviewPage() {
  const [statsData, setStatsData] = useState<any>(null);
  const [problems, setProblems] = useState<any[]>([]);
  const [emergingAlerts, setEmergingAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isBriefModalOpen, setIsBriefModalOpen] = useState(false);

  const fetchOverview = async () => {
    setIsLoading(true);
    try {
      const [statsRes, problemsRes, emergingRes] = await Promise.all([
        ApiService.getStats().catch(() => null),
        ApiService.getProblems({ limit: 6 }).catch(() => ({ data: [] })),
        ApiService.getEmergingTrends().catch(() => ({ emerging_problems: [] })),
      ]);

      setStatsData(statsRes);
      setProblems(problemsRes?.data || []);
      setEmergingAlerts(emergingRes?.emerging_problems || []);
    } catch (err) {
      console.error("Failed to load overview data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const kpis = statsData?.kpis || {};

  const statCards = [
    {
      title: "Total Conversations",
      value: kpis.total_conversations?.toLocaleString() ?? "0",
      sub: `${kpis.relevant_conversations ?? 0} relevant to photo retrieval`,
      icon: Layers,
      color: "from-blue-500/10 to-indigo-500/10 border-indigo-500/20 text-indigo-400",
    },
    {
      title: "Synthesized Problems",
      value: kpis.total_problems?.toLocaleString() ?? "0",
      sub: `${kpis.emerging_problems ?? 0} flagged as emerging`,
      icon: AlertTriangle,
      color: "from-amber-500/10 to-orange-500/10 border-amber-500/20 text-amber-400",
    },
    {
      title: "Emerging Alerts",
      value: emergingAlerts.length.toString(),
      sub: "Velocity > 25% across multiple sources",
      icon: Flame,
      color: "from-rose-500/10 to-pink-500/10 border-rose-500/20 text-rose-400",
    },
    {
      title: "Semantic Clusters",
      value: kpis.total_clusters?.toLocaleString() ?? "0",
      sub: "DBSCAN hybrid with AI labeling",
      icon: TrendingUp,
      color: "from-purple-500/10 to-violet-500/10 border-purple-500/20 text-purple-400",
    },
    {
      title: "Vector Embeddings",
      value: kpis.vector_embeddings?.toLocaleString() ?? "0",
      sub: "1536-dim HNSW indexed in pgvector",
      icon: Database,
      color: "from-emerald-500/10 to-teal-500/10 border-emerald-500/20 text-emerald-400",
    },
    {
      title: "AI Analyses Completed",
      value: kpis.analyzed_conversations?.toLocaleString() ?? "0",
      sub: "Stage 1 + Stage 2 deep extraction",
      icon: Sparkles,
      color: "from-cyan-500/10 to-sky-500/10 border-cyan-500/20 text-cyan-400",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/70 via-slate-900/90 to-purple-950/60 border border-indigo-500/20 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Phase 5 Research Dashboard Active</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Photo Retrieval Discovery Engine
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Synthesizing unstructured user conversations from Reddit, YouTube, and app reviews into validated photo discovery problem clusters and opportunity spaces.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="md"
              onClick={fetchOverview}
              icon={<RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />}
            >
              Sync
            </Button>
            <Button
              variant="glow"
              size="md"
              onClick={() => setIsBriefModalOpen(true)}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Generate Brief
            </Button>
          </div>
        </div>
      </div>

      {/* 6 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {statCards.map((card, idx) => (
          <Card key={idx} className={`bg-gradient-to-br ${card.color} border`}>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-3 w-40" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
                    {card.title}
                  </span>
                  <card.icon className="w-5 h-5 opacity-80" />
                </div>
                <div className="text-3xl font-black tracking-tight text-white">
                  {card.value}
                </div>
                <p className="text-xs text-slate-400">{card.sub}</p>
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Grid: Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Radar Chart: Memory Dimensions */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <div>
              <CardTitle>Memory Dimensions</CardTitle>
              <p className="text-xs text-slate-400">Human memory retrieval anchors</p>
            </div>
          </CardHeader>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <RadarChartComponent data={statsData?.memory_distribution || []} />
          )}
        </Card>

        {/* Bar Chart: Retrieval Failure Modes */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <div>
              <CardTitle>Retrieval Failure Modes</CardTitle>
              <p className="text-xs text-slate-400">Core breakdown of user queries</p>
            </div>
          </CardHeader>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <BarChartComponent data={statsData?.failure_distribution || []} />
          )}
        </Card>

        {/* Donut Chart: Source Platform Distribution */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <div>
              <CardTitle>Platform Distribution</CardTitle>
              <p className="text-xs text-slate-400">Evidence volume across sources</p>
            </div>
          </CardHeader>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <DonutChartComponent data={statsData?.source_breakdown || []} />
          )}
        </Card>
      </div>

      {/* Grid: Emerging Alerts & Top Problems */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Problems Table (2 cols) */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Discovered Problem Clusters</CardTitle>
              <p className="text-xs text-slate-400">Ranked by frequency, severity, and evidence backing</p>
            </div>
            <Link
              href="/problems"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              <span>View All</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </CardHeader>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : problems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No synthesized problems available yet. Run ingestion or pipeline demo to populate.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {problems.map((prob) => (
                <div
                  key={prob.id}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/30 px-3 rounded-xl transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/problems/${prob.id}`}
                        className="text-sm font-semibold text-slate-100 hover:text-indigo-400 transition-colors line-clamp-1"
                      >
                        {prob.title}
                      </Link>
                      {prob.is_emerging && (
                        <Badge variant="rose" size="sm">
                          Emerging
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{prob.statement}</p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>{prob.frequency} conversations</span>
                      <span>•</span>
                      <span>{prob.source_count || 1} platforms</span>
                      <span>•</span>
                      <span>Severity: {Math.round((prob.severity_score || 0.5) * 100)}%</span>
                    </div>
                  </div>
                  <Link
                    href={`/problems/${prob.id}`}
                    className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-indigo-600 transition-colors flex-shrink-0 self-start sm:self-center"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Emerging Alerts & Recent Activity Feed */}
        <div className="space-y-6 lg:col-span-1">
          {/* Emerging Alerts Panel */}
          <Card className="border-rose-500/20 bg-gradient-to-b from-rose-950/10 to-slate-900/60">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-rose-400" />
                <CardTitle>Emerging Problem Alerts</CardTitle>
              </div>
              <Badge variant="rose" size="sm">{emergingAlerts.length} Active</Badge>
            </CardHeader>

            {emergingAlerts.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">
                No active emerging surges exceeding 25% growth threshold.
              </p>
            ) : (
              <div className="space-y-3">
                {emergingAlerts.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-rose-500/20 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-rose-200 line-clamp-1">
                        {item.title}
                      </span>
                      <span className="text-[11px] font-bold text-rose-400">
                        +{Math.round((item.growth_rate || 0.3) * 100)}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1">{item.statement}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Activity Feed */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-400" />
                <CardTitle>Recent Activity</CardTitle>
              </div>
            </CardHeader>
            <div className="space-y-3">
              {(statsData?.recent_activity || []).slice(0, 4).map((act: any) => (
                <div key={act.id} className="text-xs flex items-start gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-slate-200 font-medium">{act.title}</p>
                    <span className="text-[10px] text-slate-500">{act.time ? new Date(act.time).toLocaleDateString() : "Just now"}</span>
                  </div>
                </div>
              ))}
              {(!statsData?.recent_activity || statsData.recent_activity.length === 0) && (
                <p className="text-xs text-slate-500 text-center py-4">No recent activity logs.</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Brief Modal */}
      <ResearchBriefModal
        isOpen={isBriefModalOpen}
        onClose={() => setIsBriefModalOpen(false)}
      />
    </div>
  );
}
