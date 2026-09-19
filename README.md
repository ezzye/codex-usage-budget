# Codex Usage Budget

A Codex skill for **least-expensive-good-enough (LEGE)** planning, local usage tracking, and project value reviews. Budget the complete deliverable before work, choose an economical suitable model, and compare measured work with useful results.

This is a planning and reporting aid, not a billing meter or enforced spending limit. It cannot change the model already running your task. Delegation depends on the models and tools available in your Codex session.

## Install

Requires Python 3.9+ and macOS or Linux for the collector. No Python packages, API keys, or Node runtime are required. The repository is public and MIT licensed.

```sh
git clone https://github.com/ezzye/codex-usage-budget.git
cd codex-usage-budget
./install.sh
```

The skill installs to `$CODEX_HOME/skills/codex-usage-budget`, or `~/.codex/skills/codex-usage-budget`. Start a new Codex task, then say:

> Use $codex-usage-budget to budget this project before starting. Define the finished result, token range, active hours, model choices, acceptance evidence and stop limits.

To request this behavior for every task on this installation:

```sh
./install.sh --always
```

`--always` adds one managed block to the Codex home `AGENTS.md`, preserving other instructions. It authorizes bounded economical delegation and exempts extra planning when its overhead would equal or exceed direct work. It does not change your default model, create an automation, or configure other computers. Instructions cannot guarantee execution in every client or override higher-priority policies.

Existing skill installations are backed up under `$CODEX_HOME/usage-budget-backups/` before replacement. This includes customized personal versions: review the backup before retiring it. To test elsewhere, use `./install.sh --codex-home /tmp/my-codex-test --always`. Re-running updates the skill without duplicating the managed instruction block.

## Enable budgeting for every task

The skill name is `codex-usage-budget`. Invoke it explicitly in Codex with `$codex-usage-budget`.

| Scope | Instruction file |
| --- | --- |
| All Codex projects on this installation | `~/.codex/AGENTS.md` (or `$CODEX_HOME/AGENTS.md`) |
| One Codex repository | `AGENTS.md` in that repository |
| All Claude Code projects | `~/.claude/CLAUDE.md` |
| One Claude Code repository | `CLAUDE.md` in that repository |

Use `AGENTS.md` with the final **S**. For Codex, `./install.sh --always` adds the standing instruction automatically; no system-prompt change is needed. Start a new session after installation. If `AGENTS.override.md` exists in the Codex home, it takes precedence over the ordinary global file; add the instruction there instead if appropriate.

A concise standing instruction is:

> Before every task, read and apply the installed codex-usage-budget/SKILL.md. Reuse a valid project budget; otherwise budget the whole deliverable using the least-expensive-good-enough route. Skip extra planning or delegation when its overhead would equal or exceed the task cost. Preserve required verification and batch completion logging.

Include the actual installed file path when placing this instruction in another agent's configuration. Claude Code can follow the planning guidance, but this package's installer, quota tools and usage collector target **Codex**. It does not measure Claude usage or install a native Claude skill. Cross-agent support requires an adapted collector and model/tool mapping; a CLAUDE.md entry alone does not provide those capabilities.

Official references: [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Claude Code CLAUDE.md](https://code.claude.com/docs/en/memory).

## Google Sheets setup

The repository contains **no personal spreadsheet, credentials or usage history**. Each person supplies their own tracker and enables a Google Sheets/Drive connection in Codex. The scripts collect local data; Codex uses that connection to update Sheets. There is no unattended Google API client in this package.

Ask Codex:

> Use $codex-usage-budget to create my private Google Sheets tracker with Task log, Project budgets, Monthly statement, Account limits and Settings tabs. Use the logging reference for the schema. Record the tracker location locally. Ask for my subscription amount and billing date rather than assuming them. Keep owner reviews separate from measured usage.

The skill's [logging reference](skill/references/logging.md) defines setup, safe updates and monthly reporting. You can instead import the CSV into any spreadsheet. Review the export before upload: project labels and optional task titles can reveal private work.

## Collect usage locally

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-usage-budget/scripts/collect.py"
```

Defaults to the current month. Run `--help` for date, timezone, project mapping and title options. Set `CODEX_USAGE_DATA_DIR` to choose a private output directory outside this repository; set `CODEX_HOME` to select the local Codex records. `--collect-only` is a compatibility flag; both JSON and CSV exports are local-only.

The collector produces `usage.json` and `usage.csv` in `~/Documents/Codex-Usage` by default. Exports omit task titles by default; `--include-titles` explicitly includes bounded titles. Source Codex records contain private content: do not commit or share them. No network requests are made by the collector.

Cached input is a subset of input, and reasoning output is a subset of output: do not count them twice. New response records are deduplicated; older cumulative records and forks have lower confidence. The collector reads retained local, version-dependent Codex records and may need updates when their format changes. It rescans retained sessions and does not preserve records deleted from your Codex history. The default local timezone is the current UTC offset; select an IANA zone (for example `--timezone Europe/London`) for daylight-saving-aware historical dates. Other hosts, missing records, image charges, and speed surcharges may be absent. A task's final response appears on the next refresh.

## What gets budgeted

- The complete usable deliverable, including coordination, verification and likely retries.
- Token ranges by model, cached-input assumptions, active hours and separate waiting time.
- Milestones, a 75% reforecast point, and a ceiling that triggers preservation and replanning.
- Technical delivery evidence and the owner's separate judgement of usefulness.

Use existing plans when scope and remaining budget fit. Do small tasks directly when planning or delegation would cost more. Cheap model selection must consider total work and retries, not just its per-token price. No model prices are hardcoded here: use current official rates and preserve the date and assumptions of each estimate.

Subscription quota percentages, tokens, comparison credits and dollars are different measures. Do not convert between them without a supported basis. An illustrative allocation of a monthly fee across observed usage is **not actual per-project billing**. Account quota snapshots can include concurrent work and resets; missing measurements remain unavailable.

## Monthly review

Ask Codex to refresh the requested calendar month, summarize usage by project/model, compare budgets with actuals, and identify delivered outcomes versus owner-rated value. Supply the subscription renewal date separately from the weekly quota reset date. For recurring reports, explicitly ask Codex to create a monthly automation; installing this skill does not schedule one.

## Update, test, remove

```sh
git pull --ff-only
./install.sh --always
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skill/scripts -p 'test_*.py' -v
```

To remove it, delete only the installed `skills/codex-usage-budget` folder and the block between `<!-- codex-usage-budget:start -->` and `<!-- codex-usage-budget:end -->` in your Codex home `AGENTS.md`. Keep your tracker and usage data, or remove them separately if desired. Restore a saved skill/AGENTS.md backup to roll back an upgrade.

## Package scope

This portable edition includes the planning skill, stdlib collector, CSV export, installer and connector workflow. The original personal workbook renderer and machine-specific synchronization scripts are deliberately excluded because they depend on a private tracker and bundled runtime. Native Sheets formatting and formulas are created through the connected Codex tools during setup.

## License

MIT; see [LICENSE](LICENSE).
