# CareerOS — User Guide

This guide teaches you how to use every feature and how to sequence them to maximize your chances of landing an internship offer.

---

## The System at a Glance

CareerOS has three layers:

| Layer | What it does | Where to find it |
|-------|-------------|------------------|
| **Foundation** | Data that powers every agent | Profile, Job Tracker, Project Library |
| **Strategy** | Big-picture coaching and outreach — Career Coach can invoke other agents directly | **Career Coach** (sidebar) — also access Study Partner, Resume Synthesizer, and Outreach via the Specialist Tools expander |
| **Job Prep** | Per-job preparation — each job gets its own set | **Job Workbench** (sidebar) — 4 tabbed agents: Resume Reviewer, Gap Identifier, Interview Coach, Study Planner |
| **Learning** | Concept-level study support | Study Partner (via Coach → Specialist Tools), Study Planner (via Job Workbench) |

### Navigation

The sidebar has 6 items:
- **Dashboard** — pipeline stats and quick coach insight
- **Job Tracker** — Kanban board with a "Prep" button on each job (navigates to Job Workbench)
- **Career Coach** — your primary AI entry point; can dispatch all other agents automatically
- **Job Workbench** — select a job, then use Resume Reviewer / Gap Identifier / Interview Coach / Study Planner in tabs
- **Project Library** — upload and manage your project knowledge base
- **My Profile** — your profile data that powers all agents

**The agents are only as good as the data you give them.** A complete profile, active tracker, and pasted JDs are what separate generic advice from advice that's actually useful.

---

## Step 1: Set Up Your Profile (Do This First)

**My Profile** (sidebar)

Fill in every field. This data is injected into every agent automatically.

| Field | What it powers | Tips |
|-------|---------------|------|
| **Name** | Personalization across agents | Just your first name is fine |
| **Target Role** | Role-specific calibration for all agents | Be specific: "ML Engineer Intern" not "tech" |
| **University** | Outreach agent for alumni targeting; Gap agent for prestige context | Exact name as it appears on LinkedIn |
| **Graduation** | All agents know your internship cycle | Format: "May 2026" or "Summer 2026 cycle" |
| **GPA** | Resume agent decides whether to surface it; Gap agent calibrates thresholds | Format: "4.2/5.0" or "3.85/4.0". Include scale. |
| **Resume (full text)** | The most important field — used by every agent | Paste raw text. Don't worry about formatting. Include all experience, projects, skills, education. |
| **Goals & Situation** | Career Coach strategy; Study Planner urgency | Write what's actually on your mind: "Targeting summer 2026. Weak on system design. Unsure SWE vs DS track." |

**After saving:** Every agent immediately uses your updated profile. No need to restart anything.

---

## Step 2: Set Up the Job Tracker

**Job Tracker → + Add Job**

The tracker is your pipeline. The Career Coach reads it directly and spots patterns you'd miss.

### What to fill in per job

| Field | Why it matters |
|-------|----------------|
| **Company + Role** | How the coach and prep agents refer to this application |
| **Status** | The coach diagnoses your funnel — where are jobs dropping off? |
| **Date Applied** | Flags stale applications (no update in 3+ weeks) |
| **Application Deadline** | ⚠️ Critical for interns. The coach flags deadlines within 14 days as urgent. Color-coded in the tracker: grey → yellow (≤14d) → red (≤7d). |
| **Job Description** | Paste the full JD in the **Notes & JD tab**. This unlocks Resume, Gap, Interview, and Study agents for that job. |
| **Progress Notes** | Add a note every time the status changes. "Strong phone screen, mentioned ML infra focus" is 10× more useful than just moving the status. |

### The 6 statuses and when to use them

```
Wishlist    → You want to apply but haven't yet
Applied     → Submitted. Start the clock.
Phone Screen → Any recruiter/HR contact made
Interview   → Technical or hiring manager round scheduled or done
Offer       → Written offer received
Rejected    → Closed. Keep it — the coach uses rejection patterns.
```

**Keep it current.** Stale data produces stale advice.

---

## Step 3: Add Projects to the Project Library

**My Work → 📚 Project Library**

The Project Library is what separates generic resume rewrites from rewrites that actually use your real work. Upload a project report, paste a description, or upload a README — Claude extracts your technologies, metrics, contributions, and challenges.

**Why this matters:** The Resume Reviewer reads your entire project library before every session. When it rewrites a bullet, it pulls from verified facts — real numbers, real tech, real outcomes — instead of inventing plausible-sounding details.

### How to add a project

1. Click **➕ Add a New Project**
2. Choose your format: PDF report, Word doc, Markdown file, or paste text directly
3. Add an optional title hint (Claude will infer it if blank)
4. Click **Extract & Add to Library**

Claude extracts: technologies, metrics, your specific contributions, challenges solved, and a JD-matching summary.

**What to add:** Any project you'd put on your resume. Academic projects, personal builds, internship work, research. The more detail in the source material, the better the extraction.

---

## Step 4: Use the Agents in Order

### The Optimal Internship Workflow

```
New job target found:
1. Add to tracker → paste JD → set deadline
2. Click "Prep" on the job card → opens Job Workbench for that job
3. Gap tab → "Should I apply now or close a gap first?"
4. Resume tab → tailor resume to this specific JD
5. Apply
6. If invited to interview → Study tab → build a plan for this role
7. Interview tab → mock interview practice
8. Career Coach → Specialist Tools → LinkedIn & Outreach for referral outreach

Cross-company, big-picture (all from Career Coach):
→ Ask the Coach directly — it dispatches agents and synthesizes results
→ Coach → Specialist Tools → Resume Synthesizer: after 3+ JDs, build one great resume
→ Coach → Specialist Tools → Study Partner: learn a concept deeply
```

---

## Agent Reference: What Each Agent Does and How to Get the Most From It

---

### Career Coach
**Sees:** Full profile (including GPA, uni, graduation) + all jobs + all statuses + deadlines + progress notes
**Best for:** Pipeline diagnosis, strategy, weekly planning, accountability, flagging urgent deadlines

The coach reads your tracker data directly. The more complete and current it is, the sharper the advice.

**The coach is an orchestrator.** It can call the other agents on your behalf — gap analysis, resume review, outreach drafting, interview prep, study plans — and synthesize the results into a single response. You don't need to navigate to each agent manually for multi-step questions. When the coach dispatches sub-agents, a small indicator appears above the response showing the pipeline (e.g., "🔍 Gap Analysis → 📚 Study Planner → 🧭 Synthesis").

**Specialist Tools:** Below the coach chat, an expandable "Specialist Tools" section gives you direct access to Study Partner, Resume Synthesizer, and LinkedIn & Outreach for extended multi-turn sessions with those agents.

**Multi-agent power prompts:**
```
"Should I apply to [Company]? Run a gap analysis and tell me."

"I want to reach out to someone at [Company]. Draft me a LinkedIn connection request."

"What are the must-know topics for the [Company] role? Build me a study plan."

"Should I apply to [Company] now, or spend 2 weeks closing gaps first? Then tell me what to study."

"Tailor my resume for the [Company] role."

"Draft outreach for [Company] — I found a senior engineer on LinkedIn."
```

**Pipeline diagnosis prompts:**
```
"Diagnose my pipeline. Where am I losing — volume, response rate, or conversion?"

"I have [X] applications and [Y] got to phone screen. What's the pattern and what do I change?"

"Which of my active applications should I double down on and which should I deprioritize? Use the tracker data."

"What's the highest-ROI thing I can do this week given where I am in the pipeline?"

"I feel like I'm applying a lot but nothing is moving. What's actually wrong?"

"Are any of my deadlines coming up soon? Tell me what to prioritize."

"Give me a 2-week plan. I have about [X hours/week]. Focus on the applications most likely to convert."
```

*With Google Calendar connected:*
```
"Block 2 hours of interview prep this week — check my calendar and find a slot that works."
"Add a reminder 3 days before my [Company] deadline."
```

---

### LinkedIn & Outreach Drafter
**Sees:** Your full profile + tracked companies
**Best for:** Cold DMs, connection requests, referral asks, cold emails, follow-ups

Always tell the agent: **who you're messaging, their role, the company, and how you found them.** The more context you give, the better the message. A personalized message gets 5–10× the reply rate of a generic one.

**The outreach sequence (follow this order):**
1. Send a LinkedIn connection request with a short note (≤300 chars)
2. Within 48 hours of them accepting: send a follow-up DM — one genuine question about their work, no internship ask yet
3. After they reply: send a referral request — direct, specific, low-friction

**Power prompts:**
```
"Draft a LinkedIn connection request to a [role] at [Company]. I found them through [how]. We both went to [school / no connection]."

"They accepted my connection request. Write a follow-up DM. Their name is [X], they work on [team/project]. I want to ask about [topic]."

"Write a referral request. I've exchanged 2 messages with [X] at [Company]. I'm applying for [Role]. Keep it direct and make it easy for them to say yes."

"Draft a cold email to a [role] at [Company]. LinkedIn wasn't available. Subject line and body."

"I messaged [X] 7 days ago and no reply. Write a one-sentence bump."

"What's the best way to approach someone from [school] who works at [Company]?"
```

**Timing:** Send LinkedIn messages Tuesday–Thursday, 8–10am or 12–1pm (their timezone). Never Friday afternoon.

---

### Resume Reviewer
**Sees:** Your resume + the JD of the job selected in the "Preparing for" dropdown
**Best for:** Bullet rewrites, ATS keyword gaps, student-specific structure, before-and-after improvements

**Before using:** Make sure the job has a JD pasted (Notes & JD tab) and you've selected it in the "Preparing for" dropdown.

**How to get the best results:**
- Start with the full review prompt — let the agent identify the highest-leverage issues first
- Then drill into specific bullets or sections
- Use the Project Library first — the agent will reference your real metrics and tech

**Power prompts:**
```
"Run a full review on my resume for this role. Start with the 6-second scan test."

"Do a JD keyword gap analysis. List every required skill from the JD that's missing from my resume."

"Rewrite my [project name] bullets. I have X in the Project Library — use those facts."

"I have no metrics on this bullet: '[paste bullet]'. Help me estimate a number I can honestly claim."

"My resume has [X] in the projects section. Rank them by relevance to this JD and cut the weakest one."

"Should I lead with Education or Experience for this specific role? Why?"

"Rewrite this bullet to a 9/10: '[paste bullet]'"

"What's the single structural change that would most improve my chances for this role?"
```

**Formatting the agent enforces:** `•` bullets only (never `-`), max 2 bullets per project, past tense for completed work.

---

### Gap Identifier
**Sees:** Your resume + the JD of the job selected in the "Preparing for" dropdown
**Best for:** Fit scoring, deciding whether to apply now or close gaps first, understanding what to address head-on in interviews

Run this **before you apply** to any competitive role. A 5/10 fit score with a clear 2-week gap-closing plan is more useful than applying blind and wondering why you got rejected.

**Power prompts:**
```
"Give me the full gap analysis for this role. Be honest about the fit score."

"Should I apply now or spend 2 weeks closing gaps first? What's the highest-ROI thing to fix?"

"What are the dealbreaker gaps — the ones that would cause a screen-out even for an intern?"

"What gaps should I address proactively in the interview rather than hoping they don't ask?"

"This is a [FAANG / startup / quant firm]. Calibrate your gap thresholds to that type of company."

"I'm a borderline fit. What's the best way to reframe my background for this specific role?"

"What's the single most important thing to fix before submitting this application?"
```

---

### Interview Coach
**Sees:** Your resume + the JD of the job selected in "Preparing for"
**Best for:** Mock interviews with realistic pressure, structured feedback, STAR behavioral coaching, hire/no-hire signals

The agent runs in different modes — **always tell it which one you want** at the start of the conversation. This gives you sharper, more focused practice.

**The 5 modes:**
| Mode | When to use it |
|------|---------------|
| **Full round** | 3–5 days before an interview. Full simulation, hire/no-hire verdict at the end. |
| **Single question drill** | When you want to get one question perfect — deep probing and detailed feedback. |
| **Behavioral only** | For behavioral/HR rounds. STAR format, competency-based questions. |
| **Technical only** | Coding, ML fundamentals, or system design for this specific role. |
| **"Tell me about yourself"** | Practice your 60-second opening pitch. Most common interview question — most people underprepare it. |

**Power prompts:**
```
"Run a full mock interview round for this role. 4–5 questions. End with a hire/no-hire verdict."

"Single question drill: ask me your hardest [ML / SWE / system design] question for this JD and probe until I hit my limit."

"Run behavioral only. Use STAR follow-ups if my answers are vague."

"I keep giving vague behavioral answers. Run through 3 behavioral questions and coach my STAR structure."

"I want to practice 'tell me about yourself'. Give me feedback on my answer and help me tighten it to 60 seconds."

"Ask me the question I'm most likely to fail at for this specific role."

"What patterns have you noticed in my answers so far? Name them explicitly."

"Give me a hire/no-hire signal for my last answer. Be honest."
```

**After a full round:** Ask for the pattern debrief — "What's the one thing that, if I fix it, would most improve my interview performance?"

---

### Study Planner
**Sees:** Your resume + the JD of the selected job + upcoming deadlines from your tracker
**Best for:** Structured study plans calibrated to your actual interview date, topic prioritization, specific resource recommendations

**Always tell it your interview date or how many weeks you have.** The agent builds the schedule backward from your deadline — a 1-week plan looks very different from a 4-week plan.

**Power prompts:**
```
"My interview is in [X weeks]. Build a study plan calibrated to that timeline."

"Classify all the topics from this JD as must-know, should-know, or good-to-know. Then tell me what to study first."

"I already know [X, Y, Z]. Build a plan that skips those and fills the actual gaps."

"What does 'interview-ready mastery' look like for this role? What should I be able to explain, code, and discuss?"

"For [topic]: give me the intuition, how it fits in the bigger system, the trade-offs, a 30-second interview answer, and one code example."

"I have 5 hours this week. What's the highest-ROI use of that time for this JD specifically?"

"Give me the best free resource for each must-know topic — specific titles, not just 'YouTube'."

"Create a question bank of the 10 most likely interview questions for this JD."
```

---

### Study Partner
**Sees:** Your full profile + all job targets
**Best for:** Learning concepts deeply enough to explain them under pressure — not just for one role, but for any interview

The Study Partner has three modes. Name the one you want:

| Mode | What to say | What happens |
|------|-------------|-------------|
| **Explain** | "Explain [X] to me" | Gets taught: why it exists → intuition/analogy → mechanism → trade-offs → 30-sec interview answer → code |
| **Quiz** | "Quiz me on [X]" | Flashcard-style drill: 5 questions, feedback after each, session summary at the end |
| **I don't know** | Just say "I don't know" when stuck | Gets a hint first, then the answer if still stuck, then an easier reask to rebuild |

**Power prompts:**
```
"Explain [concept] to me. Start with why it exists — no jargon."

"Quiz me on [topic]. 5 questions. Push back if my answers are surface-level."

"I think I understand [X] but I'm not 100% sure. Test me on it."

"Explain [concept A] vs [concept B] — what's the core difference and when do you use each?"

"What's my 30-second interview answer for 'What is [X]?'"

"I got this wrong: [paste your answer]. What pattern of misunderstanding does that reveal?"

"Teach me [X] from first principles. I've read about it but it doesn't feel solid."

"Connect [concept] to a real project — how would I actually use this?"
```

The partner tracks mistakes across the conversation. After 2–3 wrong answers on the same type of question, it'll name the pattern and fix it at the root.

---

### Resume Synthesizer
**Sees:** All JDs in your tracker + all Resume Reviewer sessions + your full profile
**Best for:** After you've added 3+ jobs with JDs — produces a complete, ready-to-send resume per role category

Run this when you have enough JDs to find patterns. The output is a **complete resume** — not a list of recommendations. Copy-paste ready, with a deployment map telling you which companies to send each version to.

**Power prompts:**
```
"Analyze all my JDs. Categorize them and find cross-cutting patterns."

"Build me a complete, ready-to-send resume for the [SWE / DS / AI-ML] intern category across all my tracked companies."

"What are the top 5 skills appearing across the most JDs? Which am I missing?"

"Rank my projects by how well they resonate across my tracked JDs. Which should I cut?"

"Build the resume version that gives me the broadest coverage — works reasonably well across all my applications."

"What should I de-emphasize on my resume based on what these companies actually care about?"

"After running the synthesizer, tell me: which 2 lines per company should I customize, and which stay the same?"
```

---

## The Recommended Weekly Rhythm

### When you're in active application mode:
```
Monday    → Career Coach: "What's the plan this week? Check my pipeline and deadlines."
            + Add any new jobs found over the weekend to the tracker

Tue–Wed   → Apply to new roles
            + LinkedIn & Outreach: send connection requests to employees at target companies

Thu       → Resume Reviewer or Gap Identifier for any new job you added this week

Fri       → Career Coach: "Anything stale or urgent in my pipeline I should address?"
            + Update statuses on any applications that moved
```

### When you have an interview coming up:
```
D-14  → Study Planner: "Interview in 2 weeks. Build the plan."
D-7   → Study Partner: deep-dive weak topics from the plan
D-3   → Interview Coach: full mock round (mode: Full Round)
D-1   → Interview Coach: "Tell me about yourself" + one behavioral question
D-0   → No new studying. Review your gap analysis notes. Sleep.
```

### When pipeline is stale (no responses in 2+ weeks):
```
1. Career Coach: "Nothing is moving. Diagnose what's wrong."
2. Resume Synthesizer: "Rebuild my resume based on all my JDs."
3. LinkedIn & Outreach: "Draft outreach to employees at [Company X] and [Company Y]."
4. Gap Identifier on your top-priority role: "Am I even a good fit for what I'm applying to?"
```

---

## What Each Agent Sees (and Doesn't See)

| Agent | Sees | Does NOT see |
|-------|------|-------------|
| Career Coach | Profile + all jobs + all statuses + deadlines + **can invoke any sub-agent as a tool** | Persistent agent chat histories |
| Resume Reviewer | Profile + selected job's JD + Project Library | Other jobs, other agents' outputs |
| Gap Identifier | Profile + selected job's JD | Project Library, other agents' outputs |
| Interview Coach | Profile + selected job's JD | Project Library, other agents' outputs |
| Study Planner | Profile + selected job's JD + upcoming deadlines | Project Library |
| Study Partner | Profile + all job targets | Per-job details, Project Library |
| Resume Synthesizer | Profile + ALL JDs + all Resume Reviewer sessions | Gap/Interview/Study sessions |
| LinkedIn & Outreach | Profile + all tracked companies | JDs, agent sessions |

**The Career Coach can act as a hub.** Ask the coach a multi-step question (e.g. "should I apply to X and what should I study?") and it will call the relevant agents, synthesize their output, and give you a single answer. The sub-agents' results are used in that response but are not stored in their individual chat histories — go to the dedicated agent page if you want a full interactive session.

---

## Getting the Best Results: Key Principles

**Give context before asking.** Every agent performs better when you tell it what you already know, what you've tried, and what you're uncertain about. "Run a gap analysis" is okay. "Run a gap analysis — I'm confident on Python and SQL but I've never used PyTorch. Be brutal." is much better.

**One job at a time in prep agents.** Always check the "Preparing for" dropdown before running Resume, Gap, Interview, or Study. Each job has its own conversation history — switching jobs doesn't lose your work.

**The context bar tells you your setup status.** Above every chat you'll see: ✅ Resume set · ✅ N jobs tracked · ✅ N jobs with JD. If any is ⚠️, fix it before expecting good output.

**Update your tracker or the coach goes blind.** The Career Coach's value comes from pattern recognition across your live data. An outdated tracker with everything stuck at "Applied" tells it nothing useful.

**Use the Project Library before resume sessions.** Run at least one project through extraction before your first Resume Reviewer session. The difference between "Built a fraud detection model" and a rewrite grounded in your actual numbers and tech is significant.

**Deadlines are urgent signals.** When you add a deadline to a job, the Career Coach reads it. Applications with deadlines within 14 days are flagged automatically in insights. Keep deadlines current.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Advice feels generic | Profile incomplete | Add resume text, goals, GPA, graduation |
| Prep agents not showing | No JD pasted | Go to Job Tracker → edit the job → Notes & JD tab → paste JD |
| Wrong company in prep agent | Wrong job selected | Use the "Preparing for" dropdown to switch |
| Resume Reviewer ignores my projects | Project Library empty | Add projects via 📚 Project Library |
| Coach doesn't mention deadlines | Deadline field empty | Edit the job → add deadline in YYYY-MM-DD format |
| Dashboard insight disappears | Normal — it used to | Now persists. Use ↺ Refresh to generate a new one. |
| Calendar features not working | Calendar not connected | Profile → Google Calendar → Connect |

---

## Quick Reference: Best First Prompt per Agent

| Agent | Best first prompt to run |
|-------|--------------------------|
| Career Coach | "Diagnose my pipeline. Where am I losing?" or "Should I apply to [Company]? Run a gap analysis." |
| Resume Reviewer | "Run a full review. Start with the 6-second scan, then do a JD keyword gap analysis." |
| Gap Identifier | "Give me the full gap analysis for this role. Should I apply now or close gaps first?" |
| Interview Coach | "Run a full mock round for this role. 4 questions. End with a hire/no-hire verdict." |
| Study Planner | "My interview is in [X weeks]. Build a study plan calibrated to that timeline." |
| Study Partner | "Explain [concept] to me. Start with why it exists." |
| Resume Synthesizer | "Categorize all my JDs and build a complete resume for the [category] intern role." |
| LinkedIn & Outreach | "Draft a LinkedIn connection request to a [role] at [Company]. I found them via [how]." |
