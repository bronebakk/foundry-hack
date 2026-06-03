/* Refined surfaces 4–6: Safeguarding, NoDeny, Inbox, Decision log. Exported to window. */

const ESC_DRAFTS = {
  "leah-sumner": "Escalation note — draft (to be edited by keyworker)\n\nDate: 20 Feb 2026 · Young person: Leah Sumner, 16\n\nRecorded concern: Leah disclosed a relationship with a man she says is 24, who has given her a phone, money for taxi fares, and overnight stays at a friend's flat in another town. She could not explain a new pair of trainers and became guarded when asked.\n\nWhy I am referring: the pattern matches recognised indicators of child exploitation. This is my professional judgement, made today.",
  "ivy-castellano": "Wellbeing note — draft (to be edited by keyworker)\n\nDate: 01 Feb 2026 · Young person: Ivy Castellano, 16\n\nRecorded concern: Marked withdrawal from activities she previously loved, flat affect in sessions, and her own words that 'everything feels pointless lately'. No disclosure of harm.\n\nWhy I am surfacing this: low mood noted; I would value a wellbeing check-in. My decision to raise it.",
};

/* ============ 4 · SAFEGUARDING ============ */
function Safeguarding({ persona, go, addLog }) {
  const riskRec = persona.records.find((r) => r.risk);
  const [done, setDone] = useS(false);
  const first = persona.name.split(" ")[0];
  const dispose = (val, text) => {
    if (val === "escalate") {
      addLog({ persona: persona.name, surface: "escalation", type: "risk_flag", disposition: "escalate",
        proposal: (riskRec && riskRec.riskCategory ? riskRec.riskCategory : "Concern") + " surfaced from " + (riskRec ? riskRec.id : "record") + ".", final: text });
      setDone("escalate");
    } else setDone("review");
  };

  if (!riskRec) {
    return (
      <div>
        <p className="eyebrow" style={{ marginBottom: ".4rem" }}>Human-owned</p>
        <h1>Safeguarding — {persona.name}</h1>
        <p className="lead">{persona.summary}</p>
        <div className="callout"><span className="ic">⬩</span><div><strong>No safeguarding signal is present</strong> in {first}'s synthetic records. There is nothing to escalate — and the system would never escalate on its own.</div></div>
        <a className="back-link" onClick={() => go("caseload")}>← Back to caseload</a>
      </div>
    );
  }

  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>Surfaced for your judgement · human-owned</p>
      <h1>Safeguarding — {persona.name}</h1>
      <p className="lead">{persona.summary}</p>
      {persona.demoNote && <p className="muted" style={{ fontStyle: "italic", fontSize: ".9rem", maxWidth: "62ch" }}>🧪 {persona.demoNote}</p>}

      <div className="callout">
        <span className="ic" aria-hidden="true">🛡️</span>
        <div><strong>No automatic action has been or will be taken.</strong> The signal below is surfaced for your judgement. The system has not notified anyone, made any referral, or decided anything. <strong>You decide what happens next.</strong></div>
      </div>

      <h2>Surfaced signal</h2>
      <div className="risk">
        <div className="risk-head">
          <span className="tag tag-risk tag-dot">safeguarding signal</span>
          <span className="title">{riskRec.riskCategory}</span>
        </div>
        <p className="eyebrow" style={{ marginBottom: ".2rem" }}>Why this was flagged</p>
        <p style={{ margin: "0 0 .2rem" }}>{riskRec.riskRationale}</p>

        <div className="record" style={{ marginTop: "1rem", background: "var(--surface)" }}>
          <div className="rec-head"><strong>Source — record <code>{riskRec.id}</code></strong> <span className="muted">— this is what triggered the signal</span></div>
          <p className="muted" style={{ margin: ".35rem 0 0", fontSize: ".84rem" }}>{riskRec.source} · {riskRec.date} · logged by {riskRec.author}</p>
          <blockquote>{riskRec.text}</blockquote>
          <p className="subtle mb0" style={{ marginTop: ".6rem", fontSize: ".82rem" }}>This indicator is present in the synthetic record. The system did not judge it — it is shown to you, with its source, so you can.</p>
        </div>

        <h4 style={{ margin: "1.3rem 0 .6rem" }}>Escalate — your decision</h4>
        {done === "escalate"
          ? <Receipt tone="commit"><strong>Sent to the safeguarding inbox.</strong> It arrived because <strong>you</strong> chose to send it. A human safeguarding lead owns it now — the system marks nothing "resolved". See the <a onClick={() => go("inbox")} style={{ cursor: "pointer" }}>inbox</a>.</Receipt>
          : done === "review"
          ? <Receipt><strong>Your review is recorded.</strong> You chose not to escalate now. Nothing was sent; this stays your decision to revisit.</Receipt>
          : <ProposalFrame
              typeLabel="Safeguarding escalation note"
              foot="The AI drafts; you decide. Nothing is sent until you escalate. Escalation is your decision and lands in a human-owned queue."
              initialText={ESC_DRAFTS[persona.id] || "Escalation note — draft\n\nRecorded concern: …\n\nWhy I am referring: my professional judgement, made today."}
              actions={[
                { value: "escalate", label: "Escalate to safeguarding lead", class: "btn-contrast btn-lg" },
                { value: "review", label: "Not now — record my review", class: "btn-ghost" },
              ]}
              onDispose={dispose}
            />}
      </div>
      <a className="back-link" onClick={() => go("context", persona.id)}>← Back to {first}'s context</a>
    </div>
  );
}

/* The "no computer says no" pattern — warm, first-class (Invariant 3). */
function NoDeny({ persona, go, addLog }) {
  const [sent, setSent] = useS(false);
  const first = persona.name.split(" ")[0];
  const send = (val, text) => {
    addLog({ persona: persona.name, surface: "escalation", type: "follow_up", disposition: "escalate",
      proposal: "Funded place 16–19 only; alternatives exist.", final: text });
    setSent(true);
  };
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>No computer says no</p>
      <h1>Options — {persona.name}</h1>
      <p className="lead">{persona.summary}</p>
      <p className="muted" style={{ marginTop: "1rem" }}>{first} asked about this in their own words — record <code>{persona.records[1].id}</code> ({persona.records[1].date}):</p>
      <blockquote style={{ borderLeft: "3px solid var(--info)", paddingLeft: "1rem", color: "var(--fg)", margin: ".4rem 0 1.4rem" }}>{persona.records[1].text}</blockquote>

      <div className="option">
        <div className="no-no"><strong>The system isn't telling {persona.name} "no".</strong> It can't — and it won't. Where an option isn't open on its usual route, a person owns that decision and delivers it with a reason and a real alternative — never a machine refusal.</div>
        <p className="muted">A keyworker reviews the open routes and alternatives with {persona.name}. Nothing is closed off automatically.</p>
        {sent
          ? <Receipt tone="commit"><strong>Handed to a keyworker.</strong> A person will review {first}'s routes and come back with a way in and a reason. The system never refuses on its own authority.</Receipt>
          : <ProposalFrame
              typeLabel="Hand-off to a keyworker"
              foot="This routes the decision to a human. The system never refuses on its own authority, and never closes a door without a person and an alternative."
              initialText={"Please review " + persona.name + "'s options and come back to them with a route they can take up and a real alternative — they specifically don't want to just be told \u201cno\u201d."}
              actions={[{ value: "send", label: "Send to a keyworker to decide", class: "btn-contrast btn-lg" }]}
              onDispose={send}
            />}
      </div>
      <a className="back-link" onClick={() => go("caseload")}>← Back to caseload</a>
    </div>
  );
}

/* ============ 5 · SAFEGUARDING INBOX ============ */
function Inbox({ go, log }) {
  const items = log.filter((e) => e.surface === "escalation");
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>A human-owned queue</p>
      <h1>Safeguarding inbox</h1>
      <p className="lead">Every item here arrived <strong>because a worker chose to send it</strong> — never automatically. The system resolves nothing here; a designated safeguarding lead owns and closes these off-system.</p>
      <div className="inbox-owner"><span aria-hidden="true">👤</span> Owned by <strong style={{ color: "var(--ink)" }}>Safeguarding Lead (human)</strong> · the machine marks nothing "resolved".</div>
      {items.length === 0
        ? <div className="card"><p className="mb0 muted">Nothing in the queue yet. Open a young person with a surfaced signal (e.g. <a onClick={() => go("safeguarding", "leah-sumner")} style={{ cursor: "pointer" }}>Leah Sumner</a>) and choose to escalate — it lands here because <em>you</em> sent it.</p></div>
        : items.map((e, i) => (
            <article className={"queue-item" + (e.type === "risk_flag" ? " escalate" : "")} key={i}>
              <header>
                <span className={"tag tag-dot " + (e.type === "risk_flag" ? "tag-risk" : "tag-synthetic")}>{e.type === "risk_flag" ? "safeguarding escalation" : "decision needed (human)"}</span>
                <strong style={{ color: "var(--ink)" }}>{e.persona}</strong>
                <span className="muted" style={{ fontSize: ".84rem" }}>· {e.when}</span>
              </header>
              <p className="arrived">↳ Arrived because <strong style={{ color: "var(--fg)" }}>{window.NF_DATA.worker}</strong> sent it. Not auto-generated.</p>
              <blockquote style={{ borderLeft: "3px solid var(--hair-strong)", paddingLeft: "1rem", whiteSpace: "pre-wrap", color: "var(--fg)", margin: ".5rem 0 .8rem" }}>{e.final}</blockquote>
              <span className="q-status">Awaiting human review</span> <span className="muted" style={{ fontSize: ".86rem" }}>· a person decides and resolves this — the system will not.</span>
            </article>
          ))}
    </div>
  );
}

/* ============ 6 · DECISION LOG ============ */
function DecisionLog({ go, log }) {
  const [filter, setFilter] = useS("All");
  const names = ["All", ...new Set(window.NF_DATA.personas.map((p) => p.name))];
  const shown = filter === "All" ? log : log.filter((e) => e.persona === filter);
  const verb = { commit: "committed as their own note.", escalate: "escalated to a human.", send: "sent it.", discard: "discarded it." };
  return (
    <div>
      <p className="eyebrow" style={{ marginBottom: ".4rem" }}>The governance spine</p>
      <h1>Decision log</h1>
      <p className="lead">Every AI proposal a worker acted on — the <strong>AI's proposal</strong>, the <strong>human's disposition</strong>, and the <strong>worker of record</strong> — in an append-only log that cannot be silently altered.</p>

      <div className="gov-immutable"><span aria-hidden="true">🔒</span><div><strong>Append-only.</strong> Entries can be added but never edited or deleted — enforced at the database layer (UPDATE/DELETE rejected by triggers) and the service layer (no mutation API exists). Read-only by construction; there is no edit or delete control to find.</div></div>
      <div className="gov-inference"><strong style={{ color: "var(--ink)" }}>Inference provenance — open-weight only, self-hostable.</strong> Primary <code>openai/gpt-oss-120b</code> · fallback <code>meta-llama/llama-3.3-70b-instruct</code>. No closed cloud model.</div>

      <div className="gov-filter">
        <span className="lbl">Filter</span>
        {names.map((n) => <span key={n} className={"chip" + (filter === n ? " active" : "")} onClick={() => setFilter(n)}>{n === "All" ? "All" : n.split(" ")[0]}</span>)}
      </div>
      <p className="muted" style={{ fontSize: ".85rem" }}>{shown.length} {shown.length === 1 ? "entry" : "entries"} · newest first.</p>

      {shown.length === 0
        ? <div className="card"><p className="mb0 muted">No entries yet. Commit a note in <a onClick={() => go("caseload")} style={{ cursor: "pointer" }}>Drafting</a> or escalate in Safeguarding — each human disposition appends here.</p></div>
        : <div className="gov-log">
            {shown.map((e, i) => (
              <article className={"gov-entry " + e.disposition} key={i}>
                <div className="gov-head">
                  <span className="gov-id">#{log.length - log.indexOf(e)}</span>
                  <Badge kind={e.disposition}>{e.disposition}</Badge>
                  <span className="gov-when">{e.when} · {e.time || "10:16:28"}</span>
                </div>
                <p className="gov-meta">{e.persona} · surface: {e.surface} · {e.type}</p>
                <div className="gov-flow">
                  <div className="gov-step ai">
                    <div className="who">⬩ AI proposed</div>
                    <p>{e.proposal}</p>
                  </div>
                  <div className="gov-connector" aria-hidden="true">↓</div>
                  <div className="gov-step human">
                    <div className="who"><span className="arrow">→</span> {window.NF_DATA.worker} {verb[e.disposition] || "disposed."}</div>
                    <p>{e.final}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>}
      <a className="back-link" onClick={() => go("caseload")}>← Back to caseload</a>
    </div>
  );
}

Object.assign(window, { Safeguarding, NoDeny, Inbox, DecisionLog });
