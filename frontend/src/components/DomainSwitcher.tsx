import { ClipboardCheck, FileCheck2, Landmark } from "lucide-react";

export type WorkspaceName = "bankops" | "awardlens" | "evaluations";

interface DomainSwitcherProps {
  active: WorkspaceName;
  onChange: (workspace: WorkspaceName) => void;
}

const workspaces = [
  { id: "bankops", label: "Bank Operations", Icon: Landmark },
  { id: "awardlens", label: "AwardLens AU", Icon: FileCheck2 },
  { id: "evaluations", label: "Evaluations", Icon: ClipboardCheck },
] as const;

export function DomainSwitcher({ active, onChange }: DomainSwitcherProps) {
  return (
    <nav className="domain-navigation" aria-label="Domain workspaces">
      {workspaces.map(({ id, label, Icon }) => (
        <button
          key={id}
          className={`domain-button ${active === id ? "domain-button-active" : ""}`}
          type="button"
          aria-current={active === id ? "page" : undefined}
          onClick={() => onChange(id)}
        >
          <Icon aria-hidden="true" size={18} strokeWidth={1.75} />
          <span>{label}</span>
        </button>
      ))}
      <div className="prototype-notice">
        <span className="notice-shield" aria-hidden="true">◇</span>
        <span>Synthetic data · Educational prototype</span>
      </div>
    </nav>
  );
}
