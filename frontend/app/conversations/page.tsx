"use client";
import React, { useEffect, useState, useMemo } from "react";
import {
  MessageSquare,
  Search,
  SlidersHorizontal,
  ExternalLink,
  Sparkles,
  Calendar,
  Layers,
  CheckCircle2,
  ShieldAlert,
  X,
  Code2,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton, EmptyState } from "@/components/ui/EmptyState";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchingNL, setIsSearchingNL] = useState(false);
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedIntent, setSelectedIntent] = useState("all");
  const [selectedMemory, setSelectedMemory] = useState("all");
  const [selectedFailure, setSelectedFailure] = useState("all");
  const [relevantOnly, setRelevantOnly] = useState(true);
  const [activeModalConv, setActiveModalConv] = useState<any | null>(null);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const res = await ApiService.getConversations({
        limit: 100,
        is_relevant: relevantOnly ? true : undefined,
      });
      setConversations(res?.data || []);
    } catch (err) {
      console.error("Failed to load conversations", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [relevantOnly]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadConversations();
      return;
    }

    setIsSearchingNL(true);
    setIsLoading(true);
    try {
      const res = await ApiService.searchConversations(searchQuery.trim(), 40);
      setConversations(res?.data || []);
    } catch (err) {
      console.error("Semantic search failed", err);
    } finally {
      setIsLoading(false);
      setIsSearchingNL(false);
    }
  };

  // Filter conversations
  const filteredList = useMemo(() => {
    return conversations.filter((c) => {
      if (selectedSource !== "all" && c.source?.toLowerCase() !== selectedSource.toLowerCase()) {
        return false;
      }
      const analysis = c.analysis;
      if (selectedIntent !== "all" && analysis?.primary_intent !== selectedIntent) {
        return false;
      }
      if (selectedMemory !== "all") {
        const mems = (analysis?.memory_types || []).map((m: string) => m.toLowerCase());
        if (!mems.includes(selectedMemory.toLowerCase())) return false;
      }
      if (selectedFailure !== "all") {
        const fails = (analysis?.failure_modes || []).map((f: string) => f.toLowerCase());
        if (!fails.includes(selectedFailure.toLowerCase())) return false;
      }
      return true;
    });
  }, [conversations, selectedSource, selectedIntent, selectedMemory, selectedFailure]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Indexed Conversations & Feedback
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Normalized user posts, reviews, and comment threads enriched with two-stage LLM intent extraction, memory dimensions, and failure modes.
          </p>
        </div>
      </div>

      {/* Semantic Search Box */}
      <Card className="p-4 bg-slate-900/80 border-slate-800">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search semantically (e.g., 'users who cannot find photos from a wedding or vacation')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button type="submit" variant="primary" size="md" isLoading={isSearchingNL}>
              Vector Search
            </Button>
            {searchQuery && (
              <Button
                type="button"
                variant="ghost"
                size="md"
                onClick={() => {
                  setSearchQuery("");
                  loadConversations();
                }}
              >
                Clear
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Main Layout: Filters + List */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
                <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                <span>Filters</span>
              </div>
              <button
                onClick={() => {
                  setSelectedSource("all");
                  setSelectedIntent("all");
                  setSelectedMemory("all");
                  setSelectedFailure("all");
                }}
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Reset
              </button>
            </div>

            {/* Relevant Only Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800">
              <label htmlFor="conv-relevant-toggle" className="text-xs font-medium text-slate-200 cursor-pointer">
                Photo Discovery Relevant
              </label>
              <input
                id="conv-relevant-toggle"
                type="checkbox"
                checked={relevantOnly}
                onChange={(e) => setRelevantOnly(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            {/* Platform Source */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Source Channel
              </label>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Sources</option>
                <option value="reddit">Reddit</option>
                <option value="youtube">YouTube</option>
                <option value="google_play">Google Play Store</option>
                <option value="demo">Synthetic Demo Dataset</option>
              </select>
            </div>

            {/* Intent */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Primary Intent
              </label>
              <select
                value={selectedIntent}
                onChange={(e) => setSelectedIntent(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Intents</option>
                <option value="find_photo">Find Photo</option>
                <option value="find_video">Find Video</option>
                <option value="find_screenshot">Find Screenshot</option>
                <option value="cleanup_duplicates">Cleanup Duplicates</option>
                <option value="album_organization">Album Organization</option>
              </select>
            </div>

            {/* Memory Anchor */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Memory Anchor
              </label>
              <select
                value={selectedMemory}
                onChange={(e) => setSelectedMemory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Dimensions</option>
                <option value="temporal">Temporal (Dates / Seasons)</option>
                <option value="spatial">Spatial (Location / Places)</option>
                <option value="social">Social (People / Faces)</option>
                <option value="visual">Visual (Colors / Composition)</option>
                <option value="event">Event (Trips / Weddings)</option>
                <option value="semantic">Semantic (Activities / Concepts)</option>
              </select>
            </div>

            {/* Failure Mode */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Failure Mode
              </label>
              <select
                value={selectedFailure}
                onChange={(e) => setSelectedFailure(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Failure Modes</option>
                <option value="keyword_mismatch">Keyword Mismatch</option>
                <option value="temporal_drift">Temporal Drift</option>
                <option value="no_results">Zero Results</option>
                <option value="false_positive">False Positives</option>
                <option value="face_failure">Face Recognition Failure</option>
                <option value="poor_ranking">Poor Result Ranking</option>
              </select>
            </div>
          </Card>
        </div>

        {/* Conversation Cards List */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Showing {filteredList.length} indexed conversations</span>
            <span>{relevantOnly ? "Filtered to Photo Retrieval" : "All Records"}</span>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-44 w-full" />
              ))}
            </div>
          ) : filteredList.length === 0 ? (
            <EmptyState
              title="No conversations found"
              description="Try broadening your filters or executing a different semantic query."
            />
          ) : (
            <div className="space-y-4">
              {filteredList.map((conv) => {
                const analysis = conv.analysis;
                const source = conv.source || "demo";
                const isDemo = conv.is_demo;

                return (
                  <Card
                    key={conv.id}
                    hover
                    className="p-6 relative overflow-hidden"
                    onClick={() => setActiveModalConv(conv)}
                  >
                    {/* DEMO DATA Watermark for mock records */}
                    {isDemo && (
                      <div className="absolute top-2 right-2 select-none pointer-events-none">
                        <Badge variant="demo">DEMO DATA</Badge>
                      </div>
                    )}

                    <div className="space-y-3">
                      {/* Top Meta */}
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="default" size="sm">
                          {source.toUpperCase()}
                        </Badge>
                        {analysis?.primary_intent && (
                          <Badge variant="indigo" size="sm">
                            Intent: {analysis.primary_intent}
                          </Badge>
                        )}
                        {conv.similarity_score !== undefined && (
                          <Badge variant="purple" size="sm">
                            Match: {Math.round(conv.similarity_score * 100)}%
                          </Badge>
                        )}
                        <span className="text-[11px] text-slate-500 ml-auto mr-16 sm:mr-0">
                          {conv.timestamp ? new Date(conv.timestamp).toLocaleDateString() : "Unknown date"}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-base font-bold text-white line-clamp-1">
                        {conv.title || "User Conversation"}
                      </h3>

                      {/* Excerpt */}
                      <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
                        {conv.highlighted_excerpt || conv.cleaned_text || conv.text}
                      </p>

                      {/* Annotation Badges */}
                      {analysis && (
                        <div className="pt-2 flex flex-wrap items-center gap-1.5">
                          {(analysis.memory_types || []).map((m: string, i: number) => (
                            <Badge key={i} variant="purple" size="sm">
                              {m}
                            </Badge>
                          ))}
                          {(analysis.failure_modes || []).map((f: string, i: number) => (
                            <Badge key={i} variant="rose" size="sm">
                              {f.replace("_", " ")}
                            </Badge>
                          ))}
                          {analysis.confidence !== undefined && (
                            <span className="text-[11px] text-slate-500 ml-auto">
                              AI Confidence: {Math.round((analysis.confidence || 0) * 100)}%
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Conversation Detail Modal */}
      {activeModalConv && (
        <Modal
          isOpen={!!activeModalConv}
          onClose={() => setActiveModalConv(null)}
          title={activeModalConv.title || "Conversation Details"}
          description={`Source: ${activeModalConv.source?.toUpperCase() || "UNKNOWN"} • ID: ${activeModalConv.id}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
            {activeModalConv.is_demo && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between">
                <span>Synthetic dataset benchmark record.</span>
                <Badge variant="demo">DEMO DATA</Badge>
              </div>
            )}

            {/* Raw Cleaned Text */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Full Conversation Text
              </h4>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap font-mono max-h-52 overflow-y-auto">
                {activeModalConv.cleaned_text || activeModalConv.text}
              </div>
            </div>

            {/* AI Analysis Breakdown */}
            {activeModalConv.analysis ? (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  AI Semantic Analysis (Stage 1 & 2)
                </h4>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-slate-500">Primary Intent</span>
                    <p className="font-semibold text-white">{activeModalConv.analysis.primary_intent || "N/A"}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-slate-500">Confidence</span>
                    <p className="font-semibold text-emerald-400">
                      {Math.round((activeModalConv.analysis.confidence || 0) * 100)}%
                    </p>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-400">Memory Dimensions</span>
                  <div className="flex flex-wrap gap-1.5">
                    {(activeModalConv.analysis.memory_types || []).map((m: string, i: number) => (
                      <Badge key={i} variant="purple">{m}</Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-400">Retrieval Failure Modes</span>
                  <div className="flex flex-wrap gap-1.5">
                    {(activeModalConv.analysis.failure_modes || []).map((f: string, i: number) => (
                      <Badge key={i} variant="rose">{f.replace("_", " ")}</Badge>
                    ))}
                  </div>
                </div>

                {activeModalConv.analysis.reasoning_summary && (
                  <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-indigo-200">
                    <span className="font-bold block mb-1">Reasoning Summary:</span>
                    <p>{activeModalConv.analysis.reasoning_summary}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-500 text-center">
                No AI analysis record generated for this conversation yet.
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
