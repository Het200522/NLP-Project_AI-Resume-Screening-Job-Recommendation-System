"use client";

import SpotlightCard from "@/components/SpotlightCard";
import { PieChart, Pie, Cell, Legend, Tooltip } from "recharts";
import { Check, X } from "lucide-react";

interface SkillMatchChartProps {
  matched: string[];
  missing: string[];
  totalJdSkills: number;
}

export default function SkillMatchChart({ matched, missing, totalJdSkills }: SkillMatchChartProps) {
  const data = [
    { name: "Matched", value: matched.length, color: "#10b981" },
    { name: "Missing", value: missing.length, color: "#ef4444" },
  ];

  return (
    <SpotlightCard className="p-6">
      <h3 className="font-medium mb-4">Skill Analysis</h3>

      <div className="flex flex-col sm:flex-row items-center gap-6 mb-6">
        <PieChart width={140} height={140}>
          <Pie data={data} dataKey="value" innerRadius={40} outerRadius={60} paddingAngle={2}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={24} iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
        <div className="grid grid-cols-3 gap-4 text-center flex-1">
          <div>
            <p className="text-xl font-semibold">{matched.length}</p>
            <p className="text-xs text-[var(--text-muted)]">Matched</p>
          </div>
          <div>
            <p className="text-xl font-semibold">{missing.length}</p>
            <p className="text-xs text-[var(--text-muted)]">Missing</p>
          </div>
          <div>
            <p className="text-xl font-semibold">{totalJdSkills}</p>
            <p className="text-xs text-[var(--text-muted)]">Total JD Skills</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">Matched Skills</p>
          <div className="flex flex-wrap gap-1.5">
            {matched.length === 0 && <span className="text-xs text-[var(--text-muted)]">None detected</span>}
            {matched.map((s) => (
              <span key={s} className="flex items-center gap-1 text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 px-2.5 py-1 rounded-full">
                <Check size={11} /> {s}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">Missing Skills</p>
          <div className="flex flex-wrap gap-1.5">
            {missing.length === 0 && <span className="text-xs text-[var(--text-muted)]">None — great coverage!</span>}
            {missing.map((s) => (
              <span key={s} className="flex items-center gap-1 text-xs bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300 px-2.5 py-1 rounded-full">
                <X size={11} /> {s}
              </span>
            ))}
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
