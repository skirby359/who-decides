"""Verify docs/who-decides-cross-state.md ("Who Returns the Ballot?").

THIS SCRIPT'S PREMISE CHANGED ON 2026-08-06, and the old premise is preserved below because
the distinction is the whole point of the file.

**What it was.** Every other paper verifier re-derives figures from a voter file. This paper
had nothing of its own to re-derive: its Methods section said Finding 1 was populated with the
"as-reported" figures from the three single-state papers, and that the harmonization script
which would compute them from one code path had not been written. Pointing this script at the
DuckDBs would have verified the single-state papers a second time and said nothing about THIS
document. So the sources were the ground truth, and the failure mode guarded against was
TRANSCRIPTION DRIFT — a source paper revised under a table that copied it.

**What changed.** `diag_cross_state_age_harmonized.py` now exists, and Findings 1 and 3 are
computed by it rather than transcribed. Those two tables therefore have a real derivation, and
the honest check is against that script — so this verifier now imports it and asserts the
paper's cells against its output. Two consequences, stated rather than left to be discovered:

  1. **This script now opens the three voter DuckDBs** (via the harmonizer) and takes ~60s
     instead of 0.2s. The old docstring's claim that it "opens no database" is retired.
  2. **Finding 2's party cuts are still transcription-checked** against the source papers,
     because they remain a synthesis of those papers' own party sections: `id_rep_65`,
     `id_dem_65` and every New York per-class share is SCRAPED from the companion, and
     `id_party_gap` is their difference. Its one exception is data-derived and worth naming
     rather than lumping in — Idaho's two May-2024 unaffiliated ballot counts come from
     `id_vrdb.duckdb`, which is what the corrected "friction, not an exclusion" sentence rests
     on. (This paragraph said Finding 2 "has no derivation of its own" until 2026-08-11, which
     was true of the party cuts and not of the finding.) The two regimes coexist on purpose and
     every probe below says which one it belongs to.

The harmonizer carries its own guard on the shared DEFINITION: it asserts that its
dissimilarity index reproduces `who-decides-washington.md`'s published ladder exactly at that
paper's printed precision, and exits non-zero otherwise. So "the paper matches the script" and
"the script matches the single-state paper it generalises" are checked in different places,
which is what keeps this verifier from being circular.

Two structural guards beyond the numbers, because both are ways this paper could ship broken:

  1. Finding 3 is a table of `[recompute]` placeholders awaiting the harmonization script. If
     that script now exists, the placeholders must be gone; if it does not, they must still be
     there. Either way round, a mismatch means the paper and the pipeline have diverged — and
     placeholders reaching a submission is the more embarrassing direction.
  2. The paper must still carry its DRAFT marker while Finding 3 is unresolved.

Reads markdown, plus the three voter DuckDBs THROUGH the harmonizer (see consequence 1 above —
the "opens no database" line that stood here was retired with the old premise and is corrected
rather than deleted, because a stale claim about data handling is the kind that gets believed).
The harmonizer emits aggregates only and never returns a row.

Run:  python scripts/verify_who_returns_ballot.py [--coverage]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _verify_prose as vp  # noqa: E402

vp.stdout_utf8()

PAPER = vp.DOCS / "who-decides-cross-state.md"
SOURCES = {
    "wa": vp.DOCS / "who-decides-washington.md",
    "ny": vp.DOCS / "who-decides-new-york.md",
    "id": vp.DOCS / "who-decides-idaho.md",
}
# The age twin of diag_cross_state_giving_turnout.py, named in the paper's Methods as the
# remaining build step. Its existence decides which way guard 1 runs.
HARMONIZER = Path(__file__).resolve().parent / "diag_cross_state_age_harmonized.py"


def scrape(text: str, label: str, rx: str, keys: tuple[str, ...], out: dict) -> None:
    """Pull the source paper's own figures. A missing anchor is fatal, per harness rule 1.

    If a source paper is reworded so this no longer matches, that is exactly the event this
    script exists to notice — the synthesis table may now be quoting a figure its source no
    longer states.
    """
    m = re.search(rx, text)
    if not m:
        raise LookupError(
            f"SOURCE ANCHOR NOT FOUND [{label}] — the source paper was reworded or the "
            f"figure changed. Re-point the probe, then re-check the synthesis table against "
            f"whatever the source now says.")
    for key, got in zip(keys, m.groups()):
        out[key] = float(got)


def build_derived() -> dict:
    src = {k: vp.normalise(p.read_text(encoding="utf-8")) for k, p in SOURCES.items()}
    d: dict[str, float] = {"_eight": 8.0}

    # --- Washington: age-composition table rows, then the summary sentence -------------
    scrape(src["wa"], "WA presidential row",
           r"\| Nov 2024 \| Presidential \| ([\d.]+)% \| [\d.]+% \| [\d.]+% \| ([\d.]+)% \|",
           ("wa_pres_1829", "wa_pres_65"), d)
    scrape(src["wa"], "WA midterm row",
           r"\| Nov 2022 \| Midterm \| ([\d.]+)% \| [\d.]+% \| [\d.]+% \| ([\d.]+)% \|",
           ("wa_mid_1829", "wa_mid_65"), d)
    scrape(src["wa"], "WA odd-year 65+ range",
           r"\(([\d.]+) / [\d.]+ / ([\d.]+)% across 2021 / 2023 / 2025\)",
           ("wa_odd_65_lo", "wa_odd_65_hi"), d)
    scrape(src["wa"], "WA odd-year 18-29 share",
           r"the 18.29 share falls from \*\*[\d.]+%\*\* to \*\*~([\d.]+)%\*\*",
           ("wa_odd_1829",), d)

    # --- New York ---------------------------------------------------------------------
    scrape(src["ny"], "NY presidential row",
           r"\| Nov 2024 \| Presidential \| \*\*([\d.]+)%\*\* \| [\d.]+% \| [\d.]+% \| ([\d.]+)% \|",
           ("ny_pres_1829", "ny_pres_65"), d)
    scrape(src["ny"], "NY midterm row",
           r"\| Nov 2022 \| Midterm \| ([\d.]+)% \| [\d.]+% \| [\d.]+% \| ([\d.]+)% \|",
           ("ny_mid_1829", "ny_mid_65"), d)
    scrape(src["ny"], "NY odd-year row",
           r"\| Nov 2023 \| Off-year \| \*\*([\d.]+)%\*\* \| [\d.]+% \| [\d.]+% \| \*\*([\d.]+)%\*\* \|",
           ("ny_odd_1829", "ny_odd_65"), d)
    # Re-pointed 2026-08-16: the NY paper's §I was rewritten when "ages hardest" was
    # withdrawn, and "vs" became "against" in this sentence. The FIGURES are unchanged --
    # this scrape failing is the cross-paper gate working, not a result moving.
    scrape(src["ny"], "NY partisan median gap",
           r"\*\*Republican median voter is (\d+) against the Democratic (\d+)\*\*",
           ("ny_rep_median", "ny_dem_median"), d)

    # The five New York generals added to Finding 2's table on 2026-08-17, scraped from the
    # source paper's own eight-row §I table on the same regime as the three above. Added
    # because extending that table put 15 numeric tokens into this synthesis with nothing
    # pointing at them -- the drift class this file exists to catch.
    for _yr, _kind in (("2016", "pres"), ("2017", "odd"), ("2019", "odd"),
                       ("2020", "pres"), ("2021", "odd")):
        _lbl = "pres" if _kind == "pres" else "odd"
        scrape(src["ny"], f"NY §I table row {_yr}",
               rf"\| Nov {_yr} \({_lbl}\) \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| "
               rf"([\d.]+)% \| \+([\d.]+) \|",
               (f"ny{_yr}_dem65", f"ny{_yr}_rep65", f"ny{_yr}_nop65",
                f"ny{_yr}_oth65", f"ny{_yr}_gap"), d)
    # And the two ranges the bullet states, so the comparison itself is bound.
    scrape(src["ny"], "NY odd-vs-presidential gap ranges",
           r"gap in odd years runs \*\*\+([\d.]+) to \+([\d.]+)\*\*; in presidential\s*years "
           r"it runs \*\*\+([\d.]+) to \+([\d.]+)\*\*",
           ("ny_oddgap_lo", "ny_oddgap_hi", "ny_presgap_lo", "ny_presgap_hi"), d)

    # --- Idaho ------------------------------------------------------------------------
    scrape(src["id"], "ID presidential row",
           r"\| Nov 2024 \| Presidential \| ([\d.]+)% \| [\d.]+% \| [\d.]+% \| ([\d.]+)% \|",
           ("id_pres_1829", "id_pres_65"), d)
    scrape(src["id"], "ID midterm row",
           r"\| Nov 2022 \| Midterm \| \*\*([\d.]+)%\*\* \| [\d.]+% \| [\d.]+% \| \*\*([\d.]+)%\*\* \|",
           ("id_mid_1829", "id_mid_65"), d)
    scrape(src["id"], "ID Republican 65+",
           r"\| Republican \| ([\d.]+)% \|", ("id_rep_65",), d)

    # --- roll scales in the cases table, added 2026-08-06 by the coverage gate ----------
    # Scraped from the source papers rather than counted from the DuckDBs: these are the
    # source papers' own headline scales, already asserted against the voter files by their
    # own verifiers, and a synthesis paper's failure mode on them is transcription.
    scrape(src["wa"], "WA roll scale", r"the ([\d.]+)M-voter roll joined to", ("wa_roll_m",), d)
    scrape(src["ny"], "NY roll scale", r"statewide file \(([\d.]+)M registrants", ("ny_roll_m",), d)
    scrape(src["id"], "ID roll scale", r"The 2026 roll \(([\d.]+)M\)", ("id_roll_m",), d)

    # --- Findings 1 and 3: DERIVED, via the harmonizer -----------------------------------
    # Imported rather than reimplemented. The paper's claim is that these cells come from one
    # code path; asserting them against a second code path here would test something the paper
    # does not claim, and would drift from it the first time either changed.
    import diag_cross_state_age_harmonized as h  # noqa: PLC0415

    hd = h.derive(vintage=2024)
    for st in ("WA", "NY", "ID"):
        pres, mid = hd[st]["pres"], hd[st]["mid"]
        d[f"h_{st}_pres_65"], d[f"h_{st}_pres_1829"] = pres["65+"], pres["18-29"]
        d[f"h_{st}_mid_65"], d[f"h_{st}_mid_1829"] = mid["65+"], mid["18-29"]
        lows = [hd[st][k] for k in h.LOW[st]]
        # Every low-salience cell is a SPAN over that state's low-salience contests, so both
        # endpoints are derived. A range asserted against a remembered pair is how two ranges
        # on the WA paper came to quote 2 of 3 off-years.
        d[f"h_{st}_low_65_lo"] = min(c["65+"] for c in lows)
        d[f"h_{st}_low_65_hi"] = max(c["65+"] for c in lows)
        d[f"h_{st}_low_1829_lo"] = min(c["18-29"] for c in lows)
        d[f"h_{st}_low_1829_hi"] = max(c["18-29"] for c in lows)
        d[f"h_{st}_dis_pres"] = hd[st]["pres"]["dissim"]
        d[f"h_{st}_dis_low_lo"] = min(c["dissim"] for c in lows)
        d[f"h_{st}_dis_low_hi"] = max(c["dissim"] for c in lows)
        d[f"h_{st}_core_lo"] = min(c["core"] for c in lows)
        d[f"h_{st}_core_hi"] = max(c["core"] for c in lows)
        # Senior-to-youth ratios, which Finding 1's prose now states per state because the
        # harmonized numbers contradicted the old "roughly triples in every state".
        d[f"h_{st}_ratio_pres"] = pres["65+"] / pres["18-29"]
        # PER-CONTEST cells (2026-08-09). Finding 1 now prints each state's
        # low-salience ladder in order of recency, because the series turned out
        # to be near-monotone in distance from the 2026 roll and that confound was
        # invisible while only the span was shown. Every cell in those ladders is
        # asserted, not just their endpoints.
        for key in h.LOW[st]:
            d[f"h_{st}_{key}_65"] = hd[st][key]["65+"]
            d[f"h_{st}_{key}_core"] = hd[st][key]["core"]
        # LAG-MATCHED CELL: this state's low-salience contest nearest the roll extract.
        # Finding 3's cross-state claim used to rest on each state's EXTREME cell, and those
        # sit at lags of 0 to 9 years — the confound Finding 1's own footnote says makes
        # level comparison unsafe. Matching on lag removes it, and the claim survives.
        #
        # Only the lag-matched cell's n and dissimilarity are stored. A first version of this
        # derived both for EVERY class in every state, which added 22 keys the paper does not
        # print and pushed this verifier's no-probe count 23 -> 45. Same rule as the WA
        # verifier: derive what a probe reads.
        _newest = h.LOW[st][-1]
        d[f"h_{st}_lagmatch_dis"] = hd[st][_newest]["dissim"]
        d[f"h_{st}_lagmatch_65"] = hd[st][_newest]["65+"]
        d[f"h_{st}_lagmatch_n"] = float(hd[st][_newest]["n"])

        d[f"h_{st}_ratio_low_lo"] = min(c["65+"] / c["18-29"] for c in lows)
        d[f"h_{st}_ratio_low_hi"] = max(c["65+"] / c["18-29"] for c in lows)
    # NY party-conditional 65+ shares, PER CLASS (2026-08-09). Finding 2 used to
    # set New York's odd-year gap beside Idaho's presidential one — different
    # rungs of the salience ladder this paper exists to build. And the striking
    # New York number is its 2025 general, which Finding 1 identifies as the
    # HIGH-salience odd-year; on New York's genuinely lowest-salience contest the
    # gap is nearly symmetric, which inverts the reading. All three classes are
    # derived so the comparison cannot silently revert to one of them.
    d["dis_quarter_ratio"] = d["h_ID_dis_low_hi"] / d["h_NY_dis_low_hi"]
    # The lag-matched margin, which is what Finding 3 now claims.
    d["lagmatch_id_over_wa"] = d["h_ID_lagmatch_dis"] - d["h_WA_lagmatch_dis"]
    # NY's odd-year 65+ SPAN against the presidential-to-Idaho separation, both endpoints.
    # The paper called the first "wider" than the second and it is not — see the ledger.
    d["ny_low_span"] = d["h_NY_low_65_hi"] - d["h_NY_low_65_lo"]
    d["ny_pres_to_id_lo"] = d["h_ID_low_65_lo"] - d["h_NY_pres_65"]
    d["ny_pres_to_id_hi"] = d["h_ID_low_65_hi"] - d["h_NY_pres_65"]
    # By how much the withdrawn "wider range" comparative actually held — 0.05 points,
    # against an Idaho age bracket of 1.7-2.6. Derived so the retraction is measured.
    d["wider_range_margin"] = d["ny_low_span"] - d["ny_pres_to_id_lo"]
    # Cross-state spans the prose states but no probe consumed until 2026-08-10.
    d["pres_65_lo"] = min(d[f"h_{s}_pres_65"] for s in ("WA", "NY", "ID"))
    d["pres_65_hi"] = max(d[f"h_{s}_pres_65"] for s in ("WA", "NY", "ID"))
    d["pres_1829_lo"] = min(d[f"h_{s}_pres_1829"] for s in ("WA", "NY", "ID"))
    d["pres_1829_hi"] = max(d[f"h_{s}_pres_1829"] for s in ("WA", "NY", "ID"))
    d["core_lo_all"] = min(d[f"h_{s}_core_lo"] for s in ("WA", "NY", "ID"))
    d["core_hi_all"] = max(d[f"h_{s}_core_hi"] for s in ("WA", "NY", "ID"))
    # The CVAP benchmark itself (2026-08-11, external referee). The dissimilarity index is
    # this paper's main cross-state instrument and every cell is measured against these
    # four numbers per state — which appeared nowhere in the paper.
    # Same vintage the harmonizer was called with above — pinned, not defaulted, because
    # a benchmark read at a different vintage would silently move every index cell.
    _cvap = h.load_cvap(2024)
    for st in ("WA", "NY", "ID"):
        for b in h.BANDS:
            d[f"cvap_{st}_{b}"] = _cvap[st][b]

    import duckdb  # noqa: PLC0415 — same lazy import as the harmonizer above
    _con = duckdb.connect(str(vp.DATA / "ny_vrdb.duckdb"), read_only=True)
    try:
        for year, tag in ((2024, "pres"), (2023, "low23"), (2025, "low25")):
            rows = dict(_con.execute(f"""
                SELECT v.party,
                       100.0 * SUM(CASE WHEN date_diff('year', v.birthdate,
                                        DATE '{year}-11-05') >= 65 THEN 1 ELSE 0 END)
                       / COUNT(*)
                FROM voters v
                JOIN (SELECT DISTINCT state_voter_id FROM voter_participation
                      WHERE election_year = {year} AND kind = 'GENERAL') h
                  USING (state_voter_id)
                WHERE v.birthdate IS NOT NULL AND v.party IN ('DEM', 'REP')
                GROUP BY 1""").fetchall())
            d[f"ny_{tag}_rep65"] = float(rows["REP"])
            d[f"ny_{tag}_dem65"] = float(rows["DEM"])
            d[f"ny_{tag}_gap"] = float(rows["REP"]) - float(rows["DEM"])
    finally:
        _con.close()


    # The prose's cross-state spans over the three presidential electorates.
    d["h_pres_dis_lo"] = min(d[f"h_{s}_dis_pres"] for s in ("WA", "NY", "ID"))
    d["h_pres_dis_hi"] = max(d[f"h_{s}_dis_pres"] for s in ("WA", "NY", "ID"))
    # The WA reconciliation footnote: the gap between the unrounded and published benchmarks,
    # and the published ladder itself. Derived rather than exempted to the WA paper, because
    # the footnote's whole claim is that this script reproduces that ladder — so the ladder is
    # this script's output on the paper's own rounded benchmark, not a transcription.
    d["h_wa_bench_gap"] = max(
        abs(hd["WA"][k]["dissim"] - hd["WA"][k]["dissim_pub"])
        for k in ("pres", "mid", *h.LOW["WA"]))
    d["h_wa_pub_pres"] = hd["WA"]["pres"]["dissim_pub"]
    d["h_wa_pub_mid"] = hd["WA"]["mid"]["dissim_pub"]
    d["h_wa_pub_low_lo"] = min(hd["WA"][k]["dissim_pub"] for k in h.LOW["WA"])
    d["h_wa_pub_low_hi"] = max(hd["WA"][k]["dissim_pub"] for k in h.LOW["WA"])
    # The multiplication of the senior-to-youth ratio, min and max across the three states.
    # The paper states this as the span "1.5x to 4.9x", so both endpoints are derived over
    # every (state, low-salience contest) pair rather than eyeballed off the ratio table.
    mults = [d[f"h_{s}_ratio_low_{e}"] / d[f"h_{s}_ratio_pres"]
             for s in ("WA", "NY", "ID") for e in ("lo", "hi")]
    d["h_mult_lo"], d["h_mult_hi"] = min(mults), max(mults)
    scrape(src["id"], "ID Democratic 65+ and under-30",
           r"\| Democratic \| ([\d.]+)% \| ([\d.]+)% \|", ("id_dem_65", "id_dem_1829"), d)
    # The UNAFFILIATED row, added 2026-08-15. Finding 2 quoted Idaho's cross-party 65+ parity
    # and then generalised it into "the youth lives outside the two major parties" — which the
    # Idaho paper withdrew that day, because Democratic and unaffiliated voters are LEVEL on the
    # under-30 share and the parity is a senior-end result only. Scraped rather than restated so
    # the synthesis cannot drift from the companion it is summarising, which is the whole reason
    # these three keys come from the paper instead of from the database.
    scrape(src["id"], "ID unaffiliated 65+ and under-30",
           r"\| \*\*Unaffiliated\*\* \| \*\*([\d.]+)%\*\* \| \*\*([\d.]+)%\*\*",
           ("id_una_65", "id_una_1829"), d)
    # Idaho's presidential party gap, the matched-class counterpart to New York's.
    # Placed at the END of this function on purpose: id_rep_65 and id_dem_65 are
    # scraped from the Idaho paper at two separate points above, and computing the
    # difference before the second one runs raises a KeyError that surfaces as
    # "SOURCE SCRAPE FAILED" with no indication that ordering is the cause.
    d["id_party_gap"] = d["id_rep_65"] - d["id_dem_65"]

    # Idaho's May-2024 unaffiliated ballot counts. Finding 2 used to say the closed
    # primary "locks that youth out by design"; it is a friction, not an exclusion —
    # the Democratic primary is open to unaffiliated voters and the Republican one
    # admits them on affiliating at the poll book. These two counts are what the
    # corrected sentence rests on.
    import duckdb  # noqa: PLC0415
    _ic = duckdb.connect(str(vp.DATA / "id_vrdb.duckdb"), read_only=True)
    try:
        for choice, key in (("DEM", "id_una_dem_n"), ("REP", "id_una_rep_n")):
            d[key], = _ic.execute(f"""
                SELECT COUNT(*) FROM voter_participation p JOIN voters v USING (state_voter_id)
                WHERE p.election_date = DATE '2024-05-21' AND p.kind = 'PRIMARY'
                  AND v.party = 'UNA' AND p.ballot_choice = '{choice}'""").fetchone()
    finally:
        _ic.close()

    # WA's habitual-core floor ON THE WA PAPER'S OWN BASIS (2026-08-11). Finding 3's WA core
    # column reads 95.5-97.5% while `who-decides-washington.md` says 92-97% of the same three
    # off-years, and BOTH are asserted by their own papers' gates. The divergence is entirely a
    # population difference: the WA verifier counts every `voting_history` row for the contest,
    # while this study's harmonizer is age-banded throughout and so joins `voters` and requires a
    # usable birthdate. For 2021 that drops 105,969 voters who overlap the 2024 presidential far
    # less, moving the floor 92.2 -> 95.5; 2023 moves 0.3 and 2025 not at all. Derived here so
    # the reconciliation is asserted rather than asserted-about, exactly as the dissimilarity
    # column's 0.05-point reconciliation already is.
    _wa = duckdb.connect(str(vp.DATA / "wa_vrdb.duckdb"), read_only=True)
    try:
        cores = []
        for date in ("2021-11-02", "2023-11-07", "2025-11-04"):
            v, = _wa.execute(f"""
                WITH off AS (SELECT DISTINCT state_voter_id sid FROM voting_history
                             WHERE election_date = DATE '{date}'),
                     pres AS (SELECT DISTINCT state_voter_id sid FROM voting_history
                              WHERE election_date = DATE '2024-11-05')
                SELECT 100.0 * COUNT(*) FILTER (WHERE sid IN (SELECT sid FROM pres))
                       / COUNT(*) FROM off""").fetchone()
            cores.append(float(v))
        d["wa_core_lo_paperbasis"] = min(cores)

        # SURVIVORSHIP, on THIS study's basis (2026-08-11, external referee on the WA
        # paper). Every core cell measured BEFORE November 2024 is an upper bound: the
        # electorate is reconstructed from a roll built after the fact, so a voter who
        # cast that ballot and has since died or moved is dropped from both sides of the
        # overlap — and is exactly the population that could not have voted in 2024.
        #
        # WA is the only one of the three states with a retained roll snapshot, so it is
        # the only place the size of the bias can be MEASURED rather than argued. It is
        # measured on the harmonizer's own age-banded population, not the WA paper's, so
        # the correction applies to the cells in Finding 3's table. All three are lower
        # bounds: the Sept-2023 snapshot cannot see anyone who left before it.
        _corr = []
        for date in ("2021-11-02", "2023-11-07", "2025-11-04"):
            n, both = _wa.execute(f"""
                WITH off AS (SELECT DISTINCT h.state_voter_id sid FROM voting_history h
                             JOIN voters v USING (state_voter_id)
                             WHERE h.election_date = DATE '{date}'
                               AND v.birthdate IS NOT NULL),
                     pres AS (SELECT DISTINCT h.state_voter_id sid FROM voting_history h
                              JOIN voters v USING (state_voter_id)
                              WHERE h.election_date = DATE '2024-11-05'
                                AND v.birthdate IS NOT NULL)
                SELECT COUNT(*), COUNT(*) FILTER (WHERE sid IN (SELECT sid FROM pres))
                FROM off""").fetchone()
            gone, = _wa.execute(f"""
                SELECT COUNT(*) FROM voters_20230901 s
                LEFT JOIN voters v USING (state_voter_id)
                WHERE v.state_voter_id IS NULL AND s.birthdate IS NOT NULL
                  AND EXISTS (SELECT 1 FROM voting_history h
                              WHERE h.state_voter_id = s.state_voter_id
                                AND h.election_date = DATE '{date}')""").fetchone()
            _corr.append(100.0 * both / (n + gone))
        # Per-cell, because the note names 2021 and 2023 specifically — the MAX of the
        # corrected values is 2025's and would silently answer a different question.
        d["wa_core_corr_lo"] = _corr[0]          # 2021, also the minimum
        d["wa_core_corr_2023"] = _corr[1]
        d["wa_core_infl_min"] = d["h_WA_low25_core"] - _corr[2]
        # The mechanism, not just the gap: voters with a 2021 history record but no usable
        # birth year, i.e. exactly the rows the age-banded population drops.
        d["wa_2021_dropped"], = _wa.execute("""
            SELECT COUNT(*) FROM (
              SELECT DISTINCT h.state_voter_id FROM voting_history h
              WHERE h.election_date = DATE '2021-11-02')
            WHERE state_voter_id NOT IN (
              SELECT state_voter_id FROM voters WHERE birthdate IS NOT NULL)"""
        ).fetchone()
    finally:
        _wa.close()

    return d


PROBES = [
    # ---- Finding 1: DERIVED from the harmonizer (see build_derived) ----------------------
    # Every low-salience cell is a SPAN, so both endpoints are asserted. Tolerance is the
    # half-width of the printed precision, not a comfort margin.
    ("Finding 1, WA row — harmonized",
     r"\*\*WA\*\* \| ([\d.]+)% / ([\d.]+)% \| ([\d.]+)% / ([\d.]+)% \| "
     r"([\d.]+)–([\d.]+)% / ([\d.]+)–([\d.]+)%",
     ("h_WA_pres_65", "h_WA_pres_1829", "h_WA_mid_65", "h_WA_mid_1829",
      "h_WA_low_65_lo", "h_WA_low_65_hi", "h_WA_low_1829_lo", "h_WA_low_1829_hi"), 0.05),
    ("Finding 1, NY row — harmonized",
     r"\*\*NY\*\* \| ([\d.]+)% / ([\d.]+)% \| ([\d.]+)% / ([\d.]+)% \| "
     r"([\d.]+)–([\d.]+)% / ([\d.]+)–([\d.]+)%",
     ("h_NY_pres_65", "h_NY_pres_1829", "h_NY_mid_65", "h_NY_mid_1829",
      "h_NY_low_65_lo", "h_NY_low_65_hi", "h_NY_low_1829_lo", "h_NY_low_1829_hi"), 0.05),
    # ID now carries a SPAN: the harmonizer was widened 2026-08-09 from one
    # Republican primary to all three loaded, and NY from two odd-year generals to
    # all five. The selection, not the states, was driving two published claims.
    ("Finding 1, ID row — harmonized, all three primaries",
     r"\*\*ID\*\* \| ([\d.]+)% / ([\d.]+)% \| ([\d.]+)% / ([\d.]+)% \| ([\d.]+)–([\d.]+)% / "
     r"([\d.]+)–([\d.]+)%",
     ("h_ID_pres_65", "h_ID_pres_1829", "h_ID_mid_65", "h_ID_mid_1829",
      "h_ID_low_65_lo", "h_ID_low_65_hi", "h_ID_low_1829_lo", "h_ID_low_1829_hi"), 0.05),
    ("Finding 1 — presidential senior-to-youth ratios, all three states",
     r"\(WA ([\d.]+), NY ([\d.]+),\s*ID ([\d.]+)\)",
     ("h_WA_ratio_pres", "h_NY_ratio_pres", "h_ID_ratio_pres"), 0.05),
    ("Finding 1 — lowest-salience ratio spans, WA then NY then ID",
     r"to \*\*([\d.]+)–([\d.]+):1\*\* in Washington, \*\*([\d.]+)–([\d.]+):1\*\* in New York,\s*"
     r"and \*\*([\d.]+)–([\d.]+):1\*\*",
     ("h_WA_ratio_low_lo", "h_WA_ratio_low_hi", "h_NY_ratio_low_lo", "h_NY_ratio_low_hi",
      "h_ID_ratio_low_lo", "h_ID_ratio_low_hi"), 0.05),
    ("Finding 1 — Idaho's lowest-salience cells restated in prose",
     r"primaries run ([\d.]+)–([\d.]+)% over 65 against ([\d.]+)–([\d.]+)% under 30",
     ("h_ID_low_65_lo", "h_ID_low_65_hi", "h_ID_low_1829_lo", "h_ID_low_1829_hi"), 0.05),
    ("Finding 1 — Idaho's weakest primary against New York's oldest general",
     r"the 2022 primary at ([\d.]+)%, sits just below New York's 2023 general at ([\d.]+)%",
     ("h_ID_low_65_lo", "h_NY_low_65_hi"), 0.05),
    # Surfaced by strict_units 2026-08-10: every endpoint below is a bare one- or
    # two-digit integer and was auto-exempt by COVERAGE_EXEMPT's small-integer rule.
    ("Finding 1 — the three presidential rows' shared span",
     r"strikingly similar \((\d+)–(\d+)% 65\+, (\d+)–(\d+)% 18–29\)",
     ("pres_65_lo", "pres_65_hi", "pres_1829_lo", "pres_1829_hi"), 0.5),
    ("Finding 3 — the dissimilarity index restated as a share of the distribution",
     r"i\.e\. ~(\d+)–(\d+)% of the distribution", ("h_pres_dis_lo", "h_pres_dis_hi"), 0.5),
    ("Finding 3 — the habitual-core span in prose",
     r"Between (\d+)% and (\d+)% of every low-salience", ("core_lo_all", "core_hi_all"), 0.5),
    ("Finding 2 — the NY party gap by class, and Idaho's",
     # Re-pointed 2026-08-17: the source table grew from three New York rows to eight, so the
     # three rows this synthesis binds are no longer adjacent. Matched individually rather
     # than as a block -- the figures are unchanged.
     r"NY, Nov 2024 presidential \| \*\*\+([\d.]+)\*\* pts \(([\d.]+) vs ([\d.]+)\) \|"
     r"(?:.|\n)*?"
     r"\| NY, Nov 2023 odd-year[^|]*\| \*\*\+([\d.]+)\*\* pts \(([\d.]+) vs ([\d.]+)\) \|"
     r"(?:.|\n)*?"
     r"\| NY, Nov 2025 odd-year[^|]*\| \*\*\+([\d.]+)\*\* pts \(([\d.]+) vs ([\d.]+)\) \|",
     ("ny_pres_gap", "ny_pres_rep65", "ny_pres_dem65",
      "ny_low23_gap", "ny_low23_rep65", "ny_low23_dem65",
      "ny_low25_gap", "ny_low25_rep65", "ny_low25_dem65"), 0.05),
    ("Finding 2 — the matched-class contrast restated",
     r"Republican electorate is ([\d.]+)\s*points older on the 65\+ share where Idaho's is ([\d.]+)",
     ("ny_pres_gap", "id_party_gap"), 0.05),
    ("Finding 2 — NY 2016 row", r"\| NY, Nov 2016 presidential \| \*\*\+([\d.]+)\*\* pts "
     r"\(([\d.]+) vs ([\d.]+)\) \|", ("ny2016_gap", "ny2016_rep65", "ny2016_dem65"), 0.05),
    ("Finding 2 — NY 2020 row", r"\| NY, Nov 2020 presidential \| \*\*\+([\d.]+)\*\* pts "
     r"\(([\d.]+) vs ([\d.]+)\) \|", ("ny2020_gap", "ny2020_rep65", "ny2020_dem65"), 0.05),
    ("Finding 2 — NY 2017 row", r"\| NY, Nov 2017 odd-year[^|]*\| \*\*\+([\d.]+)\*\* pts "
     r"\(([\d.]+) vs ([\d.]+)\) \|", ("ny2017_gap", "ny2017_rep65", "ny2017_dem65"), 0.05),
    ("Finding 2 — NY 2019 row", r"\| NY, Nov 2019 odd-year \| \*\*\+([\d.]+)\*\* pts "
     r"\(([\d.]+) vs ([\d.]+)\) \|", ("ny2019_gap", "ny2019_rep65", "ny2019_dem65"), 0.05),
    ("Finding 2 — NY 2021 row", r"\| NY, Nov 2021 odd-year[^|]*\| \*\*\+([\d.]+)\*\* pts "
     r"\(([\d.]+) vs ([\d.]+)\) \|", ("ny2021_gap", "ny2021_rep65", "ny2021_dem65"), 0.05),
    ("Finding 2 — the odd-vs-presidential range comparison",
     r"gaps run \+([\d.]+) to \+([\d.]+), against \+([\d.]+) to \+([\d.]+) in its three",
     ("ny_oddgap_lo", "ny_oddgap_hi", "ny_presgap_lo", "ny_presgap_hi"), 0.05),
    ("Finding 2 — the eight-for-eight level ordering",
     r"hold, (\d+) times out of (\d+), is the level ordering",
     ("_eight", "_eight"), 0),
    ("Finding 2 — the 2025 gap and the 2023 near-symmetry restated",
     r"a ([\d.]+)-point gap with the\s*Republican median voter[^|]*?nearly symmetric at "
     r"([\d.]+)\s*points",
     ("ny_low25_gap", "ny_low23_gap"), 0.05),
    # --- The external-referee round, 2026-08-11 -------------------------
    ("Finding 1 — the NY ladder's fifth cell, printed rather than dropped",
     r"→ \*\*41\.6\*\* \(2023\) → \*(\d+\.\d+)\* \(2025\)", "h_NY_low25_65", 0.05),
    ("Finding 1 — the NY span against the presidential-to-Idaho separation",
     r"a range of \*\*([\d.]+) points\*\* — as wide as the\s*gap between New York's\s*"
     r"presidential electorate and Idaho's \*weakest\* primary \(([\d.]+)\), though well short "
     r"of the gap\s*to its strongest \(([\d.]+)\)",
     ("ny_low_span", "ny_pres_to_id_lo", "ny_pres_to_id_hi"), 0.05),
    ("Finding 1 — the margin by which the withdrawn comparative held",
     r"exceeds\s*the narrowest of those separations by \*\*([\d.]+) points\*\*",
     "wider_range_margin", 0.005),
    ("Finding 1 — the mayoral and non-mayoral cells",
     r"and so was \*\*2017, at ([\d.]+)%\*\*.*?all three mayoral cells \(([\d.]+), ([\d.]+), "
     r"([\d.]+)\) sit below the two non-mayoral ones \(([\d.]+), ([\d.]+)\)",
     ("h_NY_low17_65", "h_NY_low17_65", "h_NY_low21_65", "h_NY_low25_65",
      "h_NY_low19_65", "h_NY_low23_65"), 0.05),
    ("Finding 3 — the CVAP benchmark, all three states",
     r"\| Washington \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
     r"\| New York \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|\s*"
     r"\| Idaho \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|",
     ("cvap_WA_18-29", "cvap_WA_30-44", "cvap_WA_45-64", "cvap_WA_65+",
      "cvap_NY_18-29", "cvap_NY_30-44", "cvap_NY_45-64", "cvap_NY_65+",
      "cvap_ID_18-29", "cvap_ID_30-44", "cvap_ID_45-64", "cvap_ID_65+"), 0.05),
    ("Finding 3 — the lag-matched cells, with their denominators",
     r"\| \*\*ID\*\* — May 2026 closed Republican primary \| ([\d,]+) \| \*\*([\d.]+)\*\* \| "
     r"([\d.]+)% \|\s*"
     r"\| \*\*WA\*\* — Nov 2025 odd-year general \| ([\d,]+) \| ([\d.]+) \| ([\d.]+)% \|\s*"
     r"\| \*\*NY\*\* — Nov 2025 odd-year general \| ([\d,]+) \| ([\d.]+) \| ([\d.]+)% \|",
     ("h_ID_lagmatch_n", "h_ID_lagmatch_dis", "h_ID_lagmatch_65",
      "h_WA_lagmatch_n", "h_WA_lagmatch_dis", "h_WA_lagmatch_65",
      "h_NY_lagmatch_n", "h_NY_lagmatch_dis", "h_NY_lagmatch_65"), 0.05),
    ("Finding 3 / boundary — the lag-matched margin, both statements",
     r"by ([\d.]+) index points over Washington", "lagmatch_id_over_wa", 0.05),
    ("boundary — the lag-matched margin restated",
     r"Idaho ahead by ([\d.]+) index points", "lagmatch_id_over_wa", 0.05),
    ("Finding 3 — the survivorship caveat on the core row, measured on WA",
     r"moves 2021 from\s*([\d.]+)% to \*\*([\d.]+)%\*\*, 2023 from ([\d.]+)% to "
     r"\*\*([\d.]+)%\*\*, and 2025 — four months from the roll — by\s*\*\*([\d.]+)\*\* points",
     ("h_WA_core_lo", "wa_core_corr_lo", "h_WA_core_hi", "wa_core_corr_2023",
      "wa_core_infl_min"), 0.05),
    # The WA habitual-core reconciliation (2026-08-11). Probed rather than described, because
    # its whole content is that two asserted figures differ and why.
    ("Finding 3 — the 2021 rows the age-banded population drops",
     r"In 2021 that drops \*\*([\d,]+)\*\* voters", "wa_2021_dropped", 0),
    ("Finding 3 — the WA habitual-core floor on the single-state paper's own basis",
     r"which reads \*\*([\d.]+)\*\*% for the same",
     "wa_core_lo_paperbasis", 0.05),
    ("Finding 2 — unaffiliated ballot counts, May 2024",
     r"In May 2024, ([\d,]+) currently-unaffiliated voters pulled a\s*Democratic ballot and "
     r"([\d,]+) pulled a Republican one",
     ("id_una_dem_n", "id_una_rep_n"), 0),
    ("Finding 2 — the surviving asymmetry restated",
     r"sits at \*high\* salience \(\+([\d.]+) against \+([\d.]+)\)",
     ("ny_pres_gap", "id_party_gap"), 0.05),
    ("Finding 2 — Idaho's presidential row in the class table",
     r"ID, Nov 2024 presidential \| \*\*\+([\d.]+)\*\* pts \(([\d.]+) vs ([\d.]+)\)",
     ("id_party_gap", "id_rep_65", "id_dem_65"), 0.05),
    ("Finding 1 — Idaho's dissimilarity span in the same bullet",
     r"dissimilarity index \(([\d.]+)–([\d.]+)\) is above every gen",
     ("h_ID_dis_low_lo", "h_ID_dis_low_hi"), 0.05),
    ("Finding 3 — the quarter-again arithmetic, stated explicitly",
     r"\(([\d.]+) / ([\d.]+) = ([\d.]+)\) as far from",
     ("h_ID_dis_low_hi", "h_NY_dis_low_hi", "dis_quarter_ratio"), 0.05),
    ("Finding 3 — Idaho's core restated in the caution",
     r"read Idaho's ([\d.]+)% as showing", "h_ID_core_hi", 0.05),
    ("Finding 1 — the NY odd-year 65+ ladder, in order of recency",
     r"NY odd-year generals, 65\+ \| \*\*([\d.]+)\*\* \(2017\) → ([\d.]+) \(2019\) → ([\d.]+) "
     r"\(2021\) → \*\*([\d.]+)\*\* \(2023\)",
     ("h_NY_low17_65", "h_NY_low19_65", "h_NY_low21_65", "h_NY_low23_65"), 0.05),
    ("Finding 1 — the ID primary 65+ ladder, in order of recency",
     r"ID closed R primaries, 65\+ \| \*\*([\d.]+)\*\* \(2022\) → ([\d.]+) \(2024\) → "
     r"\*\*([\d.]+)\*\* \(2026\)",
     ("h_ID_lowrep22_65", "h_ID_lowrep24_65", "h_ID_lowrep26_65"), 0.05),
    ("Finding 1 — the selection the widened set replaced",
     r"New York's floor read ([\d.]+)% rather than ([\d.]+)%",
     ("h_NY_low25_65", "h_NY_low17_65"), 0.5),
    ("Finding 1 — 2021 was also a mayoral year",
     r"\*\*2021 was also a mayoral year and reads ([\d.]+)%\*\*", "h_NY_low21_65", 0.05),
    ("Finding 3 — the ID core ladder shows the lag dependence",
     r"([\d.]+)% \(2022\) → \*\*([\d.]+)% \(2024\)\*\* → ([\d.]+)% \(2026\)",
     ("h_ID_lowrep22_core", "h_ID_lowrep24_core", "h_ID_lowrep26_core"), 0.05),
    ("Finding 3 — the NY core ladder",
     r"runs ([\d.]+) \(2017\) → ([\d.]+) → ([\d.]+) → ([\d.]+)\s*\(2023\) in order of recency",
     ("h_NY_low17_core", "h_NY_low19_core", "h_NY_low21_core", "h_NY_low23_core"), 0.05),
    ("Boundary — the two ladders restated",
     r"NY ([\d.]+) → ([\d.]+) across 2017–2023, ID ([\d.]+) → ([\d.]+) across 2022–2026",
     ("h_NY_low17_65", "h_NY_low23_65", "h_ID_lowrep22_65", "h_ID_lowrep26_65"), 0.05),
    ("Finding 1 — the NY odd-year 65+ span, all five generals",
     r"five odd-year generals span ([\d.]+)% to\s*([\d.]+)% over 65",
     ("h_NY_low_65_lo", "h_NY_low_65_hi"), 0.05),

    # ---- Finding 3: DERIVED from the harmonizer ------------------------------------------
    ("Finding 3 — dissimilarity row, all three states",
     r"lowest-salience\) \| ([\d.]+) → ([\d.]+)–([\d.]+) \| ([\d.]+) → ([\d.]+)–([\d.]+) \| "
     r"([\d.]+) → ([\d.]+)–([\d.]+) \|",
     ("h_WA_dis_pres", "h_WA_dis_low_lo", "h_WA_dis_low_hi",
      "h_NY_dis_pres", "h_NY_dis_low_lo", "h_NY_dis_low_hi",
      "h_ID_dis_pres", "h_ID_dis_low_lo", "h_ID_dis_low_hi"), 0.05),
    ("Finding 3 — habitual-core row, all three states",
     r"presidential\) \| ([\d.]+)–([\d.]+)% \| ([\d.]+)–([\d.]+)% \| ([\d.]+)–([\d.]+)% \|",
     ("h_WA_core_lo", "h_WA_core_hi", "h_NY_core_lo", "h_NY_core_hi",
      "h_ID_core_lo", "h_ID_core_hi"), 0.05),
    ("Finding 3 — presidential dissimilarity span in prose",
     r"population \(([\d.]+)–([\d.]+) index points", ("h_pres_dis_lo", "h_pres_dis_hi"), 0.05),
    ("Finding 3 — the low-salience dissimilarity restatements",
     r"Washington reaches ([\d.]+)–([\d.]+) and New York ([\d.]+)–([\d.]+)",
     ("h_WA_dis_low_lo", "h_WA_dis_low_hi", "h_NY_dis_low_lo", "h_NY_dis_low_hi"), 0.05),
    ("Finding 3 — Idaho's dissimilarity span restated",
     r"primaries reach ([\d.]+)–([\d.]+) — about a quarter again",
     ("h_ID_dis_low_lo", "h_ID_dis_low_hi"), 0.05),
    ("Finding 3 — the habitual-core extremes restated",
     r"most\* core-like \(([\d.]+)%\);\s*New York's 2017 general is the least \(([\d.]+)%\)",
     ("h_ID_core_hi", "h_NY_core_lo"), 0.05),
    ("Finding 3 — the benchmark-rounding gap the footnote states",
     r"It differs\s*by ([\d.]+) index points", "h_wa_bench_gap", 0.005),
    ("Finding 1 — the ratio-multiplication span across all state/contest pairs",
     r"ranges from a ([\d.]+)× to a ([\d.]+)× multiplication",
     ("h_mult_lo", "h_mult_hi"), 0.05),
    ("Finding 3 footnote — WA's published ladder, as this script reproduces it",
     r"the WA paper's own ladder\*\* \(([\d.]+) → ([\d.]+)–([\d.]+)\)",
     ("h_wa_pub_pres", "h_wa_pub_low_lo", "h_wa_pub_low_hi"), 0.05),
    ("Finding 3 footnote — the same ladder restated with the midterm",
     r"this script reproduces ([\d.]+) / ([\d.]+) / ([\d.]+)–([\d.]+) exactly",
     ("h_wa_pub_pres", "h_wa_pub_mid", "h_wa_pub_low_lo", "h_wa_pub_low_hi"), 0.05),

    ("Finding 2, NY partisan median gap",
     r"Republican median voter at (\d+) against\s*the Democratic (\d+)",
     ("ny_rep_median", "ny_dem_median"), 0),
    ("Finding 2, ID senior-share parity across the parties",
     r"same 65\+ share \(\*\*([\d.]+)% vs ([\d.]+)%\*\*", ("id_rep_65", "id_dem_65"), 0),
    ("Finding 2, ID unaffiliated senior deficit",
     r"below both on that measure \(([\d.]+)%\)", "id_una_65", 0.05),
    ("Finding 2, ID unaffiliated and Democratic level on the under-30 share",
     r"unaffiliated \(([\d.]+)%\) and Democratic \(([\d.]+)%\) voters are level",
     ("id_una_1829", "id_dem_1829"), 0.05),

    # ---- added 2026-08-06 by the coverage gate ------------------------------------------
    ("cases table — per-state roll scale, against each source paper",
     r"`data/wa_vrdb\.duckdb` \(([\d.]+)M; year of birth\)", "wa_roll_m", 0.005),
    # "party + DOB" corrected to "party + year of birth" on 2026-08-10: the NY file
    # carries a birth YEAR, materialised as a July 1 placeholder on every row. The
    # cell claimed a precision the source does not publish [ny-vrdb-birth-precision], in the
    # one table a reader consults to see what each state contributes. That claim_id carries the
    # measurement in docs/reference/source_availability_claims.csv: 1 distinct month-day
    # ('07-01') over 13,540,558 rows across 146 birth years, aggregate query only. The claim
    # scan is right to demand that backing — this comment shipped in 5470f7f without the
    # registry row, which left tests/test_infrastructure/ red at HEAD.
    ("cases table — NY roll scale",
     r"`data/ny_vrdb\.duckdb` \(([\d.]+)M; party \+ year of birth\)",
     "ny_roll_m", 0.005),
    ("cases table — ID roll scale",
     r"`data/id_vrdb\.duckdb` \(([\d.]+)M; party \+ age \+ primary ballot\)",
     "id_roll_m", 0.005),
    ("Finding 1 footnote — ID midterm 65+ restated",
     r"gradient reaching ([\d.]+)% 65\+ before the primary cut", "id_mid_65", 0.05),
]

UNCHECKED = (
    "Finding 2's NY 'GOP 65+ jumps from 32% to 43%' — the NY paper reports that cut in a "
    "party-by-election table whose column basis differs from the age-composition table used "
    "above; probing it would require asserting which basis was intended. Check by hand.",
    "Finding 3's two harmonized metrics — unbuilt by construction; see guard 1 below.",
    "Idaho's 'grayest of all' lowest-salience cell — prose, not a figure.",
    "Every source figure is checked against the SOURCE PAPER's prose, not against the voter "
    "files. The single-state verifiers own that layer.",
)


def structural_guards(raw: str) -> list[str]:
    """The two ways this paper ships broken that no numeric probe would catch."""
    fails = []
    n_recompute = raw.count("[recompute]")
    if HARMONIZER.exists():
        if n_recompute:
            fails.append(
                f"{HARMONIZER.name} now exists but the paper still carries {n_recompute} "
                f"'[recompute]' placeholder(s). Fill Finding 3 from the script.")
    else:
        if n_recompute < 2:
            fails.append(
                f"Finding 3's placeholders are gone ({n_recompute} left) but "
                f"{HARMONIZER.name} does not exist. Either the figures were filled in by hand "
                f"— which is the drift this whole script exists to prevent — or the script "
                f"was renamed and this guard needs re-pointing.")
    if n_recompute and not re.search(r"\*\*DRAFT", raw):
        fails.append("Finding 3 still has placeholders but the DRAFT marker is gone. A paper "
                     "with '[recompute]' cells must not read as final.")
    return fails


# --- Coverage gate (ported 2026-08-06; see verify_who_decides_wa for the three rules) ----
# A DRAFT gets the gate too, and for a reason specific to this paper: its whole job is to
# transcribe other papers, so an unprobed number here is an unchecked copy of somebody else's
# result. The cases table is audited alongside the findings because that is where the roll
# scales live, and a stale roll scale is the cheapest kind of transcription drift to ship.
AUDIT_BOUNDS = {
    "cases": ("## The cases", "## Harmonization protocol"),
    "finding1": ("## Finding 1", "## Finding 2"),
    "finding2": ("## Finding 2", "## Finding 3"),
    "finding3": ("## Finding 3", "## Boundary of inference"),
    "boundary": ("## Boundary of inference", "## What it means"),
}

COVERAGE_EXEMPT = [
    (r"^(?:19|20)\d{2}$", "a calendar year, not a result"),
    (r"^\d{1,2}$", "small integer — case counts, list ordinals, ratio terms"),
]

COVERAGE_EXEMPT_LITERAL: dict[str, str] = {
    "904": "part of the statutory citation Idaho Code § 34-904A, the poll-book "
           "affiliation provision that makes Idaho's party snapshot reactive. Not a "
           "quantity; its consequences are asserted in verify_who_decides_id.py",
    "84.730": "part of the statutory citation RCW 29A.84.730, Washington's "
              "presidential-primary party-declaration disclosure window. Not a quantity",
    "29001": "Census table id B29001 (citizen voting-age population by age), not a figure — "
             "the values drawn from it are the CVAP benchmark, pinned by acs_cvap_by_state.py "
             "and asserted through the dissimilarity row that uses it",
    "13": "Idaho's roll contraction, ~13%, stated in the comparability controls and in "
          "Boundary of inference. Owned by who-decides-idaho.md, whose own verifier asserts "
          "both endpoints (1.18M -> 1.03M) against the voter file",
}

COVERAGE_EXEMPT_SECTIONS: dict[str, str] = {}


def main() -> int:
    raw = PAPER.read_text(encoding="utf-8")
    norm = vp.normalise(raw)
    try:
        derived = build_derived()
    except LookupError as exc:
        print("=" * 92)
        print("Who Returns the Ballot? — SOURCE SCRAPE FAILED")
        print("=" * 92)
        print(f"  {exc}")
        return 1

    audit_sections, offsets, spans = {}, {}, {}
    for name, (start, end) in AUDIT_BOUNDS.items():
        audit_sections[name], offsets[name] = vp.slice_with_offset(norm, start, end)
    stats: dict = {}
    rc = vp.run("Who Returns the Ballot? — synthesis table vs. the three source papers",
                norm, PROBES, derived, unchecked=UNCHECKED,
                show_coverage=vp.wants_coverage(), spans_out=spans, stats_out=stats)
    if vp.audit_coverage(audit_sections, spans, offsets, tuple(AUDIT_BOUNDS),
                         COVERAGE_EXEMPT, COVERAGE_EXEMPT_LITERAL,
                         COVERAGE_EXEMPT_SECTIONS, strict_units=True):
        rc = 1
    for sat_fail in vp.audit_satellite_counts(PAPER.name, stats.get("figures")):
        print(f"  - {sat_fail}")
        rc = 1

    guards = structural_guards(raw)
    print("\n  STRUCTURAL GUARDS")
    print(f"    harmonization script present: {HARMONIZER.exists()}")
    print(f"    '[recompute]' placeholders:   {raw.count('[recompute]')}")
    if guards:
        for g in guards:
            print(f"    FAIL {g}")
        rc = 1
    else:
        print("    ok  paper's draft status is consistent with the pipeline's state")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
