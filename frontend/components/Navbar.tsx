"use client";

import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";
import { Circle } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    healthCheck().then((ok) => mounted && setOnline(ok));
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-6 py-3">
      <div>
        <p className="text-sm font-medium">Recruiter Dashboard</p>
      </div>
      <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
        <ThemeToggle />
        <div className="flex items-center gap-2">
          <Circle
            size={8}
            className={
              online === null ? "fill-slate-400 text-slate-400" : online ? "fill-emerald-500 text-emerald-500" : "fill-red-500 text-red-500"
            }
          />
          {online === null ? "Checking backend..." : online ? "Backend connected" : "Backend unavailable"}
        </div>
      </div>
    </header>
  );
}
