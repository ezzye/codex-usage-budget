#!/usr/bin/env python3
"""Export local Codex token-usage metadata without retaining prompts or paths.

The collector needs only Python's standard library.  It reads JSONL session files
under CODEX_HOME (default: ~/.codex) and writes usage.json and usage.csv under
CODEX_USAGE_DATA_DIR (default: ~/Documents/Codex-Usage).
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import sqlite3
import tempfile
from zoneinfo import ZoneInfo

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
          "reasoning_output_tokens", "cache_write_input_tokens", "total_tokens")
CSV_FIELDS = ("record_id", "date", "project", "task", "model", "effort", "requests", *FIELDS,
              "basis", "computer", "image", "web", "agents")


def local_zone(name):
    if name.upper() == "LOCAL":
        return dt.datetime.now().astimezone().tzinfo
    return ZoneInfo(name)


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def since_value(value, zone):
    if value is None:
        now = dt.datetime.now(zone)
        return dt.datetime(now.year, now.month, 1, tzinfo=zone)
    if len(value) == 7:  # YYYY-MM
        value += "-01"
    parsed = parse_time(value)
    return parsed.replace(tzinfo=zone) if parsed.tzinfo is None else parsed.astimezone(zone)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def safe_title(value):
    """Make an opt-in title suitable for a spreadsheet; never keep full prompts."""
    lines = str(value or "").splitlines()
    text = " ".join(lines[0].split()) if lines else ""
    return text[:120] or "Untitled task"


def opaque_record_id(thread, local_date, model, effort):
    """A stable upsert key without exposing a thread identifier."""
    source = "\x1f".join((str(thread), str(local_date),
                            str(model or "Unknown"), str(effort or "Unknown")))
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


def project_name(cwd, project_map):
    canonical = os.path.normcase(os.path.realpath(cwd)) if cwd else ""
    mapped = project_map.get(canonical) or project_map.get(cwd)
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()[:120]
    name = pathlib.PurePath(cwd).name if cwd else ""
    return name[:120] or "Unmapped"


def token_values(usage):
    required = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
    if any(key not in usage for key in required):
        return None
    values = {key: usage.get(key, 0) for key in FIELDS}
    # All reported measurements must be non-negative numbers. Cache writes are
    # absent in some local event formats and are represented as zero only then.
    if any(not isinstance(value, (int, float)) or value < 0 for value in values.values()):
        return None
    return values


def parse_file(path, cutoff, zone, project_map, title="", include_titles=False, seen_responses=None):
    records, snapshots, tool_names = [], [], collections.defaultdict(set)
    thread = turn = ""
    cwd, model, effort = "", "Unknown", "Unknown"
    previous = dict.fromkeys(FIELDS, 0)
    precise_turns = set()
    seen_responses = seen_responses if seen_responses is not None else set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle):
            try:
                event = json.loads(line)
            except (TypeError, ValueError):
                continue
            payload, kind, timestamp = event.get("payload", {}), event.get("type"), event.get("timestamp", "")
            if not isinstance(payload, dict):
                continue
            try:
                when = parse_time(timestamp)
            except (TypeError, ValueError):
                continue
            if kind == "session_meta":
                thread, cwd = payload.get("id", thread), payload.get("cwd", cwd)
            elif kind == "turn_context":
                turn = payload.get("turn_id", turn)
                cwd = payload.get("cwd", cwd)
                model, effort = payload.get("model", model), payload.get("effort", effort)
            elif kind == "response_item" and payload.get("type") in ("function_call", "custom_tool_call"):
                tool_names[turn].add(str(payload.get("name", "")))
                # Inspect only fixed marker names; arguments are never saved.
                argument_text = payload.get("input", payload.get("arguments", ""))
                if isinstance(argument_text, str):
                    for marker in ("mcp__cua_repl", "image_gen__imagegen", "web__run", "spawn_agent"):
                        if marker in argument_text:
                            tool_names[turn].add(marker)
            if kind == "token_usage_record":
                usage = token_values(payload.get("usage", {}))
                record_turn = payload.get("turn_id", turn)
                response_key = payload.get("response_id")
                # Deduplicate retained/rotated JSONL copies by response ID.
                if usage and when >= cutoff:
                    precise_turns.add(record_turn)
                    if response_key and response_key in seen_responses:
                        continue
                    if response_key:
                        seen_responses.add(response_key)
                    precise_turns.add(record_turn)
                    records.append((record_turn, when, model, effort, usage, "Response usage", False))
            elif kind == "event_msg" and payload.get("type") == "token_count":
                total = (payload.get("info") or {}).get("total_token_usage")
                if isinstance(total, dict):
                    current = token_values(total)
                    if current:
                        reset = any(current[key] < previous[key] for key in FIELDS)
                        delta = {key: current[key] - (0 if reset else previous[key]) for key in FIELDS}
                        previous = current
                        if when >= cutoff and delta["total_tokens"] > 0 and turn not in precise_turns:
                            records.append((turn, when, model, effort, delta,
                                            "Legacy cumulative delta; coverage uncertain", True))
    output = []
    for record_turn, when, record_model, record_effort, usage, basis, is_legacy in records:
        if is_legacy and record_turn in precise_turns:
            continue
        names = tool_names[record_turn]
        local_date = when.astimezone(zone).date().isoformat()
        row = dict(date=local_date,
                   record_id=opaque_record_id(thread, local_date, record_model, record_effort),
                   project=project_name(cwd, project_map), model=record_model or "Unknown",
                   effort=record_effort or "Unknown", basis=basis, **usage,
                   computer=any("cua" in x or "computer" in x for x in names),
                   image=any("imagegen" in x or "image_gen" in x for x in names),
                   web=any("web__run" in x for x in names),
                   agents=any("spawn_agent" in x for x in names))
        row["task"] = safe_title(title) if include_titles else "Task " + row["record_id"][:8]
        output.append(row)
    return output, snapshots


def session_paths(codex_home):
    paths = set()
    for folder in ("sessions", "archived_sessions"):
        base = codex_home / folder
        if base.exists():
            paths.update(base.rglob("*.jsonl"))
    return sorted(paths)


def session_titles(codex_home):
    """Read local title metadata transiently, only for --include-titles."""
    database = codex_home / "state_5.sqlite"
    if not database.exists():
        return {}
    try:
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            return {str(path): title for path, title in connection.execute(
                "SELECT rollout_path, title FROM threads WHERE rollout_path IS NOT NULL") if isinstance(title, str)}
    except sqlite3.Error:
        return {}


def aggregate(records, include_titles=False):
    groups = {}
    for row in records:
        key = row["record_id"]
        group = groups.setdefault(key, {key: row[key] for key in ("record_id", "date", "project", "model", "effort", "task")})
        group.setdefault("bases", set()).add(row["basis"])
        group.setdefault("requests", 0)
        group["requests"] += 1
        for field in FIELDS:
            group[field] = group.get(field, 0) + row[field]
        for field in ("computer", "image", "web", "agents"):
            group[field] = bool(group.get(field, False) or row[field])
    rows = []
    for group in groups.values():
        group["basis"] = "; ".join(sorted(group.pop("bases")))
        rows.append(group)
    return sorted(rows, key=lambda row: (row["date"], row["project"], row["model"]))


def csv_value(value):
    """Neutralize spreadsheet formula interpretation in user-controlled strings."""
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def write_csv(path, rows, include_titles=False):
    fields = CSV_FIELDS
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{key: csv_value(value) if isinstance(value, str) else value
                          for key, value in row.items()} for row in rows])
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def load_project_map(path):
    if not path:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in raw.items()):
        raise ValueError("project map must be a JSON object mapping CWD strings to project names")
    return raw


def collect(codex_home, data_dir, cutoff, zone, project_map, include_titles=False):
    records, seen_responses = [], set()
    titles = session_titles(codex_home) if include_titles else {}
    for path in session_paths(codex_home):
        parsed, _ = parse_file(path, cutoff, zone, project_map, titles.get(str(path), ""), include_titles, seen_responses)
        records.extend(parsed)
    rows = aggregate(records, include_titles)
    data = {"asof": dt.datetime.now(dt.timezone.utc).isoformat(), "since": cutoff.isoformat(),
            "timezone": str(zone), "rows": rows, "records": len(records), "files": len(session_paths(codex_home))}
    atomic_json(data_dir / "usage.json", data)
    write_csv(data_dir / "usage.csv", rows, include_titles)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="YYYY-MM (default: current month) or ISO date/time")
    parser.add_argument("--timezone", default="local", help="IANA zone, local (default), or UTC")
    parser.add_argument("--codex-home", type=pathlib.Path, default=pathlib.Path(os.environ.get("CODEX_HOME", pathlib.Path.home() / ".codex")))
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path(os.environ.get("CODEX_USAGE_DATA_DIR", pathlib.Path.home() / "Documents" / "Codex-Usage")))
    parser.add_argument("--project-map", type=pathlib.Path, help="JSON mapping from CWD to friendly project name")
    parser.add_argument("--include-titles", action="store_true", help="include sanitized first-line task titles in exports")
    parser.add_argument("--collect-only", action="store_true", help="compatibility flag; collection is always local-only")
    args = parser.parse_args()
    zone = local_zone(args.timezone)
    data = collect(args.codex_home, args.data_dir, since_value(args.since, zone), zone,
                   load_project_map(args.project_map), args.include_titles)
    print(json.dumps({key: data[key] for key in ("asof", "records", "files")}))


if __name__ == "__main__":
    main()
