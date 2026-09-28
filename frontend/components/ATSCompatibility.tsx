"use client";

import SpotlightCard from "@/components/SpotlightCard";
import type { AnalyzeResponse } from "@/lib/api";
import { AlertTriangle } from "lucide-react";

const CATEGORY_LABELS: Record<string, string> = {
  keyword_match: "Keyword Match vs. Job Description",
  section_structure: "Standard Section Structure",
  contact_completeness: "Contact Completeness",
  quantifiable_achievements: "Quantifiable Achievements",
  action_verb_usage: "Action-Verb Usage",
  formatting_risk: "Formatting Risk",
  length_structure: "Length & Structure",
};

function bandColor(score: number): string {
  if (score >= 85) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 70) return "text-brand-600 dark:text-brand-300";
  if (score >= 50) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export default function ATSCompatibility({ compatibility }: { compatibility: AnalyzeResponse["compatibility"] }) {
  const ats = compatibility.ats_score;

  return (
    <SpotlightCard className="p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between mb-1">
          <h3 className="font-medium text-sm">ATS Readiness</h3>
          <span className={`text-2xl font-bold ${bandColor(ats.overall_score)}`}>{ats.overall_score.toFixed(0)}</span>
        </div>
        <p className={`text-sm font-medium mb-4 ${bandColor(ats.overall_score)}`}>{ats.band}</p>

        <div className="space-y-2 mb-4">
          {Object.entries(ats.categories).map(([key, cat]) => (
            <div key={key}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-[var(--text-muted)]">{CATEGORY_LABELS[key] || key}</span>
                <span className="font-medium">{cat.score.toFixed(0)}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500 transition-all duration-700"
                  style={{ width: `${cat.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {ats.recommendations.length > 0 && (
        <div className="border-t border-[var(--border)] pt-3 space-y-1.5">
          {ats.recommendations.map((r, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-amber-700 dark:text-amber-400">
              <AlertTriangle size={13} className="shrink-0 mt-0.5" />
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      <p className="text-[10px] text-[var(--text-muted)] mt-3 border-t border-[var(--border)] pt-2">
        {ats.disclaimer}
      </p>
    </SpotlightCard>
  );
}
