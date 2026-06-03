/* Refined shared components. Exported to window. */
const { useState, useEffect, useRef } = React;

/* Light Northgate identity — a minimal "gate / threshold" logomark + wordmark.
   One accent, supportive neutrals; no heavy brand. */
function Mark() {
  return (
    <svg className="mark" viewBox="0 0 28 28" aria-hidden="true">
      <rect x="1.5" y="1.5" width="25" height="25" rx="6" fill="var(--accent-soft)" stroke="var(--accent)" strokeWidth="1.4"/>
      <path d="M9 20V11.5a5 5 0 0 1 10 0V20" fill="none" stroke="var(--accent)" strokeWidth="2.1" strokeLinecap="round"/>
      <path d="M14 20v-6" stroke="var(--accent)" strokeWidth="2.1" strokeLinecap="round"/>
    </svg>
  );
}

function Banner() {
  return (
    <div className="synthetic-banner" role="note">
      🧪 SYNTHETIC DEMO DATA — every persona and record is fictional. No real people, no real client data.
    </div>
  );
}

function TopBar({ route, go }) {
  const items = [
    ["caseload", "Caseload"], ["context", "Context"], ["drafting", "Drafting"],
    ["safeguarding", "Safeguarding"], ["log", "Decision log"],
  ];
  return (
    <header className="topbar">
      <div className="container topbar-inner">
        <span className="brand" onClick={() => go("caseload")}>
          <Mark />
          <span className="name">Northgate Futures</span>
          <span className="sub">Keyworker Workbench</span>
        </span>
        <nav className="nav-links" aria-label="Primary">
          {items.map(([k, label]) => (
            <a key={k} className={route.startsWith(k) ? "active" : ""} onClick={() => go(k)}>{label}</a>
          ))}
        </nav>
      </div>
    </header>
  );
}

/* Person-arc stepper — carries ONE young person through the arc with visible progress. */
function ArcStepper({ persona, route, go }) {
  if (!persona) return null;
  const steps = [
    ["context", "Context"], ["drafting", "Drafting"],
    ["safeguarding", "Safeguarding"], ["log", "Decision log"],
  ];
  return (
    <div className="arc" role="navigation" aria-label="This young person, through the flow">
      <span className="arc-who">{persona.name}, {persona.age} <span className="tag tag-synthetic">synthetic</span></span>
      <div className="arc-steps">
        {steps.map(([k, label], i) => (
          <React.Fragment key={k}>
            {i > 0 && <span className="chev" aria-hidden="true">›</span>}
            <a className={"arc-step" + (route.startsWith(k) ? " active" : "")} onClick={() => go(k, persona.id)} aria-current={route.startsWith(k) ? "step" : undefined}>
              <span className="n">{i + 1}</span><span className="lbl">{label}</span>
            </a>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function Footer() {
  return (
    <footer className="app-footer">
      <div className="container">
        The AI <strong style={{ color: "var(--ink)" }}>proposes</strong>; the worker <strong style={{ color: "var(--ink)" }}>disposes</strong>.
        Open-weight inference (<code>gpt-oss-120b</code>), self-hostable. Worker of record: {window.NF_DATA.worker}.
      </div>
    </footer>
  );
}

function Badge({ kind, children }) { return <span className={"badge badge-" + kind}>{children}</span>; }

function Statement({ text, sourceLabel, onJump }) {
  return (
    <li className="ctx-statement">
      <span className="txt">{text}</span>
      <span className="says-row">
        <span className="says-who">Says who?</span>
        <a className="source-link" onClick={onJump}>{sourceLabel}</a>
      </span>
    </li>
  );
}

/* THE hero — polished propose→dispose frame. Header strip reads DRAFT unmistakably;
   actions are weighted (primary commit, quiet discard); reassurance is explicit. */
function ProposalFrame({ typeLabel, initialText, actions, onDispose, foot }) {
  const [text, setText] = useState(initialText);
  return (
    <article className="proposal" data-uncommitted="true" aria-label="AI proposal — uncommitted draft">
      <div className="proposal-head">
        <span className="proposal-pill">⬩ Draft</span>
        <span className="meta">{typeLabel} · not committed, nothing sent</span>
      </div>
      <div className="proposal-body">
        <p className="proposal-meta">Drafted by open-weight model (<code>{window.NF_DATA.model}</code>) · <strong style={{ color: "var(--ink)" }}>you are the author of record</strong>.</p>
        <label>Your version <span className="hint">— edit freely; your words are what gets committed</span>
          <textarea rows={7} value={text} onChange={(e) => setText(e.target.value)} />
        </label>
        <div className="proposal-actions">
          {actions.map((a) => (
            <button key={a.value} className={a.class || "btn-ink"} onClick={() => onDispose(a.value, text)}>{a.label}</button>
          ))}
        </div>
        <p className="proposal-foot mb0"><span className="lock" aria-hidden="true">⬩</span> {foot || "The AI drafts; you decide. Nothing is saved and nothing is sent until you choose an action above."}</p>
      </div>
    </article>
  );
}

function Receipt({ tone, children }) {
  const ok = tone === "commit";
  return (
    <div className="callout" style={ok ? { background: "var(--commit-bg)", color: "var(--commit-text)", borderColor: "var(--commit-border)", borderLeftColor: "var(--commit-line)" } : {}}>
      <span className="ic" aria-hidden="true">{ok ? "✓" : "•"}</span>
      <div>{children}</div>
    </div>
  );
}

Object.assign(window, { Mark, Banner, TopBar, ArcStepper, Footer, Badge, Statement, ProposalFrame, Receipt });
