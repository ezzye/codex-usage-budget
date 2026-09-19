# Tracker setup and completion logging

Read this for setup or a worthwhile batched refresh. Use the configured data directory (`CODEX_USAGE_DATA_DIR`, otherwise the collector's documented default). If `tracker.json` is absent, collect locally until the user chooses a tracker. Do not infer permission to upload private data from merely installing the skill. A request to create/use a tracker authorizes relevant routine updates; never change sharing settings without authorization.

Store only the chosen spreadsheet ID/URL and tab IDs in local `tracker.json`, outside the repository. Use an available connected Google Sheets/Drive tool and its applicable skill. Create a private tracker when requested; otherwise read the selected spreadsheet first. No credentials belong in the configuration.

## Native tab schema

- **Task log:** Record ID, Date, Project, Task, Model, Reasoning effort, Computer use, Image generation, Web research, Agents, Requests, Input tokens, Cached input, Output tokens, Reasoning tokens, Cache-write tokens, Total tokens, Measurement basis, Plan ID, Estimated comparison credits, Delivery status, Owner value, Hours saved, Review notes, Evidence.
- **Project budgets:** use the A:V schema in [lege.md](lege.md). Add model/cache assumptions and estimate dates in Estimate basis. Unknown credits stay blank; token ranges remain useful.
- **Settings:** reporting month, subscription amount/currency, confirmed billing date, reserve preference, optional dated per-model comparison rates and project budgets. A weekly reset does not establish a billing date.
- **Account limits:** capture time, bucket/model scope, window duration, used percentage, remaining percentage, reset time, measurement source. Missing data is unavailable, never zero.
- **Monthly statement:** selected-month project and model totals; budget versus actual; outcome/value counts; coverage gaps; latest independent quota windows. Reference Task log/Project budgets with formulas or a verified pivot, not fabricated totals.

Use header rows, frozen headings, number/date formats and filters. Delivery choices: Not reviewed, In progress, Delivered, Blocked, Cancelled. Owner value choices: Unreviewed, Good value, Mixed value, Poor value. Leave hours saved blank until reviewed. Empty months should show zero measured totals with an explicit no-records status, not an error or invented value.

## Refresh

1. Run the local collector once; it never uploads. Use exports as measured metadata, not transcripts. Titles are opt-in because local titles may derive from user prompts. Review project labels before first upload. Keep raw caches local.
2. Read native metadata, existing records and owner-review columns in bounded ranges. Match by opaque Record ID; stop on duplicate IDs or conflicting edits. Serialize updates to a tracker and re-read before writing if another task may be editing it.
3. Append new IDs and update only changed measured fields for existing IDs. Preserve Plan ID, reviews, hours saved, evidence, original estimates, Settings controls and historical rate assumptions. Read-only existing formulas must not be replaced with values. Missing local history is not permission to delete cloud rows.
4. Price only with verified dated rates. Cached input is included in input; reasoning is included in output. Unknown models/cache-write pricing remain unpriced. Do not infer per-task quota consumption from account-wide snapshots. Label any subscription fee allocation illustrative and state the observed coverage.
5. Map actual work to its plan using explicit turn/response IDs or baseline deltas from local records; daily aggregated exports alone cannot isolate two plans in the same task/day. Never assign the entire historical project to a new plan. Union concurrent execution intervals for active hours; unmeasured time remains unavailable.
6. Write imported text as literal string values, never interpreted spreadsheet formulas. Apply bounded updates using native connector operations, inspect every response, then read back modified records, reviews, formulas, totals and filter/table coverage. A local export is not a completed cloud update. On failure retain pending local data and report the limitation.

Only retain account-limit fields from quota tools, never account IDs or credentials. Remaining percentage is `max(0, 100-usedPercent)` for each independent bucket/window. A reset invalidates simple before/after subtraction. Do not sum overlapping windows.

For monthly statements select the requested month, include failed work as cost, and compare technical results with owner acceptance. Do not invent value or hours saved. Installation does not schedule reports; use the app's automation tool if the user asks for a recurring statement. Batch logging overhead and include it in the project's costs.
