"use client";

import SpotlightCard from "@/components/SpotlightCard";

export default function ResumeSummary({ summary }: { summary: string }) {
  return (
    <SpotlightCard className="p-6">
      <h3 className="font-medium mb-3">Resume Summary</h3>
      <p className="text-sm text-[var(--text-muted)] leading-relaxed">{summary || "Not detected"}</p>
    </SpotlightCard>
  );
}
