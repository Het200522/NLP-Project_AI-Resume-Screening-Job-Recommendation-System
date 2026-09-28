"use client";

import { useEffect, useState } from "react";
import SpotlightCard from "@/components/SpotlightCard";
import EmptyState from "@/components/EmptyState";
import { listCandidates, reportDownloadUrl, type CandidateListItem } from "@/lib/api";
import { Download } from "lucide-react";

export default function ReportsPage() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listCandidates()
      .then(setCandidates)
      .catch(() => setCandidates([]))
      .finally(() => setLoaded(true));
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reports</h1>
        <p className="text-sm text-[var(--text-muted)]">Download PDF analysis reports for past resume analyses.</p>
      </div>

      {loaded && candidates.length === 0 && (
        <EmptyState title="No reports yet" description="Run a resume analysis to generate a downloadable PDF report." />
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        {candidates.map((c) => (
          <SpotlightCard key={c.id} className="p-5 flex items-center justify-between">
            <div className="min-w-0">
              <p className="font-medium truncate">{c.candidate_name || "Not detected"}</p>
              <p className="text-xs text-[var(--text-muted)] truncate">{c.job_title || "—"} · {c.final_score.toFixed(0)}% match</p>
            </div>
            <a
              href={reportDownloadUrl(c.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 ml-3 h-9 w-9 grid place-items-center rounded-lg border border-[var(--border)] hover:bg-slate-50 dark:hover:bg-slate-800"
              aria-label="Download report"
            >
              <Download size={15} />
            </a>
          </SpotlightCard>
        ))}
      </div>
    </div>
  );
}
