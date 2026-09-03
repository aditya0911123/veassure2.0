"""$ref handling for the extractor.

Several concerns live here:

1. compute_ref_status() - the single place resolvability is actually
   determined, for every DISTINCT $ref in the document, exactly once, via
   ONE mechanism (_fetch_ref_value) used for both internal and external
   refs alike - prance's own fetch/parse/pointer utilities. An internal
   '#/...' ref resolves against the base document itself (fetched once,
   cached thereafter, so no repeated disk I/O); an external ref (a local
   file path or a remote URL, with or without a '#/json/pointer'
   fragment) genuinely reads the file or makes the HTTP request. Any
   failure (a pointer segment that doesn't exist, file not found,
   unreachable host, HTTP error, network error, malformed document) marks
   it unresolvable; nothing else does. The only thing that still differs
   between the two ref kinds is timing, not mechanism: an internal ref
   can never hang (no network, cached after the first call) so it
   resolves immediately with no threading involved, while an external ref
   is wrapped in a bounded, daemonized worker thread, since prance/
   requests set no socket timeout internally and a hung connection must
   not be able to block extraction (or the process exiting) forever.
   Every other function below is handed the resulting ref -> resolved?
   dict rather than re-deciding resolvability itself, so every part of
   the pipeline (JSON extraction, the broken-ref pre-scan, the MD
   affected-endpoints computation) agrees on the same answer for the same
   ref, and an external target is only ever actually fetched once even if
   many places in the document reference it.

2. resolve_with_prance() - patches only the refs compute_ref_status found
   broken, then resolves the rest (internal AND external - RESOLVE_ALL)
   with prance's RefResolver directly (not ResolvingParser/BaseParser -
   those also run an OpenAPI meta-schema validation pass after resolving,
   which is Hard Gates' job, not extraction's, and which independently
   blows the recursion limit on the exact same bare-self-ref schemas
   already being guarded against here), configured to stop at recursion
   limits by leaving a $ref in place rather than raising.

3. build_clean_view() - the "clean internal format" builder. Walks the RAW
   spec (never the resolved one) as the structural driver: wherever raw
   holds a bare {"$ref": "..."} that compute_ref_status found resolvable,
   it's collapsed to that component's bare name string - never inlined,
   never rendered as an anonymous object, regardless of whether the
   target was internal, a local file, or a remote URL. A broken $ref
   keeps its raw {"$ref": "...", "unresolvable": true} form (warnings for
   these are reported once, comprehensively, by resolve_with_prance's
   whole-document pre-scan - not re-logged per occurrence here).
   Everything else (plain inline structure with no $ref at that position)
   is copied from the RESOLVED spec instead, so accuracy of
   nested/derived content still benefits from prance's resolution.
   Recursion stops the instant a $ref is found - the walker never follows
   a ref's target, so a schema cycle (even a bare self-reference) cannot
   cause infinite recursion here.

4. resolve_external_schema_placements() - a successfully-resolved
   EXTERNAL ref's target name (e.g. 'Widget' from
   'other-file.json#/components/schemas/Widget') gets its actual fetched
   content added to the schemas section under that name too, not just
   collapsed to a bare-name reference at each usage site - otherwise
   there'd be nothing anywhere defining what that name means. Since two
   different external refs (or an external ref and an internal schema)
   can legitimately resolve to the same trailing name, this decides who
   wins that name (first occurrence in document order; an internal schema
   always wins over any external one) and flags every losing ref as a
   naming conflict. build_clean_view renders a losing ref's usage sites
   as an {"unresolvable": true, "reason": ...} placeholder rather than a
   bare name, since collapsing it to a name that actually belongs to a
   different schema would be actively misleading.
"""

from __future__ import annotations

import threading
from typing import Any

from prance.util import path as prance_path
from prance.util import resolver as prance_resolver
from prance.util import url as prance_url
from prance.util.resolver import RefResolver

_MAX_MERGE_DEPTH = 200
_EXTERNAL_REF_TIMEOUT_SECONDS = 10


def ref_target_name(ref: str) -> str:
    """Trailing name segment of a $ref pointer, e.g.
    '#/components/schemas/Pet' -> 'Pet', or
    'https://example.com/schemas/common.json#/Address' -> 'Address'."""
    return ref.rstrip("/").rsplit("/", 1)[-1]


def _fetch_ref_value(ref: str, base_url: str, cache: dict[Any, Any]) -> Any:
    """Resolve and return the value ANY $ref points to - internal
    ('#/...', resolved against the base document itself) or external (a
    local file or a remote URL) - via prance's own fetch/parse/pointer
    utilities. This is the single mechanism underlying both; there is no
    separate hand-rolled path for internal refs. Raises on any failure: a
    pointer segment that doesn't exist, a file that isn't there, an
    unreachable host, an HTTP error, or a malformed document. The base
    document itself is fetched (read + parsed) once and cached under its
    own URL, so every internal ref after the first is a cache hit with no
    further disk I/O."""
    ref_url, obj_path = prance_url.split_url_reference(base_url, ref)
    contents = prance_url.fetch_url(ref_url, cache, None, True)
    if obj_path:
        return prance_path.path_get(contents, obj_path)
    return contents


def resolve_external_ref_value(ref: str, base_url: str, cache: dict[Any, Any]) -> Any:
    """Return the resolved value for an external $ref already confirmed
    resolvable by compute_ref_status. Reuses the shared fetch cache, so
    this is a cache hit (no new network/file I/O) rather than a
    re-fetch - used by schema_extraction to harvest the actual schema
    body for a successfully-resolved external ref."""
    return _fetch_ref_value(ref, base_url, cache)


def _resolve_ref_now(ref: str, base_url: str, cache: dict[Any, Any]) -> bool:
    """Resolve an internal '#/...' ref immediately, with no timeout
    guard. This never performs network I/O, and after the very first call
    in a given compute_ref_status pass it never even touches disk again -
    the base document is cached on its first fetch - so there is nothing
    here that can hang, and wrapping it in the timeout machinery used for
    external refs would only add pointless overhead."""
    try:
        _fetch_ref_value(ref, base_url, cache)
        return True
    except Exception:
        return False


def _resolve_ref_with_timeout(ref: str, base_url: str, cache: dict[Any, Any]) -> bool:
    """Resolve an external ref (a local file or a remote URL), bounded by
    _EXTERNAL_REF_TIMEOUT_SECONDS. Runs on a daemon thread: prance sets no
    socket timeout on its own HTTP fetches, so a genuinely hung connection
    has no clean way to be cancelled mid-flight - a daemon thread lets
    this function give up and return promptly without that stuck thread
    blocking the rest of extraction, or later blocking the process from
    exiting the way a non-daemon thread pool worker would."""
    outcome: dict[str, bool] = {}

    def worker() -> None:
        try:
            _fetch_ref_value(ref, base_url, cache)
            outcome["ok"] = True
        except Exception:
            outcome["ok"] = False

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=_EXTERNAL_REF_TIMEOUT_SECONDS)
    return outcome.get("ok", False)


def compute_ref_status(raw_spec: dict[str, Any], base_url: str) -> tuple[dict[str, bool], dict[Any, Any]]:
    """Resolve every distinct $ref in the document exactly once, via
    _fetch_ref_value - the single prance-based mechanism used for both
    internal and external refs, replacing what used to be two separate
    implementations (a hand-rolled in-memory pointer walk for internal
    refs, prance's fetch utilities for external ones). The only thing
    that still differs between the two branches below is whether a
    timeout guard applies: an internal ref can never hang (no network,
    and the base document is cached after its first fetch), so it
    resolves immediately with no threading involved; an external ref is a
    real file or network fetch and is bounded by the daemon-thread
    timeout. Returns (status, fetch_cache) - status maps each ref string
    to whether it resolved; fetch_cache accumulates every fetched
    document (the base document included), in prance's own cache format,
    so resolve_with_prance's later real resolve pass can reuse them
    instead of re-fetching."""
    cache: dict[Any, Any] = {}
    status: dict[str, bool] = {}
    for ref, _path in find_refs_in(raw_spec):
        if ref in status:
            continue
        if ref.startswith("#/"):
            status[ref] = _resolve_ref_now(ref, base_url, cache)
        else:
            status[ref] = _resolve_ref_with_timeout(ref, base_url, cache)
    return status, cache


def find_refs_in(node: Any, path: str = "$") -> list[tuple[str, str]]:
    """Every ($ref, path) pair found anywhere under node. Never follows a
    ref's target, so this terminates even on a cyclic document."""
    found: list[tuple[str, str]] = []
    _walk_find(node, path, found)
    return found


_CONFLICT_REASON_VS_EXTERNAL = "naming conflict — schema name already exists from another external ref"
_CONFLICT_REASON_VS_INTERNAL = "naming conflict — schema name already exists as an internal schema in this document"


def resolve_external_schema_placements(
    raw_spec: dict[str, Any], ref_status: dict[str, bool]
) -> tuple[dict[str, str], dict[str, str]]:
    """Decide, among all successfully-resolved EXTERNAL refs, which one
    gets to claim its target name in the schemas section. An internal
    schema of that name (already present in components.schemas) always
    wins by default, since it's already fully and correctly represented
    there. Among external refs, the first occurrence (in document order)
    wins; every later external ref that would collide with an
    already-claimed name - whether that name belongs to an internal
    schema or to an earlier external ref - is a naming conflict: letting
    it collapse to that bare name would silently point at content that
    isn't actually its own.

    Returns (winners, conflicts):
      - winners: schema name -> the external ref that claimed it (only
        for names not already used by an internal schema) - the refs
        extract_schemas should fetch content for.
      - conflicts: losing external ref -> reason string. build_clean_view
        renders these as a conflict placeholder at their usage site
        instead of a bare name."""
    claimed_by: dict[str, str] = {
        name: "internal" for name in raw_spec.get("components", {}).get("schemas", {})
    }
    winners: dict[str, str] = {}
    conflicts: dict[str, str] = {}
    seen: set[str] = set()

    for ref, _path in find_refs_in(raw_spec):
        if ref in seen or ref.startswith("#/"):
            continue
        seen.add(ref)
        if not ref_status.get(ref, False):
            continue

        name = ref_target_name(ref)
        holder = claimed_by.get(name)
        if holder == "internal":
            conflicts[ref] = _CONFLICT_REASON_VS_INTERNAL
        elif holder is not None:
            conflicts[ref] = _CONFLICT_REASON_VS_EXTERNAL
        else:
            claimed_by[name] = ref
            winners[name] = ref

    return winners, conflicts


def _walk_find(node: Any, path: str, found: list[tuple[str, str]]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            found.append((ref, path))
        for key, value in node.items():
            _walk_find(value, f"{path}.{key}", found)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_find(item, f"{path}[{i}]", found)


def _patch_broken(node: Any, broken_targets: set[str]) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref in broken_targets:
            return {}
        return {k: _patch_broken(v, broken_targets) for k, v in node.items()}
    if isinstance(node, list):
        return [_patch_broken(item, broken_targets) for item in node]
    return node


def resolve_with_prance(
    raw_spec: dict[str, Any],
    base_url: str,
    ref_status: dict[str, bool],
    fetch_cache: dict[Any, Any] | None = None,
) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Patch only the refs ref_status found broken, then resolve the rest
    - internal AND external (RESOLVE_ALL) - with prance's RefResolver.
    Returns (resolved_spec, broken_ref_occurrences) where each occurrence
    is a (ref, path) pair - one per place a broken ref appears, since the
    same broken target can be referenced from multiple spots. Every ref
    reaching the resolver was already confirmed resolvable by
    compute_ref_status, so this should not itself fail on a broken
    ref - but network state can change between the two calls, so any
    resolver failure here still falls back to leaving the document
    unresolved rather than crashing extraction."""
    all_refs = find_refs_in(raw_spec)
    broken_occurrences = [(ref, path) for ref, path in all_refs if not ref_status.get(ref, False)]
    broken_targets = {ref for ref, _ in broken_occurrences}

    patched = _patch_broken(raw_spec, broken_targets) if broken_targets else raw_spec

    resolver = RefResolver(
        patched,
        url=base_url,
        resolve_types=prance_resolver.RESOLVE_ALL,
        recursion_limit_handler=prance_resolver.keep_ref_on_recursion,
        reference_cache=fetch_cache if fetch_cache is not None else {},
    )
    try:
        resolver.resolve_references()
        resolved_spec = resolver.specs
    except Exception:
        resolved_spec = patched

    return resolved_spec, broken_occurrences


def build_clean_view(
    raw_node: Any,
    resolved_node: Any,
    ref_status: dict[str, bool],
    naming_conflicts: dict[str, str],
    path: str,
    warnings: list[str],
    _depth: int = 0,
) -> Any:
    """Build the clean internal representation of raw_node/resolved_node.
    See module docstring for the substitution rule."""
    if _depth > _MAX_MERGE_DEPTH:
        warnings.append(f"Ref traversal depth guard triggered at {path}; stopped descending.")
        return None

    if isinstance(raw_node, dict) and isinstance(raw_node.get("$ref"), str):
        ref = raw_node["$ref"]
        if ref in naming_conflicts:
            # This ref resolved fine on its own, but its target name is
            # already claimed by a different schema - collapsing to that
            # bare name here would silently point at the wrong content,
            # so this usage site is treated as unresolvable instead
            # (warning logged once by the caller).
            return {"unresolvable": True, "ref": ref, "reason": naming_conflicts[ref]}
        if ref_status.get(ref, False):
            return ref_target_name(ref)
        # Broken refs are reported once, comprehensively, by
        # resolve_with_prance's whole-document pre-scan - not re-logged
        # here, to avoid duplicate/partial-coverage warnings. The inline
        # marker below is what flags the exact spot in the JSON output.
        return {"$ref": ref, "unresolvable": True}

    if isinstance(raw_node, dict):
        resolved_dict = resolved_node if isinstance(resolved_node, dict) else {}
        return {
            key: build_clean_view(
                value,
                resolved_dict.get(key),
                ref_status,
                naming_conflicts,
                f"{path}.{key}",
                warnings,
                _depth + 1,
            )
            for key, value in raw_node.items()
        }

    if isinstance(raw_node, list):
        resolved_list = resolved_node if isinstance(resolved_node, list) else []
        return [
            build_clean_view(
                item,
                resolved_list[i] if i < len(resolved_list) else None,
                ref_status,
                naming_conflicts,
                f"{path}[{i}]",
                warnings,
                _depth + 1,
            )
            for i, item in enumerate(raw_node)
        ]

    # Scalar leaf: prefer the resolved value (prance-validated/normalized),
    # falling back to raw's own value if resolved has nothing at this spot.
    return resolved_node if resolved_node is not None else raw_node


def broken_refs_reachable_from_schema(
    schema_name: str,
    raw_spec: dict[str, Any],
    broken_refs: set[str],
    _visited: set[str] | None = None,
) -> set[str]:
    """Broken $ref pointers transitively reachable from a named component
    schema, following resolvable $refs into their target schemas. Guards
    against schema ref cycles with a visited-name set."""
    visited = _visited if _visited is not None else set()
    if schema_name in visited:
        return set()
    visited.add(schema_name)

    schemas = raw_spec.get("components", {}).get("schemas", {})
    definition = schemas.get(schema_name)
    if definition is None:
        return set()

    found: set[str] = set()
    for ref, _path in find_refs_in(definition):
        if ref in broken_refs:
            found.add(ref)
        elif ref.startswith("#/components/schemas/"):
            found |= broken_refs_reachable_from_schema(
                ref_target_name(ref), raw_spec, broken_refs, visited
            )
    return found


def direct_schema_names_used(node: Any) -> set[str]:
    """Named component-schema references directly present in a raw
    subtree (e.g. one endpoint's parameters/requestBody/responses)."""
    names = set()
    for ref, _path in find_refs_in(node):
        if ref.startswith("#/components/schemas/"):
            names.add(ref_target_name(ref))
    return names


def direct_broken_refs(node: Any, ref_status: dict[str, bool]) -> set[str]:
    """Broken $ref pointers found directly within a raw subtree (not
    counting ones only reachable through a referenced schema's own body)."""
    return {ref for ref, _ in find_refs_in(node) if not ref_status.get(ref, False)}
