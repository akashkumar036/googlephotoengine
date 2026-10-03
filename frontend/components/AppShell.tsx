"use client";

import { usePathname, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ResearchBriefModal } from "./ResearchBriefModal";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const isAuthPage = pathname === "/login";
  const [isBriefModalOpen, setIsBriefModalOpen] = useState(false);

  useEffect(() => {
    // If user lands on /login, redirect straight to dashboard
    if (isAuthPage) {
      router.replace("/");
      return;
    }

    // Ensure tokens are active in localStorage for API requests
    const token = localStorage.getItem("access_token");
    if (!token) {
      if (session?.user && (session.user as unknown as { accessToken?: string }).accessToken) {
        localStorage.setItem(
          "access_token",
          (session.user as unknown as { accessToken?: string }).accessToken as string
        );
      } else {
        // Transparent auto-sign-in with seed admin credentials
        fetch("http://localhost:8000/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: "admin@example.com",
            password: "change-me-admin-password",
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data?.access_token) {
              localStorage.setItem("access_token", data.access_token);
              if (data?.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
              }
            }
          })
          .catch(() => {});
      }
    }
  }, [session, isAuthPage, router]);

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <Sidebar />
      <div className="pl-[260px] flex flex-col min-h-screen">
        <Header onOpenBriefModal={() => setIsBriefModalOpen(true)} />
        <main className="w-full max-w-7xl mx-auto p-margin-desktop min-h-[calc(100vh-64px)] bg-surface">
          {children}
        </main>
      </div>

      <ResearchBriefModal
        isOpen={isBriefModalOpen}
        onClose={() => setIsBriefModalOpen(false)}
      />
    </div>
  );
}
