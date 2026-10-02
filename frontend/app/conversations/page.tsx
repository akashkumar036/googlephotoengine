"use client";

import { useState } from "react";
import { MessageSquare, ExternalLink, Filter, Calendar, Tag, ShieldCheck, Sparkles } from "lucide-react";

interface ConversationItem {
  id: string;
  source: string;
  sourceUrl: string;
  author: string;
  date: string;
  rawText: string;
  sentiment: "negative" | "frustrated" | "neutral" | "positive";
  intent: "pain_point" | "feature_request" | "workaround_discussion";
  isDemo: boolean;
  relevanceScore: number;
}

const MOCK_CONVERSATIONS: ConversationItem[] = [
  {
    id: "CONV-8821",
    source: "Reddit (r/googlephotos)",
    sourceUrl: "https://reddit.com/r/googlephotos/example1",
    author: "pixel_enthusiast",
    date: "2026-09-28",
    rawText: "Is anyone else completely unable to find pictures of their dog from last year? I type 'golden retriever beach summer 2025' and it literally shows pictures of cats from 2019. The semantic search feels like it broke recently.",
    sentiment: "frustrated",
    intent: "pain_point",
    isDemo: true,
    relevanceScore: 0.94,
  },
  {
    id: "CONV-8822",
    source: "Apple Support Community",
    sourceUrl: "https://discussions.apple.com/example2",
    author: "sarah_m_photo",
    date: "2026-09-29",
    rawText: "I have shared photo library turned on with my husband. Whenever we both take photos of our daughter's birthday party, iCloud duplicates both sets into my main gallery. I spent 4 hours deleting duplicates manually last night.",
    sentiment: "negative",
    intent: "pain_point",
    isDemo: true,
    relevanceScore: 0.91,
  },
  {
    id: "CONV-8823",
    source: "Reddit (r/photography)",
    sourceUrl: "https://reddit.com/r/photography/example3",
    author: "lens_crafter",
    date: "2026-09-30",
    rawText: "I found a workaround for indexing analog scans: I write the ISO, lens, and location directly in the caption and use an external script to sync it with EXIF. Wish native apps supported smart tags for scanned film.",
    sentiment: "neutral",
    intent: "workaround_discussion",
    isDemo: true,
    relevanceScore: 0.86,
  },
  {
    id: "CONV-8824",
    source: "Reddit (r/ios)",
    sourceUrl: "https://reddit.com/r/ios/example4",
    author: "tech_curious_99",
    date: "2026-10-01",
    rawText: "Can we please have an option to completely exclude screenshots and PDF receipts from Memories? My memory reel for last week had my tax return and grocery receipts mixed with my anniversary dinner.",
    sentiment: "frustrated",
    intent: "feature_request",
    isDemo: true,
    relevanceScore: 0.97,
  },
];

export default function ConversationsPage() {
  const [selectedIntent, setSelectedIntent] = useState<string>("all");

  const filtered = MOCK_CONVERSATIONS.filter((c) => {
    if (selectedIntent !== "all" && c.intent !== selectedIntent) return false;
    return true;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Ingested Conversations</h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              14,820 Records
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Raw user feedback and community discussions normalized and processed through Groq LLaMA pipeline.
          </p>
        </div>

        {/* Demo Data Badge Notice */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
          <span>SYNTHETIC DEMO DATA LABELED</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: "all", label: "All Intent Types" },
          { id: "pain_point", label: "Pain Points" },
          { id: "feature_request", label: "Feature Requests" },
          { id: "workaround_discussion", label: "Workarounds" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedIntent(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              selectedIntent === tab.id
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Conversation Feed */}
      <div className="space-y-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all space-y-3"
          >
            <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">{item.author}</span>
                <span className="text-slate-500 font-mono text-[11px]">via {item.source}</span>
                <span className="text-slate-600">•</span>
                <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                  <Calendar className="w-3 h-3" /> {item.date}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {item.isDemo && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    DEMO DATA
                  </span>
                )}
                <span
                  className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                    item.sentiment === "frustrated" || item.sentiment === "negative"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      : "bg-slate-800 text-slate-300 border border-slate-700"
                  }`}
                >
                  {item.sentiment}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
                  Rel: {(item.relevanceScore * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-950/40 p-3.5 rounded-lg border border-slate-800/50">
              "{item.rawText}"
            </p>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
              <div className="flex items-center gap-2">
                <Tag className="w-3 h-3 text-slate-500" />
                <span className="font-mono text-indigo-400 capitalize">
                  {item.intent.replace("_", " ")}
                </span>
              </div>
              <a
                href={item.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-slate-200 flex items-center gap-1 hover:underline"
              >
                <span>Original Thread</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
