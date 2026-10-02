"use client";

import { useState } from "react";
import { Search, ExternalLink, Activity, Sparkles, CheckCircle2 } from "lucide-react";
import { ApiService } from "@/lib/api";

export function Header() {
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkApi = async () => {
    setIsChecking(true);
    try {
      const res = await ApiService.checkHealth();
      setHealthStatus(res.status === "ok" ? "FastAPI: 200 OK" : "Degraded");
    } catch {
      setHealthStatus("Offline");
    } finally {
      setIsChecking(false);
      setTimeout(() => setHealthStatus(null), 3000);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Search Input */}
      <div className="relative w-96">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Semantic search across photo problems, clusters, or queries..."
          className="w-full bg-slate-900/80 border border-slate-800/80 rounded-lg pl-10 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500/60 transition-all font-sans"
        />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Phase Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-[11px] font-medium text-indigo-300">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Phase 1: Foundation Active</span>
        </div>

        {/* API Health Check */}
        <button
          onClick={checkApi}
          disabled={isChecking}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] font-medium text-slate-300 transition-colors"
          title="Verify FastAPI Health"
        >
          {healthStatus ? (
            <span className="flex items-center gap-1 text-emerald-400 font-mono">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              {healthStatus}
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <Activity className={`w-3 h-3 text-slate-400 ${isChecking ? "animate-spin" : ""}`} />
              {isChecking ? "Checking..." : "Ping API"}
            </span>
          )}
        </button>

        {/* Swagger Docs Link */}
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-colors"
          title="Open FastAPI Swagger Documentation"
        >
          <span>OpenAPI Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
}
