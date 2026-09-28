"use client";

import SpotlightCard from "@/components/SpotlightCard";
import { PieChart, Pie, Cell } from "recharts";

interface AnalysisScoreProps {
  finalScore: number;
  semanticScore: number;
  skillScore: number;
  keywordScore: number;
  categories?: Record<string, number>;
}

const CATEGORY_LABELS: Record<string, string> = {
  keyword_match: "Keyword Match",
  skill_match: "Skills Match",
  semantic_match: "Semantic Match",
  contact_info: "Contact Info",
  section_structure: "Section Structure",
  achievements: "Achievements",
  action_verbs: "Action Verbs",
};

const CATEGORY_ORDER = [
  "keyword_match", "skill_match", "semantic_match",
  "contact_info", "section_structure", "achievements", "action_verbs",
];

function scoreColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#3466ff";
  if (score >= 40) return "#f59e0b";
  return "#ef4444";
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className="font-medium">{value.toFixed(0)}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, backgroundColor: scoreColor(value) }}
        />
      </div>
    </div>
  );
}

export default function AnalysisScore({ finalScore, semanticScore, skillScore, keywordScore, categories }: AnalysisScoreProps) {
  const color = scoreColor(finalScore);
  const data = [
    { value: finalScore },
    { value: 100 - finalScore },
  ];

  const bars = categories
    ? CATEGORY_ORDER.filter((k) => categories[k] !== undefined).map((k) => ({
        label: CATEGORY_LABELS[k] || k,
        value: categories[k],
      }))
    : [
        { label: "Semantic Match", value: semanticScore },
        { label: "Skill Match", value: skillScore },
        { label: "Keyword Match", value: keywordScore },
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
            <Bar key={b.label} label={b.label} value={b.value} />
          ))}
          <p className="text-xs text-[var(--text-muted)] pt-1">
            Weighted 7-category ATS model: keyword match, skills, semantic similarity,
            contact info, section structure, achievements, action verbs.
          </p>
        </div>
      </div>
    </SpotlightCard>
  );
}
