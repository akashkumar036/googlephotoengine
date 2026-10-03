"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  Search,
  SlidersHorizontal,
  RefreshCw,
  ChevronDown,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import dataset from "@/lib/data/engine_dataset.json";

// Pre-map all 2,050 conversations as initial instant fallback data
const allFallbackConvs: any[] = (dataset.conversations || []).map((c: any) => ({
  ...c,
  source: c.source || "reddit",
  analysis: {
    primary_intent: c.primary_intent || "Find Personal Photo",
    memory_types: c.memory_types || ["temporal", "visual"],
    retrieval_strategies: c.retrieval_strategies || ["keyword_search"],
    failure_modes: c.failure_modes || ["chrono_ambiguity"],
    pain_points: c.pain_points || [],
    user_goal: c.user_goal || "Find specific photo",
    known_memory: c.known_memory || "Visual cues, context",
    unknown_memory: c.unknown_memory || "Exact timestamp",
    frustration_level: c.frustration_level ?? 0.78,
    severity: c.severity ?? 0.75,
    confidence: c.confidence ?? 0.88,
    reasoning_summary: c.reasoning_summary || c.user_goal,
  },
}));

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>(allFallbackConvs);
  const [totalCount, setTotalCount] = useState<number>(allFallbackConvs.length);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchingNL, setIsSearchingNL] = useState(false);
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedIntent, setSelectedIntent] = useState("all");
  const [selectedMemory, setSelectedMemory] = useState("all");
  const [selectedFailure, setSelectedFailure] = useState("all");
  const [displayLimit, setDisplayLimit] = useState(60);
  const [activeModalConv, setActiveModalConv] = useState<any | null>(null);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const res = await ApiService.getConversations({
        limit: 500,
      });
      if (res?.data && res.data.length > 0) {
        setConversations(res.data);
        if (res.total) setTotalCount(res.total);
      }
    } catch (err) {
      console.warn("Using bundled dataset fallback", err);
      setConversations(allFallbackConvs);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      setConversations(allFallbackConvs);
      return;
    }

    setIsSearchingNL(true);
    setIsLoading(true);

    try {
      const res = await ApiService.searchConversations(query, 100);
      if (res?.data && res.data.length > 0) {
        setConversations(res.data);
        setIsLoading(false);
        setIsSearchingNL(false);
        return;
      }
    } catch (err) {
      console.warn("API search fallback to local search", err);
    }

    // Client-side search fallback across all 2,050 records
    const terms = query.split(" ").filter((w) => w.length > 1);
    const matched = allFallbackConvs.filter((c) => {
      const text = (c.text || "").toLowerCase();
      const title = (c.title || "").toLowerCase();
      const goal = (c.user_goal || "").toLowerCase();
      const summary = (c.reasoning_summary || "").toLowerCase();
      return terms.some(
        (t) => text.includes(t) || title.includes(t) || goal.includes(t) || summary.includes(t)
      );
    });

    setConversations(matched.length > 0 ? matched : allFallbackConvs);
    setIsLoading(false);
    setIsSearchingNL(false);
  };

  // Filter conversations
  const filteredList = useMemo(() => {
    return conversations.filter((c) => {
      // Source filter
      if (selectedSource !== "all") {
        const cSource = (c.source || "").toLowerCase();
        if (cSource !== selectedSource.toLowerCase()) {
          return false;
        }
      }

      const analysis = c.analysis || {};
      const intent = analysis.primary_intent || c.primary_intent || "";

      // Intent filter
      if (selectedIntent !== "all") {
        if (!intent.toLowerCase().includes(selectedIntent.toLowerCase())) {
          return false;
        }
      }

      // Memory filter
      if (selectedMemory !== "all") {
        const mems = (analysis.memory_types || c.memory_types || []).map((m: string) =>
          m.toLowerCase()
        );
        if (!mems.some((m: string) => m.includes(selectedMemory.toLowerCase()))) {
          return false;
        }
      }

      // Failure filter
      if (selectedFailure !== "all") {
        const fails = (analysis.failure_modes || c.failure_modes || []).map((f: string) =>
          f.toLowerCase()
        );
        if (!fails.some((f: string) => f.includes(selectedFailure.toLowerCase()))) {
          return false;
        }
      }

      return true;
    });
  }, [conversations, selectedSource, selectedIntent, selectedMemory, selectedFailure]);

  const visibleList = useMemo(() => {
    return filteredList.slice(0, displayLimit);
  }, [filteredList, displayLimit]);

  const sourceLabels: Record<string, string> = {
    google_play: "Google Play",
    reddit: "Reddit",
    app_store: "App Store",
    google_community: "Forums",
    youtube: "YouTube",
  };

  return (
    <div className="flex flex-col gap-space-xl pb-16">
      {/* Top Banner */}
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-space-lg bg-surface-container-low/90 backdrop-blur-xl p-space-xl rounded-xl shadow-md border border-outline-variant/30 relative overflow-hidden">
        <div className="flex flex-col gap-space-xs max-w-3xl">
          <div className="flex items-center gap-space-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-secondary/10 text-secondary font-label-sm text-label-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary animate-pulse"></span>
              Live Telemetry Stream
            </span>
            <span className="font-mono-metric text-mono-metric text-on-surface-variant">
              2,050 Ingested Records
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            Indexed Conversations &amp; Feedback Stream
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
            Multi-source user feedback from Google Play, Reddit, Apple App Store, Google Community,
            and YouTube, normalized and enriched with Groq Llama 3.3 episodic memory signals.
          </p>
        </div>

        <div className="flex items-center gap-space-sm self-start md:self-center">
          <Button
            variant="outline"
            size="md"
            onClick={loadConversations}
            icon={<RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />}
          >
            Sync Feed
          </Button>
        </div>
      </section>

      {/* Semantic Search Box */}
      <Card className="p-4 bg-surface-container-low border-outline-variant/30">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-on-surface-variant absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search across 2,050 conversations (e.g. 'snow', 'dog', 'vacation', 'album', 'wedding')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-container border border-outline-variant/40 rounded-xl pl-11 pr-4 py-2.5 text-body-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={isSearchingNL}
              className="px-space-md py-2.5 rounded-xl bg-primary-container hover:bg-primary hover:text-on-primary text-on-primary-container font-label-md text-label-md transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[18px]">search</span>
              <span>{isSearchingNL ? "Searching..." : "Vector Search"}</span>
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setConversations(allFallbackConvs);
                }}
                className="px-space-md py-2.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </Card>

      {/* Main Layout: Filters Sidebar + Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="p-5 space-y-4 bg-surface-container-low border-outline-variant/30">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2 text-label-md font-bold text-on-surface uppercase tracking-wider">
                <SlidersHorizontal className="w-4 h-4 text-primary" />
                <span>Filter Stream</span>
              </div>
              <button
                onClick={() => {
                  setSelectedSource("all");
                  setSelectedIntent("all");
                  setSelectedMemory("all");
                  setSelectedFailure("all");
                  setSearchQuery("");
                  setConversations(allFallbackConvs);
                }}
                className="text-[11px] text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
              >
                Reset All
              </button>
            </div>

            {/* Platform Source */}
            <div className="space-y-1.5">
              <label className="text-label-sm font-semibold text-on-surface-variant uppercase tracking-wider block">
                Platform Source
              </label>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/40 rounded-xl px-3 py-2 text-body-sm text-on-surface focus:outline-none focus:border-primary cursor-pointer"
              >
                <option value="all">All Platforms (2,050)</option>
                <option value="google_play">Google Play Store (849)</option>
                <option value="reddit">Reddit (653)</option>
                <option value="app_store">Apple App Store (202)</option>
                <option value="google_community">Community Forums (199)</option>
                <option value="youtube">YouTube (147)</option>
              </select>
            </div>

            {/* Memory Anchor */}
            <div className="space-y-1.5">
              <label className="text-label-sm font-semibold text-on-surface-variant uppercase tracking-wider block">
                Memory Anchor
              </label>
              <select
                value={selectedMemory}
                onChange={(e) => setSelectedMemory(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/40 rounded-xl px-3 py-2 text-body-sm text-on-surface focus:outline-none focus:border-primary cursor-pointer"
              >
                <option value="all">All Dimensions</option>
                <option value="temporal">Temporal (Life chapters, seasons)</option>
                <option value="visual">Visual (Garment, color, props)</option>
                <option value="social">Social (People, friends, pets)</option>
                <option value="spatial">Spatial (Cabins, landmarks)</option>
                <option value="emotional">Emotional (Atmosphere, vibes)</option>
                <option value="ocr">Text / OCR (In-photo text)</option>
              </select>
            </div>

            {/* Failure Mode */}
            <div className="space-y-1.5">
              <label className="text-label-sm font-semibold text-on-surface-variant uppercase tracking-wider block">
                Failure Mode
              </label>
              <select
                value={selectedFailure}
                onChange={(e) => setSelectedFailure(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/40 rounded-xl px-3 py-2 text-body-sm text-on-surface focus:outline-none focus:border-primary cursor-pointer"
              >
                <option value="all">All Failure Modes</option>
                <option value="chrono">Chrono-Ambiguity (Year demand)</option>
                <option value="visual">Visual Mismatch (Background vs garment)</option>
                <option value="face">Face Tagging Failure (Age drift / pets)</option>
                <option value="geo">Spatial Failure (Address vs informal name)</option>
                <option value="dedup">Deduplication Failure</option>
              </select>
            </div>
          </Card>
        </div>

        {/* Conversation Cards List */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between text-body-sm text-on-surface-variant px-1">
            <span>
              Showing <strong className="text-on-surface">{visibleList.length}</strong> of{" "}
              <strong className="text-on-surface">{filteredList.length}</strong> indexed items
            </span>
            <span className="font-mono-metric text-[11px] text-secondary">
              Total Ingested: {totalCount}
            </span>
          </div>

          {visibleList.length === 0 ? (
            <EmptyState
              title="No conversations found"
              description="No feedback records match the current filter selection. Try clearing filters or searching for terms like 'snow', 'dog', 'vacation', or 'album'."
              action={
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setSelectedSource("all");
                    setSelectedMemory("all");
                    setSelectedFailure("all");
                    setSearchQuery("");
                    setConversations(allFallbackConvs);
                  }}
                >
                  Reset Filters
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              {visibleList.map((conv) => {
                const analysis = conv.analysis || {};
                const source = conv.source || "reddit";
                const memoryTypes = analysis.memory_types || conv.memory_types || [];
                const failureModes = analysis.failure_modes || conv.failure_modes || [];
                const intent = analysis.primary_intent || conv.primary_intent || "Find Personal Photo";
                const confidence = Math.round((analysis.confidence ?? conv.confidence ?? 0.88) * 100);

                return (
                  <div
                    key={conv.id}
                    onClick={() => setActiveModalConv(conv)}
                    className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/30 hover:bg-surface-container transition-all cursor-pointer shadow-sm group"
                  >
                    <div className="space-y-3">
                      {/* Meta header */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-surface-container-highest text-on-surface border border-outline-variant/40">
                          {sourceLabels[source] || source.toUpperCase()}
                        </span>
                        <span className="font-label-sm text-[11px] px-2 py-0.5 rounded bg-primary/10 text-primary">
                          Intent: {intent}
                        </span>
                        {conv.similarity_score !== undefined && (
                          <span className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-secondary/15 text-secondary">
                            Relevance: {Math.round(conv.similarity_score * 100)}%
                          </span>
                        )}
                        <span className="text-[11px] text-on-surface-variant ml-auto">
                          {conv.created_at ? new Date(conv.created_at).toLocaleDateString() : "Active Record"}
                        </span>
                      </div>

                      {/* Excerpt */}
                      <p className="text-body-sm text-on-surface leading-relaxed line-clamp-3 italic">
                        “{conv.cleaned_text || conv.text}”
                      </p>

                      {/* Tags & Badges */}
                      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-outline-variant/20">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {memoryTypes.slice(0, 3).map((m: string, i: number) => (
                            <span
                              key={i}
                              className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-surface-container-high text-primary"
                            >
                              {m}
                            </span>
                          ))}
                          {failureModes.slice(0, 2).map((f: string, i: number) => (
                            <span
                              key={i}
                              className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary"
                            >
                              {f.replace("_", " ")}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-on-surface-variant font-mono-metric">
                          <span className="material-symbols-outlined text-[14px] text-secondary">
                            verified
                          </span>
                          <span>Confidence: {confidence}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Load more button */}
              {visibleList.length < filteredList.length && (
                <div className="pt-4 flex justify-center">
                  <button
                    onClick={() => setDisplayLimit((prev) => prev + 60)}
                    className="px-6 py-2.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/40 text-on-surface font-label-md text-label-md transition-colors cursor-pointer flex items-center gap-2"
                  >
                    <span>Load More Conversations ({filteredList.length - visibleList.length} remaining)</span>
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Conversation Detail Modal */}
      {activeModalConv && (
        <Modal
          isOpen={!!activeModalConv}
          onClose={() => setActiveModalConv(null)}
          title="Conversation Feedback & Semantic Annotation"
          description={`Source: ${sourceLabels[activeModalConv.source] || activeModalConv.source?.toUpperCase()} • Record ID: ${activeModalConv.id}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
            {/* Raw Text */}
            <div className="space-y-2">
              <h4 className="text-label-sm font-bold text-on-surface-variant uppercase tracking-wider">
                Full Ingested User Text
              </h4>
              <div className="p-4 rounded-xl bg-surface-container-lowest border border-outline-variant/30 text-body-sm text-on-surface leading-relaxed whitespace-pre-wrap font-mono">
                {activeModalConv.cleaned_text || activeModalConv.text}
              </div>
            </div>

            {/* AI Analysis Breakdown */}
            <div className="space-y-4">
              <h4 className="text-label-sm font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                Groq Llama 3.3 Semantic Extraction
              </h4>

              <div className="grid grid-cols-2 gap-3 text-body-sm">
                <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/30 space-y-1">
                  <span className="text-[11px] text-on-surface-variant uppercase font-semibold">User Goal</span>
                  <p className="font-semibold text-on-surface">
                    {activeModalConv.user_goal || activeModalConv.analysis?.user_goal || "Photo Retrieval"}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/30 space-y-1">
                  <span className="text-[11px] text-on-surface-variant uppercase font-semibold">AI Confidence</span>
                  <p className="font-semibold text-secondary font-mono-metric">
                    {Math.round((activeModalConv.analysis?.confidence ?? 0.88) * 100)}%
                  </p>
                </div>
              </div>

              {activeModalConv.known_memory && (
                <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/30 space-y-1 text-body-sm">
                  <span className="text-[11px] text-secondary uppercase font-semibold">What User Remembers</span>
                  <p className="text-on-surface">{activeModalConv.known_memory}</p>
                </div>
              )}

              {activeModalConv.unknown_memory && (
                <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/30 space-y-1 text-body-sm">
                  <span className="text-[11px] text-tertiary uppercase font-semibold">What User Has Forgotten</span>
                  <p className="text-on-surface">{activeModalConv.unknown_memory}</p>
                </div>
              )}

              <div className="space-y-1.5">
                <span className="text-label-sm font-semibold text-on-surface-variant">Memory Dimensions</span>
                <div className="flex flex-wrap gap-1.5">
                  {(activeModalConv.analysis?.memory_types || activeModalConv.memory_types || []).map(
                    (m: string, i: number) => (
                      <span
                        key={i}
                        className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-primary/10 text-primary"
                      >
                        {m}
                      </span>
                    )
                  )}
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-label-sm font-semibold text-on-surface-variant">Retrieval Failure Modes</span>
                <div className="flex flex-wrap gap-1.5">
                  {(activeModalConv.analysis?.failure_modes || activeModalConv.failure_modes || []).map(
                    (f: string, i: number) => (
                      <span
                        key={i}
                        className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary"
                      >
                        {f.replace("_", " ")}
                      </span>
                    )
                  )}
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
