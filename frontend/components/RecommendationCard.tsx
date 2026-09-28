"use client";

import SpotlightCard from "@/components/SpotlightCard";
import type { AnalyzeResponse } from "@/lib/api";
import { GraduationCap } from "lucide-react";

export default function RecommendationCard({ recommendations }: { recommendations: AnalyzeResponse["recommendations"] }) {
  if (recommendations.length === 0) {
    return (
      <SpotlightCard className="p-6">
        <h3 className="font-medium mb-2">Recommendations</h3>
        <p className="text-sm text-[var(--text-muted)]">All required skills matched — no gaps to recommend against.</p>
      </SpotlightCard>
    );
  }

  return (
    <div>
      <h3 className="font-medium mb-3">Recommended Skills</h3>
      <div className="grid sm:grid-cols-2 gap-4">
        {recommendations.map((rec, i) => (
          <SpotlightCard key={rec.skill} className="p-5">
            <div className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-lg bg-brand-50 dark:bg-brand-900/30 grid place-items-center shrink-0">
                <GraduationCap size={16} className="text-brand-600 dark:text-brand-300" />
              </div>
              <div className="min-w-0">
                <p className="font-medium text-sm">{i + 1}. {rec.skill}</p>
                <p className="text-xs text-[var(--text-muted)] mb-2">{rec.level}</p>
                <div className="flex flex-wrap gap-1">
                  {rec.topics.slice(0, 4).map((t) => (
                    <span key={t} className="text-[11px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full text-[var(--text-muted)]">
                      {t}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-2">{rec.project_idea}</p>
              </div>
            </div>
          </SpotlightCard>
        ))}
      </div>
    </div>
  );
}
