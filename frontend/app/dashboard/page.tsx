"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SpotlightCard from "@/components/SpotlightCard";
import EmptyState from "@/components/EmptyState";
import { listCandidates, type CandidateListItem } from "@/lib/api";
import { ScanSearch, Users, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listCandidates()
      .then(setCandidates)
      .catch(() => setCandidates([]))
      .finally(() => setLoaded(true));
  }, []);

  const avgScore = candidates.length
    ? Math.round(candidates.reduce((sum, c) => sum + c.final_score, 0) / candidates.length)
    : 0;

  const stats = [
    { label: "Total Analyses", value: candidates.length, icon: ScanSearch },
    { label: "Unique Candidates", value: new Set(candidates.map((c) => c.email || c.candidate_name)).size, icon: Users },
    { label: "Average ATS Score", value: `${avgScore}%`, icon: TrendingUp },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-[var(--text-muted)]">Overview of your resume screening activity.</p>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <SpotlightCard key={label} className="p-5">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-brand-50 dark:bg-brand-900/30 grid place-items-center">
                <Icon size={17} className="text-brand-600 dark:text-brand-300" />
              </div>
              <div>
                <p className="text-xl font-semibold">{value}</p>
                <p className="text-xs text-[var(--text-muted)]">{label}</p>
              </div>
            </div>
          </SpotlightCard>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium">Recent Analyses</h2>
          <Link href="/analyze" className="text-sm text-brand-600 dark:text-brand-300 hover:underline">
            New Analysis →
          </Link>
        </div>

        {loaded && candidates.length === 0 && (
          <EmptyState title="No analyses yet" description="Analyze a resume to see it show up here." />
        )}

        {candidates.length > 0 && (
          <SpotlightCard className="overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-left text-xs text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">Candidate</th>
                  <th className="px-4 py-3 font-medium">Job Title</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.slice(0, 8).map((c) => (
                  <tr key={c.id} className="border-t border-[var(--border)]">
                    <td className="px-4 py-3">{c.candidate_name || "Not detected"}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{c.job_title || "—"}</td>
                    <td className="px-4 py-3 font-medium">{c.final_score.toFixed(0)}%</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{c.status || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </SpotlightCard>
        )}
      </div>
    </div>
  );
}
