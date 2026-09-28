"use client";

import SpotlightCard from "@/components/SpotlightCard";

function SectionBlock({ title, text }: { title: string; text: string }) {
  const detected = text && text !== "Not detected";
  return (
    <div>
      <p className="text-xs font-medium text-[var(--text-muted)] mb-1.5">{title}</p>
      {detected ? (
        <p className="text-sm whitespace-pre-line leading-relaxed">{text}</p>
      ) : (
        <p className="text-sm text-[var(--text-muted)] italic">Not detected</p>
      )}
    </div>
  );
}

export default function ResumeSections({
  experience,
  projects,
  education,
}: {
  experience: string;
  projects: string;
  education: string;
}) {
  return (
    <SpotlightCard className="p-6 space-y-5">
      <h3 className="font-medium">Experience &amp; Projects</h3>
      <SectionBlock title="Experience" text={experience} />
      <SectionBlock title="Projects" text={projects} />
      <SectionBlock title="Education" text={education} />
    </SpotlightCard>
  );
}
