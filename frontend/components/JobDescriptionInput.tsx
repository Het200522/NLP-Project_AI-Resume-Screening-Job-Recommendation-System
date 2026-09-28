"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";
import { api, listRoles, getRoleDescription, getErrorMessage, API_URL, type RoleTemplate } from "@/lib/api";

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
}

type InputMode = "role" | "paste" | "upload";

const ALLOWED_EXTENSIONS = [".txt", ".pdf", ".docx"];
const MAX_SIZE_MB = 10;

export default function JobDescriptionInput({ value, onChange }: JobDescriptionInputProps) {
  const [mode, setMode] = useState<InputMode>("role");
  const [roles, setRoles] = useState<RoleTemplate[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);
  const [rolesError, setRolesError] = useState<string | null>(null);
  const [rolesAttempt, setRolesAttempt] = useState(0);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [roleLoading, setRoleLoading] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const retryRoles = useCallback(() => setRolesAttempt((n) => n + 1), []);

  useEffect(() => {
    let cancelled = false;
    setRolesLoading(true);
    setRolesError(null);
    listRoles()
      .then((data) => {
        if (!cancelled) setRoles(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setRoles([]);
        setRolesError(`${getErrorMessage(err)} (tried ${API_URL}/api/job-description/roles)`);
      })
      .finally(() => {
        if (!cancelled) setRolesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [rolesAttempt]);

  function handleModeSwitch(newMode: InputMode) {
    setMode(newMode);
    setUploadError(null);
    if (newMode === "paste") {
      setUploadedFile(null);
      setSelectedRole(null);
    }
    if (newMode === "role") {
      setUploadedFile(null);
    }
  }

  async function handleRoleSelect(roleId: string) {
    setSelectedRole(roleId);
    setRoleLoading(true);
    try {
      const role = await getRoleDescription(roleId);
      onChange(role.description);
    } catch {
      onChange("");
    } finally {
      setRoleLoading(false);
    }
  }

  async function handleFileUpload(file: File) {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setUploadError(`Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setUploadError(`File exceeds ${MAX_SIZE_MB}MB limit.`);
      return;
    }

    setUploadError(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post<{ filename: string; text: string }>(
        "/api/job-description/upload",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      onChange(data.text);
      setUploadedFile(data.filename);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to upload file. Please try again.";
      setUploadError(message);
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFileUpload(dropped);
  }

  function handleRemoveFile() {
    setUploadedFile(null);
    onChange("");
  }

  return (
    <div className="border border-[var(--border)] rounded-xl bg-[var(--surface)] overflow-hidden">
      {/* Mode tabs */}
      <div className="flex border-b border-[var(--border)]">
        <button
          onClick={() => handleModeSwitch("role")}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
            mode === "role"
              ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300 border-b-2 border-brand-500"
              : "text-[var(--text-muted)] hover:bg-slate-50 dark:hover:bg-slate-800/50"
          }`}
        >
          Select Role
        </button>
        <button
          onClick={() => handleModeSwitch("paste")}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
            mode === "paste"
              ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300 border-b-2 border-brand-500"
              : "text-[var(--text-muted)] hover:bg-slate-50 dark:hover:bg-slate-800/50"
          }`}
        >
          Paste Text
        </button>
        <button
          onClick={() => handleModeSwitch("upload")}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
            mode === "upload"
              ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300 border-b-2 border-brand-500"
              : "text-[var(--text-muted)] hover:bg-slate-50 dark:hover:bg-slate-800/50"
          }`}
        >
          Upload File
        </button>
      </div>

      {/* Role selection mode */}
      {mode === "role" && (
        <div className="p-4">
          {rolesError ? (
            <div className="rounded-lg border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-3">
              <div className="flex items-start gap-2">
                <AlertCircle size={16} className="text-red-500 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-red-700 dark:text-red-300">
                    Could not load role templates
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1 break-words">
                    {rolesError}
                  </p>
                  <button
                    onClick={retryRoles}
                    className="mt-2 text-xs font-medium text-red-700 dark:text-red-300 underline hover:no-underline"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          ) : rolesLoading ? (
            <p className="text-sm text-[var(--text-muted)] text-center py-4">Loading roles...</p>
          ) : (
            <>
              <select
                value={selectedRole || ""}
                onChange={(e) => {
                  if (e.target.value) handleRoleSelect(e.target.value);
                }}
                disabled={roleLoading}
                className="w-full px-4 py-3 rounded-lg border border-[var(--border)] bg-transparent text-[var(--text)] text-sm focus:outline-none focus:border-brand-400 transition-colors dark:[color-scheme:dark]"
              >
                <option value="" disabled>
                  {roleLoading ? "Loading..." : "Choose a role..."}
                </option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.title} — {role.category}
                  </option>
                ))}
              </select>
              {roles.length === 0 && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  The backend returned an empty role list.
                </p>
              )}
            </>
          )}
          {selectedRole && !roleLoading && !rolesError && (
            <p className="text-xs text-[var(--text-muted)] mt-3">
              Job description loaded. Switch to &quot;Paste Text&quot; to edit it.
            </p>
          )}
        </div>
      )}

      {/* Paste mode */}
      {mode === "paste" && (
        <>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Paste the job description here..."
            className="w-full h-56 p-4 text-sm bg-transparent resize-none focus:outline-none"
          />
          <div className="flex justify-end px-4 py-2 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
            {value.length.toLocaleString()} characters
          </div>
        </>
      )}

      {/* Upload mode */}
      {mode === "upload" && (
        <div className="p-4">
          {uploadedFile ? (
            <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-800/50 rounded-lg px-4 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <FileText size={18} className="text-brand-500 shrink-0" />
                <span className="text-sm font-medium truncate">{uploadedFile}</span>
              </div>
              <button
                onClick={handleRemoveFile}
                className="text-[var(--text-muted)] hover:text-red-500 shrink-0 ml-2"
                aria-label="Remove file"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-lg py-10 px-4 cursor-pointer transition-colors border-[var(--border)] hover:border-brand-400"
            >
              <Upload size={24} className="text-brand-500" />
              <p className="text-sm font-medium">
                {uploading ? "Uploading..." : "Drag & drop a file, or click to browse"}
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                TXT, PDF, or DOCX, up to {MAX_SIZE_MB}MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.pdf,.docx"
                className="hidden"
                disabled={uploading}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileUpload(f);
                }}
              />
            </div>
          )}
          {uploadError && <p className="text-xs text-red-500 mt-2">{uploadError}</p>}
        </div>
      )}
    </div>
  );
}
