# CareerOS User Guide — Maximize Your Job Search

This guide shows you how to get the most out of CareerOS. The system has two layers: **Career Coach** (monitors everything) and **Job Preparation** (each job gets its own agents).

---

## How It Works

| Layer | Agents | Scope |
|-------|--------|-------|
| **Career Coach** | One global coach | Monitors all jobs, diagnoses your pipeline, builds strategy |
| **Job Preparation** | Resume · Gap · Interview · Study | **Each job has its own set** — switch jobs via the dropdown |

When you add a job and paste its JD, that job automatically gets its own Resume Reviewer, Gap Identifier, Interview Coach, and Study Planner. Use the **"Preparing for"** dropdown to switch between jobs.

---

## Step 1: Build Your Foundation (Do This First)

### Profile (Settings → My Profile)

| Field | Why It Matters |
|-------|----------------|
| **Name** | Used when agents talk to you |
| **Target Role** | Helps agents tailor advice |
| **Resume (full text)** | Paste your full resume — all preparation agents use this |
| **Goals & Current Situation** | Career Coach uses this for strategy and action plans |

**Tip:** Paste your resume as plain text. Formatting is less important than including experience, skills, projects, and education.

### Job Tracker

1. **Add every application** — even rejections. Career Coach uses your full pipeline for pattern recognition.
2. **Use all 6 status columns** — Wishlist → Applied → Phone Screen → Interview → Offer (or Rejected).
3. **Add Progress notes** — when you move a job, add a note. This helps the coach understand what's happening.
4. **Paste Job Descriptions (JD)** — go to the **Notes & JD** tab and paste the full job description. Jobs with JDs unlock their preparation agents.

---

## Step 2: Use Job Preparation — Pick a Job, Then Prepare

**Each job with a JD gets its own agents.** No more "which job am I preparing for?" confusion.

1. Add jobs in the **Job Tracker** and paste JDs in the **Notes & JD** tab.
2. Open **Resume Reviewer**, **Gap Identifier**, **Interview Coach**, or **Study Planner**.
3. Use the **"Preparing for"** dropdown to select the job you want to focus on.
4. Each job keeps its own chat history — switch jobs anytime without losing context.

**Example:** Preparing for Meta ML Engineer and Anthropic SWE? Add both jobs, paste both JDs, then switch between them in the dropdown. Each has its own Resume feedback, Gap analysis, Interview practice, and Study plan.

---

## Step 3: Connect Google Calendar (Optional but High-Value)

**Profile → Google Calendar → Connect**

Once connected, the **Career Coach** can:

- See your upcoming events
- Propose time slots that don't conflict
- Create events for study time, interview prep, and application deadlines

**Examples:**
- "Plan my week and block study time"
- "Add 2 hours of interview prep tomorrow at 2pm"
- "When am I free this week to work on applications?"

---

## Step 4: Use Each Agent Strategically

### Career Coach
**Sees:** Full profile + all jobs + all statuses + notes  
**Use for:** Strategy, patterns, bottlenecks, action plans, accountability

- Ask: "What's my biggest bottleneck?"
- Ask: "Build me a 30-day plan"
- Ask: "Why am I not getting interviews?" — the coach uses your tracker to spot patterns
- With Calendar: "Plan my week and block study time"

### Resume Reviewer / Gap Identifier / Interview Coach / Study Planner
**Sees:** Your resume + the job you selected in the dropdown  
**Use for:** Job-specific prep — each job has its own conversations

- Pick the job in **"Preparing for"**, then ask for reviews, fit scores, mock interviews, or study plans
- Switch jobs anytime — each keeps its own chat history

### Study Partner
**Sees:** Profile + job targets  
**Use for:** Explaining concepts, quizzing, interview-style answers (global, not per-job)

- "Explain transformers to me"
- "Quiz me on what I should know"
- "Help me understand RAG"

---

## Step 5: Recommended Workflow

```
1. Profile → Resume + Goals
2. Job Tracker → Add jobs, paste JDs, keep statuses current
3. Career Coach → Get pipeline analysis and 30-day plan
4. Pick a job in "Preparing for" → Gap Identifier (fit score)
5. Resume Reviewer → Tailor resume to that JD
6. Study Planner → Build a prep plan for that role
7. Interview Coach → Practice before interviews
8. Study Partner → Deep-dive into weak areas
```

Repeat steps 4–8 as you add new roles and move through the pipeline.

---

## Pro Tips

| Tip | Why |
|-----|-----|
| **Update statuses regularly** | Career Coach uses recency to spot patterns (e.g., "Your application rate dropped 3 weeks ago"). |
| **Add notes when changing status** | Extra context makes advice more relevant. |
| **Switch jobs via the dropdown** | Each job has its own agents — no need to re-paste or re-add. |
| **Be specific in Goals** | "Targeting ML Engineer at FAANG in 6 months, weak on system design" beats "Want a better job." |
| **Check the context bar** | Above the chat: ✅ Resume · ✅ Jobs · ✅ X jobs with JD. All green = best results. |

---

## Dashboard Quick Wins

- **Recent Applications** — quick overview of your pipeline.
- **Coach Insight** — click "Generate Insight" for a short, targeted take on your situation. Fill in profile and jobs first for best results.

---

## What Each Agent Does *Not* Know

- **Resume, Gap, Interview, Study** don't see each other's output. If Gap says "work on system design," tell Interview Coach explicitly.
- **Career Coach** doesn't see agent outputs. Summarize what others found if you want it factored in.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agents feel generic | Add resume, goals, and at least one JD. |
| "Add jobs and paste JDs" message | Paste a JD in the Notes & JD tab of at least one job. |
| Wrong company/role in prep agents | Use the **"Preparing for"** dropdown to select the correct job. |
| Calendar not working | Connect in Profile, ensure `google_credentials.json` is set up (see README). |
| Coach doesn't suggest times | Connect Google Calendar in Profile. |

---

## Summary

1. **Profile first** — resume, goals, target role.
2. **Track every job** — statuses and progress notes.
3. **Paste JDs** — each job with a JD gets its own preparation agents.
4. **Use the dropdown** — switch between jobs when using Resume, Gap, Interview, or Study.
5. **Connect Calendar** — for schedule-aware coaching.
6. **Keep data current** — update statuses and JDs as you go.

Career Coach monitors everything. Job Preparation is per-job — pick a job and prepare.
