"use client";

import SpotlightCard from "@/components/SpotlightCard";
import { Mail, Phone, MapPin, Linkedin, Github } from "lucide-react";
import type { AnalyzeResponse } from "@/lib/api";

export default function CandidateProfile({ candidate }: { candidate: AnalyzeResponse["candidate"] }) {
  const fields = [
    { icon: Mail, value: candidate.email },
    { icon: Phone, value: candidate.phone },
    { icon: MapPin, value: candidate.location },
    { icon: Linkedin, value: candidate.linkedin },
    { icon: Github, value: candidate.github },
  ];

  return (
    <SpotlightCard className="p-6">
      <h3 className="font-medium mb-4">Candidate Profile</h3>
      <p className="text-lg font-semibold mb-3">{candidate.name || "Not detected"}</p>
      <div className="space-y-2">
        {fields.map(({ icon: Icon, value }, i) => (
          <div key={i} className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <Icon size={14} className="shrink-0" />
            <span className="truncate">{value || "Not detected"}</span>
          </div>
        ))}
      </div>
    </SpotlightCard>
  );
}
