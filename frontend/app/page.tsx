import Link from "next/link";
import SpotlightCard from "@/components/SpotlightCard";
import { ArrowRight, ScanSearch, Sparkles, BarChart3, ListChecks } from "lucide-react";

const FEATURES = [
  { icon: ScanSearch, title: "Resume Parsing", desc: "Extracts text, contact info, education, experience, and projects from PDF/DOCX resumes." },
  { icon: BarChart3, title: "Semantic Matching", desc: "Combines TF-IDF and sentence embeddings to score how well a resume fits a job description." },
  { icon: ListChecks, title: "Skill Gap Analysis", desc: "Identifies matched, missing, and additional skills, with tailored learning recommendations." },
  { icon: Sparkles, title: "ATS Readiness", desc: "A transparent, weighted compatibility score based on real-world resume-parsing best practices." },
];

const PIPELINE = [
  "Text Extraction", "Preprocessing", "NER", "Skill Extraction",
  "TF-IDF", "Sentence Embeddings", "Cosine Similarity", "Recommendations",
];

const STACK = ["Next.js", "React", "TypeScript", "FastAPI", "spaCy", "scikit-learn", "sentence-transformers", "SQLite"];

export default function LandingPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-16 animate-fade-in">
      <section className="text-center pt-10 space-y-5">
        <span className="inline-block text-xs font-medium text-brand-700 bg-brand-50 dark:bg-brand-900/30 dark:text-brand-300 px-3 py-1 rounded-full">
          NLP-Powered Resume Intelligence
        </span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          AI Resume Screening &amp; Job Recommendation System
        </h1>
        <p className="text-[var(--text-muted)] max-w-2xl mx-auto text-lg">
          Upload a resume, paste a job description, and get an explainable match score,
          skill gap analysis, and personalized recommendations — built on a transparent NLP pipeline.
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <Link
            href="/analyze"
            className="inline-flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white font-medium px-5 py-2.5 rounded-lg transition-colors"
          >
            Analyze a Resume <ArrowRight size={16} />
          </Link>
          <Link
            href="/candidates"
            className="inline-flex items-center gap-2 border border-[var(--border)] px-5 py-2.5 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Rank Multiple Candidates
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-5">Key Features</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <SpotlightCard key={title} className="p-5">
              <div className="h-9 w-9 rounded-lg bg-brand-50 dark:bg-brand-900/30 grid place-items-center mb-3">
                <Icon size={18} className="text-brand-600 dark:text-brand-300" />
              </div>
              <h3 className="font-medium mb-1">{title}</h3>
              <p className="text-sm text-[var(--text-muted)]">{desc}</p>
            </SpotlightCard>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-5">NLP Pipeline</h2>
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <span className="text-sm px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)]">
                {step}
              </span>
              {i < PIPELINE.length - 1 && <ArrowRight size={14} className="text-[var(--text-muted)]" />}
            </div>
          ))}
        </div>
      </section>

      <section className="pb-10">
        <h2 className="text-xl font-semibold mb-5">Technology Stack</h2>
        <div className="flex flex-wrap gap-2">
          {STACK.map((t) => (
            <span key={t} className="text-sm px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-[var(--text-muted)]">
              {t}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
