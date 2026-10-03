"use client";
import React, { useState } from "react";
import { Modal } from "./ui/Modal";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { ApiService } from "@/lib/api";
import { Sparkles, Download, FileText, CheckCircle2, AlertCircle, Copy, Check } from "lucide-react";

interface ResearchBriefModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultProblemIds?: string[];
}

export function ResearchBriefModal({
  isOpen,
  onClose,
  defaultProblemIds = [],
}: ResearchBriefModalProps) {
  const [timePeriod, setTimePeriod] = useState("30d");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [isGenerating, setIsGenerating] = useState(false);
  const [brief, setBrief] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await ApiService.generateResearchBrief({
        problem_ids: defaultProblemIds.length > 0 ? defaultProblemIds : undefined,
        source_filter: sourceFilter === "all" ? undefined : sourceFilter,
        time_period: timePeriod,
      });
      setBrief(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to generate research brief. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (brief?.markdown) {
      navigator.clipboard.writeText(brief.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generate UX Research Brief"
      description="Synthesize an executive-ready photo retrieval research brief grounded in live evidence."
      maxWidth="4xl"
    >
      {!brief ? (
        <div className="space-y-6 py-2">
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                Time Horizon
              </label>
              <select
                value={timePeriod}
                onChange={(e) => setTimePeriod(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="7d">Last 7 Days (Sprint focus)</option>
                <option value="30d">Last 30 Days (Monthly synthesis)</option>
                <option value="90d">Last 90 Days (Quarterly review)</option>
                <option value="1y">Last 1 Year (Macro shifts)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                Source Filter
              </label>
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Platforms (Cross-platform synthesis)</option>
                <option value="reddit">Reddit Discussions Only</option>
                <option value="youtube">YouTube Reviews & Comments</option>
                <option value="google_play">Google Play Store</option>
              </select>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/20 text-xs text-slate-400 space-y-2">
            <div className="flex items-center gap-2 font-medium text-indigo-400">
              <Sparkles className="w-4 h-4" />
              <span>Synthesis Scope</span>
            </div>
            <p>
              {defaultProblemIds.length > 0
                ? `Analyzing ${defaultProblemIds.length} targeted problem area(s) and their linked conversation evidence.`
                : "Analyzing top problems ranked by frequency, severity, and emerging velocity across all indexed evidence."}
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="ghost" onClick={onClose} disabled={isGenerating}>
              Cancel
            </Button>
            <Button
              variant="glow"
              onClick={handleGenerate}
              isLoading={isGenerating}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Generate Brief
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
          {/* Header & Export Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div>
              <h4 className="text-base font-bold text-white">{brief.title}</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                {brief.problem_count} Problems • {brief.evidence_count} Evidence Records Analyzed
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={handleCopyMarkdown} icon={copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}>
                {copied ? "Copied" : "Copy MD"}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => downloadFile(brief.markdown, `${brief.id || "brief"}.md`, "text/markdown")}
                icon={<Download className="w-3.5 h-3.5" />}
              >
                Markdown
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => downloadFile(JSON.stringify(brief, null, 2), `${brief.id || "brief"}.json`, "application/json")}
              >
                JSON
              </Button>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="space-y-2">
            <h5 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
              Executive Summary
            </h5>
            <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              {brief.executive_summary}
            </p>
          </div>

          {/* Key Problems */}
          <div className="space-y-2">
            <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Key Discovered Problems
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {brief.key_problems?.map((prob: string, idx: number) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-200 flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="leading-snug">{prob}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Human Memory Models */}
          <div className="space-y-2">
            <h5 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
              Human Memory Models & Behavioral Anchors
            </h5>
            <div className="space-y-2">
              {brief.memory_models?.map((mm: string, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-purple-950/20 border border-purple-800/30 text-xs text-purple-200">
                  {mm}
                </div>
              ))}
            </div>
          </div>

          {/* Representative Quotes */}
          <div className="space-y-2">
            <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Representative User Evidence
            </h5>
            <div className="space-y-3">
              {brief.representative_quotes?.map((q: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border-l-4 border-indigo-500 border border-slate-800 text-xs">
                  <p className="italic text-slate-200 mb-1.5 leading-relaxed">
                    "{q.quote}"
                  </p>
                  <span className="text-[11px] text-slate-500">
                    Context: {q.context}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Opportunity Spaces */}
          <div className="space-y-2">
            <h5 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <span>Strategic Opportunities</span>
              <Badge variant="amber" size="sm">Hypotheses — Not Validated</Badge>
            </h5>
            <div className="space-y-2">
              {brief.opportunity_spaces?.map((opp: string, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 text-xs text-emerald-200 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{opp}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <Button variant="ghost" size="sm" onClick={() => setBrief(null)}>
              Generate Another Scope
            </Button>
            <Button variant="secondary" size="sm" onClick={onClose}>
              Done
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
