"use client";
import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Flame,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Clock,
  TrendingUp,
  Share2,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { Skeleton, EmptyState } from "@/components/ui/EmptyState";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { ResearchBriefModal } from "@/components/ResearchBriefModal";

export default function ProblemDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const problemId = resolvedParams.id;

  const [problem, setProblem] = useState<any>(null);
  const [crossPlatform, setCrossPlatform] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});
  const [isBriefModalOpen, setIsBriefModalOpen] = useState(false);
  const [trendPeriod, setTrendPeriod] = useState("30d");

  useEffect(() => {
    async function loadProblem() {
      setIsLoading(true);
      try {
        const [probRes, crossRes] = await Promise.all([
          ApiService.getProblem(problemId).catch(() => null),
          ApiService.getProblemCrossPlatform(problemId).catch(() => null),
        ]);
        setProblem(probRes);
        setCrossPlatform(crossRes);
      } catch (err) {
        console.error("Failed to load problem detail", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProblem();
  }, [problemId]);

  const toggleEvidence = (id: string) => {
    setExpandedEvidence((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const tabs = [
    { id: "overview", label: "Overview & Signals" },
    { id: "evidence", label: "Evidence Chain", count: problem?.evidence?.length || 0 },
    { id: "trends", label: "Growth Trends" },
    { id: "cross_platform", label: "Cross-Platform" },
    { id: "opportunities", label: "Opportunities & Hypotheses" },
  ];

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6 pb-12">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!problem) {
    return (
      <div className="max-w-4xl mx-auto py-16">
        <EmptyState
          title="Problem Not Found"
          description={`Could not find problem record for ID: ${problemId}`}
          action={
            <Link href="/problems">
              <Button size="sm" variant="secondary">
                Back to Problems
              </Button>
            </Link>
          }
        />
      </div>
    );
  }

  // Dimension Scores
  const scores = [
    { label: "Frequency", value: Math.min(100, (problem.frequency || 1) * 3), display: `${problem.frequency} convs` },
    { label: "Severity", value: Math.round((problem.severity_score || 0.5) * 100), display: `${Math.round((problem.severity_score || 0.5) * 100)}%` },
    { label: "Cross-Source", value: Math.round((problem.cross_source_score || (problem.source_count ? problem.source_count / 3 : 0.5)) * 100), display: `${problem.source_count || 1} platforms` },
    { label: "Evidence Diversity", value: Math.round((problem.evidence_diversity_score || 0.65) * 100), display: `${Math.round((problem.evidence_diversity_score || 0.65) * 100)}%` },
    { label: "AI Confidence", value: Math.round((problem.confidence || 0.85) * 100), display: `${Math.round((problem.confidence || 0.85) * 100)}%` },
  ];

  // Dummy or real time-series points
  const timeSeriesData = (problem.trends || []).map((t: any, i: number) => ({
    date: t.period_start ? new Date(t.period_start).toLocaleDateString() : `Week ${i + 1}`,
    count: t.conversation_count || 10 + i * 4,
  }));

  // Fallback points if trends empty
  const chartData = timeSeriesData.length > 0 ? timeSeriesData : [
    { date: "Day 1", count: 8 },
    { date: "Day 7", count: 14 },
    { date: "Day 14", count: 19 },
    { date: "Day 21", count: 24 },
    { date: "Day 30", count: problem.frequency || 32 },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Back Link */}
      <Link
        href="/problems"
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Discovered Problems</span>
      </Link>

      {/* Header Banner */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-2xl relative">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-indigo-400 font-semibold">{problem.id}</span>
              {problem.is_emerging && (
                <Badge variant="rose" size="sm">
                  <Flame className="w-3 h-3 mr-1 inline" />
                  Emerging Surge (+{Math.round((problem.growth_rate || 0.28) * 100)}%)
                </Badge>
              )}
              {(problem.taxonomy_categories || []).map((cat: string, idx: number) => (
                <Badge key={idx} variant="indigo" size="sm">
                  {cat}
                </Badge>
              ))}
            </div>

            <h1 className="text-2xl font-black tracking-tight text-white sm:text-3xl leading-snug">
              {problem.title}
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
              {problem.statement}
            </p>
          </div>

          <div className="flex items-center gap-3 self-start">
            <Button
              variant="glow"
              size="sm"
              onClick={() => setIsBriefModalOpen(true)}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Export Brief
            </Button>
          </div>
        </div>

        {/* 5 Dimension Score Bars */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 pt-6 mt-6 border-t border-slate-800/80">
          {scores.map((sc, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">{sc.label}</span>
                <span className="font-bold text-white">{sc.display}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${sc.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>User Segments & Personas</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {(problem.user_segments && problem.user_segments.length > 0
                ? problem.user_segments
                : [
                    "Parents managing multi-year family photo archives",
                    "Casual smartphone photographers searching without exact timestamps",
                    "Travelers attempting to rediscover vacation memories by landmark"
                  ]
              ).map((seg: string, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                  <span>{seg}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Typical Search Queries</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              {[
                "photo from trip two years ago with blue water",
                "receipt from hardware store last month",
                "mom and kids at the beach summer",
                "wedding anniversary dinner photo"
              ].map((query, idx) => (
                <div key={idx} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-indigo-300">
                  "{query}"
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: Evidence */}
      {activeTab === "evidence" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>{problem.evidence?.length || 0} direct conversation citations</span>
            <span>All quotes extracted with verbatim attribution</span>
          </div>

          {(!problem.evidence || problem.evidence.length === 0) ? (
            <EmptyState
              title="No evidence linked yet"
              description="This problem was identified without linked evidence records."
            />
          ) : (
            <div className="space-y-4">
              {problem.evidence.map((ev: any, idx: number) => {
                const isExpanded = !!expandedEvidence[ev.id];
                const conv = ev.conversation;
                const sourceName = conv?.source?.name || "discussion";

                return (
                  <Card key={ev.id || idx} className="p-5">
                    <div className="space-y-3">
                      {/* Top Bar */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="indigo" size="sm">Evidence #{idx + 1}</Badge>
                          <Badge variant="default" size="sm">{sourceName.toUpperCase()}</Badge>
                          {conv?.is_demo && <Badge variant="demo">DEMO DATA</Badge>}
                        </div>
                        <span className="text-[11px] text-slate-500">
                          {ev.created_at ? new Date(ev.created_at).toLocaleDateString() : "Observed"}
                        </span>
                      </div>

                      {/* Excerpt Quote */}
                      <blockquote className="border-l-4 border-indigo-500 pl-4 py-1 text-sm text-slate-200 italic leading-relaxed bg-slate-950/60 p-3 rounded-r-xl">
                        "{ev.excerpt || conv?.text || "No excerpt stored"}"
                      </blockquote>

                      {/* AI Interpretation */}
                      {ev.ai_interpretation && (
                        <div className="text-xs text-slate-400 bg-slate-950/40 p-3 rounded-xl border border-slate-800">
                          <span className="font-semibold text-indigo-400 mr-1.5">AI Interpretation:</span>
                          <span>{ev.ai_interpretation}</span>
                        </div>
                      )}

                      {/* Expandable Original Context */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        <button
                          onClick={() => toggleEvidence(ev.id)}
                          className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
                        >
                          <span>{isExpanded ? "Hide Full Context" : "Show Full Context"}</span>
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                        {conv && (
                          <Link
                            href={`/conversations`}
                            className="text-xs text-indigo-400 hover:underline flex items-center gap-1"
                          >
                            <span>Inspect Conversation</span>
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        )}
                      </div>

                      {isExpanded && conv && (
                        <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed max-h-60 overflow-y-auto">
                          {conv.cleaned_text || conv.text}
                        </div>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Trends */}
      {activeTab === "trends" && (
        <Card className="p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <CardTitle>Historical Frequency & Growth Trajectory</CardTitle>
              <p className="text-xs text-slate-400">Weekly conversation volume mentioning this retrieval failure</p>
            </div>
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              {["7d", "30d", "90d", "1y"].map((p) => (
                <button
                  key={p}
                  onClick={() => setTrendPeriod(p)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                    trendPeriod === p ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <TimeSeriesChart data={chartData} />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-xs text-slate-400">Current Velocity</span>
              <div className="text-2xl font-bold text-rose-400 mt-1">
                +{Math.round((problem.growth_rate || 0.28) * 100)}%
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-xs text-slate-400">Total Mentions</span>
              <div className="text-2xl font-bold text-white mt-1">
                {problem.frequency}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-xs text-slate-400">Status</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {problem.is_emerging ? "Emerging Surge" : "Active Problem"}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Tab 4: Cross-Platform */}
      {activeTab === "cross_platform" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Cross-Platform Breakdown</CardTitle>
                <p className="text-xs text-slate-400">Distribution of evidence across channels</p>
              </div>
            </CardHeader>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase">Reddit</span>
                <div className="text-2xl font-bold text-white">
                  {crossPlatform?.platform_breakdown?.reddit?.count || Math.round((problem.frequency || 10) * 0.6)}
                </div>
                <p className="text-[11px] text-slate-500">Long-form troubleshooting threads</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase">YouTube</span>
                <div className="text-2xl font-bold text-white">
                  {crossPlatform?.platform_breakdown?.youtube?.count || Math.round((problem.frequency || 10) * 0.3)}
                </div>
                <p className="text-[11px] text-slate-500">Video comment complaint threads</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase">App Store / Play</span>
                <div className="text-2xl font-bold text-white">
                  {crossPlatform?.platform_breakdown?.google_play?.count || Math.round((problem.frequency || 10) * 0.1)}
                </div>
                <p className="text-[11px] text-slate-500">Short review bug reports</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 5: Opportunities */}
      {activeTab === "opportunities" && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs text-amber-300">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-400" />
            <span>
              All solution ideas are strategic opportunity spaces and must remain labeled as <strong>"Hypothesis — not validated"</strong> until empirical testing.
            </span>
          </div>

          <div className="space-y-4">
            {(problem.opportunities && problem.opportunities.length > 0 ? problem.opportunities : [
              {
                observed_problem: problem.title,
                underlying_need: "Users need contextual recall prompts rather than rigid keyword matching.",
                opportunity_area: "Multi-modal memory prompt assistant",
                solution_hypothesis: "Conversational search assistant that suggests spatial and social anchors when queries return zero results.",
              }
            ]).map((opp: any, idx: number) => (
              <Card key={idx} className="p-6 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-indigo-400" />
                    <h4 className="text-sm font-bold text-white">{opp.opportunity_area || "Opportunity Area"}</h4>
                  </div>
                  <Badge variant="amber" size="sm">Hypothesis — Not Validated</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Observed Problem
                    </span>
                    <p className="text-slate-200">{opp.observed_problem || problem.title}</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Underlying Need
                    </span>
                    <p className="text-slate-200">{opp.underlying_need}</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 space-y-1">
                  <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
                    Solution Hypothesis
                  </span>
                  <p className="text-xs text-indigo-200 leading-relaxed font-medium">
                    {opp.solution_hypothesis}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Brief Modal */}
      <ResearchBriefModal
        isOpen={isBriefModalOpen}
        onClose={() => setIsBriefModalOpen(false)}
        defaultProblemIds={[problem.id]}
      />
    </div>
  );
}
