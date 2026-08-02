"""Stratified, blinded match-precision validation sampler (2026-07-27).

Replaces the 2026-07-10 sampler for the donor-class paper's precision gate. The external
review found four defects in that pass, and this fixes all four:

  1. It sampled the POOLED `voter_donor_affiliation` table, not either paper panel, and
     only Washington. -> This samples all six panels (3 states x federal/state).
  2. It sampled UNSTRATIFIED, so the weak tiers got 3-4 records and per-tier precision
     was unestimable. -> This stratifies on tier and allocates equally, oversampling the
     weak tiers relative to their population share, then reweights when reporting.
  3. It was not blinded. -> The evidence file the rater reads carries NO stratum labels
     (no state, no panel, no tier, no dollar decile) and rows are shuffled; labels live
     in a separate key file joined only after verdicts are recorded.
  4. Its verdicts were never persisted. -> The evidence file has a `verdict` column, and
     `score_match_validation.py` refuses to score until it is filled.

DOLLAR DECILE. Errors in the top dollar decile matter most (they drive the concentration
finding), so within each tier x panel cell half the sample is drawn from the top decile
and half from the rest, and the scorer reports precision for both bands.

WHAT BLINDING CAN AND CANNOT ACHIEVE HERE. The rater sees no stratum label and cannot
tell which cell a row came from, so no per-cell standard can be applied and there is no
batch/priming effect. The rater CAN partly infer the tier from the evidence itself (if
the donor's full first name equals the voter's, the row is probably the full-name tier),
because the tier IS a fact about how the two names relate. That is unavoidable without
withholding the evidence needed to judge, so it is disclosed rather than engineered away.

VERDICT VOCABULARY (the reviewer asked for these separated, not pooled):
  Y      same person
  NC     confirmed different person  (e.g. donor first name is a different given name)
  NP     probably different person   (weak/ambiguous mismatch)
  U      unverifiable                (insufficient donor detail to judge)

PII. The evidence file carries voter and donor names. It is written under gitignored
`data/validation/` and must never be committed. This script prints only counts.

Run:  python scripts/diag_match_validation_stratified.py
      python scripts/diag_match_validation_stratified.py --per-cell 10
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTDIR = DATA / "validation"
EVIDENCE = OUTDIR / "match_validation_stratified.csv"
KEYFILE = OUTDIR / "match_validation_stratified_key.csv"
# sample_id -> state_voter_id, written so that a LATER fresh draw can exclude the records
# this one already rated (`--exclude-rated`). Added 2026-07-28: no prior artifact carried the
# voter id — not the published verdicts, not the stratum key, not the evidence file — which
# is good PII hygiene but made an "independent sample" unverifiable, since there was no way
# to prove a new draw did not re-draw the old records. This file is PII-adjacent (it links a
# sample row to a real registrant) and lives under gitignored data/validation/; it must never
# be committed or published.
IDFILE = OUTDIR / "match_validation_stratified_ids.csv"

DEFAULT_SEED = "2026-07-27"   # the seed of the published 480-record pass
SEED = DEFAULT_SEED           # rebound by --seed; the draw is md5(state_voter_id || SEED)

# (state, statewide db, vrdb db, {panel: contribution_id prefix})
STATES = [
    ("WA", "wa_statewide", "wa_vrdb", {"federal": "FEC", "state": "PDC"}),
    ("NY", "ny_statewide", "ny_vrdb", {"federal": "FEC", "state": "NY"}),
    ("ID", "id_statewide", "id_vrdb", {"federal": "FEC", "state": "SUNSHINE"}),
]
# The `_alltier` SNAPSHOTS, not the live primaries (repointed 2026-07-27). The primaries
# were rebuilt full-name-only, which leaves nothing to stratify: three of the four tiers
# would return zero rows and the by-tier precision estimate — the whole point of this
# sampler — would die silently. `scripts/snapshot_alltier_panels.py` creates these.
PANEL_TABLE = {"federal": "voter_donor_affiliation_fec_alltier",
               "state": "voter_donor_affiliation_state_alltier"}

TIERS = ["STRICT_ZIP5_FULL", "STRICT_ZIP5_MID", "STRICT_ZIP5", "RELAXED_ZIP3_MID"]

# Per-tier join condition against the reconstructed contribution keys. These mirror
# `match_voters_to_donors` exactly, so the donor side shown to the rater is the evidence
# the matcher actually acted on.
TIER_JOIN = {
    "STRICT_ZIP5_FULL": "c.lk = s.lk AND c.ffull = s.ffull AND c.z5 = s.z5",
    "STRICT_ZIP5_MID":  "c.lk = s.lk AND c.fi = s.fi AND c.mi = s.mi AND c.z5 = s.z5",
    "STRICT_ZIP5":      "c.lk = s.lk AND c.fi = s.fi AND c.z5 = s.z5",
    "RELAXED_ZIP3_MID": "c.lk = s.lk AND c.fi = s.fi AND c.mi = s.mi AND c.z3 = s.z3",
}

# Replicates the matcher's contributor-name parsing. FEC / NYSBOE / Sunshine file people
# as "LAST, FIRST MID"; WA PDC files them as "LAST FIRST MID" with no comma.
CK_SQL = """
CREATE OR REPLACE TEMP TABLE _ck AS
SELECT
  CASE WHEN contributor_name LIKE '%,%'
       THEN UPPER(TRIM(SPLIT_PART(contributor_name, ',', 1)))
       ELSE UPPER(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 1))) END           AS lk,
  CASE WHEN contributor_name LIKE '%,%'
       THEN UPPER(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 1))
       ELSE UPPER(SPLIT_PART(TRIM(contributor_name), ' ', 2)) END                 AS ffull,
  CASE WHEN contributor_name LIKE '%,%'
       THEN UPPER(SUBSTR(TRIM(SPLIT_PART(contributor_name, ',', 2)), 1, 1))
       ELSE UPPER(SUBSTR(TRIM(SPLIT_PART(TRIM(contributor_name), ' ', 2)), 1, 1)) END AS fi,
  CASE WHEN contributor_name LIKE '%,%'
       THEN UPPER(SUBSTR(SPLIT_PART(TRIM(SPLIT_PART(contributor_name, ',', 2)), ' ', 2), 1, 1))
       ELSE UPPER(SUBSTR(SPLIT_PART(TRIM(contributor_name), ' ', 3), 1, 1)) END   AS mi,
  SUBSTR(contributor_zip, 1, 5) AS z5,
  SUBSTR(contributor_zip, 1, 3) AS z3,
  contributor_name, contribution_amount
FROM individual_contributions
WHERE contributor_name IS NOT NULL AND contributor_name <> ''
  AND contributor_zip IS NOT NULL AND contributor_zip <> ''
  AND contribution_amount > 0
  AND UPPER(contributor_name) NOT IN ('SMALL CONTRIBUTIONS', 'UNITEMIZED', 'ANONYMOUS')
  AND contribution_id LIKE '{prefix}:%'
"""


def sample_cell(con, panel_tbl, tier, band, n, exclude_ids=(), party=None):
    """Sample up to n matched voters from one tier x dollar-band cell.

    band: 'top10' = top donor-dollar decile within the panel, 'rest' = deciles 2-10.
    party: when set, additionally restrict to that registered party (review round 17 —
    Idaho's party rows are the result that fails the panel-specific bound, so its
    replacement sample is stratified on the variable the finding is about; without that,
    a 100-record draw from a panel that is 20% Democratic yields ~20 Democratic records
    and says little about the cell under attack).
    Deterministic via md5(state_voter_id || SEED).
    """
    band_pred = "d.decile = 1" if band == "top10" else "d.decile > 1"
    # A FRESH sample must not re-draw records the published pass already rated, or the
    # "independent sample" claim is false: exclude_ids carries those voter ids.
    excl = ""
    params = [tier]
    if exclude_ids:
        excl = " AND d.state_voter_id NOT IN (" +                ",".join("?" for _ in exclude_ids) + ")"
        params += list(exclude_ids)
    if party:
        excl += " AND UPPER(TRIM(v.party)) = ?"
        params.append(party)
    return [r[0] for r in con.execute(f"""
        WITH d AS (
            SELECT state_voter_id, match_quality,
                   NTILE(10) OVER (ORDER BY total_donated DESC) AS decile
            FROM {panel_tbl} WHERE total_donated > 0)
        SELECT d.state_voter_id
        FROM d
        JOIN vrdb.voters v USING (state_voter_id)
        WHERE d.match_quality = ? AND {band_pred}{excl}
          AND v.first_name IS NOT NULL AND v.last_name IS NOT NULL
          AND v.reg_zip IS NOT NULL
        ORDER BY md5(d.state_voter_id || '{SEED}')
        LIMIT {int(n)}
    """, params).fetchall()]


def evidence_for(con, panel_tbl, tier, voter_ids):
    """Reconstruct the donor side for sampled voters using the tier's own key."""
    if not voter_ids:
        return []
    con.execute("CREATE OR REPLACE TEMP TABLE _samp_ids (state_voter_id VARCHAR)")
    con.executemany("INSERT INTO _samp_ids VALUES (?)", [(v,) for v in voter_ids])
    return con.execute(f"""
        WITH s AS (
            SELECT a.state_voter_id, a.donation_count, a.total_donated,
                   v.first_name, v.middle_name, v.last_name, v.reg_city,
                   UPPER(TRIM(v.last_name))                               AS lk,
                   UPPER(SPLIT_PART(UPPER(TRIM(v.first_name)), ' ', 1))    AS ffull,
                   UPPER(SUBSTR(TRIM(v.first_name), 1, 1))                 AS fi,
                   UPPER(SUBSTR(TRIM(COALESCE(v.middle_name, '')), 1, 1))  AS mi,
                   SUBSTR(v.reg_zip, 1, 5)                                 AS z5,
                   SUBSTR(v.reg_zip, 1, 3)                                 AS z3
            FROM {panel_tbl} a
            JOIN _samp_ids USING (state_voter_id)
            JOIN vrdb.voters v USING (state_voter_id))
        SELECT s.state_voter_id, s.first_name, s.middle_name, s.last_name, s.z5, s.reg_city,
               s.donation_count, s.total_donated,
               COUNT(c.contributor_name)                                   AS ic_rows,
               COALESCE(ROUND(SUM(c.contribution_amount), 0), 0)           AS ic_total,
               COUNT(DISTINCT c.ffull)                                     AS n_first,
               LIST(DISTINCT c.contributor_name)                           AS names,
               LIST(DISTINCT c.z5)                                         AS zips
        FROM s LEFT JOIN _ck c ON {TIER_JOIN[tier]}
        GROUP BY ALL
    """).fetchall()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-cell", type=int, default=10,
                    help="target records per (state x panel x tier x dollar-band) cell")
    ap.add_argument("--seed", default=DEFAULT_SEED,
                    help="draw seed. Change it to draw a DIFFERENT sample; the default "
                         "reproduces the published 480-record pass exactly.")
    ap.add_argument("--tiers", nargs="+", default=None, metavar="TIER",
                    help="restrict to these tiers (e.g. --tiers STRICT_ZIP5_FULL to test "
                         "the primary specification alone)")
    ap.add_argument("--live-panels", action="store_true",
                    help="sample the LIVE primary panels instead of the _alltier snapshots. "
                         "The live panels hold only STRICT_ZIP5_FULL, so this is the right "
                         "source for a full-name-key draw and the wrong one for a by-tier "
                         "precision estimate (three tiers would return zero rows).")
    ap.add_argument("--exclude-rated", nargs="*", metavar="CSV",
                    help="verdict CSV(s) whose state_voter_id column names records to "
                         "EXCLUDE, so a fresh draw is independent of the published pass")
    ap.add_argument("--states", nargs="+", default=None, metavar="ST",
                    help="restrict the draw to these states (e.g. --states ID)")
    # nargs="+", not "*": a bare `--by-party` would otherwise parse to [] and fall through to
    # an UNSTRATIFIED draw, silently giving the caller the opposite of what they asked for.
    ap.add_argument("--by-party", nargs="+", default=None, metavar="PARTY",
                    help="stratify equally across these registered parties, e.g. "
                         "--by-party DEM REP UNA. Only meaningful where the roll "
                         "publishes party (NY, ID).")
    ap.add_argument("--label", default=None, metavar="NAME",
                    help="write to a NAMED output set with a fresh opaque id space, for a "
                         "draw handed to a different rater. Required for any independent "
                         "sample: the published `S####` and `H####` ids carry verdicts "
                         "anyone can look up, which turns an inter-rater statistic into a "
                         "copying exercise.")
    args = ap.parse_args()

    global SEED, PANEL_TABLE, TIERS, STATES
    SEED = args.seed
    if args.live_panels:
        PANEL_TABLE = {"federal": "voter_donor_affiliation_fec",
                       "state": "voter_donor_affiliation_state"}
    if args.tiers:
        unknown = [x for x in args.tiers if x not in TIERS]
        if unknown:
            print(f"  !! unknown tier(s): {unknown}; valid are {TIERS}")
            return 2
        TIERS = list(args.tiers)
    if args.by_party:
        # Washington's roll publishes no party — that absence is the reason the paper's party
        # comparison runs only in NY and ID. Without this guard the draw dies mid-run on a
        # DuckDB binder error naming a column, which reads like a schema bug rather than a
        # request for something the data cannot answer.
        _no_party = {"WA"} & {s.upper() for s in (args.states or ["WA", "NY", "ID"])}
        if _no_party:
            print(f"  !! --by-party is not available for {sorted(_no_party)}: that roll "
                  f"publishes no party of record. Restrict with --states NY ID, or drop "
                  f"--by-party.")
            return 2
    if args.states:
        want = {s.upper() for s in args.states}
        unknown = want - {s[0] for s in STATES}
        if unknown:
            print(f"  !! unknown state(s): {sorted(unknown)}")
            return 2
        STATES = [s for s in STATES if s[0] in want]

    # A named draw gets its own id space and its own files. The prefix is derived from the
    # label and must not collide with a PUBLISHED one: `S` is the 480-record ledger and `H`
    # the 150-record re-rate, and both are published WITH their verdicts.
    id_prefix, evidence_path, key_path, idmap_path = "S", EVIDENCE, KEYFILE, IDFILE
    if args.label:
        if not args.label.replace("_", "").replace("-", "").isalnum():
            print(f"  !! --label must be alphanumeric: {args.label!r}")
            return 2
        id_prefix = args.label[0].upper()
        if id_prefix in ("S", "H"):
            print(f"  !! label {args.label!r} yields id prefix {id_prefix!r}, which is a "
                  f"PUBLISHED id space (S=480-record ledger, H=150-record re-rate). A rater "
                  f"handed those ids can look up the prior verdict. Pick another label.")
            return 2
        evidence_path = OUTDIR / f"match_validation_{args.label}.csv"
        key_path = OUTDIR / f"match_validation_{args.label}_key.csv"
        idmap_path = OUTDIR / f"match_validation_{args.label}_ids.csv"
        for fp in (evidence_path, key_path, idmap_path):
            if fp.exists():
                print(f"  !! {fp} exists — refusing to overwrite a drawn sample. "
                      f"Delete it deliberately, or pick another --label.")
                return 2

    exclude_ids: set[str] = set()
    for path in (args.exclude_rated or []):
        fp = Path(path)
        if not fp.exists():
            print(f"  !! --exclude-rated file not found: {fp}")
            return 2
        with fp.open(encoding="utf-8-sig", newline="") as fh:
            rdr = csv.DictReader(fh)
            col = next((c for c in (rdr.fieldnames or [])
                        if c and c.strip().lower() == "state_voter_id"), None)
            if col is None:
                print(f"  !! {fp} has no state_voter_id column — cannot exclude by id. "
                      f"The published verdict files are PII-free by design, so a fresh "
                      f"independent draw needs the gitignored key file instead.")
                return 2
            exclude_ids.update(r[col].strip() for r in rdr if r.get(col))
    if exclude_ids:
        print(f"  excluding {len(exclude_ids):,} already-rated voter ids")

    print(f"  seed={SEED}  tiers={TIERS}  panels="
          f"{'LIVE primaries' if args.live_panels else '_alltier snapshots'}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for state, db, vrdb, panels in STATES:
        con = duckdb.connect(str(DATA / f"{db}.duckdb"), read_only=True)
        con.execute(f"ATTACH '{DATA / f'{vrdb}.duckdb'}' AS vrdb (READ_ONLY)")
        for panel, prefix in panels.items():
            con.execute(CK_SQL.format(prefix=prefix))
            tbl = PANEL_TABLE[panel]
            for tier in TIERS:
                # With --by-party the tier's allocation is drawn once per party, so a cell
                # is (tier x band x party) and the party mix of the sample is fixed by
                # design rather than inherited from the panel.
                parties = args.by_party if args.by_party else [None]
                got = {}
                party_of: dict[str, str] = {}
                for pty in parties:
                    for band in ("top10", "rest"):
                        ids = sample_cell(con, tbl, tier, band, args.per_cell,
                                          exclude_ids, party=pty)
                        got.setdefault(band, [])
                        got[band] += ids
                        for i in ids:
                            party_of[i] = pty or ""
                # Backfill a short band from the other so the tier keeps its allocation.
                # Skipped under --by-party: borrowing across bands there would also borrow
                # across parties and silently unbalance the stratum the draw exists for.
                if not args.by_party:
                    short = 2 * args.per_cell - len(got["top10"]) - len(got["rest"])
                    if short > 0:
                        for band in ("rest", "top10"):
                            extra = [i for i in sample_cell(con, tbl, tier, band,
                                                            args.per_cell + short)
                                     if i not in got[band]][:short]
                            got[band] += extra
                            short -= len(extra)
                            if short <= 0:
                                break
                for band, ids in got.items():
                    for r in evidence_for(con, tbl, tier, ids):
                        (svid, vf, vm, vl, vz, vcity, dcount, dtot,
                         ic_rows, ic_total, n_first, names, zips) = r
                        rows.append({
                            "_state": state, "_panel": panel, "_tier": tier,
                            "_band": band, "_svid": svid,
                            "_party": party_of.get(svid, ""),
                            "voter_first": vf or "", "voter_middle": vm or "",
                            "voter_last": vl or "", "voter_zip5": vz or "",
                            "voter_city": vcity or "",
                            "matched_gifts": dcount, "matched_total": float(dtot or 0),
                            "donor_rows_refound": ic_rows,
                            "donor_total_refound": float(ic_total or 0),
                            "donor_distinct_first_names": n_first,
                            "donor_names": " | ".join(sorted(n for n in (names or []) if n)[:6]),
                            "donor_zip5s": " ".join(sorted(set(z for z in (zips or []) if z))[:4]),
                        })
        con.close()
        print(f"  {state}: cumulative {len(rows):,} sampled")

    # Shuffle deterministically, THEN assign opaque ids, so id order carries no stratum
    # information at all.
    rows.sort(key=lambda r: hashlib.md5(
        (r["_svid"] + r["_tier"] + SEED).encode()).hexdigest())
    for i, r in enumerate(rows, 1):
        r["sample_id"] = f"{id_prefix}{i:04d}"

    # `partial_merge` was MISSING here until 2026-08-01, and the omission was silent: both
    # rater instruction documents tell the rater to tick it, and the pre-specified scoring
    # requires it reported separately from identity errors, but a draw from this script gave
    # them nowhere to record it. The `idaho1` draw shipped without it and had the column added
    # after the fact. Keep it adjacent to `verdict` — the earlier hand-built evidence files
    # (`_human`, `_rater2`) put it there and a rater reads the two columns together.
    ev_cols = ["sample_id", "voter_first", "voter_middle", "voter_last", "voter_zip5",
               "voter_city", "matched_gifts", "matched_total", "donor_names",
               "donor_zip5s", "donor_distinct_first_names", "donor_rows_refound",
               "donor_total_refound", "partial_merge", "verdict", "notes"]
    with open(evidence_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ev_cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "partial_merge": "", "verdict": "", "notes": ""})

    with open(key_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sample_id", "state", "panel", "tier", "dollar_band",
                    "reg_party", "matched_total"])
        for r in rows:
            w.writerow([r["sample_id"], r["_state"], r["_panel"], r["_tier"],
                        r["_band"], r["_party"], r["matched_total"]])

    print(f"\nwrote {len(rows):,} rows")
    print(f"  blinded evidence -> {evidence_path}   (NO stratum labels; PII; gitignored)")
    with open(idmap_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sample_id", "state_voter_id"])
        for r in rows:
            w.writerow([r["sample_id"], r["_svid"]])

    print(f"  stratum key      -> {key_path}    (join only AFTER verdicts are recorded)")
    print(f"  voter-id map     -> {idmap_path}     (gitignored; feeds a later "
          f"--exclude-rated)")
    print("\nallocation actually achieved (counts only):")
    from collections import Counter
    for key, label in ((("_tier",), "tier"), (("_state", "_panel"), "state x panel"),
                       (("_band",), "dollar band"), (("_party",), "registered party")):
        print(f"  by {label}:")
        for k, n in sorted(Counter(tuple(r[c] for c in key) for r in rows).items()):
            print(f"    {' / '.join(k):34} {n:>5,}")
    print("\nNEXT: fill `verdict` with Y / NC / NP / U (and `partial_merge` with y), then score.")
    if args.label:
        print(f"  A LABELLED draw is not scored by score_match_validation.py — that script is "
              f"hard-coded to the 480-record pass and tier-reweights, which is wrong for a "
              f"single-tier or party-stratified draw. Use the scorer written for this design "
              f"(for the Idaho draw: scripts/score_idaho_validation.py --label {args.label}).")
    else:
        print("  python scripts/score_match_validation.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
