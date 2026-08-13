import { FileUp } from "lucide-react";
import { useState } from "react";

import { apiClient } from "../api/client";

export function IngestionPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [token, setToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function upload() {
    if (!file || !token) return;
    try {
      const result = await apiClient.ingestBankOps(file, token);
      setMessage(`${result.chunk_count} chunk${result.chunk_count === 1 ? "" : "s"} indexed.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  return (
    <details className="ingestion-panel">
      <summary><FileUp aria-hidden="true" size={16} /> Local document ingestion</summary>
      <div>
        <input aria-label="Choose policy document" type="file" accept=".md,.txt,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <input aria-label="Local administration token" type="password" placeholder="Local token" value={token} onChange={(event) => setToken(event.target.value)} />
        <button type="button" disabled={!file || !token} onClick={upload}>Index document</button>
      </div>
      {message ? <p role="status">{message}</p> : null}
    </details>
  );
}
