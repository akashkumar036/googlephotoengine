"use client";

import React, { useState } from "react";
import Link from "next/link";

interface Citation {
  id: string;
  quote: string;
}

const PROBLEM_CLUSTERS = [
  {
    id: "tax-01",
    title: "Temporal Chapter Blur (Chrono-Ambiguity)",
    tag: "TAX-01: Temporal Semantics",
    tagClass: "text-primary bg-primary/10",
    category: "Semantic Indexing",
    frequency: 684,
    share: "33.4% of total",
    growth: "+35%",
    growthIcon: "local_fire_department",
    isCritical: true,
    severity: "0.86 / 1.0",
    severityClass: "bg-error-container/40 text-error",
    citations: [
      {
        id: "E-14",
        quote:
          "I spent 45 minutes searching for pictures from that winter I lived in Portland. Photos insists I pick an exact year.",
      },
      {
        id: "E-92",
        quote: "Querying last Thanksgiving brings up random Thursdays in October.",
      },
      {
        id: "E-188",
        quote:
          "Why cant it understand before COVID vs after COVID? That is literally how humans think.",
      },
    ],
  },
  {
    id: "tax-02",
    title: "Visual Attribute Mismatch (Color/Garment)",
    tag: "TAX-02: Multi-Modal Vision",
    tagClass: "text-secondary bg-secondary/10",
    category: "Semantic Indexing",
    frequency: 512,
    share: "25.0% of total",
    growth: "+28%",
    growthIcon: "local_fire_department",
    isCritical: true,
    severity: "0.79 / 1.0",
    severityClass: "bg-amber-500/20 text-amber-300",
    citations: [
      {
        id: "E-07",
        quote:
          "I typed blue sweater in snow and it showed me 300 blue sky skiing pictures without any sweaters.",
      },
      {
        id: "E-43",
        quote:
          "Color tags apply to the entire background instead of foreground subject clothing.",
      },
      {
        id: "E-156",
        quote: "Searching red dress brings up strawberries and fire hydrants.",
      },
    ],
  },
  {
    id: "tax-03",
    title: "Social Graph & Entity Ambiguity",
    tag: "TAX-03: People & Cohorts",
    tagClass: "text-tertiary bg-tertiary-container/10",
    category: "Metadata Failures",
    frequency: 394,
    share: "19.2% of total",
    growth: "+18%",
    growthIcon: "north_east",
    isCritical: false,
    severity: "0.72 / 1.0",
    severityClass: "bg-amber-500/20 text-amber-300",
    citations: [
      {
        id: "E-22",
        quote:
          "Searching me and Sarah together leaves out 80% of photos because face clustering broke.",
      },
      {
        id: "E-81",
        quote:
          "It duplicates my son into three separate people as he aged from 2 to 5.",
      },
      {
        id: "E-301",
        quote:
          "Can not search for whole team from marketing without tagging all 9 individually.",
      },
    ],
  },
  {
    id: "tax-04",
    title: "Spatial Hierarchy Failure (Cabin vs Address)",
    tag: "TAX-04: Geo-Spatial",
    tagClass: "text-secondary bg-secondary/10",
    category: "Metadata Failures",
    frequency: 266,
    share: "13.0% of total",
    growth: "+12%",
    growthIcon: "north_east",
    isCritical: false,
    severity: "0.68 / 1.0",
    severityClass: "bg-surface-container-highest text-on-surface-variant",
    citations: [
      {
        id: "E-03",
        quote:
          "Photos taken 50 yards apart get separated into two different township names.",
      },
      {
        id: "E-67",
        quote:
          "Cant type up north or beach house to encompass our regular summer spots.",
      },
    ],
  },
];

export default function OverviewPage() {
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [tableFilter, setTableFilter] = useState<string>("All");
  const [timeFilter, setTimeFilter] = useState<string>("Last 30 Days");
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const handleCitationClick = (id: string, quote: string) => {
    setActiveCitation({ id, quote });
  };

  const closeCitationModal = () => {
    setActiveCitation(null);
  };

  const handleExport = () => {
    setIsExporting(true);
    const exportData = {
      dataset_version: "v2.4 Enterprise AI",
      generated_at: new Date().toISOString(),
      sample_size: 2050,
      sources: {
        google_play: 849,
        reddit: 653,
        apple_app_store: 202,
        community_forums: 199,
        youtube_commentaries: 147,
      },
      clusters: PROBLEM_CLUSTERS.map((c) => ({
        tag: c.tag,
        title: c.title,
        frequency: c.frequency,
        share: c.share,
        growth: c.growth,
        severity: c.severity,
        evidence_samples: c.citations,
      })),
      telemetry_kpis: {
        total_feedback: 2050,
        synthesized_signals: 2050,
        high_signal_friction: 1856,
        avg_frustration: 0.78,
      },
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `photo_retrieval_telemetry_2050_${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setIsExporting(false);
  };

  const filteredClusters = PROBLEM_CLUSTERS.filter((cluster) => {
    if (tableFilter === "All") return true;
    if (tableFilter === "Critical Growth") return cluster.isCritical;
    if (tableFilter === "Semantic Indexing") return cluster.category === "Semantic Indexing";
    if (tableFilter === "Metadata Failures") return cluster.category === "Metadata Failures";
    return true;
  });

  return (
    <div className="flex flex-col w-full gap-space-xl pb-12">
      {/* 1. Top Context Banner / Page Header */}
      <section className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg bg-surface-container-low/90 backdrop-blur-xl p-space-xl rounded-xl shadow-md relative overflow-hidden">
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col gap-space-xs max-w-3xl">
          <div className="flex items-center gap-space-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-secondary/10 text-secondary font-label-sm text-label-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary animate-pulse"></span>
              Ingestion Cycle Active
            </span>
            <span className="font-mono-metric text-mono-metric text-on-surface-variant">
              Llama 3.3 Node #4
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            Retrieval Gap Analysis &amp; Signal Synthesis
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
            Real-time telemetry and thematic clustering from{" "}
            <span className="text-primary font-medium">2,050 ingested complaints</span> across Google Play,
            Reddit, App Store, and YouTube.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-space-sm self-start lg:self-center">
          {/* Time Range Select */}
          <div className="relative">
            <button
              className="flex items-center gap-2 px-space-md py-2 bg-surface-container rounded-lg font-label-md text-label-md text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer"
              id="timeFilterBtn"
              type="button"
              onClick={() => {
                const options = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"];
                const nextIdx = (options.indexOf(timeFilter) + 1) % options.length;
                setTimeFilter(options[nextIdx]);
              }}
            >
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
                calendar_today
              </span>
              <span>{timeFilter}</span>
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                expand_more
              </span>
            </button>
          </div>

          {/* Confidence Pill */}
          <button
            className="flex items-center gap-1.5 px-space-md py-2 bg-surface-container rounded-lg font-label-md text-label-md text-on-surface hover:bg-surface-container-high transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-secondary">
              verified
            </span>
            <span>Confidence &gt; 85%</span>
          </button>

          {/* Export Action */}
          <button
            className="flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md hover:bg-primary hover:text-on-primary shadow-sm transition-all cursor-pointer"
            onClick={handleExport}
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">
              {isExporting ? "hourglass_empty" : "download"}
            </span>
            <span>Export Findings (JSON/CSV)</span>
          </button>
        </div>
      </section>

      {/* 2. 5 KPI Metric Cards Row */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-gutter">
        {/* Card 1 */}
        <div className="flex flex-col justify-between p-space-lg rounded-xl bg-surface-container-low shadow-sm relative overflow-hidden group hover:bg-surface-container transition-all">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
              Total Feedback
            </span>
            <span className="px-2 py-0.5 rounded bg-surface-container-highest font-label-sm text-label-sm text-on-surface-variant">
              Multi-source
            </span>
          </div>
          <div className="my-space-sm">
            <div className="font-display-lg text-display-lg text-on-surface font-headline-md tracking-tight">
              2,050
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant">
              100% of pipeline capacity
            </div>
          </div>
          <div className="flex items-center gap-1 text-secondary font-label-md text-label-md">
            <span className="material-symbols-outlined text-[16px]">trending_up</span>
            <span>+14.2% vs last cycle</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="flex flex-col justify-between p-space-lg rounded-xl bg-surface-container-low shadow-sm relative overflow-hidden group hover:bg-surface-container transition-all">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
              Synthesized Signals
            </span>
            <span className="px-2 py-0.5 rounded bg-secondary/15 text-secondary font-label-sm text-label-sm">
              100% Ingested
            </span>
          </div>
          <div className="my-space-sm">
            <div className="font-display-lg text-display-lg text-on-surface font-headline-md tracking-tight">
              2,050
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant">
              Zero unparsed items
            </div>
          </div>
          <div className="flex items-center gap-1 text-on-surface-variant font-body-sm text-body-sm">
            <span className="material-symbols-outlined text-[16px] text-secondary">
              check_circle
            </span>
            <span>Parser latency 18ms</span>
          </div>
        </div>

        {/* Card 3 (Ambient Rose/Indigo Accent Line) */}
        <div className="flex flex-col justify-between p-space-lg rounded-xl bg-surface-container-low shadow-sm relative overflow-hidden group hover:bg-surface-container transition-all">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-tertiary-container via-primary-container to-primary"></div>
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
              High-Signal Friction
            </span>
            <span className="px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary font-label-sm text-label-sm">
              Critical
            </span>
          </div>
          <div className="my-space-sm">
            <div className="font-display-lg text-display-lg text-tertiary font-headline-md tracking-tight">
              1,856
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant">
              90.5% identified pain points
            </div>
          </div>
          <div className="flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm">
            <span>194 filtered (noise)</span>
            <span className="font-mono-metric">9.5%</span>
          </div>
        </div>

        {/* Card 4 */}
        <div className="flex flex-col justify-between p-space-lg rounded-xl bg-surface-container-low shadow-sm relative overflow-hidden group hover:bg-surface-container transition-all">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
              Problem Clusters
            </span>
            <span className="px-2 py-0.5 rounded bg-primary-container/20 text-primary font-label-sm text-label-sm">
              +2 Emerging
            </span>
          </div>
          <div className="my-space-sm">
            <div className="flex items-baseline gap-1.5">
              <span className="font-display-lg text-display-lg text-on-surface font-headline-md tracking-tight">
                4
              </span>
              <span className="font-headline-sm text-headline-sm text-on-surface-variant">
                Core
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant">
              6 total thematic nodes
            </div>
          </div>
          <div className="flex items-center gap-1 text-on-surface-variant font-mono-metric text-mono-metric truncate">
            <span className="material-symbols-outlined text-[16px] text-primary">
              hub
            </span>
            <span className="truncate">Embedding Sim &gt; 0.88</span>
          </div>
        </div>

        {/* Card 5 */}
        <div className="flex flex-col justify-between p-space-lg rounded-xl bg-surface-container-low shadow-sm relative overflow-hidden group hover:bg-surface-container transition-all">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
              Avg Frustration
            </span>
            <span className="px-2 py-0.5 rounded bg-error-container/40 text-error font-label-sm text-label-sm font-semibold">
              High Severity
            </span>
          </div>
          <div className="my-space-sm">
            <div className="flex items-baseline gap-1">
              <span className="font-display-lg text-display-lg text-error font-headline-md tracking-tight">
                0.78
              </span>
              <span className="font-body-md text-body-md text-on-surface-variant">
                / 1.00
              </span>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant">
              Severe retrieval impediment
            </div>
          </div>
          <div className="w-full">
            <div className="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-tertiary via-tertiary-container to-error rounded-full"
                style={{ width: "78%" }}
              ></div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Signature Hero Card: 'The Memory-to-Retrieval Gap' Comparison Architecture */}
      <section className="rounded-xl bg-surface-container-low/95 p-space-xl shadow-xl relative overflow-hidden">
        {/* Ambient glow under the split card */}
        <div className="absolute -top-32 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-32 right-1/4 w-96 h-96 bg-tertiary-container/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col gap-space-lg relative z-10">
          {/* Section Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md pb-space-md bg-surface-container-low/50">
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-center gap-space-xs">
                <span className="px-2 py-0.5 rounded bg-primary-container/20 text-primary font-label-sm text-label-sm uppercase tracking-wider">
                  Core Paradigm Mismatch
                </span>
                <span className="font-mono-metric text-mono-metric text-on-surface-variant">
                  N=2,050 Signal Ingestion
                </span>
              </div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-[28px] text-primary">
                  psychology_alt
                </span>
                The Memory-to-Retrieval Gap
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant max-w-4xl">
                Why 2,050 users report abandoning photo searches: Human episodic memory encodes
                associative, emotional narratives, while commercial search engines query rigid
                categorical metadata.
              </p>
            </div>
            <div className="flex items-center gap-space-xs px-space-md py-1.5 rounded-lg bg-surface-container-high text-on-surface font-label-sm text-label-sm self-start">
              <span className="material-symbols-outlined text-[16px] text-secondary">
                compare_arrows
              </span>
              <span>Cognitive vs. Deterministic</span>
            </div>
          </div>

          {/* Split Architecture Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
            {/* Left Side: Human Episodic Memory */}
            <div className="flex flex-col gap-space-md p-space-lg rounded-xl bg-surface-container/70 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between pb-space-sm">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-primary text-[22px]">
                    neurology
                  </span>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">
                    Human Episodic Memory
                  </h3>
                </div>
                <span className="font-label-sm text-label-sm px-2 py-0.5 rounded bg-primary/10 text-primary">
                  Associative Anchors
                </span>
              </div>

              {/* Anchor 1 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-primary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">schedule</span>
                    Relative Life Chapters &amp; Chrono-Ambiguity
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-12",
                          "The summer before college, packed red Volvo near lake."
                        )
                      }
                      type="button"
                    >
                      [E-12]
                    </button>
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-88",
                          "Around when we adopted Bruno, he fit into a shoebox."
                        )
                      }
                      type="button"
                    >
                      [E-88]
                    </button>
                  </div>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface italic">
                  “The summer before college”, “Around when we adopted Bruno”, “That winter trip
                  right after the promotion”
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Mental cue: episodic temporal boundaries rather than solar calendars.
                </span>
              </div>

              {/* Anchor 2 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-primary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">palette</span>
                    Visual Salience &amp; Accidental Clues
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-31",
                          "She was wearing that oversized yellow raincoat at the ferry."
                        )
                      }
                      type="button"
                    >
                      [E-31]
                    </button>
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-104",
                          "The birthday cake had sparkling sparklers instead of wax candles."
                        )
                      }
                      type="button"
                    >
                      [E-104]
                    </button>
                  </div>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface italic">
                  “She was wearing that oversized yellow raincoat”, “The birthday cake had
                  sparkling sparklers instead of candles”
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Mental cue: foreground garment color, anomalous prop detail, high contrast.
                </span>
              </div>

              {/* Anchor 3 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-primary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">
                      sentiment_satisfied
                    </span>
                    Emotional Atmosphere &amp; Vibe
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-45",
                          "Chaotic family dinner where everyone was laughing so hard."
                        )
                      }
                      type="button"
                    >
                      [E-45]
                    </button>
                    <button
                      className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                      onClick={() =>
                        handleCitationClick(
                          "E-219",
                          "Moody sunset on the rocky coastline after the rain stopped."
                        )
                      }
                      type="button"
                    >
                      [E-219]
                    </button>
                  </div>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface italic">
                  “Chaotic family dinner where everyone was laughing”, “Moody sunset on the rocky
                  coastline”
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Mental cue: affective valence, sensory atmosphere, social warmth.
                </span>
              </div>
            </div>

            {/* Right Side: Algorithmic Indexing */}
            <div className="flex flex-col gap-space-md p-space-lg rounded-xl bg-surface-container/70 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between pb-space-sm">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-tertiary text-[22px]">
                    terminal
                  </span>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">
                    Algorithmic Query Index
                  </h3>
                </div>
                <span className="font-label-sm text-label-sm px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary">
                  Deterministic Schema
                </span>
              </div>

              {/* Friction 1 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-tertiary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">calendar_month</span>
                    Absolute Timestamp Required
                  </span>
                  <span className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-error-container/40 text-error font-semibold">
                    Friction: 82%
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Engine schema demands{" "}
                  <code className="font-mono-metric text-on-surface bg-surface-container-highest px-1 rounded">
                    YYYY-MM-DD
                  </code>
                  . Queries with temporal relative descriptors (“two summers ago”) trigger empty
                  state or arbitrary date bounds.
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Failure mode: Zero associative decay handling.
                </span>
              </div>

              {/* Friction 2 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-tertiary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">pin_drop</span>
                    Exact Reverse-Geocoded GPS
                  </span>
                  <span className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-error-container/40 text-error font-semibold">
                    Friction: 74%
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Engine maps exclusively to municipality/county reverse geo. When user enters “near
                  the lake cabin”, search evaluates to 0 matches because EXIF contains “Lincoln
                  Township, MI 49454”.
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Failure mode: Lack of colloquial spatial topological hierarchy.
                </span>
              </div>

              {/* Friction 3 */}
              <div className="p-space-md rounded-lg bg-surface-container-high/60 flex flex-col gap-space-xs hover:bg-surface-container-high transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-tertiary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">image_search</span>
                    Literal Object Labels (OCR/YOLO)
                  </span>
                  <span className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-error-container/40 text-error font-semibold">
                    Friction: 91%
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Image classifiers prioritize discrete high-frequency visual tags like ‘umbrella’
                  or ‘dining table’. The qualitative story (“cozy dinner with friends”) is
                  stripped at vector embedding stage.
                </p>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Failure mode: Semantic compression drops interpersonal affect.
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Synthesis Banner */}
          <div className="flex items-center justify-between flex-wrap gap-space-md p-space-md rounded-lg bg-surface-container-highest/60">
            <div className="flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-secondary text-[20px]">
                lightbulb
              </span>
              <span className="font-body-md text-body-md text-on-surface">
                <strong className="font-semibold text-secondary">Telemetry Synthesis:</strong>{" "}
                71% of all abandoned searches occur when users compound 2+ associative anchors (e.g.,{" "}
                <span className="text-primary font-mono-metric">Color + Person + Season</span>).
              </span>
            </div>
            <span className="font-mono-metric text-mono-metric text-on-surface-variant">
              Llama-3.3 Cross-Encoder Validation
            </span>
          </div>
        </div>
      </section>

      {/* 4. Middle Section (2 Columns: Ranked Clusters Table (66%) & Telemetry Breakdown (34%)) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
        {/* Column A: Ranked Problem Clusters Table (8 cols / ~66%) */}
        <div className="lg:col-span-8 flex flex-col gap-space-md p-space-lg rounded-xl bg-surface-container-low shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pb-space-xs">
            <div className="flex flex-col">
              <h3 className="font-headline-md text-headline-md text-on-surface">
                Ranked Problem Clusters &amp; Friction Taxonomy
              </h3>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                Derived from unsupervised K-Means (k=6) + embedding cosine similarity &gt; 0.88
              </span>
            </div>
            {/* Table Filter Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto py-1">
              {["All", "Critical Growth", "Semantic Indexing", "Metadata Failures"].map((chip) => (
                <button
                  key={chip}
                  onClick={() => setTableFilter(chip)}
                  className={`px-2.5 py-1 rounded-md font-label-sm text-label-sm transition-all cursor-pointer ${
                    tableFilter === chip
                      ? "bg-primary-container text-on-primary-container font-semibold"
                      : "bg-surface-container text-on-surface-variant hover:text-on-surface"
                  }`}
                  type="button"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* Responsive Table Container */}
          <div className="overflow-x-auto">
            <table className="w-full text-left font-body-sm text-body-sm">
              <thead>
                <tr className="bg-surface-container font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                  <th className="py-3 px-space-md rounded-l-lg">Cluster &amp; Taxonomy Tag</th>
                  <th className="py-3 px-space-md">Frequency &amp; Share</th>
                  <th className="py-3 px-space-md">30-Day Growth</th>
                  <th className="py-3 px-space-md">Severity Score</th>
                  <th className="py-3 px-space-md rounded-r-lg">Direct Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y-0">
                {filteredClusters.map((cluster) => (
                  <tr
                    key={cluster.id}
                    className="hover:bg-surface-container/60 transition-colors group border-b border-outline-variant/10 last:border-0"
                  >
                    <td className="py-3.5 px-space-md">
                      <div className="flex flex-col">
                        <Link
                          href="/problems"
                          className="font-headline-sm text-headline-sm text-on-surface group-hover:text-primary transition-colors"
                        >
                          {cluster.title}
                        </Link>
                        <span
                          className={`inline-block mt-1 font-mono-metric text-[11px] px-2 py-0.5 rounded w-max ${cluster.tagClass}`}
                        >
                          {cluster.tag}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md font-mono-metric text-on-surface">
                      <div className="flex flex-col">
                        <span className="font-semibold text-on-surface">
                          {cluster.frequency}
                        </span>
                        <span className="text-on-surface-variant text-[11px]">
                          {cluster.share}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <div
                        className={`flex items-center gap-1.5 font-label-md text-label-md ${
                          cluster.isCritical ? "text-secondary" : "text-on-surface-variant"
                        }`}
                      >
                        <span
                          className={`material-symbols-outlined text-[16px] ${
                            cluster.isCritical ? "text-secondary" : "text-secondary"
                          }`}
                        >
                          {cluster.growthIcon}
                        </span>
                        <span className="font-mono-metric font-semibold">
                          {cluster.growth}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <span
                        className={`px-2 py-1 rounded font-mono-metric font-semibold text-[12px] ${cluster.severityClass}`}
                      >
                        {cluster.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {cluster.citations.map((c) => (
                          <button
                            key={c.id}
                            className="font-mono-metric text-[11px] px-2 py-0.5 rounded bg-surface-container-high text-primary hover:bg-primary hover:text-on-primary transition-colors cursor-pointer"
                            onClick={() => handleCitationClick(c.id, c.quote)}
                            type="button"
                          >
                            [{c.id}]
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Column B: Visual Telemetry Cards (Stacked, 4 cols / ~34%) */}
        <div className="lg:col-span-4 flex flex-col gap-space-lg">
          {/* Card 1: Memory Dimensions Breakdown */}
          <div className="p-space-lg rounded-xl bg-surface-container-low shadow-sm flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[20px] text-primary">
                  data_usage
                </span>
                <h4 className="font-headline-sm text-headline-sm text-on-surface">
                  Memory Dimensions
                </h4>
              </div>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                Anchor Freq
              </span>
            </div>
            <div className="flex flex-col gap-space-sm pt-space-xs">
              {/* Item 1 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Temporal Semantics</span>
                  <span className="font-mono-metric text-primary">42%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: "42%" }}></div>
                </div>
              </div>
              {/* Item 2 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Visual Salience / Garment</span>
                  <span className="font-mono-metric text-secondary">31%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-secondary rounded-full" style={{ width: "31%" }}></div>
                </div>
              </div>
              {/* Item 3 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Social / Cohort Graph</span>
                  <span className="font-mono-metric text-primary-container">24%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-container rounded-full"
                    style={{ width: "24%" }}
                  ></div>
                </div>
              </div>
              {/* Item 4 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Spatial / Topographic</span>
                  <span className="font-mono-metric text-on-surface-variant">19%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-outline rounded-full" style={{ width: "19%" }}></div>
                </div>
              </div>
              {/* Item 5 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Emotional Vibe / Atmosphere</span>
                  <span className="font-mono-metric text-tertiary">18%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary rounded-full" style={{ width: "18%" }}></div>
                </div>
              </div>
              {/* Item 6 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface">Text / OCR In-Image</span>
                  <span className="font-mono-metric text-on-surface-variant">15%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div
                    className="h-full bg-outline-variant rounded-full"
                    style={{ width: "15%" }}
                  ></div>
                </div>
              </div>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant pt-2 border-t-0 bg-surface-container/40 p-2 rounded">
              Multi-anchor queries comprise{" "}
              <strong className="text-on-surface font-semibold">64.8%</strong> of high-frustration
              feedback.
            </p>
          </div>

          {/* Card 2: Source Ingestion Distribution */}
          <div className="p-space-lg rounded-xl bg-surface-container-low shadow-sm flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[20px] text-secondary">
                  pie_chart
                </span>
                <h4 className="font-headline-sm text-headline-sm text-on-surface">
                  Ingestion Sources
                </h4>
              </div>
              <span className="font-label-sm text-label-sm text-secondary flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span>
                Sync 15m
              </span>
            </div>

            {/* Inline SVG Donut Chart matching Stitch */}
            <div className="flex items-center justify-center py-2">
              <div className="relative w-36 h-36 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  {/* Background Ring */}
                  <circle
                    className="text-surface-container"
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="currentColor"
                    strokeWidth="12"
                  ></circle>
                  {/* Play Store: 41.4% */}
                  <circle
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="#4edea3"
                    strokeDasharray="98.8 139.9"
                    strokeDashoffset="0"
                    strokeWidth="12"
                  ></circle>
                  {/* Reddit: 31.9% */}
                  <circle
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="#8083ff"
                    strokeDasharray="76.1 162.6"
                    strokeDashoffset="-98.8"
                    strokeWidth="12"
                  ></circle>
                  {/* App Store: 9.9% */}
                  <circle
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="#c0c1ff"
                    strokeDasharray="23.6 215.1"
                    strokeDashoffset="-174.9"
                    strokeWidth="12"
                  ></circle>
                  {/* Community Forums: 9.7% */}
                  <circle
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="#ffb2b7"
                    strokeDasharray="23.1 215.6"
                    strokeDashoffset="-198.5"
                    strokeWidth="12"
                  ></circle>
                  {/* YouTube: 7.1% */}
                  <circle
                    cx="50"
                    cy="50"
                    fill="transparent"
                    r="38"
                    stroke="#ff516a"
                    strokeDasharray="16.9 221.8"
                    strokeDashoffset="-221.6"
                    strokeWidth="12"
                  ></circle>
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="font-display-lg text-[22px] leading-tight font-bold text-on-surface">
                    2,050
                  </span>
                  <span className="font-label-sm text-[10px] text-on-surface-variant uppercase">
                    Signals
                  </span>
                </div>
              </div>
            </div>

            {/* Legend Items */}
            <div className="flex flex-col gap-1.5 font-label-md text-label-md">
              <div className="flex items-center justify-between text-on-surface">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-secondary"></span>
                  Google Play Store
                </span>
                <span className="font-mono-metric text-on-surface-variant">849 (41.4%)</span>
              </div>
              <div className="flex items-center justify-between text-on-surface">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary-container"></span>
                  Reddit (r/googlephotos)
                </span>
                <span className="font-mono-metric text-on-surface-variant">653 (31.9%)</span>
              </div>
              <div className="flex items-center justify-between text-on-surface">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary"></span>
                  Apple App Store
                </span>
                <span className="font-mono-metric text-on-surface-variant">202 (9.9%)</span>
              </div>
              <div className="flex items-center justify-between text-on-surface">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-tertiary"></span>
                  Community Forums
                </span>
                <span className="font-mono-metric text-on-surface-variant">199 (9.7%)</span>
              </div>
              <div className="flex items-center justify-between text-on-surface">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-tertiary-container"></span>
                  YouTube Commentaries
                </span>
                <span className="font-mono-metric text-on-surface-variant">147 (7.1%)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Emerging Problems Alert Feed */}
      <section className="flex flex-col gap-space-md p-space-xl rounded-xl bg-surface-container-low shadow-sm">
        <div className="flex items-center justify-between flex-wrap gap-space-sm pb-space-xs">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-[24px] text-tertiary-container">
              local_fire_department
            </span>
            <div className="flex flex-col">
              <h3 className="font-headline-md text-headline-md text-on-surface">
                Emerging Velocity Alerts (Growth &gt; 25%)
              </h3>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                Detected anomalous complaint acceleration in the last 7-14 telemetry days.
              </span>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-tertiary-container/15 text-tertiary font-label-md text-label-md">
            <span className="h-2 w-2 rounded-full bg-tertiary-container animate-ping"></span>
            2 High-Velocity Clusters
          </span>
        </div>

        {/* Alert Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
          {/* Alert Card 1 */}
          <div className="p-space-lg rounded-xl bg-surface-container flex flex-col justify-between gap-space-md hover:bg-surface-container-high transition-colors shadow-sm">
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary font-label-sm text-label-sm font-semibold">
                  <span className="material-symbols-outlined text-[14px]">trending_up</span>
                  Velocity +44%
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm">
                  Impact: 0.84 (High)
                </span>
              </div>
              <h4 className="font-headline-sm text-headline-sm text-on-surface mt-1">
                Cross-Device Deduplication Failure After OS Cloud Sync
              </h4>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                Detected in Reddit &amp; Play Store • +44% surge in 7 days • Under Investigation
              </span>
              {/* User Quote snippet */}
              <div className="p-space-md rounded-lg bg-surface-container-lowest/80 mt-space-xs">
                <p className="font-body-sm text-body-sm text-on-surface italic">
                  “I have 4 copies of every vacation photo because iCloud and Google Photos fight over
                  who is primary, and searching ‘beach’ shows duplicate walls.”
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between pt-space-xs">
              <div className="flex items-center gap-1">
                <button
                  className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                  onClick={() =>
                    handleCitationClick(
                      "E-412",
                      "Duplicate flood on Pixel 8 after enabling background sync with iOS devices."
                    )
                  }
                  type="button"
                >
                  [E-412]
                </button>
                <button
                  className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                  onClick={() =>
                    handleCitationClick(
                      "E-418",
                      "Searching beach showed 8 copies of every single picture."
                    )
                  }
                  type="button"
                >
                  [E-418]
                </button>
              </div>
              <Link
                href="/conversations?query=duplicate"
                className="flex items-center gap-1 px-space-md py-1.5 rounded-lg bg-surface-container-highest text-on-surface hover:bg-primary hover:text-on-primary font-label-md text-label-md transition-colors"
              >
                <span>Inspect 114 Clustered Logs</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          {/* Alert Card 2 */}
          <div className="p-space-lg rounded-xl bg-surface-container flex flex-col justify-between gap-space-md hover:bg-surface-container-high transition-colors shadow-sm">
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-label-sm text-label-sm font-semibold">
                  <span className="material-symbols-outlined text-[14px]">trending_up</span>
                  Velocity +31%
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm">
                  Impact: 0.76 (Moderate)
                </span>
              </div>
              <h4 className="font-headline-sm text-headline-sm text-on-surface mt-1">
                Pet Recognition Degradation Across Multi-Pet Households
              </h4>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                Detected in App Store Reviews • +31% surge in 14 days • Prompt Regression Test
                Queued
              </span>
              {/* User Quote snippet */}
              <div className="p-space-md rounded-lg bg-surface-container-lowest/80 mt-space-xs">
                <p className="font-body-sm text-body-sm text-on-surface italic">
                  “It keeps tagging my black cat as my black labrador. I tried typing ‘dog with red
                  collar’ and it gave me pictures of shoes.”
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between pt-space-xs">
              <div className="flex items-center gap-1">
                <button
                  className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                  onClick={() =>
                    handleCitationClick(
                      "E-520",
                      "Cat / Dog confusion in low light night mode shots."
                    )
                  }
                  type="button"
                >
                  [E-520]
                </button>
                <button
                  className="font-mono-metric text-[11px] px-1.5 py-0.5 rounded bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary transition-all cursor-pointer"
                  onClick={() =>
                    handleCitationClick(
                      "E-544",
                      "Red collar query yielded zero canine hits, classified as apparel accessory."
                    )
                  }
                  type="button"
                >
                  [E-544]
                </button>
              </div>
              <Link
                href="/conversations?query=pet"
                className="flex items-center gap-1 px-space-md py-1.5 rounded-lg bg-surface-container-highest text-on-surface hover:bg-primary hover:text-on-primary font-label-md text-label-md transition-colors"
              >
                <span>Inspect 88 Clustered Logs</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Interactive Evidence Drawer Trigger */}
      <div className="flex items-center justify-between p-space-md rounded-xl bg-surface-container-low shadow-md">
        <div className="flex items-center gap-space-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-secondary"></span>
          </span>
          <span className="font-label-md text-label-md text-on-surface">
            Live Evidence Drawer ready
          </span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            • 2,050 quotes indexed with semantic vector similarity
          </span>
        </div>
        <button
          className="flex items-center gap-1 px-space-md py-1.5 rounded-lg bg-primary-container text-on-primary-container hover:bg-primary hover:text-on-primary font-label-md text-label-md transition-colors shadow-sm cursor-pointer"
          onClick={() =>
            handleCitationClick(
              "LIVE-SAMPLE",
              "Telemetry sample: 2,050 ingested raw quotes synchronized across 4 platform adapters. Filtering enabled for Groq 3.3 pipeline."
            )
          }
          type="button"
        >
          <span className="material-symbols-outlined text-[18px]">quick_reference_all</span>
          <span>Browse Evidence Repository</span>
        </button>
      </div>

      {/* Interactive Citation Slide-out Modal / Drawer */}
      {activeCitation && (
        <div
          className="fixed inset-0 z-50 bg-surface-container-lowest/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={closeCitationModal}
        >
          <div
            className="w-full max-w-lg rounded-xl bg-surface-container-high p-space-xl shadow-2xl flex flex-col gap-space-md relative border border-outline-variant/30"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface cursor-pointer p-1"
              onClick={closeCitationModal}
              type="button"
              title="Close modal"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
            <div className="flex items-center gap-space-xs">
              <span className="px-2 py-0.5 rounded bg-primary-container/30 text-primary font-mono-metric text-mono-metric font-semibold">
                [{activeCitation.id}]
              </span>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                Verified User Telemetry Citation
              </span>
            </div>
            <div className="p-space-md rounded-lg bg-surface-container-low border border-outline-variant/20">
              <p className="font-body-md text-body-md text-on-surface italic leading-relaxed">
                “{activeCitation.quote}”
              </p>
            </div>
            <div className="flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm pt-2">
              <span className="flex items-center gap-1.5 text-secondary">
                <span className="material-symbols-outlined text-[16px]">verified</span>
                Verified by Groq Llama 3.3 Semantic Parser
              </span>
              <button
                className="px-space-md py-1 rounded-lg bg-surface-container text-on-surface font-label-md text-label-md hover:bg-surface-container-highest cursor-pointer transition-colors"
                onClick={closeCitationModal}
                type="button"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
