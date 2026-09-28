"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ScanSearch, Users, FileText, Settings, Sparkles } from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analyze", label: "Analyze Resume", icon: ScanSearch },
  { href: "/candidates", label: "Candidates", icon: Users },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)] px-4 py-5">
      <Link href="/" className="flex items-center gap-2 px-2 mb-8">
        <div className="grid place-items-center h-8 w-8 rounded-lg bg-brand-500 text-white">
          <Sparkles size={16} />
        </div>
        <span className="font-semibold text-sm">Resume Screener</span>
      </Link>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-brand-50 text-brand-700 font-medium dark:bg-brand-900/30 dark:text-brand-300"
                  : "text-[var(--text-muted)] hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-2 pt-6 text-xs text-[var(--text-muted)]">
        <p>NLP Pipeline Active</p>
        <p className="mt-1">TF-IDF · Embeddings · NER</p>
      </div>
    </aside>
  );
}
