import { Menu } from "lucide-react";
import { useEffect, useState } from "react";

import { apiClient } from "./api/client";
import type { RuntimeConfig } from "./api/types";
import { DomainSwitcher, type WorkspaceName } from "./components/DomainSwitcher";
import { BankOpsWorkspace } from "./features/bankops/BankOpsWorkspace";
import { AwardLensWorkspace } from "./features/awardlens/AwardLensWorkspace";
import { EvaluationView } from "./features/evaluation/EvaluationView";

function Wordmark() {
  return (
    <div className="wordmark" aria-label="OpsGraph">
      <svg className="wordmark-mark" viewBox="0 0 32 32" aria-hidden="true">
        <path d="M16 3 27 9v14l-11 6-11-6V9l11-6Z" />
        <path d="m5 9 11 7 11-7M16 16v13" />
        <circle cx="16" cy="3" r="2.2" /><circle cx="27" cy="9" r="2.2" />
        <circle cx="27" cy="23" r="2.2" /><circle cx="16" cy="29" r="2.2" />
        <circle cx="5" cy="23" r="2.2" /><circle cx="5" cy="9" r="2.2" />
      </svg>
      <span>OpsGraph</span>
    </div>
  );
}

function App() {
  const [active, setActive] = useState<WorkspaceName>("bankops");
  const [mobileMenu, setMobileMenu] = useState(false);
  const [config, setConfig] = useState<RuntimeConfig | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    apiClient.config(controller.signal).then(setConfig).catch(() => undefined);
    return () => controller.abort();
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <Wordmark />
        <button
          type="button"
          className="mobile-menu-button"
          aria-label="Toggle workspace navigation"
          aria-expanded={mobileMenu}
          onClick={() => setMobileMenu((value) => !value)}
        >
          <Menu aria-hidden="true" size={25} />
        </button>
      </header>
      <div className={`navigation-shell ${mobileMenu ? "navigation-shell-open" : ""}`}>
        <DomainSwitcher
          active={active}
          onChange={(workspace) => {
            setActive(workspace);
            setMobileMenu(false);
          }}
        />
      </div>
      <div className="workspace-shell">
        <div hidden={active !== "bankops"}><BankOpsWorkspace config={config} /></div>
        <div hidden={active !== "awardlens"}><AwardLensWorkspace config={config} /></div>
        <div hidden={active !== "evaluations"}><EvaluationView /></div>
      </div>
      <footer className="mobile-prototype-notice">Synthetic data · Educational prototype</footer>
    </div>
  );
}

export default App;
