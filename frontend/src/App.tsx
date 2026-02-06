import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { FileUpload } from "./components/FileUpload";
import { MatchAnalysis } from "./components/MatchAnalysis";
import { ChatInterface } from "./components/ChatInterface";
import type { MatchAnalysis as MatchAnalysisType } from "./api";

function App() {
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [jdUploaded, setJdUploaded] = useState(false);
  const [analysis, setAnalysis] = useState<MatchAnalysisType | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [resumeInfo, setResumeInfo] = useState<{ filename?: string; text_length?: number; message?: string } | null>(null);
  const [jdInfo, setJdInfo] = useState<{ filename?: string; text_length?: number; message?: string } | null>(null);

  const handleResumeUpload = (info: { filename?: string; text_length?: number; message?: string }) => {
    setResumeUploaded(true);
    setAnalysis(null);
    setAnalysisError(null);
    setResumeInfo(info);
  };

  const handleJDUpload = (info: { filename?: string; text_length?: number; message?: string }) => {
    setJdUploaded(true);
    setAnalysis(null);
    setAnalysisError(null);
    setJdInfo(info);
  };

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const res = await fetch("/health");
        if (!cancelled) setBackendOk(res.ok);
      } catch {
        if (!cancelled) setBackendOk(false);
      }
    };
    check();
    const id = window.setInterval(check, 8000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  const loadAnalysis = async () => {
    setLoading(true);
    setAnalysisError(null);
    try {
      const res = await fetch("/api/analysis");
      const data = await res.json();
      if (data.success && data.analysis) {
        setAnalysis(data.analysis);
      } else {
        setAnalysisError(data.error || "Failed to load analysis");
      }
    } catch {
      setAnalysisError("Failed to fetch analysis");
    } finally {
      setLoading(false);
    }
  };

  const canAnalyze = resumeUploaded && jdUploaded;

  const quickStats = useMemo(() => {
    if (!analysis) return null;
    return {
      overlap: analysis.skill_overlap?.length ?? 0,
      missing: analysis.missing_skills?.length ?? 0,
      strengths: analysis.strengths?.length ?? 0,
      gaps: analysis.gaps?.length ?? 0,
    };
  }, [analysis]);

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <h1>Resume Intelligence Studio</h1>
          <p>Upload → analyze → ask questions. RAG keeps answers grounded in the resume.</p>
          <div className="brand-badge">
            <span className={`dot ${backendOk === null ? "" : backendOk ? "ok" : "bad"}`} />
            <span className="status-strong">
              {backendOk === null ? "Checking backend..." : backendOk ? "Backend connected" : "Backend not reachable"}
            </span>
            <span className="tiny">(dev proxy uses `VITE_API_TARGET`)</span>
          </div>
        </div>

        <div className="status-card">
          <div>
            <div className="status-strong">Session checklist</div>
            <div className="tiny">Make sure backend is running, then upload both files.</div>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="left-col">
          <section className="section upload-section">
            <h2>1) Upload documents</h2>
            <div className="upload-grid">
              <FileUpload label="Resume" accept=".pdf,.txt" endpoint="/api/upload/resume" onSuccess={handleResumeUpload} />
              <FileUpload label="Job description" accept=".pdf,.txt" endpoint="/api/upload/jd" onSuccess={handleJDUpload} />
            </div>

            <div className="stepper">
              <div className="step">
                <div className="step-left">
                  <div className="step-title">Resume indexed for RAG</div>
                  <div className="step-sub">
                    {resumeInfo?.filename ? `${resumeInfo.filename}${resumeInfo.text_length ? ` • ${resumeInfo.text_length} chars` : ""}` : "Upload a resume (PDF/TXT)."}
                  </div>
                </div>
                <span className={`step-state ${resumeUploaded ? "done" : "todo"}`}>{resumeUploaded ? "DONE" : "TODO"}</span>
              </div>
              <div className="step">
                <div className="step-left">
                  <div className="step-title">Job description ready</div>
                  <div className="step-sub">
                    {jdInfo?.filename ? `${jdInfo.filename}${jdInfo.text_length ? ` • ${jdInfo.text_length} chars` : ""}` : "Upload a JD (PDF/TXT)."}
                  </div>
                </div>
                <span className={`step-state ${jdUploaded ? "done" : "todo"}`}>{jdUploaded ? "DONE" : "TODO"}</span>
              </div>
              <div className="step">
                <div className="step-left">
                  <div className="step-title">Match analysis</div>
                  <div className="step-sub">{canAnalyze ? "Ready to run scoring + insights." : "Requires both uploads."}</div>
                </div>
                <span className={`step-state ${analysis ? "done" : canAnalyze ? "todo" : "todo"}`}>{analysis ? "DONE" : "READY"}</span>
              </div>
            </div>
          </section>

          <section className="section analysis-section">
            <h2>2) Generate match analysis</h2>
            {!canAnalyze ? (
              <p className="hint">Upload both resume and job description to view match analysis.</p>
            ) : (
              <>
                <div className="analysis-actions">
                  <button className="btn btn-primary" onClick={loadAnalysis} disabled={loading}>
                    {loading ? "Crunching signals..." : "Run analysis"}
                  </button>
                  <div className="tiny">
                    {quickStats ? (
                      <>
                        Strengths: <span className="status-strong">{quickStats.strengths}</span> • Gaps:{" "}
                        <span className="status-strong">{quickStats.gaps}</span> • Overlap:{" "}
                        <span className="status-strong">{quickStats.overlap}</span> • Missing:{" "}
                        <span className="status-strong">{quickStats.missing}</span>
                      </>
                    ) : (
                      "Tip: run analysis before asking deep questions."
                    )}
                  </div>
                </div>
                {analysisError && <p className="error">{analysisError}</p>}
                {analysis && <MatchAnalysis data={analysis} />}
              </>
            )}
          </section>
        </div>

        <div className="right-col">
          <section className="section chat-section">
            <h2>3) Ask grounded questions</h2>
            {!resumeUploaded ? (
              <p className="hint">Upload a resume first to use RAG-powered chat.</p>
            ) : (
              <ChatInterface />
            )}
            <p className="tiny" style={{ margin: "0.75rem 0 0" }}>
              Privacy note: chat answers should reference only retrieved resume sections. If the resume doesn’t mention something, the best answer is “not enough info”.
            </p>
          </section>

          <section className="section">
            <h2>How it works</h2>
            <p className="hint">
              We chunk the resume, embed it, retrieve only the most relevant sections for each question, then generate the answer from that context.
              This reduces hallucinations and keeps responses resume-grounded.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
