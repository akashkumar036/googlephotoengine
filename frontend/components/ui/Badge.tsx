"use client";
import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "indigo" | "amber" | "emerald" | "rose" | "purple" | "cyan" | "demo";
  size?: "sm" | "md";
}

export function Badge({
  children,
  className,
  variant = "default",
  size = "sm",
  ...props
}: BadgeProps) {
  const base = "inline-flex items-center font-medium rounded-full border transition-colors";
  
  const variants = {
    default: "bg-slate-800/80 text-slate-300 border-slate-700/60",
    indigo: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    rose: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    cyan: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    demo: "bg-amber-500/20 text-amber-300 border-amber-400/40 tracking-wider uppercase font-semibold text-[10px]",
  };

  const sizes = {
    sm: "px-2.5 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
  };

  return (
    <span
      className={twMerge(clsx(base, variants[variant], sizes[size], className))}
      {...props}
    >
      {children}
    </span>
  );
}
