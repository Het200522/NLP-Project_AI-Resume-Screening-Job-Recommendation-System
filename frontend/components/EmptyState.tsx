"use client";

import { FileSearch } from "lucide-react";

export default function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
      <FileSearch size={32} className="text-[var(--text-muted)] mb-2" />
      <p className="font-medium">{title}</p>
      <p className="text-sm text-[var(--text-muted)] max-w-sm">{description}</p>
    </div>
  );
}
