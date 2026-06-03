/* Refined surfaces 1–3: Caseload, Context, Drafting. Exported to window. */
const { useState: useS, useRef: useR } = React;
const byId = (id) => window.NF_DATA.personas.find((p) => p.id === id);

const CASE_DRAFTS = {
  "noah-bennett": "Today I met with Noah Bennett (18). He demonstrated a game prototype he has been developing; the quality was impressive and highlighted his self-taught IT and game-design skills. We discussed the Open College evening Level 2 IT course that begins at 4pm, which aligns with his need for later start times. Noah raised concerns about funding the course and the cost of transport. I agreed to look into available funding and will relay what I find. He confirmed he will attend next Tuesday's drop-in. His mood was noticeably uplifted.",
  "amara-okafor": "Met with Amara Okafor (19). She is keen to re-engage but found full-time college 'too much, too fast'. We explored part-time and online routes that let her build up gradually. Anxiety remains the main barrier; she responds well to a clear, low-pressure plan. Agreed I would shortlist two flexible options and check in next week.",
  "default": "Met with the young person today. We discussed next steps toward education or work, and agreed a small, concrete action before the next session. Mood and engagement noted. I will follow up as agreed.",
};
const draftFor = (id) => CASE_DRAFTS[id] || CASE_DRAFTS.default;

/* ============ 1 · CASELOAD ============ */
function Caseload({ go }) {
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>Your workbench</p>
      <h1>Your caseload</h1>
      <p className="lead">Six young people. Open one to build pre-meeting context, draft notes, or review safeguarding signals — all as editable proposals you author and commit.</p>
      <div className="grid cols-3" style={{ marginTop: "1.6rem" }}>
        {window.NF_DATA.personas.map((p) => {
          const risk = p.records.some((r) => r.risk);
          return (
            <article className="card card-hover" key={p.id} onClick={() => go("context", p.id)} style={{ cursor: "pointer", display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: ".5rem" }}>
                <h3 style={{ margin: 0 }}>{p.name}</h3>
                <span className="muted" style={{ fontSize: ".9rem", fontVariantNumeric: "tabular-nums" }}>{p.age}</span>
              </div>
              <span className="tag tag-synthetic" style={{ alignSelf: "flex-start", marginTop: ".5rem" }}>synthetic</span>
              <p style={{ margin: ".9rem 0 0", fontSize: ".93rem" }}>{p.summary}</p>
              <div style={{ marginTop: "auto", paddingTop: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: ".5rem" }}>
                <span className="subtle" style={{ fontSize: ".82rem" }}>{p.records.length} source records</span>
                {risk
                  ? <span className="tag tag-risk tag-dot">safeguarding signal</span>
                  : <span className="source-link" style={{ pointerEvents: "none" }}>Open</span>}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

/* ============ 2 · CONTEXT ============ */
function Context({ persona, go }) {
  const [flash, setFlash] = useS(null);
  const refs = useR({});
  const jump = (id) => {
    setFlash(id);
    const el = refs.current[id];
    if (el) { const top = el.getBoundingClientRect().top + window.scrollY - 120; window.scrollTo({ top, behavior: "smooth" }); }
    setTimeout(() => setFlash(null), 1800);
  };
  const statements = persona.records.map((r) => ({
    text: r.risk ? r.text.split(".")[0] + "." : r.text.split(".").slice(0, 2).join(".") + ".",
    id: r.id, sourceLabel: r.source,
  }));
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>Walk in prepared</p>
      <h1>Context — {persona.name}</h1>
      <p className="lead">{persona.summary}</p>

      <article className="proposal" style={{ margin: "1.3rem 0 1.8rem" }}>
        <div className="proposal-head">
          <span className="proposal-pill">⬩ Brief</span>
          <span className="meta">Pre-meeting synthesis — not a record of truth</span>
        </div>
        <div className="proposal-body">
          <p className="proposal-meta">Synthesised from {persona.records.length} source records · drafted by open-weight model (<code>{window.NF_DATA.model}</code>). Check each line against its source before you rely on it.</p>
          <ul className="brief-list">
            {statements.map((s) => <Statement key={s.id} text={s.text} sourceLabel={s.sourceLabel} onJump={() => jump(s.id)} />)}
          </ul>
          <p className="proposal-foot mb0"><span className="lock" aria-hidden="true">⬩</span> Every line traces to a source — follow a "says who?" link to see it. Nothing here is committed or sent.</p>
        </div>
      </article>

      <h2>Source records <span className="muted" style={{ fontWeight: 400 }}>({persona.records.length})</span></h2>
      {persona.records.map((r) => (
        <div key={r.id} ref={(el) => (refs.current[r.id] = el)} className={"record" + (flash === r.id ? " flash" : "")}>
          <div className="rec-head">
            <strong>{r.source}</strong>
            <span className="muted">· {r.date} · {r.author}</span>
            {r.risk && <span className="tag tag-risk tag-dot">safeguarding signal</span>}
          </div>
          <blockquote>{r.text}</blockquote>
        </div>
      ))}
      <a className="back-link" onClick={() => go("drafting", persona.id)}>Continue to drafting →</a>
    </div>
  );
}

/* ============ 3 · DRAFTING (hero) ============ */
function Drafting({ persona, go, addLog }) {
  const [draft, setDraft] = useS(null);
  const [committed, setCommitted] = useS([]);
  const dispose = (val, text) => {
    if (val === "commit") {
      setCommitted((c) => [{ text, when: "2026-06-03" }, ...c]);
      addLog({ persona: persona.name, surface: "drafting", type: "case_note", disposition: "commit", proposal: draftFor(persona.id), final: text });
    }
    setDraft(null);
  };
  const first = persona.name.split(" ")[0];
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>The propose → dispose moment</p>
      <h1>Drafting for {persona.name}</h1>
      <p className="lead">{persona.summary}</p>

      <div className="grid cols-2" style={{ margin: "1.5rem 0" }}>
        <article className="card">
          <h3>Draft a case note</h3>
          <label>What happened in the meeting? <span className="hint">(optional — helps the draft)</span>
            <textarea rows={3} placeholder={"e.g. Showed me his game prototype; keen on the evening IT course; worried about bus money."} />
          </label>
          <button className="btn-block" onClick={() => setDraft("case")}>Draft case note</button>
        </article>
        <article className="card">
          <h3>Draft a follow-up message</h3>
          <p className="muted">A short message to {first} in your voice. It stays a draft — sending is a separate, explicit action.</p>
          <button className="btn-block btn-ghost" onClick={() => setDraft("case")}>Draft follow-up message</button>
        </article>
      </div>

      {draft && (
        <div style={{ margin: "0 0 1.8rem" }}>
          <ProposalFrame
            typeLabel="Case note"
            initialText={draftFor(persona.id)}
            actions={[
              { value: "commit", label: "Commit as my note", class: "btn-ink btn-lg" },
              { value: "discard", label: "Discard", class: "btn-ghost" },
            ]}
            onDispose={dispose}
          />
        </div>
      )}

      <div className="grid cols-2">
        <article className="card">
          <h3 style={{ marginBottom: ".6rem" }}>Committed case notes <span className="muted" style={{ fontWeight: 400 }}>({committed.length})</span></h3>
          {committed.length === 0
            ? <p className="muted mb0">No committed notes yet. Drafting alone never writes here — only your explicit "Commit".</p>
            : committed.map((c, i) => (
                <div className="committed-record" key={i}>
                  <span className="attrib">✓ Committed by {window.NF_DATA.worker} · {c.when}</span>
                  <p>{c.text}</p>
                </div>
              ))}
        </article>
        <article className="card">
          <h3 style={{ marginBottom: ".6rem" }}>Sent messages <span className="muted" style={{ fontWeight: 400 }}>(0)</span></h3>
          <p className="muted mb0">Nothing sent. A follow-up stays a draft until you explicitly press "Send".</p>
        </article>
      </div>
      <p className="muted" style={{ marginTop: "1rem", fontSize: ".9rem" }}>Every commit also appends to the immutable <a onClick={() => go("log", persona.id)} style={{ cursor: "pointer" }}>decision log</a>, alongside the original AI proposal.</p>
      <a className="back-link" onClick={() => go("caseload")}>← All personas</a>
    </div>
  );
}

Object.assign(window, { Caseload, Context, Drafting, byId, draftFor });
