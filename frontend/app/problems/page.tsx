"use client";

import { useState } from "react";
import { AlertCircle, Filter, ArrowUpRight, Search, Sparkles, CheckCircle2, SlidersHorizontal } from "lucide-react";

interface ProblemItem {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: "P0" | "P1" | "P2";
  evidenceCount: number;
  opportunityScore: number;
  velocity: string;
  status: "Verified" | "Review Pending" | "Needs Evidence";
}

const MOCK_PROBLEMS: ProblemItem[] = [
  {
    id: "PROB-001",
    title: "Exact Date and Location Search Query Failures",
    description: "Users struggle to recall exact timestamps or geolocations, leading to repetitive query abandonment when searching for vacation or family photos.",
    category: "Search Accuracy",
    severity: "P0",
    evidenceCount: 542,
    opportunityScore: 92,
    velocity: "+28%",
    status: "Verified",
  },
  {
    id: "PROB-002",
    title: "Accidental Duplicate Explosion Across Shared Albums",
    description: "Family sharing and cross-device sync creates unlinked duplicates that clutter search galleries and inflate storage quotas.",
    category: "Library Organization",
    severity: "P1",
    evidenceCount: 388,
    opportunityScore: 84,
    velocity: "+14%",
    status: "Verified",
  },
  {
    id: "PROB-003",
    title: "Multi-Subject Semantic Search Confusion",
    description: "Natural language searches with multiple entities (e.g., 'photo of dad holding the brown dog at the beach in 2021') drop key qualifiers and return false positives.",
    category: "NLP Retrieval",
    severity: "P1",
    evidenceCount: 310,
    opportunityScore: 78,
    velocity: "+41%",
    status: "Review Pending",
  },
  {
    id: "PROB-004",
    title: "Surfacing Grief and Sensitive Memories Automatically",
    description: "Algorithmic 'On this day' widgets inappropriately surface traumatic life events or ex-partners without explicit opt-out controls.",
    category: "Privacy & Emotional",
    severity: "P0",
    evidenceCount: 224,
    opportunityScore: 88,
    velocity: "+19%",
    status: "Verified",
  },
  {
    id: "PROB-005",
    title: "Receipt, Document, and Screenshot Clutter",
    description: "Ephemeral utility captures drown out artistic and personal memories, making legacy photo discovery laborious.",
    category: "Utility Separation",
    severity: "P2",
    evidenceCount: 195,
    opportunityScore: 68,
    velocity: "+7%",
    status: "Needs Evidence",
  },
];

export default function ProblemsPage() {
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = MOCK_PROBLEMS.filter((p) => {
    if (filterSeverity !== "all" && p.severity !== filterSeverity) return false;
    if (
      searchQuery &&
      !p.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !p.description.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Problems & Opportunities</h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
              Synthesized by AI
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized product problem statements extracted from semantic clusters and user evidence.
          </p>
        </div>

        <button className="self-start sm:self-auto inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/30 transition-all">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Synthesize New Problems</span>
        </button>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Filter problems..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <SlidersHorizontal className="w-4 h-4 text-slate-500 shrink-0" />
          <span className="text-xs text-slate-400">Severity:</span>
          {["all", "P0", "P1", "P2"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterSeverity === sev
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {sev.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Problems List */}
      <div className="space-y-4">
        {filtered.map((problem) => (
          <div
            key={problem.id}
            className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all duration-200 group hover:shadow-xl space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      problem.severity === "P0"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        : problem.severity === "P1"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    }`}
                  >
                    {problem.severity}
                  </span>
                  <span className="text-xs font-mono text-slate-500">{problem.id}</span>
                  <h3 className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors">
                    {problem.title}
                  </h3>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
                  {problem.description}
                </p>
              </div>

              <div className="flex sm:flex-col items-end gap-1.5 shrink-0">
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-slate-500 block">
                    Opportunity Score
                  </span>
                  <span className="text-base font-bold font-mono text-emerald-400">
                    {problem.opportunityScore}/100
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400 flex-wrap gap-2">
              <div className="flex items-center gap-4">
                <span>Category: <strong className="text-slate-300">{problem.category}</strong></span>
                <span>Evidence: <strong className="text-slate-300">{problem.evidenceCount} sources</strong></span>
                <span>Velocity: <strong className="text-emerald-400">{problem.velocity}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {problem.status}
                </span>
                <button className="text-indigo-400 hover:text-indigo-300 text-xs font-medium flex items-center gap-1 group/btn">
                  <span>Deep Dive</span>
                  <ArrowUpRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
