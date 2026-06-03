# Discovery Interview — Former Youth Worker / Guidance Counsellor

*Purpose: anchor and validate the Keyworker Force-Multiplier functionality against lived frontline experience. Built to **validate or falsify** the project's core bets, not to pitch them. Maps to the Hard Invariants (CLAUDE.md) and the `VAL-` assertions (validation-contract.md). Findings that challenge a bet should be logged in `decisions.md`.*

## How to run it
- **Ask about the last real time, not the hypothetical.** "Tell me about the last time you prepped for a meeting with a young person you didn't know well" beats "would context help?"
- **Don't describe the tool until the end.** Let his problems surface first; pitching contaminates validation. Save "here's what we're thinking" for the last 10 minutes.
- **Listen for the charges the briefing predicts:** professional pride, job-security fear, scar tissue from failed IT systems. If they don't show up, that's a finding too.

---

## 1. Their actual world (anchor in reality)
- Walk me through a typical day — where does the time actually go?
- Roughly what fraction of your week was face-to-face youth work versus admin/paperwork/systems?
- What systems did you have to use, and how did you feel about them? Tell me about the worst one.
- What did you do *because the system made you*, that you felt added nothing for the young person?

*Tests: the "admin crowds out relational work" premise — the whole value proposition. If the admin burden isn't large or resented, the foundation is weak.*

## 2. Walking into a meeting (validates CTX — context synthesis)
- Before meeting a young person you didn't know well, how did you get up to speed? Where did the information live?
- When information was scattered across services/records, what did that cost you — give me an example.
- Have you ever walked into a meeting "cold" and had it go badly because you were missing context? What happened?
- If you could have a one-page picture before a meeting, what would *have* to be on it — and what would you not trust unless you could see where it came from?

*Tests: VAL-CTX-001/002. The last question probes whether "every claim traces to source" is a real need or a nice-to-have.*

## 3. The paperwork itself (validates DRAFT + authorship)
- What do you write after a session — case notes, referrals, follow-ups? Which drained you most?
- How much does *how a note is written* matter — is there a "right voice" for these records? Who reads them later?
- If something drafted your case note for you, what would make you trust it — and what would make you bin it and start over?
- How would you feel about a record that was partly machine-drafted? Does it matter whether your name is on it as the author?

*Tests: VAL-DRAFT-001/002, Invariant 5 (authorship). Probes the "pride is a feature" hypothesis.*

## 4. Risk and safeguarding (validates ESCALATE — handle with care)
- When you spotted a safeguarding or risk concern, what did you actually do — what was the process, who owned it?
- Have you ever *missed* something, or worried you had? What would have helped — and what would have made it worse?
- If a system flagged a possible risk to you, what would you need to see to take it seriously rather than dismiss it?
- How would you feel about a tool that surfaced a risk flag but did *nothing* automatically — left the decision entirely to you? Right call, or too much on you?

*Tests: VAL-ESCALATE-001/002, Invariant 6. The last question is the crux — does human-owned escalation feel like respect or like liability dumped on him?*

## 5. The trust boundary (validates PROPOSE / DENY — the core primitive)
- How would you feel about an AI that *suggests* but never *decides* — drafts and surfaces, but you commit everything?
- Is there anything you'd want it to just *do* automatically? (Listen hard — this is where people ask you to violate Invariant 1.)
- Imagine a young person can't get something they want, and a screen tells them "no." Your reaction to a *machine* delivering that versus you delivering it?

*Tests: Invariants 1 & 2 — whether "AI proposes, human disposes" is felt as safety or friction.*

## 6. Fears and failure modes (the briefing's hard truths)
- If your manager rolled out an "efficiency tool" for your role, what would go through your head?
- What would make you quietly stop using a tool like this within a week?
- Have you seen tech promised to frontline staff that failed? Why did it fail?
- Is there a version of this that would feel like surveillance — of you, or of the young people? Where's that line?

*Tests: job-security and "surveillance smell" risks (briefing §4, §6). The disqualifiers.*

## 7. The young person's experience (the indirect beneficiary)
- When you used a laptop/system mid-conversation, how did the young person react? Did it change the encounter?
- What separates a young person feeling *helped* from feeling *processed*? An example of each?

*Tests: the "don't depersonalise the encounter" requirement (briefing §4, Angle 3).*

## 8. The killer questions (ask near the end)
- If we built one thing that genuinely gave you back time for the actual youth work, what would it be?
- What's the thing that, if we got it wrong, would make this worse than useless — or even harmful?
- Who else *must* we talk to — and who would be the hardest sceptic to convince?

---

*Core bets to listen against: (1) admin burden is the binding constraint; (2) "AI proposes, human disposes" reads as respect, not friction. Pushback on either — "the bottleneck was caseload, not paperwork", or "I'd want it to just file routine notes itself" — is the most valuable thing you can hear. Log it in `decisions.md`.*
