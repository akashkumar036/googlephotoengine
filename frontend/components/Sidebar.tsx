"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertCircle,
  MessageSquare,
  TrendingUp,
  Compass,
  CheckSquare,
  Cpu,
  Database,
  Radio,
  LogOut,
  UserCheck,
} from "lucide-react";
import { useSession, signOut } from "next-auth/react";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard, badge: "Live" },
  { href: "/problems", label: "Problems & Needs", icon: AlertCircle, badge: "P0/P1" },
  { href: "/conversations", label: "Conversations", icon: MessageSquare, badge: null },
  { href: "/trends", label: "Emerging Trends", icon: TrendingUp, badge: "Velocity" },
  { href: "/explore", label: "AI Assistant", icon: Compass, badge: "RAG" },
  { href: "/review", label: "Human Review", icon: CheckSquare, badge: "HITL" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <aside className="w-72 bg-slate-950/80 backdrop-blur-xl border-r border-slate-800/80 flex flex-col h-screen sticky top-0 select-none z-30 transition-all duration-300">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/70">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all duration-300">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <span className="text-xl">📸</span>
            </div>
          </div>
          <div>
            <div className="font-bold text-slate-100 tracking-tight text-base flex items-center gap-1.5">
              <span>PhotoDiscovery</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v0.1
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">AI Retrieval Research</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Intelligence Platform
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm shadow-indigo-950"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors duration-200 ${
                    isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-md font-mono transition-colors ${
                    isActive
                      ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      : "bg-slate-900 text-slate-500 group-hover:text-slate-400 border border-slate-800"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Engine Status Card */}
      <div className="p-3 mx-3 mb-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5 font-medium text-[11px]">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            Backend Pipeline
          </span>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40">
            ONLINE
          </span>
        </div>
        <div className="space-y-1 pt-1 text-[11px] text-slate-400">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-slate-500" /> Primary LLM
            </span>
            <span className="font-mono text-slate-300 text-[10px]">Groq (Llama 3.3)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-slate-500" /> Vector Store
            </span>
            <span className="font-mono text-slate-300 text-[10px]">pgvector HNSW</span>
          </div>
        </div>
      </div>

      {/* User Session Footer */}
      <div className="p-3 border-t border-slate-800/70 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-700 to-slate-800 flex items-center justify-center text-slate-300 border border-slate-700/60 font-semibold text-xs shrink-0">
            <UserCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-200 truncate">
              {session?.user?.email || "admin@example.com"}
            </p>
            <p className="text-[10px] text-indigo-400 font-mono capitalize">
              {(session?.user as unknown as { role?: string })?.role || "Admin"} • Researcher
            </p>
          </div>
        </div>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          title="Sign out"
          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 border border-transparent hover:border-rose-900/40 transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
