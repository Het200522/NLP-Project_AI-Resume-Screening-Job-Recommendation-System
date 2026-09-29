"use client";

import SpotlightCard from "@/components/SpotlightCard";
import { PieChart, Pie, Cell } from "recharts";
import type { ExperienceInfo } from "@/lib/api";

interface AnalysisScoreProps {
  finalScore: number;
  semanticScore: number;
  skillScore: number;
  keywordScore: number;
  categories?: Record<string, number | null>;
  weights?: Record<string, number>;
  experience?: ExperienceInfo;
}

const CATEGORY_LABELS: Record<string, string> = {
  skill_match: "JD Skills",
  keyword_match: "Role Keywords",
  semantic_match: "Role Relevance",
  experience_match: "Experience",
  parseability: "Parseability",
};

/** Requirement coverage first; parser readability is the only resume-only signal, so it is last. */
const CATEGORY_ORDER = [
  "skill_match", "keyword_match", "semantic_match", "experience_match", "parseability",
];

function scoreColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#3466ff";
  if (score >= 40) return "#f59e0b";
  return "#ef4444";
}

function Bar({
  label,
  value,
  weight,
}: {
  label: string;
  value: number | null;
  weight?: number;
}) {
  const title = value === null ? `${label} — not applicable for this role` : undefined;

  return (
    <div title={title}>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-[var(--text-muted)]">
          {label}
          {weight !== undefined && (
            <span className="text-[var(--text-muted)]/60 ml-1">({Math.round(weight * 100)}%)</span>
          )}
        </span>
        <span className={value === null ? "text-[var(--text-muted)]/60" : "font-medium"}>
          {value === null ? "n/a" : `${value.toFixed(0)}%`}
        </span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        {value !== null && (
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${value}%`, backgroundColor: scoreColor(value) }}
          />
        )}
      </div>
    </div>
  );
}

export default function AnalysisScore({
  finalScore,
  semanticScore,
  skillScore,
  keywordScore,
  categories,
  weights,
  experience,
}: AnalysisScoreProps) {
  const color = scoreColor(finalScore);
  const data = [
    { value: finalScore },
    { value: 100 - finalScore },
  ];

  const hasCategories = categories && Object.keys(categories).length > 0;
  const bars = hasCategories
    ? CATEGORY_ORDER.filter((k) => k in (categories ?? {})).map((k) => ({
        label: CATEGORY_LABELS[k] || k,
        value: categories?.[k] ?? null,
        weight: weights?.[k],
      }))
    : [
        { label: "Semantic Match", value: semanticScore, weight: undefined },
        { label: "Skill Match", value: skillScore, weight: undefined },
        { label: "Keyword Match", value: keywordScore, weight: undefined },
      ];

  return (
    <SpotlightCard className="p-6">
      <div className="flex flex-col md:flex-row items-center gap-8">
        <div className="relative shrink-0">
          <PieChart width={160} height={160}>
            <Pie
              data={data}
              dataKey="value"
              innerRadius={62}
              outerRadius={78}
              startAngle={90}
              endAngle={-270}
              stroke="none"
            >
              <Cell fill={color} />
              <Cell fill="var(--border)" />
            </Pie>
          </PieChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold">{finalScore.toFixed(0)}%</span>
            <span className="text-xs text-[var(--text-muted)]">ATS Score</span>
          </div>
        </div>

        <div className="flex-1 w-full space-y-3">
          {bars.map((b) => (
            <Bar key={b.label} label={b.label} value={b.value} weight={b.weight} />
          ))}

          {experience && experience.years > 0 && (
            <p className="text-xs text-[var(--text-muted)] pt-1">
              {experience.years} year{experience.years === 1 ? "" : "s"} of experience
              {experience.required ? ` estimated; this role asks for ${experience.required}` : ""}.
            </p>
          )}

          <p className="text-xs text-[var(--text-muted)] pt-1">
            This is the single ATS score. It is driven by how much of what the job asks for the
            resume actually covers; parseability only checks that an ATS can read the file at all.
            Categories that cannot be evaluated for a given role are marked n/a and their weight is
            redistributed. Minimum requirements are reported separately as pass/fail gates.
          </p>
        </div>
      </div>
    </SpotlightCard>
  );
}
