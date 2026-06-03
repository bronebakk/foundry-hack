/* Synthetic persona data — lifted from bronebakk/foundry-hack app/data/personas/*.json.
   All entirely fictional (Invariant 6). Exposed as window.NF_DATA. */
window.NF_DATA = {
  worker: "Sam Ellison (keyworker)",
  model: "openai/gpt-oss-120b",
  personas: [
    {
      id: "amara-okafor", name: "Amara Okafor", age: 19, synthetic: true,
      summary: "19, left a college course mid-year; anxiety is the main barrier; engagement comes and goes.",
      records: [
        { id: "amara-r1", date: "2026-01-15", source: "Springfield College — Pastoral note", author: "J. Reed (Tutor)", text: "Withdrew from Level 3 Health & Social Care in November. Anxiety cited; missed assessments. Bright, conscientious when present." },
        { id: "amara-r2", date: "2026-02-03", source: "Self-referral form (Amara's own words)", author: "Amara Okafor", text: "Wants to get back into something but college 'felt like too much, too fast'. Asked about part-time or online options." }
      ]
    },
    {
      id: "noah-bennett", name: "Noah Bennett", age: 18, synthetic: true,
      summary: "18, left sixth form after one term; days and nights flipped; wants games/IT work; opens up over shared interests.",
      records: [
        { id: "noah-r1", date: "2026-01-20", source: "Riverside Sixth Form — Exit note", author: "T. Bauer (HoY)", text: "Left after one term. Disengaged from A-levels; strong informal IT/coding ability. Sleep pattern reversed — rarely up before midday." },
        { id: "noah-r2", date: "2026-02-12", source: "Bridge Project — Drop-in note", author: "M. Adeyemi (Youth Worker)", text: "Showed a game prototype he built himself; clearly talented. Keen on the Open College evening Level 2 IT course (starts 4pm — suits his hours). Worried about funding and bus money." }
      ]
    },
    {
      id: "marcus-fielding", name: "Marcus Fielding", age: 20, synthetic: true,
      summary: "20, set on a Level 3 engineering course, but the fully-funded place he applied for is 16–19 only; motivated and ready to start.",
      noDeny: true,
      records: [
        { id: "marcus-r1", date: "2026-02-08", source: "Adult Skills service — Enquiry", author: "Caseworker note", text: "Applied for the fully-funded Level 3 engineering place. Eligibility is 16–19 only; Marcus is 20. Highly motivated, ready to start now." },
        { id: "marcus-r2", date: "2026-02-18", source: "Self-referral form (Marcus's own words)", author: "Marcus Fielding", text: "Just wants a straight answer and a way in — 'don't tell me no, tell me how'." }
      ]
    },
    {
      id: "leah-sumner", name: "Leah Sumner", age: 16, synthetic: true,
      summary: "16, persistently absent from school; recently more withdrawn; a safeguarding indicator is present in the records.",
      demoNote: "Fictional persona — synthetic demo data only. Not a real person, no real records. The safeguarding indicator below is a fictional teaching example for the escalation demo.",
      records: [
        { id: "leah-r1", date: "2026-01-22", source: "Oakfield School — Education Welfare Officer", author: "P. Nkomo (EWO)", text: "Attendance down to 41%. Mother reports Leah is often out in the evenings and vague about where. Bright but has 'checked out' of school. Home situation stretched; mum working nights." },
        { id: "leah-r2", date: "2026-02-20", source: "Bridge Project (charity) — Drop-in note", author: "M. Adeyemi (Youth Worker)", risk: true, riskCategory: "Possible child sexual / criminal exploitation (CSE/CCE)", riskRationale: "16-year-old; significantly older male; gifts (phone, trainers); unexplained money; travel to and overnight stays at an unknown address — recognised indicators of exploitation. Surfaced for the worker's judgement; not acted on automatically.", text: "Leah came to drop-in. Mentioned a new 'boyfriend' — said he is 24. He bought her a new phone and gives her money for taxis to his friend's flat a few towns over, where she's been staying some nights. Became guarded when asked about it and changed the subject. New trainers she couldn't explain." },
        { id: "leah-r3", date: "2026-02-28", source: "Bridge Project — Self-referral form (Leah's own words)", author: "Leah Sumner", text: "Wrote that she wants help finding a college course in hair and beauty for September but 'everyone treats me like a problem'. Asked if the youth worker she likes could be the one to help her." }
      ]
    },
    {
      id: "ivy-castellano", name: "Ivy Castellano", age: 16, synthetic: true,
      summary: "16, recently much more withdrawn; dropped the activities she used to love; a wellbeing/low-mood indicator is present in the records.",
      records: [
        { id: "ivy-r1", date: "2026-02-01", source: "School counsellor — Note", author: "R. Hale (Counsellor)", risk: true, riskCategory: "Low mood / wellbeing concern", riskRationale: "Marked withdrawal from previously-loved activities and flat affect. A wellbeing indicator surfaced for the worker's judgement — not a diagnosis, not acted on automatically.", text: "Has stepped back from football and art club, which she loved. Quieter, flat in sessions. No disclosure of harm; low mood noted." },
        { id: "ivy-r2", date: "2026-02-22", source: "Self-referral form (Ivy's own words)", author: "Ivy Castellano", text: "'Everything feels pointless lately.' Said she might like to try something creative again if it wasn't a big commitment." }
      ]
    },
    {
      id: "kofi-mensah", name: "Kofi Mensah", age: 17, synthetic: true,
      summary: "17, care-experienced; strong interest in trades; misses appointments but turns up for hands-on work.",
      records: [
        { id: "kofi-r1", date: "2026-01-30", source: "Leaving Care team — Note", author: "D. Owusu (PA)", text: "Care-experienced. Reliable for practical sessions; misses office-based appointments. Keen on construction/trades." },
        { id: "kofi-r2", date: "2026-02-19", source: "Bridge Project — Drop-in note", author: "M. Adeyemi (Youth Worker)", text: "Asked about a CSCS card and a college taster in bricklaying. Responds best to text reminders the morning of, not days ahead." }
      ]
    }
  ]
};
