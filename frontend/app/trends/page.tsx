"use client";

import { TrendingUp, Flame, ArrowUpRight, Zap, Clock, BarChart3 } from "lucide-react";

interface TrendItem {
  id: string;
  topic: string;
  category: string;
  growthRate: string;
  acceleration: "Hyper-Growth" | "High" | "Moderate";
  volume: number;
  firstSeen: string;
  summary: string;
}

const MOCK_TRENDS: TrendItem[] = [
  {
    id: "TR-01",
    topic: "Multi-modal Voice Photo Search Failures",
    category: "Voice & Conversational AI",
    growthRate: "+64% WoW",
    acceleration: "Hyper-Growth",
    volume: 512,
    firstSeen: "2 weeks ago",
    summary: "Sharp spike in user complaints when attempting to dictate complex multi-attribute queries into smart assistants (e.g. 'show me my cat jumping onto the couch last winter').",
  },
  {
    id: "TR-02",
    topic: "Local On-Device Photo Indexing Privacy Demand",
    category: "Privacy & Cloud Security",
    growthRate: "+42% WoW",
    acceleration: "High",
    volume: 389,
    firstSeen: "1 month ago",
    summary: "Users migrating away from pure cloud indexing due to data sovereignty concerns and seeking local vector embeddings on mobile hardware.",
  },
  {
    id: "TR-03",
    topic: "Accidental Deletion via Aggressive AI Cleanup Suggestions",
    category: "Data Integrity & UX",
    growthRate: "+31% WoW",
    acceleration: "High",
    volume: 275,
    firstSeen: "3 weeks ago",
    summary: "Smart storage cleanup utilities flagging bursts and bracketed exposures as redundant, causing inadvertent loss of intentional sequence shots.",
  },
  {
    id: "TR-04",
    topic: "Digitized Analog Negative & Slide Categorization",
    category: "Format Diversity",
    growthRate: "+26% WoW",
    acceleration: "Moderate",
    volume: 198,
    firstSeen: "6 weeks ago",
    summary: "Resurgence in analog film scanning where users demand automated timestamp backdating and film stock color profile tagging.",
  },
];

export default function TrendsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Emerging Trends & Velocity</h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
              Velocity Threshold: &gt;25% WoW
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time detection of rapidly growing pain points before they become saturated market complaints.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>Window: Last 30 Days</span>
        </div>
      </div>

      {/* Grid of Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {MOCK_TRENDS.map((trend) => (
          <div
            key={trend.id}
            className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all duration-200 group hover:shadow-2xl flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">{trend.category}</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                    trend.acceleration === "Hyper-Growth"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
                      : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  }`}
                >
                  {trend.acceleration}
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                {trend.topic}
              </h3>

              <p className="text-xs text-slate-400 leading-relaxed">
                {trend.summary}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1 text-emerald-400 font-bold font-mono">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>{trend.growthRate}</span>
                </div>
                <span className="text-slate-600">•</span>
                <span className="text-slate-400 font-mono text-[11px]">{trend.volume} signals</span>
              </div>

              <span className="text-[11px] text-slate-500">First seen {trend.firstSeen}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
