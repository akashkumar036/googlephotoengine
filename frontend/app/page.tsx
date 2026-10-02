"use client";

import Link from "next/link";
import {
  Layers,
  AlertTriangle,
  Flame,
  ArrowUpRight,
  Database,
  Cpu,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronRight,
  CheckCircle2,
  Clock,
  Sparkles,
} from "lucide-react";

export default function OverviewPage() {
  const stats = [
    {
      title: "Ingested Conversations",
      value: "14,820",
      change: "+18.4% this week",
      trend: "up",
      icon: Layers,
      color: "from-blue-500/20 to-indigo-500/20 text-indigo-400 border-indigo-500/30",
    },
    {
      title: "Synthesized Problems",
      value: "42",
      change: "12 Critical (P0/P1)",
      trend: "up",
      icon: AlertTriangle,
      color: "from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/30",
    },
    {
      title: "Emerging Trends",
      value: "9",
      change: "4 with velocity > 30%",
      trend: "up",
      icon: Flame,
      color: "from-rose-500/20 to-pink-500/20 text-rose-400 border-rose-500/30",
    },
    {
      title: "Vector Embeddings",
      value: "14,820",
      change: "1536-dim HNSW Cosine",
      trend: "neutral",
      icon: Database,
      color: "from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30",
    },
  ];

  const recentProblems = [
    {
      id: "P-101",
      title: "Inability to find specific photos by date or context",
      category: "search_accuracy",
      severity: "P0",
      conversations: 412,
      trend: "+34%",
      status: "Verified",
    },
    {
      id: "P-102",
      title: "Accidental duplicates after cloud sync and family sharing",
      category: "sync_duplicates",
      severity: "P1",
      conversations: 289,
      trend: "+12%",
      status: "In Review",
    },
    {
      id: "P-103",
      title: "Failed natural language queries with multi-attribute criteria",
      category: "nlp_search",
      severity: "P1",
      conversations: 204,
      trend: "+45%",
      status: "Verified",
    },
    {
      id: "P-104",
      title: "Unwanted memories surfaced during sensitive events",
      category: "privacy_emotional",
      severity: "P2",
      conversations: 135,
      trend: "-5%",
      status: "Monitoring",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900/80 to-purple-950/50 border border-indigo-500/20 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-xs font-medium text-indigo-300">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Phase 1 Initialized • Foundation Scaffold Active</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Photo Retrieval Discovery Engine
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Automated user signal intelligence: aggregating public discussions, Reddit threads, and community feedback to discover unmet photo search needs, synthesize clusters, and surface high-value product opportunities.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/explore"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/30 hover:scale-[1.02]"
            >
              <Search className="w-4 h-4" />
              <span>Semantic Explorer</span>
            </Link>
            <Link
              href="/problems"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-medium text-sm transition-all hover:scale-[1.02]"
            >
              <span>View Problems</span>
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div
              key={i}
              className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all duration-200 group hover:shadow-xl"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{stat.title}</span>
                <div className={`p-2 rounded-lg bg-gradient-to-br border ${stat.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-slate-100 tracking-tight font-mono">
                  {stat.value}
                </div>
                <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="text-emerald-400 font-medium">{stat.change}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Architecture & Pipeline Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Architecture */}
        <div className="lg:col-span-1 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Engine Architecture
            </h2>
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
              STABLE
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Primary LLM Provider</span>
                <span className="text-slate-200 font-semibold">Groq Cloud</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Llama-3.1-8b-instant (Stage 1) & Llama-3.3-70b-versatile (Stage 2)
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Vector Search</span>
                <span className="text-slate-200 font-semibold">pgvector 0.7+</span>
              </div>
              <p className="text-[11px] text-slate-500">
                1536-dimensional embeddings with HNSW indexing
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Job Orchestration</span>
                <span className="text-slate-200 font-semibold">Celery + Redis 7</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Crash-safe processing with acks_late & retry backoff
              </p>
            </div>
          </div>
        </div>

        {/* Synthesized Top Problems */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                High-Impact Discovered Problems
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Problems synthesized from unsupervised clustering & AI classification
              </p>
            </div>
            <Link
              href="/problems"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              <span>View all 42</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-800/70">
            {recentProblems.map((prob) => (
              <div
                key={prob.id}
                className="py-3 flex items-center justify-between gap-4 hover:bg-slate-800/30 px-2 rounded-lg transition-colors group"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        prob.severity === "P0"
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                          : prob.severity === "P1"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                      }`}
                    >
                      {prob.severity}
                    </span>
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors truncate">
                      {prob.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span>{prob.conversations} evidence quotes</span>
                    <span>•</span>
                    <span className="text-emerald-400 font-medium">{prob.trend} growth</span>
                    <span>•</span>
                    <span className="capitalize">{prob.category.replace("_", " ")}</span>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {prob.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
