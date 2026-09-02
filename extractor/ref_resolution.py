"""$ref handling for the extractor.

Two separate concerns live here:

1. Raw-spec pointer checks (ref_resolves, find_refs_in) - used to pre-scan
   the *unresolved* document for broken $refs before handing it to prance,
   since prance aborts its whole resolve on the first unresolvable pointer.
   Broken spots get patched to `{}` in a copy so prance can resolve
   everything else; the originals are what actually get reported.

2. resolve_with_prance() - runs prance's ResolvingParser on the patched
   spec to get a fully-inlined version, configured to stop at recursion
   limits (self/mutually-referencing schemas) by leaving a $ref in place
   rather than raising.

3. build_clean_view() - the "clean internal format" builder. Walks the RAW
   spec (never the resolved one) as the structural driver: wherever raw
   holds a bare {"$ref": "..."} pointing at a resolvable named component,
   it's collapsed to that component's bare name string - never inlined,
   never rendered as an anonymous object. A broken $ref keeps its raw
   {"$ref": "...", "unresolvable": true} form - the extra flag marks the
   exact spot inline, in addition to the summary in warnings (reported
   once, comprehensively, by resolve_with_prance's whole-document
   pre-scan - not re-logged per occurrence here). Everything else (plain inline structure
   with no $ref at that position) is copied from the RESOLVED spec instead,
   so accuracy of nested/derived content still benefits from prance's
   resolution. Recursion stops the instant a $ref is found - the walker
   never follows a ref's target, so a schema cycle (even a bare
   self-reference) cannot cause infinite recursion here.
"""

from __future__ import annotations

from typing import Any

import prance
from prance.util import resolver as prance_resolver
from prance.util.resolver import RefResolver

_MAX_MERGE_DEPTH = 200


def ref_target_name(ref: str) -> str:
    """Trailing name segment of a $ref pointer, e.g.
    '#/components/schemas/Pet' -> 'Pet'."""
    return ref.rstrip("/").rsplit("/", 1)[-1]


def ref_resolves(ref: str, spec: dict[str, Any]) -> bool:
    """Whether a $ref pointer resolves within this document. External refs
    (not starting with '#/') are unresolvable - extraction only reads the
    one swagger.json file."""
    if not ref.startswith("#/"):
        return False
    node: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return False
        else:
            return False
    return True


def find_refs_in(node: Any, path: str = "$") -> list[tuple[str, str]]:
    """Every ($ref, path) pair found anywhere under node. Never follows a
    ref's target, so this terminates even on a cyclic document."""
    found: list[tuple[str, str]] = []
    _walk_find(node, path, found)
    return found


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


def resolve_with_prance(raw_spec: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Pre-scan the WHOLE raw_spec document for broken $refs (not just the
    schemas/paths subtrees the extractor walks - this also catches a
    broken ref sitting in components.parameters or anywhere else), patch
    just those spots, then resolve the patched copy with prance's
    RefResolver directly (not ResolvingParser/BaseParser - those also run
    an OpenAPI meta-schema validation pass after resolving, which is
    Hard Gates' job, not extraction's, and which independently blows the
    recursion limit on the exact same bare-self-ref schemas we're already
    guarding against here). Returns (resolved_spec, broken_ref_occurrences)
    where each occurrence is a (ref, path) pair - one per place a broken
    ref appears, since the same broken target can be referenced from
    multiple spots. Broken refs never reach the resolver, so this never
    raises on them; a recursive schema is handled by configuring the
    resolver to leave a $ref in place once its recursion limit is hit,
    instead of raising or unrolling indefinitely."""
    all_refs = find_refs_in(raw_spec)
    broken_occurrences = [(ref, path) for ref, path in all_refs if not ref_resolves(ref, raw_spec)]
    broken_targets = {ref for ref, _ in broken_occurrences}

    patched = _patch_broken(raw_spec, broken_targets) if broken_targets else raw_spec

    resolver = RefResolver(
        patched,
        url=prance._PLACEHOLDER_URL,
        recursion_limit_handler=prance_resolver.keep_ref_on_recursion,
    )
    resolver.resolve_references()
    return resolver.specs, broken_occurrences


def build_clean_view(
    raw_node: Any,
    resolved_node: Any,
    raw_spec: dict[str, Any],
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
        if ref_resolves(ref, raw_spec):
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
                value, resolved_dict.get(key), raw_spec, f"{path}.{key}", warnings, _depth + 1
            )
            for key, value in raw_node.items()
        }

    if isinstance(raw_node, list):
        resolved_list = resolved_node if isinstance(resolved_node, list) else []
        return [
            build_clean_view(
                item,
                resolved_list[i] if i < len(resolved_list) else None,
                raw_spec,
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


def direct_broken_refs(node: Any, raw_spec: dict[str, Any]) -> set[str]:
    """Broken $ref pointers found directly within a raw subtree (not
    counting ones only reachable through a referenced schema's own body)."""
    return {ref for ref, _ in find_refs_in(node) if not ref_resolves(ref, raw_spec)}
