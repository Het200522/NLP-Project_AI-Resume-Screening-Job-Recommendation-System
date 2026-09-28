"use client";

import SpotlightCard from "@/components/SpotlightCard";

const ATS_CATEGORIES = [
  { label: "Keyword Match", weight: "30%", description: "JD keywords found in resume" },
  { label: "Skills Match", weight: "25%", description: "Required skills matched" },
  { label: "Semantic Match", weight: "15%", description: "Sentence-embedding similarity" },
  { label: "Contact Info", weight: "10%", description: "Name, email, phone, LinkedIn, GitHub" },
  { label: "Section Structure", weight: "10%", description: "Standard resume sections present" },
  { label: "Achievements", weight: "5%", description: "Quantifiable metrics (numbers, %, $)" },
  { label: "Action Verbs", weight: "5%", description: "Strong action verb usage" },
];

export default function SettingsPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-[var(--text-muted)]">Scoring configuration is managed on the backend for consistency across all analyses.</p>
      </div>

      <SpotlightCard className="p-6">
        <h3 className="font-medium mb-3">Real-World ATS Scoring Formula</h3>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Final Score = Σ (weight × category_score) across 7 categories modeled after how
          commercial ATS systems (Workday, Taleo, Greenhouse, iCIMS) are publicly known
          to rank candidates. Configured in{" "}
          <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">backend/app/config.py</code>{" "}
          via environment variables.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          {ATS_CATEGORIES.map((cat) => (
            <div key={cat.label} className="flex items-center justify-between border border-[var(--border)] rounded-lg px-3 py-2">
              <div>
                <p className="font-medium">{cat.label}</p>
                <p className="text-[var(--text-muted)] text-xs">{cat.description}</p>
              </div>
              <span className="font-semibold text-lg shrink-0 ml-3">{cat.weight}</span>
            </div>
          ))}
        </div>
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
