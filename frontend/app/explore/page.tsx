"use client";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Send,
  Bot,
  User,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertCircle,
  Lightbulb,
  FileText,
  Clock,
  ArrowRight,
  Database,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  answerType?: "evidence_grounded" | "interpretation" | "hypothesis";
  confidence?: number;
  evidence?: any[];
  relatedProblems?: any[];
  keyInsights?: string[];
  openQuestions?: string[];
  timestamp: string;
}

export default function ExploreAssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [starters, setStarters] = useState<string[]>([]);
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadStarters() {
      try {
        const res = await ApiService.getResearchStarters();
        setStarters(res?.starters || []);
      } catch {
        setStarters([
          "What are the most common reasons people fail to find old photos?",
          "Which failure modes are increasing the fastest across Reddit and YouTube?",
          "Give me 5 unmet needs related to forgotten photos and screenshots.",
          "How do users describe lost memories when searching without exact dates?",
        ]);
      }
    }
    loadStarters();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (queryText: string) => {
    const q = queryText.trim();
    if (!q || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const historyPayload = messages.map((m) => ({
        role: m.sender === "user" ? "user" : "assistant",
        content: m.text,
      }));

      const res = await ApiService.askResearchAssistant(q, historyPayload);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: res.answer,
        answerType: res.answer_type || "evidence_grounded",
        confidence: res.confidence,
        evidence: res.evidence || [],
        relatedProblems: res.related_problems || [],
        keyInsights: res.key_insights || [],
        openQuestions: res.open_questions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: "I encountered an error querying the research knowledge base. Please ensure the backend is running and try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              AI Research Assistant
            </h1>
            <Badge variant="purple" size="sm">
              <Database className="w-3 h-3 mr-1 inline" />
              Grounded RAG
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Ask complex UX research questions. Answers are synthesized exclusively from indexed conversation evidence with verifiable inline citations.
          </p>
        </div>
      </div>

      {/* Chat Container */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl min-h-[500px] flex flex-col shadow-2xl overflow-hidden backdrop-blur-md">
        {/* Messages Body */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto max-h-[65vh]">
          {messages.length === 0 ? (
            <div className="py-12 px-4 text-center space-y-6">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto shadow-inner">
                <Bot className="w-7 h-7" />
              </div>
              <div className="space-y-1.5 max-w-md mx-auto">
                <h3 className="text-base font-semibold text-white">Ask the Photo Discovery Knowledge Base</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Query across all synthesized clusters, retrieval failure modes, and user quotes with automated evidence grounding.
                </p>
              </div>

              {/* Starter Questions */}
              <div className="max-w-xl mx-auto space-y-2 pt-2 text-left">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block px-1">
                  Suggested Research Questions
                </span>
                <div className="grid grid-cols-1 gap-2">
                  {starters.map((starter, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSubmit(starter)}
                      className="text-left text-xs text-slate-300 hover:text-white p-3 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 transition-all flex items-center justify-between group"
                    >
                      <span className="line-clamp-1">{starter}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors flex-shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`space-y-3 max-w-2xl ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`p-5 rounded-2xl text-sm leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20 ml-12 rounded-br-none"
                        : "bg-slate-950/90 border border-slate-800 text-slate-200 rounded-bl-none shadow-md"
                    }`}
                  >
                    {/* Header for assistant message */}
                    {msg.sender === "assistant" && msg.answerType && (
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800/80">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              msg.answerType === "evidence_grounded"
                                ? "emerald"
                                : msg.answerType === "interpretation"
                                ? "indigo"
                                : "amber"
                            }
                            size="sm"
                          >
                            {msg.answerType.replace("_", " ").toUpperCase()}
                          </Badge>
                          {msg.confidence !== undefined && (
                            <span className="text-[11px] text-slate-400">
                              Confidence: {Math.round(msg.confidence * 100)}%
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
                      </div>
                    )}

                    {/* Answer text */}
                    <div className="whitespace-pre-wrap">{msg.text}</div>

                    {/* Key Insights Pills */}
                    {msg.keyInsights && msg.keyInsights.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5">
                        <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider block">
                          Key Insights
                        </span>
                        <div className="space-y-1">
                          {msg.keyInsights.map((insight, i) => (
                            <div key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                              <span>{insight}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Evidence Cards Tray */}
                  {msg.evidence && msg.evidence.length > 0 && (
                    <div className="space-y-2 pt-1 pl-1">
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
                        <FileText className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Supporting Evidence Records ({msg.evidence.length})</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {msg.evidence.map((ev, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-1.5 hover:border-slate-700 transition-colors cursor-pointer"
                            onClick={() =>
                              setExpandedCitation(expandedCitation === ev.citation_id ? null : ev.citation_id)
                            }
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-indigo-400 font-bold">[{ev.citation_id}]</span>
                              <Badge variant="default" size="sm">{ev.source?.toUpperCase() || "SOURCE"}</Badge>
                            </div>
                            <p className="text-slate-300 line-clamp-2 italic leading-relaxed">
                              "{ev.excerpt}"
                            </p>
                            {expandedCitation === ev.citation_id && (
                              <div className="pt-2 mt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1 animate-in fade-in">
                                <div><strong>Intent:</strong> {ev.intent}</div>
                                <div><strong>Failure Modes:</strong> {(ev.failure_modes || []).join(", ") || "None"}</div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related Problems */}
                  {msg.relatedProblems && msg.relatedProblems.length > 0 && (
                    <div className="pt-2 pl-1 flex flex-wrap items-center gap-2 text-xs">
                      <span className="text-slate-500">Related Problems:</span>
                      {msg.relatedProblems.map((p: any) => (
                        <Link
                          key={p.id}
                          href={`/problems/${p.id}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-indigo-300 hover:text-white hover:border-indigo-500 transition-colors line-clamp-1"
                        >
                          {p.title}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                {msg.sender === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex gap-3.5 items-start">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center flex-shrink-0 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center gap-3">
                <Sparkles className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Searching vector embeddings and synthesizing evidence-grounded answer...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-slate-950 border-t border-slate-800">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(inputQuery);
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              placeholder="Ask a question (e.g., 'What causes users to abandon search when looking for vacation photos?')..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isLoading}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <Button
              type="submit"
              variant="glow"
              size="md"
              disabled={!inputQuery.trim() || isLoading}
              icon={<Send className="w-4 h-4" />}
            >
              Ask
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
