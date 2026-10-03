"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";

const NAV_ITEMS = [
  {
    href: "/",
    label: "Overview",
    icon: "dashboard",
    badge: null,
  },
  {
    href: "/conversations",
    label: "Live Feed",
    icon: "rss_feed",
    badge: "2,050",
    badgeClass: "bg-surface-container-highest text-on-surface-variant",
  },
  {
    href: "/explore",
    label: "Research Assistant",
    icon: "auto_awesome",
    badge: "Groq 3.3",
    badgeClass: "bg-primary/20 text-primary",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <aside className="fixed left-0 top-0 h-screen w-[260px] bg-surface-container-low/90 backdrop-blur-xl border-r border-outline-variant/30 z-40 flex flex-col justify-between overflow-y-auto select-none">
      <div className="p-space-lg flex flex-col gap-space-lg">
        {/* Brand Header */}
        <Link href="/" className="flex items-center gap-space-sm group">
          <div className="h-10 w-10 rounded-lg bg-surface-container-highest border border-outline-variant/40 flex items-center justify-center text-primary shadow-sm group-hover:scale-105 transition-transform">
            <span className="material-symbols-outlined text-[24px]">camera</span>
          </div>
          <div className="flex flex-col">
            <span className="font-headline-sm text-headline-sm text-on-surface leading-tight">
              Photo Discovery
            </span>
            <div className="flex items-center gap-space-xs mt-0.5">
              <span className="font-label-sm text-label-sm px-1.5 py-0.5 rounded bg-surface-container-highest text-primary border border-outline-variant/40 uppercase tracking-wider">
                v2.4 Enterprise AI
              </span>
            </div>
          </div>
        </Link>

        {/* Pipeline Status Widget */}
        <div className="p-space-md rounded-xl bg-surface-container/60 backdrop-blur-md border border-outline-variant/30 flex flex-col gap-space-xs shadow-inner">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-space-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
              </span>
              <span className="font-label-md text-label-md text-secondary font-semibold">
                Pipeline ONLINE
              </span>
            </div>
            <span className="font-mono-metric text-mono-metric text-on-surface-variant">
              94ms
            </span>
          </div>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            2,050 Ingested • Groq Llama 3.3
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-col gap-space-xs">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-space-md py-space-sm rounded-lg transition-all ${
                  isActive
                    ? "bg-primary-container text-on-primary-container font-semibold shadow-[0_0_16px_-2px_rgba(128,131,255,0.4)]"
                    : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                }`}
              >
                <div className="flex items-center gap-space-md">
                  <span className="material-symbols-outlined text-[20px]">
                    {item.icon}
                  </span>
                  <span className="font-label-md text-label-md">
                    {item.label}
                  </span>
                </div>
                {item.badge && (
                  <span
                    className={`font-label-sm text-label-sm px-1.5 py-0.5 rounded-full ${
                      item.badgeClass ||
                      "bg-surface-container-highest text-on-surface-variant"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Footer: Active Feeds & User Profile */}
      <div className="p-space-lg flex flex-col gap-space-md border-t border-outline-variant/30">
        <div className="flex flex-col gap-space-xs">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
            Active Ingestion Feeds
          </span>
          <div className="flex flex-wrap gap-space-xs">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-sm text-label-sm border border-outline-variant/30">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span>Play
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-sm text-label-sm border border-outline-variant/30">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span>Reddit
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-sm text-label-sm border border-outline-variant/30">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span>YT
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-on-surface font-label-sm text-label-sm border border-outline-variant/30">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span>App Store
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-space-xs">
          <div className="flex items-center gap-space-sm">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary text-[18px]">
                person
              </span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-md text-label-md text-on-surface leading-snug">
                {session?.user?.name || "Dr. Elena Vance"}
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant leading-none">
                Lead UX AI
              </span>
            </div>
          </div>
          <Link
            href="/evaluation"
            className="text-on-surface-variant hover:text-on-surface transition-colors p-1"
            title="System Settings & Evaluation"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </Link>
        </div>
      </div>
    </aside>
  );
}
