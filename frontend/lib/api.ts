import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { API_URL };

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
});

export interface ExperienceInfo {
  years: number;
  source: string;
  detail: string;
  required: string | null;
  required_min_years: number | null;
  required_max_years: number | null;
  match_score: number | null;
}

export interface AnalyzeResponse {
  id: number | null;
  candidate: {
    name: string | null;
    email: string | null;
    phone: string | null;
    location: string | null;
    linkedin: string | null;
    github: string | null;
    organizations: string[];
  };
  job_title: string | null;
  scores: {
    semantic_score: number;
    tfidf_score: number;
    skill_score: number;
    keyword_score: number;
    final_score: number;
    used_semantic_model: boolean;
    categories: Record<string, number | null>;
    weights: Record<string, number>;
    raw_semantic_score: number | null;
    experience_score: number | null;
    parseability_score: number | null;
    keyword_detail: {
      keywords?: string[];
      matched?: string[];
      missing?: string[];
      fuzzy_matches?: string[];
    };
    parseability_detail: {
      contact_info?: number;
      section_structure?: number;
      formatting?: number;
      length?: number;
    };
  };
  matched_skills: string[];
  missing_skills: string[];
  additional_skills: string[];
  total_jd_skills: number;
  required_skills: string[];
  preferred_skills: string[];
  matched_required: string[];
  missing_required: string[];
  matched_preferred: string[];
  missing_preferred: string[];
  experience: ExperienceInfo;
  summary: string;
  sections: {
    experience: string;
    projects: string;
    education: string;
    certifications: string;
  };
  recommendations: {
    skill: string;
    level: string;
    topics: string[];
    project_idea: string;
    resource_hint: string;
  }[];
  quality: {
    checks: { label: string; passed: boolean; detail: string }[];
    passed: number;
    total: number;
    score_percent: number;
  };
  compatibility: {
    indicators: { label: string; ok: boolean; note: string }[];
  };
  /**
   * Hard minimums the job description states, reported separately from the
   * score. `passed` is false only when the posting states a requirement the
   * resume does not meet, so a candidate is told exactly what is missing
   * instead of having the number quietly lowered.
   */
  knockouts: {
    gates: {
      label: string;
      requirement: string;
      requirement_met: boolean;
      detail: string;
    }[];
    failed: string[];
    passed: boolean;
    evaluated: boolean;
  };
  status: string;
  created_at: string | null;
}

export interface CandidateListItem {
  id: number;
  candidate_name: string | null;
  email: string | null;
  resume_filename: string;
  job_title: string | null;
  final_score: number;
  status: string | null;
  created_at: string;
}

export interface BulkCandidateResult {
  filename: string;
  candidate_name: string | null;
  final_score: number;
  skills_matched: number;
  missing_skills: number;
  status: string;
  error: string | null;
}

export async function analyzeResume(resume: File, jobDescription: string): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("resume", resume);
  formData.append("job_description", jobDescription);
  const { data } = await api.post<AnalyzeResponse>("/api/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function bulkAnalyze(resumes: File[], jobDescription: string): Promise<BulkCandidateResult[]> {
  const formData = new FormData();
  resumes.forEach((r) => formData.append("resumes", r));
  formData.append("job_description", jobDescription);
  const { data } = await api.post<BulkCandidateResult[]>("/api/candidates/bulk-analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listCandidates(): Promise<CandidateListItem[]> {
  const { data } = await api.get<CandidateListItem[]>("/api/candidates");
  return data;
}

export function reportDownloadUrl(analysisId: number): string {
  return `${API_URL}/api/analysis/${analysisId}/report`;
}

export async function healthCheck(): Promise<boolean> {
  try {
    await api.get("/api/health");
    return true;
  } catch {
    return false;
  }
}

export interface RoleTemplate {
  id: string;
  title: string;
  category: string;
}

export async function listRoles(): Promise<RoleTemplate[]> {
  const { data } = await api.get<RoleTemplate[]>("/api/job-description/roles");
  return data;
}

export async function getRoleDescription(roleId: string): Promise<{ id: string; title: string; description: string }> {
  const { data } = await api.get<{ id: string; title: string; description: string }>(
    `/api/job-description/roles/${roleId}`
  );
  return data;
}

export interface ScoringConfig {
  weights: Record<string, number>;
  parseability_weights: Record<string, number>;
  semantic_floor: number;
  semantic_ceiling: number;
  formula: string;
  knockouts_note: string;
}

export async function getScoringConfig(): Promise<ScoringConfig> {
  const { data } = await api.get<ScoringConfig>("/api/scoring/config");
  return data;
}

/** Extracts a user-friendly error message from an Axios error, never a raw stack trace. */
export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (err.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!err.response) return "Could not reach the backend server. Is it running?";
  }
  return "Something went wrong. Please try again.";
}
