"use client";

import SpotlightCard from "@/components/SpotlightCard";
import type { AnalyzeResponse } from "@/lib/api";
import { CheckCircle2, AlertCircle } from "lucide-react";

export default function ResumeQuality({ quality }: { quality: AnalyzeResponse["quality"] }) {
  if (!quality?.checks?.length) return null;

  return (
    <SpotlightCard className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium">Resume Quality Checks</h3>
        <span className="text-sm text-[var(--text-muted)]">
          {quality.passed}/{quality.total} passed
        </span>
      </div>
      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
        {quality.checks.map((check) => (
          <div key={check.label} className="flex items-start gap-2 text-sm">
            {check.passed ? (
              <CheckCircle2 size={15} className="text-emerald-500 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle size={15} className="text-amber-500 shrink-0 mt-0.5" />
            )}
            <div>
              <span className={check.passed ? "" : "text-[var(--text-muted)]"}>{check.label}</span>
              {!check.passed && check.detail && (
                <p className="text-xs text-[var(--text-muted)]">{check.detail}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
