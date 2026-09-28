"use client";

import { useCallback, useState } from "react";
import { UploadCloud, FileText, X } from "lucide-react";

interface ResumeUploaderProps {
  file: File | null;
  onFileSelected: (file: File | null) => void;
}

const ALLOWED_TYPES = [".pdf", ".docx"];
const MAX_SIZE_MB = 10;

export default function ResumeUploader({ file, onFileSelected }: ResumeUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateAndSet = useCallback(
    (f: File) => {
      const ext = "." + f.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_TYPES.includes(ext)) {
        setError(`Unsupported file type. Allowed: ${ALLOWED_TYPES.join(", ")}`);
        return;
      }
      if (f.size > MAX_SIZE_MB * 1024 * 1024) {
        setError(`File exceeds ${MAX_SIZE_MB}MB limit.`);
        return;
      }
      setError(null);
      onFileSelected(f);
    },
    [onFileSelected]
  );

  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) validateAndSet(dropped);
  }

  if (file) {
    return (
      <div className="border border-[var(--border)] rounded-xl p-4 flex items-center justify-between bg-[var(--surface)]">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-10 w-10 rounded-lg bg-brand-50 dark:bg-brand-900/30 grid place-items-center shrink-0">
            <FileText size={18} className="text-brand-600 dark:text-brand-300" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-[var(--text-muted)]">{(file.size / 1024).toFixed(0)} KB · Ready</p>
          </div>
        </div>
        <button
          onClick={() => onFileSelected(null)}
          className="text-[var(--text-muted)] hover:text-red-500 shrink-0"
          aria-label="Remove file"
        >
          <X size={18} />
        </button>
      </div>
    );
  }

  return (
    <div>
      <label
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl py-10 px-4 cursor-pointer transition-colors ${
          dragActive ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20" : "border-[var(--border)] hover:border-brand-400"
        }`}
      >
        <UploadCloud size={28} className="text-brand-500" />
        <p className="text-sm font-medium">Drag &amp; drop a resume, or click to browse</p>
        <p className="text-xs text-[var(--text-muted)]">PDF or DOCX, up to {MAX_SIZE_MB}MB</p>
        <input
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) validateAndSet(f);
          }}
        />
      </label>
      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
    </div>
  );
}
