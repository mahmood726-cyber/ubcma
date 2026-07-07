"""Locate the two EXISTING external tools this periphery layer wires in, without
hardcoding a single local path in shippable code (lessons.md: "Do not hardcode
one drive ... use config, candidate-root discovery, or explicit path inputs and
fail closed if no snapshot is found").

Two tools, both authored by Mahmood, both already on disk:

  * KMDigitizer      -- Guyot (2012) Kaplan-Meier curve -> pseudo-IPD reconstructor
                        + log-rank HR re-derivation. Pure-stdlib Python.
                        https://github.com/<user>/KMDigitizer  (local clone).
  * rct-extractor-v2 -- deterministic RCT effect / arm-level extractor over trial
                        free text (HR/OR/RR/MD + CI, poolable 2x2, continuous).
                        Importable package `rct_extractor`.

Resolution order for each:  env var  ->  candidate roots  ->  fail closed.

Nothing here touches the network; it only puts two local packages on sys.path.
"""
from __future__ import annotations
import os
import sys

# --- candidate roots (searched only if the env var is unset) --------------------
# Deliberately drive-agnostic: we probe a small set of plausible clone locations
# across F:/C. If none resolves we raise with an actionable message rather than
# silently degrading (fail closed).
_KM_CANDIDATES = [
    r"F:\Models\KMDigitizer",
    r"C:\Models\KMDigitizer",
    r"C:\Projects\KMDigitizer",
    os.path.expanduser(r"~\KMDigitizer"),
]
_RCT_CANDIDATES = [
    r"C:\Projects\rct-extractor-v2",
    r"F:\allmeta\rct-extractor",
    r"F:\Projects\rct-extractor-v2",
    os.path.expanduser(r"~\rct-extractor-v2"),
]


def _resolve(env_var, candidates, sentinel, human):
    """Return the first directory that exists and contains ``sentinel``.

    ``sentinel`` is a relative path we expect inside a valid clone, so we do not
    accept an empty/broken shell of a directory (lessons.md: broken git shells
    fool bare path-exists checks)."""
    override = os.environ.get(env_var)
    roots = [override] if override else candidates
    tried = []
    for root in roots:
        if not root:
            continue
        tried.append(root)
        if os.path.isfile(os.path.join(root, sentinel)):
            return root
    raise FileNotFoundError(
        f"{human} not found. Set {env_var} to the clone dir "
        f"(the one containing {sentinel!r}). Tried: {tried}"
    )


def kmdigitizer_home() -> str:
    return _resolve("KMDIGITIZER_HOME", _KM_CANDIDATES, "kmdigitizer.py",
                    "KMDigitizer (Guyot KM->IPD reconstructor)")


def rct_extractor_home() -> str:
    return _resolve("RCT_EXTRACTOR_HOME", _RCT_CANDIDATES,
                    os.path.join("rct_extractor", "__init__.py"),
                    "rct-extractor-v2 (RCT full-text extractor)")


def ensure_on_path():
    """Idempotently put both tool roots on sys.path. Returns (km_home, rct_home)."""
    km = kmdigitizer_home()
    rct = rct_extractor_home()
    for p in (km, rct):
        if p not in sys.path:
            sys.path.insert(0, p)
    return km, rct


def parsed_fulltext_dir() -> str:
    """Directory of Phase-1 parsed full-text JSON (jats.py output).

    Defaults to ``<repo>/regpub_pilot/data/fulltext_parsed`` (reproducible via
    ``src/fetch_fulltext.py``). Overridable with REGPUB_FT_PARSED so an isolated
    worktree can read the concurrent Phase-1 lane's cache without copying it."""
    override = os.environ.get("REGPUB_FT_PARSED")
    if override:
        return override
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)  # regpub_pilot/
    return os.path.join(root, "data", "fulltext_parsed")
