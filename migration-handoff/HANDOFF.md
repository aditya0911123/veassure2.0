# Handoff: Hard Gates + Extraction as Tools for an Orchestrator Agent

## Context / what you're being asked to do

This folder contains two pieces of **deterministic, non-LLM Python code**, copied
byte-for-byte from a working ingestion pipeline (VeAssure 2.0 Ingestion
Service). Your job is to wrap them as **tools** callable by a main
orchestrator agent, built with **DeepAgents / LangChain**.

Do **not** change their internal logic. They are finished, tested, and their
behavior is intentionally specific (see the docstrings in each file — they
explain *why*, not just *what*). Your work is integration: give each one a
tool wrapper (name, description, JSON-schema-ish args, and a thin function
that calls into this code and returns a tool-friendly result) so the
orchestrator LLM can invoke them as steps in a larger agentic flow. If you
think the internals genuinely need to change to fit the new system (e.g. to
stop writing to stdout, or to accept in-memory bytes instead of a file path),
ask before doing it — don't silently rewrite the deterministic logic.

The two pieces are meant to run **in sequence**: Hard Gates first (gate on a
raw swagger/OpenAPI file), then Extraction second (only if gates pass).
Both are pure/deterministic — no network calls to an LLM, no randomness.
Given the same input file, they always produce the same output.

## Piece 1: Hard Gates (`ingestion_service/hard_gates.py`)

**Purpose:** Decide whether a swagger/OpenAPI spec file is even safe to
proceed with, before any extraction happens. Three sequential checks
("gates"). If any gate fails, everything downstream must stop — this is a
hard stop, not a warning.

**Entry point:** `run_hard_gates(swagger_path: Path) -> GateResult`

- **Input:** a `pathlib.Path` to a swagger/OpenAPI JSON file on disk.
- **Output:** a `GateResult` dataclass:
  - `file_parsing_pass: bool`
  - `version_pass: bool`
  - `spec_validation_pass: bool`
  - `warnings: list[str]`
  - `errors: list[str]`
  - `spec: dict | None` — the parsed JSON document (only set if gate 1 passed)
  - `overall_pass` (property) — `True` only if all three gates passed
- **Side effects:** none. Nothing is written to disk. It reads the one input
  file and returns a result object. (There's also `format_report(result) ->
  str` which renders a human-readable PASS/FAIL report — currently used for
  terminal printing, but it's just a pure string formatter, safe to reuse for
  a tool's return message.)

**What each gate actually checks:**

1. **Gate 1 — File Parsing.** The file must exist, be readable, valid UTF-8,
   and parse as JSON whose top-level value is an object. Any failure here
   (file not found, bad encoding, invalid JSON, non-object root) is fatal and
   stops immediately — gates 2 and 3 never run.
2. **Gate 2 — OpenAPI Version.** The document must declare either
   `"swagger": "2.0"` or an `"openapi"` field matching `3.0.x` or `3.1.x`.
   Anything else (missing field, unsupported version) is fatal.
3. **Gate 3 — OpenAPI Spec Validation.** Runs the real
   `openapi-spec-validator` library against the document (choosing the
   validator class for the detected version). Two important nuances:
   - Broken/unresolvable `$ref`s are **not** fatal — they're collected as
     entries in `warnings`, and the spec is patched (broken refs replaced
     with `{}`) so the validator can actually finish running instead of
     crashing on an unresolvable pointer.
   - Any *other* spec violation (genuine schema violations the validator
     finds) is fatal and goes into `errors`.
   - If the validator library itself throws (not a $ref issue, an internal
     failure) that also counts as a fatal Gate 3 failure.

**Tool-wrapping notes:**
- This is a natural single tool: `run_hard_gates_tool(path: str) -> {pass: bool, errors: [...], warnings: [...], report: str}`.
- The orchestrator should treat `overall_pass == False` as a signal to stop
  the pipeline for this document and surface `errors` to the user/agent —
  do not proceed to extraction.
- Dependency: `openapi-spec-validator>=0.7` (see `requirements.txt`).

## Piece 2: Extraction (`extractor/` package)

**Purpose:** Given a swagger/OpenAPI file (that has already passed Hard
Gates), deterministically pull out a clean, structured representation:
metadata, security config, endpoints, and schemas — with `$ref`s resolved
but *not* inlined (they collapse to bare schema names, preserving identity,
e.g. a property typed `Pet` stays `"Pet"` rather than being expanded into an
anonymous object).

> **New-system note — drop user stories from this tool.** In the original
> code, `run_extraction()` also accepted an optional `userstories_path` and
> put its raw text into `extracted_data["user_stories"]`. **In the new
> system, don't wire that up.** User stories are going to a separate
> business-requirements agent instead — this extraction tool should only
> ever be called with the spec file. When you wrap `run_extraction()` as a
> tool, either pass `userstories_path=None` always and ignore/drop the
> `user_stories` key from the tool's result, or (cleaner) strip the
> parameter and that dict key out of this copy entirely. Either way, the
> tool's contract to the orchestrator should not include a user-stories
> input at all.

**Entry point:** `run_extraction()` in `extractor/main.py`:

```python
def run_extraction(
    swagger_path: Path,
    userstories_path: Path | None,
    on_prance_resolved: Callable[[dict], None] | None = None,
) -> tuple[dict, dict, dict[str, bool], list[dict[str, str]]]
```

- **Inputs:**
  - `swagger_path` — path to the same swagger/OpenAPI file that passed Hard
    Gates.
  - `userstories_path` — optional path to a plain-text user stories file; if
    `None`, that section of the output is just `None`. **Not used in the new
    system** — see the note above; always pass `None` (or remove the
    parameter) since a separate business-requirements agent owns user
    stories now.
  - `on_prance_resolved` — optional callback, invoked once with the fully
    `prance`-resolved spec document. Used by the original CLI to save a
    debug artifact (`prance_resolved_swagger.json`); can be omitted entirely
    for a tool wrapper if that intermediate isn't needed.
- **Output:** a 4-tuple `(extracted_data, raw_spec, ref_status, broken_refs)`:
  1. `extracted_data: dict` — the actual deliverable, with keys `metadata`,
     `security`, `endpoints`, `schemas`, `user_stories`. This is what you'd
     normally serialize as `extracted_data.json`. (`generate_markdown(data)`
     from `extractor/md_generation.py` turns this same dict into a
     human-readable Markdown mirror — also pure/deterministic, no I/O.)
  2. `raw_spec: dict` — the original parsed spec, unmodified.
  3. `ref_status: dict[str, bool]` — every distinct `$ref` string found in
     the document, mapped to whether it resolved successfully.
  4. `broken_refs: list[dict]` — full detail of every broken/unresolvable ref
     and every schema-name naming conflict encountered, each entry shaped
     like `{"type": "unresolvable"|"naming_conflict"|"depth_guard", "path":
     ..., "ref": ..., "reason": ...}`. **This is deliberately not baked into
     `extracted_data`** — at a usage site a broken/conflicting ref just
     collapses to `{}` there, indistinguishable from a genuinely empty
     schema. This list is the only place that detail survives, and it exists
     specifically so a downstream consumer (originally: a validation agent)
     can fold it into a report. If your orchestrator has a validation step,
     this is the artifact to hand it.
- **Side effects:** none beyond `print()` progress lines (safe to ignore/redirect)
  and whatever `on_prance_resolved` does if you pass one. It reads the two
  input files; it does not write anything itself.

**Key behavior to preserve (don't "simplify" these away):**
- `$ref` resolution covers both internal (`#/...`) and external (other files/
  URLs) refs, resolved via `prance`, with external fetches bounded by a
  10-second timeout on a daemon thread so a hung network call can't block
  extraction.
- A resolvable `$ref` to a named schema collapses to that schema's bare name
  string at every usage site (never inlined). An unresolvable ref, or one
  that lost a naming conflict against another schema of the same name,
  collapses to `{}` instead — with the *why* recorded only in `broken_refs`.
- Two external refs (or an external ref and an internal schema) can resolve
  to the same trailing name; `resolve_external_schema_placements()` decides
  who "wins" that name (internal always wins; otherwise first occurrence in
  document order), and the loser is flagged as a naming conflict.
- Recursion/cycles are guarded (`_MAX_MERGE_DEPTH = 200` in
  `ref_resolution.py`) since a schema can legitimately self-reference.

**Files in `extractor/` and what each owns:**
- `main.py` — `run_extraction()` is the pure function to call as a tool.
  **Note:** the original source file also had an interactive CLI
  `main()`/`if __name__ == "__main__"` (prompted for a project via
  `ingestion_service.project_picker`, ran hard gates, wrote
  `extracted_data.json`/`.md` to disk). That CLI wiring — and the now-unused
  `project_picker` module it depended on — was **intentionally stripped
  from this handoff copy** so there's nothing here that implies a human
  needs to pick a project interactively. Your orchestrator supplies the
  input path itself and decides what to do with the result. `run_extraction()`
  is the only thing meant to be wrapped as a tool.
- `ref_resolution.py` — all `$ref` resolution logic (see module docstring
  inside the file for the full mechanism; it's dense and deliberate, read it
  before touching anything here).
- `schema_extraction.py` — builds the `schemas` section.
- `endpoint_extraction.py` — builds the `endpoints` section.
- `md_generation.py` — pure `dict -> Markdown string` renderer for the
  extracted data, if a human-readable artifact is still wanted downstream.
  Not called automatically by anything in this folder — call
  `generate_markdown(extracted_data)` yourself if you want that artifact.

## Suggested tool shapes for the orchestrator

Two tools, run in sequence, is the natural mapping:

1. `check_hard_gates(swagger_path: str) -> dict` — wraps `run_hard_gates()`.
   Returns pass/fail + errors/warnings. Orchestrator halts this document's
   pipeline on failure.
2. `extract_spec_data(swagger_path: str) -> dict` — wraps `run_extraction()`,
   called only after gate 1 passes. No `userstories_path` argument — per the
   note above, user stories are handled by a separate business-requirements
   agent in this system, not by this tool. Returns `extracted_data` (and
   probably `broken_refs`, for a later validation step to consume) as the
   tool result.

Both tools are safe to call with plain string paths from the LLM side; just
convert to `Path` at the boundary.

## Dependencies

See `requirements.txt` in this folder:
```
openapi-spec-validator>=0.7
prance>=23.6
```
Install these in whatever environment hosts the orchestrator/tools.

## Source of truth

This code was copied from a working repo (VeAssure 2.0 Ingestion Service,
`ingestion_service/` and `extractor/` packages) on 2026-09-18. If anything
here is ambiguous, the module docstrings in each file are authoritative —
they were written specifically to capture non-obvious design decisions
(why refs aren't inlined, why external fetches are threaded, why broken refs
aren't written into the main output, etc.). Read those before changing
behavior.
