import { Check, Clipboard, LockKeyhole } from "lucide-react";
import { useState } from "react";

import type { SqlResult } from "../api/types";

export function SqlPanel({ sql }: { sql: SqlResult | null }) {
  const [copied, setCopied] = useState(false);
  if (!sql) return <p className="empty-panel">No SQL was required for this route.</p>;

  async function copySql() {
    await navigator.clipboard?.writeText(sql?.normalized_sql ?? "");
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1_200);
  }

  return (
    <section className="sql-panel" aria-label="Generated SQL">
      <pre><code>{sql.normalized_sql}</code></pre>
      <footer>
        <span><LockKeyhole aria-hidden="true" size={15} /> Read-only · {sql.row_count} rows · {sql.elapsed_ms.toFixed(1)}ms</span>
        <button type="button" onClick={copySql}>
          {copied ? <Check aria-hidden="true" size={15} /> : <Clipboard aria-hidden="true" size={15} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </footer>
    </section>
  );
}
