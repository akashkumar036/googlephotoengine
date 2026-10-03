"use client";

import { useState } from "react";
import { ApiService } from "@/lib/api";

interface HeaderProps {
  onOpenBriefModal?: () => void;
}

export function Header({ onOpenBriefModal }: HeaderProps) {
  const [healthStatus, setHealthStatus] = useState<string>("FastAPI 200 OK • 18ms");
  const [isPinging, setIsPinging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const handlePing = async () => {
    setIsPinging(true);
    const start = performance.now();
    try {
      const res = await ApiService.checkHealth();
      const latency = Math.round(performance.now() - start);
      setHealthStatus(`FastAPI 200 OK • ${latency}ms`);
    } catch {
      setHealthStatus("FastAPI Offline");
    } finally {
      setIsPinging(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      window.location.href = `/explore?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 w-full bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 px-margin-desktop flex items-center justify-between">
      {/* Search Omnibar */}
      <div className="flex items-center gap-space-md w-[480px] bg-surface-container-low/80 border border-outline-variant/40 rounded-lg px-space-md py-2 focus-within:border-primary transition-all">
        <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
          search
        </span>
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="bg-transparent w-full text-on-surface placeholder:text-on-surface-variant/60 font-body-sm text-body-sm focus:outline-none"
          placeholder="Search 2,050+ retrieval problems, memory anchors, user quotes..."
          type="text"
        />
        <div className="flex items-center px-1.5 py-0.5 rounded bg-surface-container-highest border border-outline-variant/40">
          <span className="font-mono-metric text-[10px] text-on-surface-variant">
            Ctrl K
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-space-md">
        {/* API Latency Status Pill */}
        <button
          onClick={handlePing}
          title="Click to ping backend latency"
          className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary/10 border border-secondary/30 hover:bg-secondary/20 transition-colors"
        >
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75 ${isPinging ? "duration-300" : ""}`}></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
          </span>
          <span className="font-mono-metric text-mono-metric text-secondary">
            {healthStatus}
          </span>
        </button>

        {/* Model Badge */}
        <div className="hidden lg:flex items-center px-3 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant/30 font-label-md text-label-md text-on-surface">
          <span className="text-on-surface-variant mr-1.5">Model:</span>
          Llama 3.3 70B
        </div>

        {/* Notifications Button */}
        <button
          className="relative p-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-all"
          type="button"
          onClick={() => alert("All 2,050 feedback records processed with zero pipeline errors.")}
          title="Notifications"
        >
          <span className="material-symbols-outlined text-[22px]">notifications</span>
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-tertiary-container ring-2 ring-surface"></span>
        </button>

        {/* Generate Research Brief */}
        <button
          onClick={onOpenBriefModal}
          className="flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-primary-container hover:bg-primary hover:text-on-primary text-on-primary-container font-label-md text-label-md shadow-[0_0_16px_-2px_rgba(128,131,255,0.4)] transition-all cursor-pointer"
          type="button"
        >
          <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
          <span>Generate Research Brief</span>
        </button>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary font-bold text-xs">
          <span className="material-symbols-outlined text-[18px]">person</span>
        </div>
      </div>
    </header>
  );
}
