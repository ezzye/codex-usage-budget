---
name: codex-usage-budget
description: Plan Codex work using least-expensive-good-enough (LEGE) budgets, then record measured usage in the user's Google Sheets tracker. Use before project execution and at task completion under the standing logging instruction, or for usage-budget requests.
---

# Codex usage budget

Read local `tracker.json` in the usage data directory if configured. Never assume a tracker URL, account, subscription price, or billing day. Without a tracker, retain local usage and provide the setup instructions.

Use a brief LEGE plan before executing a concrete project deliverable. Reuse an existing applicable plan; do not create a second planner. The planner budgets the whole deliverable to completion, with a provisional usage range and elapsed agent hours, success evidence, milestone caps, and stop/replan conditions. Present the estimate before work, then proceed within it. At 75%, reforecast. At the ceiling, save the partial result and request a larger budget only if necessary. Keep the original estimate immutable and record later versions separately.

Separate project, task, actual hours saved, elapsed agent hours, and waiting time; include coordination and child costs. Activity and technical checks do not establish usefulness: record delivery evidence and owner acceptance separately.

Use the cheapest suitable available model: for example an available low-cost model for a short planner and a suitable economical model for implementation. More expensive models require a justified difficult/high-risk slice. A parent-selected model cannot be changed by this skill. Independent bounded subtasks may be delegated alongside useful local work with an explicit model, minimal brief, no recursive planning/delegation, and bounded evidence returned. Do not create an agent for serial work. If material cost cannot be reduced in the current root session, recommend a cheaper root session. Do not invent quota/token conversions, claim hard technical enforcement, or automatically purchase credits.

First apply a minimal overhead check, including to trivial tasks. Reuse the current project plan when the task is within its remaining scope and budget. Skip extra planning/delegation and defer cloud logging when their incremental overhead would cost at least as much as completing the work directly. Never skip verification needed for the task itself. Use deterministic local collection and batch deferred entries into the next worthwhile refresh. Record the exemption reason in the next existing log, not a separate planning task. If cost is uncertain, use a short provisional range rather than a second estimator. Do not recursively apply this preflight to planners or logging. Tool-goal budgets do not cap ordinary tasks; use them only for an explicitly requested goal.

The parent creates and maintains the `Project budgets` Google Sheet tab. Each plan records Plan ID, scope, success criteria, planner/executor, usage-range inputs and cache/output assumptions, credits and elapsed-hour estimates, opening quota snapshot, actual totals and elapsed time, status, acceptance, and evidence. Credit forecasts require dated, verified rates supplied by the user or official documentation; otherwise record token ranges and leave credits unavailable.

At completion, record usage with low overhead and preserve user reviews. Follow [references/logging.md](references/logging.md). Follow [references/lege.md](references/lege.md) for budget and delegation detail.
