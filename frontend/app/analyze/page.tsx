"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download } from "lucide-react";

import ResumeUploader from "@/components/ResumeUploader";
import JobDescriptionInput from "@/components/JobDescriptionInput";
import LoadingAnalysis from "@/components/LoadingAnalysis";
import AnalysisScore from "@/components/AnalysisScore";
import SkillMatchChart from "@/components/SkillMatchChart";
import CandidateProfile from "@/components/CandidateProfile";
import ResumeSummary from "@/components/ResumeSummary";
import RecommendationCard from "@/components/RecommendationCard";
import ATSCompatibility from "@/components/ATSCompatibility";
import ResumeQuality from "@/components/ResumeQuality";
import ResumeSections from "@/components/ResumeSections";
import EmptyState from "@/components/EmptyState";
import { analyzeResume, getErrorMessage, reportDownloadUrl, type AnalyzeResponse } from "@/lib/api";

export default function AnalyzePage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const canAnalyze = resumeFile !== null && jobDescription.trim().length > 20;

  async function handleAnalyze() {
    if (!resumeFile) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeResume(resumeFile, jobDescription);
      setResult(data);
      toast.success("Analysis complete");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Analyze Resume</h1>
        <p className="text-sm text-[var(--text-muted)]">Upload a resume and provide a job description to generate a match report.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <p className="text-sm font-medium mb-2">Resume</p>
          <ResumeUploader file={resumeFile} onFileSelected={setResumeFile} />
        </div>
        <div>
          <p className="text-sm font-medium mb-2">Job Description</p>
          <JobDescriptionInput value={jobDescription} onChange={setJobDescription} />
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze || loading}
          className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium px-8 py-3 rounded-lg transition-colors"
        >
          {loading ? "Analyzing…" : "Analyze Resume"}
        </button>
      </div>

      {loading && <LoadingAnalysis />}

      {!loading && !result && (
        <EmptyState
          title="No analysis yet"
          description="Upload a resume and paste a job description, then click Analyze Resume to see the match report."
        />
      )}

      {!loading && result && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            <AnalysisScore
              finalScore={result.scores.final_score}
              semanticScore={result.scores.semantic_score}
              skillScore={result.scores.skill_score}
              keywordScore={result.scores.keyword_score}
              categories={result.scores.categories}
              weights={result.scores.weights}
              experience={result.experience}
            />
            <ATSCompatibility
              compatibility={result.compatibility}
              knockouts={result.knockouts}
            />
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <SkillMatchChart
                matched={result.matched_skills}
                missing={result.missing_skills}
                totalJdSkills={result.total_jd_skills}
              />
              <RecommendationCard recommendations={result.recommendations} />
            </div>
            <div className="space-y-6">
              <CandidateProfile candidate={result.candidate} />
              <ResumeSummary summary={result.summary} />
              <ResumeSections
                experience={result.sections.experience}
                projects={result.sections.projects}
                education={result.sections.education}
              />
            </div>
          </div>

          <ResumeQuality quality={result.quality} />

          {result.id && (
            <div className="flex justify-center pb-4">
              <a
                href={reportDownloadUrl(result.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 border border-[var(--border)] px-5 py-2.5 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <Download size={16} /> Download PDF Report
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
