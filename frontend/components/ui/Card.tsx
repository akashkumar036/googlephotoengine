"use client";
import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glow?: boolean;
}

export function Card({
  children,
  className,
  hover = false,
  glow = false,
  ...props
}: CardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          "bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden",
          hover && "transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/80 hover:shadow-2xl hover:translate-y-[-2px]",
          glow && "border-indigo-500/30 shadow-indigo-500/5",
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={twMerge("flex items-center justify-between gap-4 mb-4", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={twMerge("text-lg font-semibold text-white tracking-tight", className)}>{children}</h3>;
}

export function CardDescription({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={twMerge("text-xs text-slate-400 leading-relaxed", className)}>{children}</p>;
}
