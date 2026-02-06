import { useMemo, useState } from "react";
import "./FileUpload.css";

interface FileUploadProps {
  label: string;
  accept: string;
  endpoint: string;
  onSuccess: (info: { filename?: string; text_length?: number; message?: string }) => void;
}

export function FileUpload({ label, accept, endpoint, onSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const helpText = useMemo(() => {
    const types = accept
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean)
      .join(" • ");
    return types ? `Accepted: ${types}` : "Accepted: PDF or TXT";
  }, [accept]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setFile(f ?? null);
    setStatus("idle");
    setMessage("");
  };

  const setPickedFile = (f: File | null) => {
    setFile(f);
    setStatus("idle");
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(endpoint, {
        method: "POST",
        body: form,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const err = typeof data.detail === "string" ? data.detail : Array.isArray(data.detail) ? data.detail[0]?.msg : "Upload failed";
        throw new Error(err || "Upload failed");
      }
      setStatus("success");
      setMessage(data.message || "Uploaded");
      onSuccess({ filename: data.filename, text_length: data.text_length, message: data.message });
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Upload failed");
    }
  };

  return (
    <div className="file-upload">
      <div className="file-upload-head">
        <div>
          <div className="file-upload-label">{label}</div>
          <div className="file-upload-help">{helpText}</div>
        </div>
        <span className={`pill pill-${status}`}>{status === "idle" ? "Ready" : status}</span>
      </div>

      <label
        className={`dropzone ${isDragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
        onDragEnter={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(false);
          const f = e.dataTransfer.files?.[0];
          setPickedFile(f ?? null);
        }}
      >
        <input type="file" accept={accept} onChange={handleChange} className="file-input-hidden" />
        <div className="dropzone-inner">
          <div className="dropzone-title">{file ? "File selected" : "Drop a file here"}</div>
          <div className="dropzone-subtitle">{file ? file.name : "or click to browse"}</div>
        </div>
      </label>

      <div className="file-upload-actions">
        <button className="btn btn-ghost" onClick={() => setPickedFile(null)} disabled={!file || status === "uploading"}>
          Clear
        </button>
        <button className="btn btn-primary" onClick={handleUpload} disabled={!file || status === "uploading"}>
          {status === "uploading" ? "Uploading..." : "Upload"}
        </button>
      </div>

      {message && <span className={`upload-msg ${status}`}>{message}</span>}
    </div>
  );
}
