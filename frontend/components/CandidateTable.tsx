"use client";

import { useMemo, useState } from "react";
import type { BulkCandidateResult } from "@/lib/api";
import { ArrowUpDown } from "lucide-react";

type SortKey = "final_score" | "skills_matched" | "missing_skills";

export default function CandidateTable({ results }: { results: BulkCandidateResult[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("final_score");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...results];
    copy.sort((a, b) => (asc ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey]));
    return copy;
  }, [results, sortKey, asc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(false);
    }
  }

  function statusStyle(status: string) {
    if (status === "Error") return "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300";
    if (status === "Strong Match") return "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300";
    if (status === "Good Match") return "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300";
    if (status === "Partial Match") return "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300";
    return "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300";
  }

  const HeaderCell = ({ label, sortableKey }: { label: string; sortableKey?: SortKey }) => (
    <th
      className={`px-4 py-3 font-medium ${sortableKey ? "cursor-pointer select-none" : ""}`}
      onClick={() => sortableKey && toggleSort(sortableKey)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sortableKey && <ArrowUpDown size={12} />}
      </span>
    </th>
  );

  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface)]">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 dark:bg-slate-800/50 text-left text-xs text-[var(--text-muted)]">
          <tr>
            <HeaderCell label="Candidate" />
            <HeaderCell label="ATS Score" sortableKey="final_score" />
            <HeaderCell label="Skills Matched" sortableKey="skills_matched" />
            <HeaderCell label="Missing Skills" sortableKey="missing_skills" />
            <HeaderCell label="Status" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={i} className="border-t border-[var(--border)]">
              <td className="px-4 py-3">
                <p className="font-medium">{r.candidate_name || r.filename}</p>
                {r.error && <p className="text-xs text-red-500">{r.error}</p>}
              </td>
              <td className="px-4 py-3 font-medium">{r.final_score.toFixed(0)}%</td>
              <td className="px-4 py-3">{r.skills_matched}</td>
              <td className="px-4 py-3">{r.missing_skills}</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2.5 py-1 rounded-full ${statusStyle(r.status)}`}>{r.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
