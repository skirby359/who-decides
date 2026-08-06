"""Shared prose-scraping assertion harness for the paper verifiers.

WHY THIS EXISTS. Two designs were in use in `scripts/` and only one of them worked.

The constants design — hold the published figure as a Python literal and compare it to a
fresh derivation — never reads the paper. It cannot see a sentence edited out from under it,
it cannot see a paper contradicting itself, and its "paper:" column is an unverifiable claim
about a document the script never opened. `verify_cross_state_money.py` carried
`n_donor=312_337` for a figure the paper prints as "312.3K"; nothing tied the two together.

Worse, four of the paper verifiers had no assertions at all: `verify_who_decides_wa.py`,
`_ny.py`, `_id.py` and `verify_safe_seat.py` printed derived values beside a hand-typed
"(paper: ...)" for a human to eyeball, and always exited 0. The release checklist ran them as
`verify_$v.py || echo FAILED`, which could never print FAILED for any of them.

`verify_whitepaper.py` solved this by SCRAPING THE PROSE: every probe is a regex anchored on
the words around the figure, and every occurrence of that figure must equal the derived
value. This module is that mechanism, factored out so the rest of the series can use it.

THE THREE RULES IT ENFORCES, each earned:

1. **A probe whose anchor matches nothing is a FAILURE, not a skip.** Rewording a sentence out
   from under a check is the thing to catch; silence there is how the white paper drifted to
   -0.42 against the money paper's -0.39.
2. **Every occurrence is checked, not the first.** A figure stated in an abstract and again in
   a table is checked twice, so a paper that contradicts itself fails on whichever occurrence
   is wrong. Finding 5 once gave the same top-1% as 41.2% and 42.4% four lines apart.
3. **Report what is NOT covered.** `--coverage` lists every numeric token no probe touched.
   It is a report rather than a gate here: the donor paper's full coverage audit is worth its
   friction across 48 sections of a journal submission, less so on a 1,800-word working paper.
   But an unprobed figure should at least be visible, because unaudited sections are where
   reviewers keep finding the defects.

Not packaged — `scripts/` is a plain directory, so siblings import this directly. The same
pattern the public repo already uses for `donor_matcher.py`.
"""
from __future__ import annotations

import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"


def stdout_utf8() -> None:
    """Windows consoles default to cp1252 and die on the × and – these papers use."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def normalise(text: str) -> str:
    """Strip blockquote markers and collapse whitespace.

    Anchors then span line wraps, so re-flowing a paragraph does not silently disarm a probe
    — which would otherwise turn rule 1 into a false pass.
    """
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text))


def section(text: str, start: str, end: str | None = None) -> str:
    """Normalised slice from `start` to `end`, both plain substrings.

    Guarded, because both traps have bitten in this repo: a start anchor that is absent
    silently yields the whole document, and an end anchor that appears BEFORE the start
    yields an empty slice that passes every probe by matching nothing. Raise instead.
    """
    i = text.find(start)
    if i < 0:
        raise LookupError(f"section start anchor not found: {start!r}")
    j = len(text) if end is None else text.find(end, i + len(start))
    if end is not None and j < 0:
        raise LookupError(f"section end anchor not found after start: {end!r}")
    return normalise(text[i:j])


# Numeric tokens the coverage report should not nag about. Anything genuinely a RESULT must
# NOT be here — over-reporting costs ten seconds of reading, under-reporting hides a figure.
#
# THIS LIST ONCE CONTAINED `^\d{1,2}\.\d$`, meant to skip "§3.1"-style section numbering. It
# also skipped 41.2, 83.5, 26.5 and every other one-decimal percentage with one or two integer
# digits — which is the single most common figure shape in these papers. The coverage report
# was blind to most of what it existed to find, and said nothing while being so. Section
# references are now recognised by their CONTEXT instead (see _SECTION_REF), which is what
# distinguishes them from a result.
_COVERAGE_SKIP = re.compile(
    r"^(?:19|20)\d{2}$"          # years
    r"|^\d{1,2}$"                # small integers: list ordinals, chamber ids, column counts
)

# A number is section numbering only if something immediately before it says so.
_SECTION_REF = re.compile(
    r"(?:§+\s*|[Ss]ections?\s+|[Aa]ppendix\s+|[Ff]inding\s+|[Tt]able\s+|[Ff]igure\s+"
    r"|[Nn]ote\s+|C\.?F\.?R\.?\s*§?\s*|doi:[\d.]*|\d+\.)\s*$")
# The trailing `(?<![,.])` matters: without it "$14,212, or 0.02%" tokenises as `14,212,`
# WITH the sentence comma, whose span runs one character past the probe's capture span — so a
# figure that IS asserted reports as unprobed. Over-reporting is the cheap failure here, but it
# is still noise in a list whose whole job is to be read.
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?(?<![,.])")


def _coverage(norm: str, covered: list[tuple[int, int]]) -> list[str]:
    """Numeric tokens in the scraped text that no probe's match span covered."""
    out = []
    for m in _NUMBER.finditer(norm):
        if any(a <= m.start() and m.end() <= b for a, b in covered):
            continue
        tok = m.group(0)
        if _COVERAGE_SKIP.match(tok):
            continue
        if _SECTION_REF.search(norm[max(0, m.start() - 24):m.start()]):
            continue
        lo, hi = max(0, m.start() - 45), min(len(norm), m.end() + 45)
        out.append(f"{tok:>12}   …{norm[lo:hi]}…")
    return out


def _round_half_up(value: float, places: int) -> Decimal:
    """Round the way a person writing a paper rounds.

    Python's built-in `round` is half-to-EVEN: round(0.5) is 0 and round(2.5) is 2. Nobody
    writes a paper that way, so comparing a printed figure against it would manufacture
    failures at exactly the boundary values this check exists to examine. Decimal with
    ROUND_HALF_UP matches the convention the papers actually use, and sidesteps binary
    float representation while it is at it.
    """
    q = Decimal(1).scaleb(-places)
    return Decimal(repr(float(value))).quantize(q, rounding=ROUND_HALF_UP)


def _places(printed: str) -> int:
    """Decimal places in the figure AS PRINTED — the precision the paper committed to."""
    return len(printed.split(".")[1]) if "." in printed else 0


def check_rounding(printed: str, derived: float) -> str | None:
    """Return a message when `printed` is not the correct rounding of `derived`.

    WHY THIS EXISTS, and why a tolerance cannot replace it. A tolerance asks "is the printed
    figure CLOSE to the data?" — this asks "is it the RIGHT figure?", which is a different
    and stricter question. On 2026-08-02 five defects across four papers were of exactly this
    shape and every one passed its tolerance:

        Idaho, Other-party median age        38    against 39
        Idaho, May-2024 primary R-D        76.9    against 76.82
        New York, 2023 30-44 share         15.8    against 15.85055
        money paper, local-trend r         0.32    against 0.314932
        cross-state, NY donor Republican     25    against 24.4958

    Each was found by hand, by noticing full precision. The rule is exact and has no false
    positives, so it belongs in the harness rather than in anyone's attention.
    """
    try:
        want = _round_half_up(derived, _places(printed))
        got = Decimal(printed.replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    if got == want:
        return None
    return f"printed {printed}, but {derived:.6g} rounds to {want}"


def run(title: str, norm: str, probes, derived: dict, unchecked=(),
        show_coverage: bool = False, sections: dict[str, str] | None = None,
        round_exempt: dict[str, str] | None = None,
        spans_out: dict[str | None, list[tuple[int, int]]] | None = None) -> int:
    """Assert every probe against `derived`. Returns a process exit code.

    probes: (label, regex, key | (keys...), tolerance[, section]). Each capture group in the
    regex is compared to the correspondingly-positioned key. A tolerance of 0 demands an
    exact match.

    The optional 5th element names a slice in `sections` to search instead of the whole
    document. Use it when a pattern is genuinely ambiguous document-wide rather than
    contorting the regex: safe-seat's four-column universe row is indistinguishable from a
    year-header row `| 2016 | 2018 | 2020 | 2022 | 2024 |` elsewhere in the paper, and no
    amount of lookahead fixes that honestly.

    Coverage spans are recorded per section, so a probe scoped to a slice does not mark
    anything covered in the full text. Only whole-document probes feed the coverage report.

    ROUNDING is checked on every figure in addition to the tolerance, because the two ask
    different questions — see `check_rounding`. `round_exempt` maps a probe label to the
    reason its printed form is legitimately not a rounding of the derived value: an
    abbreviated count, a figure the paper states as an approximation, or a documented
    difference between two constructions. A reason is required, so an exemption is a
    decision on the record rather than a silence.

    `spans_out`, when given, is filled with the character spans this run actually
    asserted, keyed by section name (None = whole document). That is what a caller
    needs to turn the advisory coverage REPORT into a GATE: the report can only ask
    "what did no probe touch in the full text", whereas a gate has to ask it per
    result section — and a section-scoped probe records against its own slice, so
    without the per-section breakdown its figures look unprobed.
    """
    round_exempt = round_exempt or {}
    bar = "=" * 92
    print(bar)
    print(title)
    print(bar)
    fails: list[str] = []
    covered: list[tuple[int, int]] = []
    by_section: dict[str | None, list[tuple[int, int]]] = {}
    n_checked = 0
    n_scoped = 0
    n_round = 0

    for probe in probes:
        label, rx, keys, tol = probe[:4]
        sec = probe[4] if len(probe) > 4 else None
        if sec is not None:
            if not sections or sec not in sections:
                print(f"  FAIL {label:56} SECTION {sec!r} NOT DEFINED")
                fails.append(f"{label}: probe names section {sec!r}, which was not sliced")
                continue
            haystack, in_full = sections[sec], False
            n_scoped += 1
        else:
            haystack, in_full = norm, True
        keys = (keys,) if isinstance(keys, str) else keys
        hits = list(re.finditer(rx, haystack))
        if not hits:
            print(f"  FAIL {label:56} ANCHOR NOT FOUND")
            fails.append(f"{label}: anchor not found — the sentence was reworded or the "
                         f"figure removed. Re-point the probe, or restore the text.")
            continue
        for m in hits:
            groups = m.groups()
            if len(groups) != len(keys):
                print(f"  FAIL {label:56} {len(groups)} capture(s), {len(keys)} key(s)")
                fails.append(f"{label}: regex captures {len(groups)} values but "
                             f"{len(keys)} derived keys were given")
                break
            for gi, (got, key) in enumerate(zip(groups, keys)):
                want = derived.get(key)
                if want is None:
                    print(f"  FAIL {label:56} no derived value for {key!r}")
                    fails.append(f"{label}: derivation {key!r} unavailable")
                    continue
                try:
                    val = float(got.replace(",", ""))
                except ValueError:
                    # An over-greedy `([\d.]+)` swallows the sentence's full stop, so the
                    # capture reads "0.998." and float() raises mid-run, killing every probe
                    # after it. Report it as the probe bug it is instead of crashing.
                    print(f"  FAIL {label:56} captured {got!r}, not a number")
                    fails.append(f"{label}: captured {got!r} — the regex is over-greedy, "
                                 f"most likely a trailing '.' or '%'. Tighten it.")
                    continue
                ok = abs(val - float(want)) <= tol
                big = abs(val) >= 10_000
                shown = f"{val:,.0f}" if (tol == 0 or tol >= 1 or big) else f"{val:g}"
                wshown = (f"{want:,.0f}" if (tol == 0 or tol >= 1 or big)
                          else f"{want:.4g}")
                print(f"  {'ok  ' if ok else 'FAIL'} {label:56} "
                      f"paper {shown:>12}   derived {wshown}")
                n_checked += 1
                if not ok:
                    fails.append(f"{label}: paper says {shown}, data says {wshown}")
                elif label not in round_exempt:
                    # Only when the tolerance PASSED: a figure that already failed on value
                    # does not need a second complaint about how it was rounded.
                    msg = check_rounding(got.strip(), float(want))
                    if msg:
                        print(f"  ROUND {label:56} {msg}")
                        fails.append(f"{label}: {msg}")
                        n_round += 1
                by_section.setdefault(sec, []).append(m.span(gi + 1))
                if in_full:
                    covered.append(m.span(gi + 1))
        if len(hits) > 1:
            print(f"       ({len(hits)} occurrences checked — a figure stated more than once "
                  f"must agree with the data every time)")

    if spans_out is not None:
        spans_out.update(by_section)

    if unchecked:
        print("\n  NOT covered by this script, and why:")
        for u in unchecked:
            print(f"    - {u}")

    if show_coverage:
        gaps = _coverage(norm, covered)
        print(f"\n  COVERAGE — {n_checked} figures asserted; "
              f"{len(gaps)} numeric token(s) in the scraped text unprobed:")
        if n_scoped:
            print(f"    (NB {n_scoped} probe(s) were section-scoped. Their spans are recorded "
                  f"against the slice, not the full text, so the figures they DO check can "
                  f"still appear below. Check the list against the probe set before adding "
                  f"a duplicate.)")
        for g in gaps:
            print(f"    {g}")

    print("\n" + bar)
    if fails:
        rnd = f" ({n_round} of them a rounding direction)" if n_round else ""
        print(f"{title.split(' —')[0]}: {len(fails)} FAILURE(S){rnd}")
        print(bar)
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"{title.split(' —')[0]}: {n_checked} figures agree with the data")
    print(bar)
    return 0


def wants_coverage(argv=None) -> bool:
    return "--coverage" in (sys.argv[1:] if argv is None else argv)


# --------------------------------------------------------------------------
# Coverage GATE (as distinct from the advisory report above), ported out of
# verify_who_decides_wa 2026-08-06 so a third and fourth paper do not each
# grow their own copy. Exemption tables stay with the paper that owns them.
# --------------------------------------------------------------------------
def audit_coverage(sections: dict, spans: dict, offsets: dict, audited,
                   exempt_patterns=(), exempt_literals=None,
                   exempt_sections=None) -> list[str]:
    """Fail on any numeric token in an audited section that no probe captured.

    Two coordinate spaces have to be reconciled or the audit lies. A
    section-scoped probe records spans relative to its own slice; a
    whole-document probe records them relative to the full normalised text.
    Most probes are whole-document, so comparing only section-local spans
    reported ~90 already-asserted figures as unmapped when this first ran
    against the WA paper. `offsets` gives each slice's start in the full text, which
    is what lets a whole-document span be translated into section coordinates.
    """
    print("\n" + "-" * 78)
    print("COVERAGE AUDIT — every number in a result section must be probed or exempt")
    print("-" * 78)
    exempt_literals = exempt_literals or {}
    exempt_sections = exempt_sections or {}
    fails, used_exempt = [], set()
    for name in audited:
        if name in exempt_sections:
            print(f"  reason {name:14} closed by written reason, not derivation")
            continue
        hay = sections.get(name)
        if hay is None:
            fails.append(f"coverage: audited section {name!r} was not sliced")
            print(f"  FAIL {name:14} SECTION NOT SLICED")
            continue
        off = offsets[name]
        covered = list(spans.get(name, []))                     # section-scoped, already local
        covered += [(a - off, b - off) for a, b in spans.get(None, [])   # whole-document
                    if a < off + len(hay) and off < b]
        unmapped = []
        for m in _NUMBER.finditer(hay):
            # OVERLAP, not containment: a probe's capture group holds the numeric
            # core (`1.6`) while the token may carry a suffix (`1.6%`), so the
            # token's end runs past the group's. Containment reported every
            # probed table cell as unmapped when the donor audit first ran.
            if any(m.start() < b and a < m.end() for a, b in covered):
                continue
            tok = m.group(0)
            bare = tok.lstrip("$").rstrip("%M×")
            if bare in exempt_literals or tok in exempt_literals:
                used_exempt.add(bare if bare in exempt_literals else tok)
                continue
            if any(re.match(p, bare) for p, _ in exempt_patterns):
                continue
            if _SECTION_REF.search(hay[max(0, m.start() - 24):m.start()]):
                continue
            ctx = re.sub(r"\s+", " ", hay[max(0, m.start() - 45):m.end() + 25])
            unmapped.append((tok, ctx))
        if unmapped:
            print(f"  FAIL {name:14} {len(unmapped)} unmapped numeric token(s)")
            for tok, ctx in unmapped[:60]:
                print(f"         {tok:>10}   …{ctx}…")
            if len(unmapped) > 60:
                print(f"         … and {len(unmapped) - 60} more")
            fails.append(f"coverage [{name}]: {len(unmapped)} unmapped token(s) — first is "
                         f"{unmapped[0][0]!r}. Probe it, or exempt it with a reason.")
        else:
            print(f"  ok   {name:14} fully mapped")
    stale = sorted(set(exempt_literals) - used_exempt)
    if stale:
        print(f"\n  note {len(stale)} literal exemption(s) no longer fire — prunable: "
              + ", ".join(stale))
    return fails


def slice_with_offset(norm: str, start: str, end: str) -> tuple[str, int]:
    """Section text plus its start offset in the normalised document.

    Sliced from the NORMALISED text, not the raw file, so that section
    coordinates and whole-document probe spans live in the same space. Same
    anchor discipline as vp.section: both anchors must be present and the end
    must follow the start, or the slice silently runs to end-of-document.
    """
    a = norm.find(start)
    if a < 0:
        raise LookupError(f"section start anchor not found: {start!r}")
    b = norm.find(end, a + len(start))
    if b < 0:
        raise LookupError(f"section end anchor not found after start: {end!r}")
    return norm[a:b], a


