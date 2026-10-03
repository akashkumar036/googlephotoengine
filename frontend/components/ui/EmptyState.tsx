"use client";
import React from "react";
import { FolderSearch } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = "No records found",
  description = "Try adjusting your filters or search terms.",
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={twMerge(
        clsx(
          "flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30",
          className
        )
      )}
    >
      <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4 shadow-inner">
        {icon || <FolderSearch className="w-6 h-6" />}
      </div>
      <h4 className="text-base font-semibold text-white mb-1.5">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mb-6 leading-relaxed">{description}</p>
      {action}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={twMerge("animate-pulse bg-slate-800/60 rounded-xl", className)} />
  );
}
