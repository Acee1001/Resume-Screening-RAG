/**
 * API client for Resume Screening Tool backend.
 */

const API_BASE = "/api";

export interface UploadResponse {
  success: boolean;
  message: string;
  filename?: string;
  text_length?: number;
}

export interface MatchAnalysis {
  match_score: number;
  strengths: string[];
  gaps: string[];
  key_insights: string[];
  skill_overlap: string[];
  missing_skills: string[];
}

export interface AnalysisResponse {
  success: boolean;
  analysis?: MatchAnalysis;
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  question: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  error?: string;
}

export async function uploadResume(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload/resume`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadJD(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload/jd`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalysis(): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis`);
  return res.json();
}

export async function chat(question: string, history: ChatMessage[]): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
  return res.json();
}
