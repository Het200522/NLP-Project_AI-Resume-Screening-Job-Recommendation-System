"use client";

import SpotlightCard from "@/components/SpotlightCard";
import type { AnalyzeResponse } from "@/lib/api";
import { CheckCircle2, XCircle, ShieldCheck, ShieldAlert } from "lucide-react";

/**
 * Hard requirements and parser compatibility.
 *
 * This panel deliberately shows no score. The single ATS score lives in
 * AnalysisScore; duplicating a number here is what previously let two panels
 * disagree (contact 50% vs 100%, achievements 33% vs 100%). What is shown
 * instead is the set of minimums the posting states, and whether the resume
 * clears each one, which is what a real ATS does before it ranks anyone.
 */
export default function ATSCompatibility({
  compatibility,
  knockouts,
}: {
  compatibility: AnalyzeResponse["compatibility"];
  knockouts: AnalyzeResponse["knockouts"];
}) {
  const failedIndicators = compatibility.indicators.filter((i) => !i.ok);

  return (
    <SpotlightCard className="p-6 flex flex-col">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <h3 className="font-medium text-sm">Hard Requirements</h3>
          {knockouts.evaluated ? (
            knockouts.passed ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <ShieldCheck size={14} /> All met
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600 dark:text-red-400">
                <ShieldAlert size={14} /> {knockouts.failed.length} not met
              </span>
            )
          ) : null}
        </div>
        <p className="text-xs text-[var(--text-muted)] mb-4">
          {knockouts.evaluated
            ? "Minimums this job description states. These are pass/fail filters, not part of the score."
            : "This job description states no hard minimum requirements, so there is nothing to filter on."}
        </p>

        {knockouts.gates.length > 0 && (
          <div className="space-y-3 mb-4">
            {knockouts.gates.map((gate, i) => (
              <div key={i} className="flex items-start gap-2">
                {gate.requirement_met ? (
                  <CheckCircle2
                    size={15}
                    className="shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400"
                  />
                ) : (
                  <XCircle
                    size={15}
                    className="shrink-0 mt-0.5 text-red-600 dark:text-red-400"
                  />
                )}
                <div>
                  <p className="text-xs font-medium">{gate.label}</p>
                  <p className="text-xs text-[var(--text-muted)]">{gate.detail}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {failedIndicators.length > 0 && (
          <div className="border-t border-[var(--border)] pt-3">
            <h4 className="text-xs font-medium text-amber-700 dark:text-amber-400 mb-1.5">
              Parser compatibility
            </h4>
            <ul className="space-y-1">
              {failedIndicators.map((ind, i) => (
                <li key={i} className="text-xs text-[var(--text-muted)]">
                  {ind.label}
                  {ind.note ? ` — ${ind.note}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </SpotlightCard>
  );
}
