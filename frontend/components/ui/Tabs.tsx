"use client";
import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div className={twMerge("flex items-center gap-1 p-1 bg-slate-900/80 border border-slate-800 rounded-xl overflow-x-auto", className)}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={clsx(
              "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap",
              isActive
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            )}
          >
            {tab.icon}
            {tab.label}
            {typeof tab.count === "number" && (
              <span
                className={clsx(
                  "px-1.5 py-0.2 rounded-full text-[10px]",
                  isActive ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
