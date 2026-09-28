"use client";

import { useState } from "react";
import { toast } from "sonner";
import { UploadCloud, X, FileText } from "lucide-react";

import JobDescriptionInput from "@/components/JobDescriptionInput";
import CandidateTable from "@/components/CandidateTable";
import LoadingAnalysis from "@/components/LoadingAnalysis";
import EmptyState from "@/components/EmptyState";
import { bulkAnalyze, getErrorMessage, type BulkCandidateResult } from "@/lib/api";

export default function CandidatesPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BulkCandidateResult[] | null>(null);

  function addFiles(newFiles: FileList | null) {
    if (!newFiles) return;
    const valid = Array.from(newFiles).filter((f) => /\.(pdf|docx)$/i.test(f.name));
    setFiles((prev) => [...prev, ...valid]);
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleRank() {
    if (files.length === 0 || jobDescription.trim().length < 20) return;
    setLoading(true);
    setResults(null);
    try {
      const data = await bulkAnalyze(files, jobDescription);
      setResults(data);
      toast.success(`Ranked ${data.length} candidate(s)`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const canRank = files.length > 0 && jobDescription.trim().length >= 20;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Candidates</h1>
        <p className="text-sm text-[var(--text-muted)]">
          Upload multiple resumes and rank them against one job description. Results are for recruiter review, not automated decisions.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <p className="text-sm font-medium mb-2">Resumes</p>
          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-[var(--border)] hover:border-brand-400 rounded-xl py-8 px-4 cursor-pointer transition-colors">
            <UploadCloud size={24} className="text-brand-500" />
            <p className="text-sm font-medium">Add resumes (PDF/DOCX)</p>
            <input type="file" multiple accept=".pdf,.docx" className="hidden" onChange={(e) => addFiles(e.target.files)} />
          </label>

          {files.length > 0 && (
            <div className="mt-3 space-y-2">
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between border border-[var(--border)] rounded-lg px-3 py-2 bg-[var(--surface)]">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText size={14} className="text-brand-500 shrink-0" />
                    <span className="text-sm truncate">{f.name}</span>
                  </div>
                  <button onClick={() => removeFile(i)} className="text-[var(--text-muted)] hover:text-red-500">
                    <X size={15} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="text-sm font-medium mb-2">Job Description</p>
          <JobDescriptionInput value={jobDescription} onChange={setJobDescription} />
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleRank}
          disabled={!canRank || loading}
          className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium px-8 py-3 rounded-lg transition-colors"
        >
          {loading ? "Ranking…" : `Rank ${files.length || ""} Candidate${files.length === 1 ? "" : "s"}`}
        </button>
      </div>

      {loading && <LoadingAnalysis />}

      {!loading && !results && (
        <EmptyState title="No ranking yet" description="Upload resumes and a job description, then click Rank Candidates." />
      )}

      {!loading && results && results.length > 0 && <CandidateTable results={results} />}
    </div>
  );
}
