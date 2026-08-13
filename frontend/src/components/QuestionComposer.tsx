import { Play, Search, X } from "lucide-react";
import type { FormEvent } from "react";

interface QuestionComposerProps {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
}

export function QuestionComposer({
  question,
  onQuestionChange,
  onSubmit,
  busy,
}: QuestionComposerProps) {
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!busy && question.trim().length >= 3) onSubmit();
  }

  return (
    <form className="question-composer" onSubmit={submit}>
      <div className="question-field">
        <Search aria-hidden="true" size={20} strokeWidth={1.75} />
        <label className="visually-hidden" htmlFor="bankops-question">
          Question for Bank Operations Copilot
        </label>
        <textarea
          id="bankops-question"
          maxLength={2000}
          rows={2}
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          disabled={busy}
        />
        {question.length > 0 && !busy ? (
          <button
            className="icon-button clear-question"
            type="button"
            aria-label="Clear question"
            onClick={() => onQuestionChange("")}
          >
            <X aria-hidden="true" size={18} />
          </button>
        ) : null}
        <span className="character-count">{question.length}/2000</span>
      </div>
      <button className="primary-action" type="submit" disabled={busy || question.trim().length < 3}>
        <Play aria-hidden="true" size={17} fill="currentColor" />
        {busy ? "Running…" : "Run analysis"}
      </button>
    </form>
  );
}
