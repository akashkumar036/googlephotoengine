"use client";

import { useState } from "react";
import { Compass, Search, Sparkles, Sliders, Database, Layers, ArrowRight } from "lucide-react";

interface SemanticCluster {
  id: string;
  name: string;
  exemplarQuote: string;
  memberCount: number;
  cohesionScore: number;
  topTerms: string[];
}

const MOCK_CLUSTERS: SemanticCluster[] = [
  {
    id: "CLUST-14",
    name: "Multi-Attribute Temporal Search Dropouts",
    exemplarQuote: "I try searching for 'blue dress Italy vacation 2022' and it matches any picture with blue sky.",
    memberCount: 284,
    cohesionScore: 0.88,
    topTerms: ["temporal", "conjunctions", "false_positives", "attributes"],
  },
  {
    id: "CLUST-09",
    name: "Cloud Sync Collisions & Ghost Albums",
    exemplarQuote: "Google Photos and iCloud fighting over local storage causing photos to vanish from recent gallery.",
    memberCount: 196,
    cohesionScore: 0.84,
    topTerms: ["sync", "conflict", "icloud", "ghost_album"],
  },
  {
    id: "CLUST-22",
    name: "Analog EXIF Metadata Injection",
    exemplarQuote: "Need a way to automatically predict camera and date for scanned negatives based on surrounding roll context.",
    memberCount: 142,
    cohesionScore: 0.79,
    topTerms: ["scans", "negatives", "exif", "backdating"],
  },
];

export default function ExplorePage() {
  const [similarityQuery, setSimilarityQuery] = useState("");
  const [threshold, setThreshold] = useState(0.82);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight text-white">Semantic Explorer</h1>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            pgvector HNSW Cosine
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Explore semantic clusters, query the 1536-dimensional embedding space, and discover latent photo problems.
        </p>
      </div>

      {/* Query Bar & Vector Controls */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Enter hypothetical user frustration or query (e.g., 'can't search by pet name without tag')..."
              value={similarityQuery}
              onChange={(e) => setSimilarityQuery(e.target.value)}
              className="w-full bg-slate-950/70 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Vector Match</span>
          </button>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 text-xs text-slate-400 border-t border-slate-800/60">
          <div className="flex items-center gap-3">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <span>Cosine Similarity Cutoff:</span>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-32 accent-indigo-500 cursor-pointer"
            />
            <span className="font-mono text-indigo-400 font-bold">{threshold}</span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span>Metric: vector_cosine_ops</span>
            <span>Index: HNSW (m=16, ef=64)</span>
          </div>
        </div>
      </div>

      {/* Discovered Semantic Clusters */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Discovered DBSCAN Semantic Clusters
          </h2>
          <span className="text-xs text-slate-400">12 Active Clusters Found</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {MOCK_CLUSTERS.map((cluster) => (
            <div
              key={cluster.id}
              className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-indigo-400 font-semibold">{cluster.id}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Cohesion: {(cluster.cohesionScore * 100).toFixed(0)}%
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-100">{cluster.name}</h3>
                <p className="text-xs text-slate-400 italic bg-slate-950/50 p-3 rounded-lg border border-slate-800/40">
                  "{cluster.exemplarQuote}"
                </p>
              </div>

              <div className="space-y-3 pt-2">
                <div className="flex flex-wrap gap-1">
                  {cluster.topTerms.map((term, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/50"
                    >
                      #{term}
                    </span>
                  ))}
                </div>

                <div className="pt-2 border-t border-slate-800/70 flex items-center justify-between text-xs text-slate-400">
                  <span>{cluster.memberCount} members</span>
                  <button className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 text-xs">
                    <span>Inspect</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
