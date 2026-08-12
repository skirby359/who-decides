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
        spans_out: dict[str | None, list[tuple[int, int]]] | None = None,
        stats_out: dict | None = None) -> int:
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

    `stats_out`, when given, receives {"figures": n} — the count this run asserted, which
    is what `audit_satellite_counts` compares the submission documents' claims against.

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

    if stats_out is not None:
        stats_out["figures"] = n_checked

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
# Satellite figure-count guard (2026-08-06)
#
# THE PROBLEM IT SOLVES, because the shape recurs. Every paper's submission
# metadata states how many figures its verifier asserts ("asserts **211
# figures**"), and that sentence reaches a journal form. It is NOT checkable by
# `check_cross_doc_consistency.py`'s orphan pass: the count is a property of the
# verifier RUN and appears nowhere in the paper, so the orphan check sees it as
# absent-by-construction and an allowlist entry waives it. Which means the
# waiver — not the check — was carrying seven of the eight papers, and it was
# carrying them by NOT looking. Measured, not assumed: on 2026-08-06 the NY
# satellites said 135 against 137, the Idaho ones 210 against 211, and the
# cross-state money data-availability statement said 125 against 208.
#
# The failed intermediate fix is worth recording. The allowlist enumerated the
# counts it waived (`88|125|135|210`), so a changed count failed the checker —
# loudly, for the right reason, at the wrong layer: it reported a legitimate
# document as unguarded rather than reporting a stale claim. Widening it to the
# category stopped the false alarms and widened the blindness. Neither is a fix,
# because the orphan pass is structurally the wrong instrument here.
#
# THE OWNER IS THE VERIFIER. It is the only thing that knows the number, it
# already runs in every paper's pre-upload checklist, and it costs nothing extra
# — so a stale count now fails at the moment the count changes, which is the one
# moment somebody is looking. `check_cross_doc_consistency.py` keeps a waiver for
# these tokens, but its recorded reason is now true.
#
# TWO DELIBERATE LIMITS. (1) Only PRESENT-TENSE claims are checked. A checklist
# line recording what a past run produced ("Verifier 125 → **139 figures**",
# 2026-08-06) is history and must keep saying what it said — the same rule the
# corrections ledgers and the audit log live by. (2) A missing satellite is a
# SKIP with a notice, not a failure: all of these files are in
# `sync_public_repo.NEVER`, so the public checkout legitimately has none of them.
# --------------------------------------------------------------------------
SATELLITES = {
    # The CORRECTIONS LEDGER was added 2026-08-11 and it was not a theoretical gap: it stated
    # "verify_who_decides_wa.py now asserts 246 figures", present tense, against a real 539 — the
    # count as of the round that wrote it, four rounds stale. It is the one satellite of a POSTED
    # paper that records what the posted artifact still gets wrong, so a stale claim there is the
    # worst-placed of any in the series. Registering it is what makes the guard see it.
    "who-decides-washington.md": ("submission-metadata.md",
                                  "who-decides-wa-submission-notes.md",
                                  "who-decides-wa-corrections-ledger.md"),
    "safe-seat-washington.md": ("safe-seat-submission-metadata.md",
                                "safe-seat-submission-notes.md"),
    "does-money-move-votes.md": ("money-votes-submission-metadata.md",
                                 "money-votes-submission-notes.md"),
    "who-decides-new-york.md": ("ny-submission-metadata.md",
                                "ny-submission-notes.md"),
    "who-decides-idaho.md": ("id-submission-metadata.md",
                             "id-submission-notes.md"),
    "cross-state-fec-money.md": ("cross-state-money-submission-metadata.md",
                                 "cross-state-money-submission-notes.md"),
    "who-decides-cross-state.md": ("who-returns-ballot-submission-metadata.md",
                                   "who-returns-ballot-submission-notes.md"),
    # The white paper is a prospectus and deliberately has no submission metadata
    # (author's call, 2026-08-06). Present with an empty tuple rather than absent,
    # so "no satellites" is a recorded decision and not a missing registration.
    "electoral-health-whitepaper.md": (),
}

# Each pattern must capture a count a document states about THIS verifier, in the
# present tense. Whitespace is `\s+` everywhere, never a literal space: these
# files are hard-wrapped at 96 columns, so any two words in a claim can be split
# by a newline (and by `> ` when the claim sits in a blockquote). The first
# version used literal spaces and reported "no claim found" for safe-seat, whose
# sentence wraps between "asserts" and "**197 figures**" — a silent downgrade
# from checked to unchecked, which is the failure this whole guard exists to stop.
_COUNT_CLAIMS = (
    r"asserts\s+(?:>\s*)?\*\*([\d,]+)\s+figures\*\*",
    r"asserting\s+(?:>\s*)?\*\*([\d,]+)\s+figures\*\*",
    # The papers say "re-derives N figures" rather than "asserts"; that phrasing
    # went unchecked until 2026-08-09.
    r"re-derives\s+\*\*([\d,]+)\s+figures\*\*",
    r"exit 0 = ([\d,]+) figures agree",
    # PASSIVE VOICE, added 2026-08-10. The money paper's notes answered a referee
    # objection with "208 figures are asserted" while the run asserted 255, and no
    # anchor above reaches a claim whose number precedes the verb. It was invisible
    # for a second reason worth recording: its sibling metadata file states the
    # count correctly twice, so `n_claims` was non-zero and the "no claim found —
    # re-anchor _COUNT_CLAIMS" notice never fired. A partially-anchored satellite
    # set reads exactly like a fully-anchored one.
    r"([\d,]+)\s+figures\s+are\s+asserted",
    # BOLD ON THE NUMBER ONLY, added 2026-08-11. The anchors above all require the `**` to span
    # the number AND the word "figures"; `who-decides-wa-corrections-ledger.md` writes
    # "asserts **246** figures", which is the same claim with the emphasis one word shorter, and
    # it went unmatched. Third phrasing variant this review series has had to add — the pattern
    # to notice is that each new document invents its own emphasis, so the anchor set has to be
    # about the WORDS and tolerant of the markup between them.
    r"asserts\s+\*\*([\d,]+)\*\*\s+figures",
    r"asserting\s+\*\*([\d,]+)\*\*\s+figures",
)

# Anchors used ONLY on satellite documents. The loose "— N of them" idiom belongs
# to the satellites' data-availability boilerplate ("reproduced by verify_x.py —
# 521 of them"). Applied to a PAPER it false-positives: safe-seat-washington.md
# says "every distinct party string in the five certified files — 32 of them",
# which counts party strings, not asserted figures. Scoped rather than dropped,
# because it is the only anchor the satellites' phrasing offers.
_SATELLITE_ONLY_CLAIMS = (
    r"—\s*(?:\n>\s*)?([\d,]+)\s*(?:\n>\s*)?of them",
)

# The residual risk, stated because it is real: a claim reworded past every anchor
# above reports "none found" and is then unchecked. That is why the no-claim case
# prints a loud notice naming what to do, rather than passing quietly — and why
# the anchors are deliberately loose about whitespace and tight about wording.


def audit_satellite_counts(paper_name: str, figures: int | None) -> list[str]:
    """Fail when a satellite states a figure count this run did not produce."""
    print("\n" + "-" * 78)
    print("SATELLITE FIGURE COUNTS — every present-tense claim must match this run")
    print("-" * 78)
    if paper_name not in SATELLITES:
        msg = (f"satellite guard: {paper_name!r} is not in _verify_prose.SATELLITES. "
               f"Register it (an empty tuple is a valid answer) so 'no satellites' is a "
               f"decision rather than an omission.")
        print(f"  FAIL {msg}")
        return [msg]
    # THE PAPER ITSELF IS SCANNED TOO (added 2026-08-09). It was not, and the WA
    # paper carried "re-derives 311 figures" while the verifier asserted 489 —
    # live in the public record, on a posted paper, with its own satellite
    # correctly saying 489 and passing. A guard that checks every document about
    # the paper except the paper is the defect class this file exists to close.
    names = (paper_name,) + tuple(SATELLITES[paper_name])
    if not SATELLITES[paper_name]:
        print("  note no satellite documents registered; scanning the paper itself only")
    if figures is None:
        msg = ("satellite guard: the run reported no figure count, so the guard could not "
               "run. Pass stats_out= to vp.run().")
        print(f"  FAIL {msg}")
        return [msg]
    fails, n_claims, n_present = [], 0, 0
    for name in names:
        path = DOCS / name
        if not path.exists():
            print(f"  skip {name:44} absent (withheld from this checkout by design)")
            continue
        n_present += 1
        text = path.read_text(encoding="utf-8")
        pats = (_COUNT_CLAIMS if name == paper_name
                else _COUNT_CLAIMS + _SATELLITE_ONLY_CLAIMS)
        for pat in pats:
            for m in re.finditer(pat, text):
                stated = int(m.group(1).replace(",", ""))
                n_claims += 1
                line = text[:m.start()].count("\n") + 1
                if stated == figures:
                    print(f"  ok   {name}:{line:<4} states {stated:,}")
                else:
                    print(f"  FAIL {name}:{line:<4} states {stated:,}, this run asserts "
                          f"{figures:,}")
                    fails.append(f"{name}:{line} states {stated:,} figures; this run "
                                 f"asserts {figures:,}")
    if not fails and n_claims:
        print(f"  {n_claims} present-tense claim(s) checked, all matching {figures:,}")
    elif not n_present:
        # Distinguished from the reworded-anchor case below on purpose: in the PUBLIC
        # checkout every satellite is absent by design, and printing "re-anchor
        # _COUNT_CLAIMS" there reads as a warning about a defect that does not exist.
        print("  n/a  every registered satellite is withheld from this checkout — "
              "nothing to check here, which is the expected public-repo result")
    elif not n_claims:
        print("  none  no present-tense figure-count claim found in the registered "
              "satellites — if one was reworded, re-anchor _COUNT_CLAIMS")
    return fails


# --------------------------------------------------------------------------
# Coverage GATE (as distinct from the advisory report above), ported out of
# verify_who_decides_wa 2026-08-06 so a third and fourth paper do not each
# grow their own copy. Exemption tables stay with the paper that owns them.
# --------------------------------------------------------------------------
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_BOLD_MAX_WORDS = 2


def _bold_spans(text: str) -> list[tuple[int, int]]:
    """Ranges of `**...**` runs SHORT enough that the emphasis is on the figure itself.

    Used by `bold_is_result`. Non-greedy and DOTALL, because the harness normalises
    whitespace before slicing, so a bold run can span what were several source lines.

    WHY A WORD LIMIT, measured rather than guessed. The first version of this returned
    every bold run, and against `who-decides-washington.md` it surfaced 25 tokens of which
    three were real. The rest were figures that happen to sit inside a bolded PHRASE:

        **April 2026 roll**                    a year, inside a noun phrase
        **positive in all 39 counties**        a count whose probe covers it
        **42.8% 65+ and 6.1% under 30**        two cohort edges inside a clause
        **1. Maybe the off-year electorate…**  a bolded list heading

    Emphasis on a phrase is emphasis on the sentence, not on the number in it. Emphasis on
    one or two words IS the number — `**12**`, `**16–17 years**`, `**4–25%**`, `**2:1**`.
    So the run must be at most `_BOLD_MAX_WORDS` words, which keeps every one of the four
    2026-08-11 defects and drops every false positive above.
    """
    out = []
    for m in _BOLD.finditer(text):
        if len(m.group(1).split()) <= _BOLD_MAX_WORDS:
            out.append((m.start(), m.end()))
    return out


def audit_coverage(sections: dict, spans: dict, offsets: dict, audited,
                   exempt_patterns=(), exempt_literals=None,
                   exempt_sections=None, strict_units: bool = False,
                   bold_is_result: bool = False) -> list[str]:
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
        bold = _bold_spans(hay) if bold_is_result else []
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
            # PATTERN EXEMPTIONS AND THE UNIT SUFFIX (strict_units).
            #
            # The near-universal exemption `^\d{1,2}$` ("small integer — ordinals,
            # cohort edges, counts") also swallows every integer PERCENTAGE, because
            # `_NUMBER` captures the digits and stops. In the WA paper that hid the
            # headline off-year band "~37-40%", the "2:1" and "~5:1" ratios, "about
            # 16%" and "~61%" — real results inside sections the gate called "fully
            # mapped". Same shape as the retired `^\d{1,2}\.\d$` skip this module's
            # docstring records.
            #
            # HOW THIS WAS FIRST WRITTEN, AND WHY IT DID NOTHING (corrected
            # 2026-08-09, found by an adversarial pass). The first attempt tested
            # `re.match(p, tok)` alongside `re.match(p, bare)`. But `_NUMBER` never
            # captures `%`, `M`, `×` or `$` in the first place, so `tok == bare` for
            # every token that exists and the extra conjunct was ALWAYS satisfied.
            # It was a check that could not fail, added to close a check that could
            # not fail, and shipped with a comment naming five figures it caught. It
            # caught none of them.
            #
            # The unit is in the SOURCE TEXT, not in the token, so that is where it
            # has to be read from.
            # WHAT `strict_units` MATCHES AGAINST (revised 2026-08-10). The first
            # working version made a unit-carrying token INELIGIBLE for pattern
            # exemption outright. That is too strong: some tokens carry a `%` and
            # are still labels rather than measurements — "the top 1% of donors"
            # names a cohort, and the result is the 41.2% share beside it, not
            # the 1. With no way to say so, the only remaining route was a
            # literal exemption on "1", which waives every bare 1 in the
            # document. A blanket waiver to express a narrow exception is how
            # coverage gaps get built.
            #
            # So strict_units now means: match the pattern against the token AS
            # WRITTEN, unit included. `^\d{1,2}$` still fails on `16%` — the
            # defect this flag exists for — while a caller that means it can
            # write `^1%$` and have it apply to nothing else.
            _unit = hay[m.end():m.end() + 1]
            _prefix = hay[m.start() - 1:m.start()] if m.start() else ""
            written = ("$" if _prefix == "$" else "") + tok + (
                _unit if _unit in ("%", "×") else "")
            # BOLD MEANS RESULT (bold_is_result, 2026-08-11).
            #
            # `strict_units` closed the case where `^\d{1,2}$` swallowed an integer
            # PERCENTAGE, by matching the pattern against the token as written. It
            # reaches `%` and `×` and nothing else, so a bare small integer carrying no
            # unit is still waived — and on 2026-08-11 that turned out to be hiding
            # something load-bearing FOUR times in one paper, in one day:
            #
            #   * "a median of about **16-17 years** ... versus **12**" — registration
            #     tenure, a published result, three bare integers.
            #   * the precinct cut's "a floor of **50** presidential votes" — a threshold
            #     the SQL reads, so a value changed in code but not in prose was invisible.
            #   * five odd-year office ranges whose LOW endpoints are all one or two
            #     digits, so only the upper half of each range was visible.
            #   * Appendix B's "every birth value resolves to a July-**1** sentinel".
            #
            # What every one of them has in common is that the AUTHOR bolded it. Prose
            # does not emphasise an ordinal or a cohort edge; it emphasises a finding.
            # So under this flag a small integer inside a `**...**` run is ineligible
            # for pattern exemption and must be probed or exempted by literal — while
            # `65+`, `18-29` and "the four objections" stay waived, because nobody bolds
            # those. Rolled out per-caller like `strict_units` before it; see
            # `tests/test_infrastructure/test_bold_is_result_rollout.py`.
            # ...and only for a ONE- OR TWO-DIGIT token. A bolded four-digit year is
            # still a year — `**2021**` heading a list, `**Ornstein (2024)**` — and the
            # calendar-year exemption must survive emphasis. Restricting by width is what
            # makes that automatic instead of a second special case.
            _in_bold = (bold_is_result and len(bare) <= 2 and bare.isdigit()
                        and any(a < m.start() < b for a, b in bold))
            if not _in_bold and any(re.match(p, written if strict_units else bare)
                                    for p, _ in exempt_patterns):
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


# --------------------------------------------------------------------------
# Basis registry (2026-08-10)
#
# THE DEFECT CLASS. Five of this series' figure reversals were not data changes and
# not model drift. They were a derivation and a sentence disagreeing about the
# FOOTING of a number, with nothing written down to appeal to:
#
#   df91534 / 5a7992b  Idaho May-2024 R-D  +76.8 -> +76.9 -> +76.8
#                      one round differenced the printed columns, the other the
#                      unrounded shares. Neither was wrong on its own basis.
#   69ae5af            odd-year roll-off 34.7-36.0% -> 4.9-6.6%
#                      a 38-county numerator over a statewide denominator.
#   e3938bd            a "sign flip at 2023" given a causal reading
#                      full-roll reconstruction against an active-roll official figure.
#   487091e            Section I's inferred cap
#                      per-cycle inflow against pooled outflow.
#   0b6f7c1            three state donor tables never on one basis.
#
# Every one is a label that does not describe its query. So the basis goes next to
# the derivation, in `docs/reference/derivation-bases.csv`, and a key with no
# declared basis FAILS.
#
# WHAT IS AND IS NOT ENFORCED, stated plainly because this repo's first-named
# failure mode is "writing a control as implemented that the workflow cannot
# enforce":
#
#   ENFORCED   every numeric derived key matches a declared pattern (require_bases)
#   ENFORCED   rows sharing a `quantity` agree on every basis column
#              (audit_basis_consistency) — this is 0b6f7c1 caught at write time
#   DECLARED   `computed_on`. The registry records whether a composite is computed
#              on unrounded values; nothing here evaluates the arithmetic, because
#              the composites are built through f-string key families and there is
#              no honest static way to reconstruct them. It is a disclosure, not a
#              check, and is labelled as one.
#
# Patterns are fnmatch globs over key FAMILIES, not one row per key: safe-seat's
# 203 numeric keys collapse to 39 families. A per-key registry would be 1,500 rows
# of mostly-guessed metadata across the series, which is how a register becomes
# something nobody reads.
# --------------------------------------------------------------------------

BASES_CSV = DOCS / "reference" / "derivation-bases.csv"

_BASIS_COLS = ("population", "county_footprint", "source_prefix",
               "tier_spec", "cycle_window", "computed_on")

# A declared-but-undetermined basis. Visible and countable rather than a silent
# omission — the same convention `docs/reference/source_field_register.csv` uses.
UNRESOLVED = "*** UNRESOLVED"


def load_bases(path: Path | None = None) -> list[dict]:
    """Registry rows, or [] when the file is absent."""
    import csv
    p = path or BASES_CSV
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh) if (r.get("key_pattern") or "").strip()]


def require_bases(verifier: str, derived: dict, path: Path | None = None) -> list[str]:
    """Fail on any numeric derived key whose basis is not declared for `verifier`."""
    from fnmatch import fnmatchcase
    rows = [r for r in load_bases(path) if r.get("verifier") == verifier]
    print("\n" + "-" * 78)
    print(f"BASIS REGISTRY — every derived figure must declare its footing ({verifier})")
    print("-" * 78)
    if not rows:
        print(f"  FAIL no rows for {verifier} in {BASES_CSV.name}")
        return [f"basis: {verifier} has no rows in {BASES_CSV.name}. A figure whose "
                f"population, footprint, source and cycle window are undeclared is the "
                f"defect class this registry exists for."]
    numeric = sorted(k for k, v in derived.items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    patterns = [r["key_pattern"] for r in rows]
    undeclared = [k for k in numeric
                  if not any(fnmatchcase(k, p) for p in patterns)]
    n_unres = sum(1 for r in rows
                  if any((r.get(c) or "").strip() == UNRESOLVED for c in _BASIS_COLS))
    stale = [p for p in patterns if not any(fnmatchcase(k, p) for k in numeric)]
    print(f"  {len(numeric) - len(undeclared)} of {len(numeric)} keys declared "
          f"by {len(patterns)} pattern(s); {n_unres} pattern(s) carry {UNRESOLVED}")
    if stale:
        print(f"  note {len(stale)} pattern(s) match no current key — prunable: "
              + ", ".join(sorted(stale)[:8]))
    if not undeclared:
        print("  ok   every derived figure has a declared basis")
        return []
    for k in undeclared[:40]:
        print(f"  FAIL {k}")
    if len(undeclared) > 40:
        print(f"       … and {len(undeclared) - 40} more")
    return [f"basis: {len(undeclared)} derived key(s) with no declared basis — first is "
            f"{undeclared[0]!r}. Add a pattern row to {BASES_CSV.name}."]


def audit_basis_consistency(path: Path | None = None) -> list[str]:
    """Rows naming the same `quantity` must agree on every basis column.

    This is the check that would have caught `0b6f7c1` — three state donor panels
    presented side by side on three different bases — at the moment the third was
    declared, rather than two rounds later. A blank `quantity` opts a row out: most
    keys are local to one paper and share nothing across the series.

    A divergence is not automatically an error — Texas's canvass returns omit uncontested
    seats, so the four-state seat comparison genuinely puts one state on a backfilled
    footprint. What is an error is a divergence nobody wrote down. So a row departing from
    its group's MODAL value must name where the paper discloses it, in
    `divergence_disclosed`. That keeps the finding visible instead of resolving it by
    loosening the check, which is this repo's standing rule for a failing gate.
    """
    from collections import Counter, defaultdict
    groups = defaultdict(list)
    for r in load_bases(path):
        q = (r.get("quantity") or "").strip()
        if q:
            groups[q].append(r)
    fails = []
    for q, rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        for col in _BASIS_COLS:
            vals = [(r.get(col) or "").strip() for r in rows]
            if len(set(vals)) < 2:
                continue
            modal = Counter(vals).most_common(1)[0][0]
            undisclosed = [r for r, v in zip(rows, vals)
                           if v != modal and not (r.get("divergence_disclosed") or "").strip()]
            if undisclosed:
                who = ", ".join(f"{r['verifier']}:{r['key_pattern']}" for r in undisclosed)
                fails.append(
                    f"basis: quantity {q!r} departs from its modal {col} "
                    f"({modal!r}) at {who}, with no divergence_disclosed. Either put the "
                    f"rows on one footing or name where the paper discloses the "
                    f"difference — an undisclosed basis difference inside a comparison is "
                    f"how a comparison becomes a contradiction (0b6f7c1).")
    return fails


