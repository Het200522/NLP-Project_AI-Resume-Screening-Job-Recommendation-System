"use client";

import { useEffect, useState } from "react";

import SpotlightCard from "@/components/SpotlightCard";
import { getScoringConfig, getErrorMessage, type ScoringConfig } from "@/lib/api";

const CATEGORY_LABELS: Record<string, { label: string; description: string }> = {
  skill_match: { label: "JD Skill Coverage", description: "Share of the job's skills present in the resume" },
  keyword_match: { label: "Role Keywords", description: "Job keywords present, synonym and fuzzy aware" },
  semantic_match: { label: "Semantic Relevance", description: "Sentence-embedding similarity, calibrated" },
  experience_match: { label: "Experience Fit", description: "Years of experience vs. the role's requirement" },
  parseability: { label: "Parseability", description: "Whether an ATS can read the file at all" },
};

const PARSEABILITY_LABELS: Record<string, string> = {
  contact_info: "Contact completeness",
  section_structure: "Section structure",
  formatting: "Formatting risk",
  length: "Length & structure",
};

function percent(weight: number): string {
  return `${Math.round(weight * 100)}%`;
}

export default function SettingsPage() {
  const [config, setConfig] = useState<ScoringConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getScoringConfig()
      .then(setConfig)
      .catch((err) => setError(getErrorMessage(err)));
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-[var(--text-muted)]">Scoring configuration is managed on the backend for consistency across all analyses.</p>
      </div>

      <SpotlightCard className="p-6">
        <h3 className="font-medium mb-3">ATS Scoring Formula</h3>
        {error ? (
          <p className="text-sm text-red-600 dark:text-red-400">
            Could not load the scoring configuration: {error}
          </p>
        ) : !config ? (
          <p className="text-sm text-[var(--text-muted)]">Loading scoring configuration…</p>
        ) : (
          <>
            <p className="text-sm text-[var(--text-muted)] mb-4">
              {config.formula} Configured in{" "}
              <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">backend/app/config.py</code>{" "}
              via environment variables. Weights shown below are read live from the backend.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm mb-5">
              {Object.entries(config.weights).map(([key, weight]) => {
                const meta = CATEGORY_LABELS[key] ?? { label: key, description: "" };
                return (
                  <div key={key} className="flex items-center justify-between border border-[var(--border)] rounded-lg px-3 py-2">
                    <div>
                      <p className="font-medium">{meta.label}</p>
                      <p className="text-[var(--text-muted)] text-xs">{meta.description}</p>
                    </div>
                    <span className="font-semibold text-lg shrink-0 ml-3">{percent(weight)}</span>
                  </div>
                );
              })}
            </div>

            <p className="text-sm text-[var(--text-muted)] mb-3">
              Parseability sub-weights (they compose the category above, they are not added on top):
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm mb-5">
              {Object.entries(config.parseability_weights).map(([key, weight]) => (
                <div key={key} className="flex items-center justify-between border border-[var(--border)] rounded-lg px-3 py-2">
                  <p className="font-medium">{PARSEABILITY_LABELS[key] ?? key}</p>
                  <span className="font-semibold text-lg shrink-0 ml-3">{percent(weight)}</span>
                </div>
              ))}
            </div>

            <p className="text-xs text-[var(--text-muted)] border-t border-[var(--border)] pt-3">
              {config.knockouts_note} Semantic calibration maps cosine similarity below {config.semantic_floor} to 0 and at or above {config.semantic_ceiling} to 100.
            </p>
          </>
        )}
      </SpotlightCard>

      <SpotlightCard className="p-6">
        <h3 className="font-medium mb-3">Backend Connection</h3>
        <p className="text-sm text-[var(--text-muted)]">
          API URL: <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</code>
        </p>
      </SpotlightCard>
    </div>
  );
}
