"use client";

import { useState } from "react";
import { CheckSquare, Check, X, Edit3, Merge, Sparkles, UserCheck } from "lucide-react";

interface ReviewQueueItem {
  id: string;
  type: "problem" | "cluster" | "extraction";
  title: string;
  proposedSeverity: string;
  confidence: number;
  reasoning: string;
  evidenceQuotes: string[];
}

const MOCK_REVIEWS: ReviewQueueItem[] = [
  {
    id: "REV-201",
    type: "problem",
    title: "AI Deletion of Raw Image Backups",
    proposedSeverity: "P0",
    confidence: 0.94,
    reasoning: "Groq Stage 2 synthesis identified 28 corroborating complaints where phone cleanup algorithms treated high-res DNG files as redundant copies of processed JPEGs.",
    evidenceQuotes: [
      "Lost 3 months of raw travel photography because phone suggested 'clean up storage' and deleted all my .DNG files while keeping blurry preview JPEGs.",
      "Google Photos wiped my RAW files on the pixel and only retained compressed versions.",
    ],
  },
  {
    id: "REV-202",
    type: "problem",
    title: "Facial Recognition Drift Across Infant Growth",
    proposedSeverity: "P1",
    confidence: 0.88,
    reasoning: "Users report person clustering breaks completely when children grow from 6 months to 2 years, fragmenting into 8 different unrecognized person albums.",
    evidenceQuotes: [
      "My baby is recognized as 7 different people. Why doesn't the algorithm understand human aging progression?",
      "Every time my toddler gets a haircut, Google photos creates a brand new person identity.",
    ],
  },
];

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewQueueItem[]>(MOCK_REVIEWS);
  const [reviewedCount, setReviewedCount] = useState(0);

  const handleAction = (id: string, action: "approve" | "reject") => {
    setItems((prev) => prev.filter((i) => i.id !== id));
    setReviewedCount((prev) => prev + 1);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Human Review & Evaluation</h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/30">
              HITL Feedback Loop
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Validate AI-synthesized problem cards, correct severity classifications, and curate gold evaluation benchmarks.
          </p>
        </div>

        <div className="inline-flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <span className="text-slate-400">Reviewed Today:</span>
          <span className="font-mono text-emerald-400 font-bold">{reviewedCount} items</span>
        </div>
      </div>

      {/* Review Cards */}
      <div className="space-y-5">
        {items.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
            <UserCheck className="w-10 h-10 text-emerald-400 mx-auto" />
            <h3 className="text-base font-semibold text-slate-200">Review Queue Cleared</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              All candidate problems and clusters have been reviewed by a human researcher.
            </p>
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4 shadow-xl"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-mono text-slate-500">{item.id}</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-bold">
                    {item.type}
                  </span>
                  <h3 className="text-base font-bold text-slate-100">{item.title}</h3>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Proposed Severity:</span>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {item.proposedSeverity}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    (Conf: {(item.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>

              {/* AI Reasoning */}
              <div className="text-xs text-slate-300 bg-slate-950/50 p-4 rounded-lg border border-slate-800/60 space-y-1.5">
                <div className="flex items-center gap-1.5 text-indigo-400 font-semibold text-[11px]">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Groq Synthesis Reasoning</span>
                </div>
                <p className="leading-relaxed text-slate-400">{item.reasoning}</p>
              </div>

              {/* Evidence Quotes */}
              <div className="space-y-2">
                <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block">
                  Grounding Evidence Quotes ({item.evidenceQuotes.length})
                </span>
                <div className="space-y-1.5">
                  {item.evidenceQuotes.map((quote, idx) => (
                    <blockquote
                      key={idx}
                      className="text-xs text-slate-300 bg-slate-950/30 pl-3 pr-2 py-2 rounded border-l-2 border-indigo-500 italic"
                    >
                      "{quote}"
                    </blockquote>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-end gap-3">
                <button
                  onClick={() => handleAction(item.id, "reject")}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/50 text-slate-400 hover:text-rose-300 border border-slate-800 hover:border-rose-900/40 text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject / Hallucination</span>
                </button>
                <button
                  onClick={() => handleAction(item.id, "approve")}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition-all"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve Problem</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
