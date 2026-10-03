"use client";
import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Filter,
  ArrowUpRight,
  Search,
  Sparkles,
  SlidersHorizontal,
  Flame,
  CheckCircle2,
  Layers,
  ChevronDown,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton, EmptyState } from "@/components/ui/EmptyState";
import { ResearchBriefModal } from "@/components/ResearchBriefModal";

export default function ProblemsPage() {
  const [problems, setProblems] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedSource, setSelectedSource] = useState("all");
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [emergingOnly, setEmergingOnly] = useState(false);
  const [sortBy, setSortBy] = useState("frequency");
  const [isBriefModalOpen, setIsBriefModalOpen] = useState(false);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const res = await ApiService.getProblems({ limit: 100 });
        setProblems(res?.data || []);
      } catch (err) {
        console.error("Failed to load problems", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Extract all available taxonomy categories
  const categories = useMemo(() => {
    const set = new Set<string>();
    problems.forEach((p) => {
      (p.taxonomy_categories || []).forEach((c: string) => set.add(c));
    });
    return Array.from(set);
  }, [problems]);

  // Filter & Sort
  const filteredProblems = useMemo(() => {
    return problems
      .filter((p) => {
        // Search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchTitle = (p.title || "").toLowerCase().includes(q);
          const matchStmt = (p.statement || "").toLowerCase().includes(q);
          if (!matchTitle && !matchStmt) return false;
        }

        // Emerging only
        if (emergingOnly && !p.is_emerging) return false;

        // Taxonomy Category
        if (selectedCategory !== "all") {
          if (!p.taxonomy_categories || !p.taxonomy_categories.includes(selectedCategory)) {
            return false;
          }
        }

        // Min Confidence
        if (p.confidence !== null && p.confidence !== undefined && p.confidence < minConfidence) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === "frequency") return (b.frequency || 0) - (a.frequency || 0);
        if (sortBy === "severity") return (b.severity_score || 0) - (a.severity_score || 0);
        if (sortBy === "growth") return (b.growth_rate || 0) - (a.growth_rate || 0);
        return 0;
      });
  }, [problems, searchQuery, selectedCategory, emergingOnly, minConfidence, sortBy]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Discovered Problems & Needs
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Synthesized problem clusters extracted from user conversations, cross-referenced with human memory models and retrieval failure taxonomy.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="glow"
            size="md"
            onClick={() => setIsBriefModalOpen(true)}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Generate Research Brief
          </Button>
        </div>
      </div>

      {/* Main Layout: Filters Sidebar + Problem Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
                <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                <span>Filters</span>
              </div>
              <button
                onClick={() => {
                  setSearchQuery("");
                  setSelectedCategory("all");
                  setSelectedSource("all");
                  setMinConfidence(0.0);
                  setEmergingOnly(false);
                }}
                className="text-[11px] text-slate-400 hover:text-white transition-colors"
              >
                Reset
              </button>
            </div>

            {/* Emerging Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800">
              <label htmlFor="emerging-toggle" className="text-xs font-medium text-slate-200 flex items-center gap-1.5 cursor-pointer">
                <Flame className="w-4 h-4 text-rose-400" />
                <span>Emerging Only</span>
              </label>
              <input
                id="emerging-toggle"
                type="checkbox"
                checked={emergingOnly}
                onChange={(e) => setEmergingOnly(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            {/* Taxonomy Category */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Taxonomy Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Categories ({categories.length})</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Minimum AI Confidence */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300 uppercase tracking-wider">
                  Min AI Confidence
                </span>
                <span className="font-bold text-indigo-400">{Math.round(minConfidence * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.95"
                step="0.05"
                value={minConfidence}
                onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
            </div>

            {/* Sort Order */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="frequency">Conversation Frequency (High to Low)</option>
                <option value="severity">Severity Score (High to Low)</option>
                <option value="growth">Growth Velocity (Fastest Emerging)</option>
              </select>
            </div>
          </Card>
        </div>

        {/* Problems List */}
        <div className="lg:col-span-3 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search problem statements, failure modes, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/60 border border-slate-800/80 rounded-2xl pl-11 pr-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/80 shadow-lg"
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Showing {filteredProblems.length} discovered problems</span>
            <span>Sorted by {sortBy}</span>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-40 w-full" />
              ))}
            </div>
          ) : filteredProblems.length === 0 ? (
            <EmptyState
              title="No problems found"
              description="No synthesized problems match the current filter or search criteria."
              action={
                <Button size="sm" variant="outline" onClick={() => { setSearchQuery(""); setSelectedCategory("all"); setEmergingOnly(false); }}>
                  Clear Filters
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              {filteredProblems.map((prob) => {
                const severityPct = Math.round((prob.severity_score || 0.5) * 100);
                const confidencePct = Math.round((prob.confidence || 0.8) * 100);
                const growthRate = prob.growth_rate ? Math.round(prob.growth_rate * 100) : 0;

                return (
                  <Card key={prob.id} hover className="p-6">
                    <div className="space-y-4">
                      {/* Card Header */}
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                        <div className="space-y-1.5 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <Link
                              href={`/problems/${prob.id}`}
                              className="text-base font-bold text-white hover:text-indigo-400 transition-colors"
                            >
                              {prob.title}
                            </Link>
                            {prob.is_emerging && (
                              <Badge variant="rose" size="sm">
                                <Flame className="w-3 h-3 mr-1 inline" />
                                +{growthRate}% Emerging
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {prob.statement}
                          </p>
                        </div>

                        <Link
                          href={`/problems/${prob.id}`}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-indigo-600 transition-colors text-xs font-medium self-start flex-shrink-0"
                        >
                          <span>Explore Detail</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>

                      {/* Taxonomy Pills */}
                      <div className="flex flex-wrap gap-1.5">
                        {(prob.taxonomy_categories || []).map((cat: string, idx: number) => (
                          <Badge key={idx} variant="indigo" size="sm">
                            {cat}
                          </Badge>
                        ))}
                      </div>

                      {/* Metrics Footer */}
                      <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400">
                        <div className="flex items-center gap-4">
                          <div>
                            <span className="text-slate-500 mr-1.5">Frequency:</span>
                            <span className="font-semibold text-white">{prob.frequency} convs</span>
                          </div>
                          <div>
                            <span className="text-slate-500 mr-1.5">Platforms:</span>
                            <span className="font-semibold text-white">{prob.source_count || 1}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 mr-1.5">Severity:</span>
                            <span className={`font-semibold ${severityPct > 70 ? "text-rose-400" : "text-amber-400"}`}>
                              {severityPct}%
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-slate-500">AI Confidence:</span>
                          <span className="font-semibold text-slate-200">{confidencePct}%</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
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
