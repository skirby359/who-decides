"""Cross-state donor-vs-electorate representativeness (WA / NY / ID).

The money-linked individual layer (Section F-b of docs/cross-state-fec-money.md),
extended from WA to NY + ID now that both carry a voter file + a voter<->donor
match. For each state with a VRDB + a populated voter_donor_affiliation:

  - Donor AGE skew: matched-donor generation distribution vs the full roll's,
    RAW and matcher-bias inverse-propensity re-weighted. P(matchable|gen) is the
    share of a generation's voters whose (last, first-initial, zip5) key is
    UNIQUE on the roll — the matcher's own uniqueness guard — so the reweight
    strips the "older voters are easier to uniquely match" selection.
  - Donor $ concentration among matched donors (top1% / top10% / Gini).
  - Donor PARTY skew (party-of-record states only, i.e. NY + ID): the registered
    party of matched-donor voters vs the electorate's — a cut WA cannot do (no
    party of record).

Generation is derived uniformly from BIRTH YEAR so the three states are
comparable: WA/NY from `birthdate`, ID from its `age` snapshot (birth_year =
REFERENCE_YEAR - age). `voter_scores` is NOT used (it is empty for NY/ID);
everything comes from the VRDB + voter_donor_affiliation.

Scope notes: TX has no voter file (skipped). The turnout-linked findings
(turnout-by-age, giving->turnout) stay WA-only in diag_wa_individual_findings.py
— NY/ID have no per-voter turnout scores here (NY vote history is an encoded
column; ID has none loaded). State enumeration via cross_state_common.
"""
from __future__ import annotations

import duckdb

from cross_state_common import region_states, write_json

REFERENCE_YEAR = 2026  # ID age is a ~2026 snapshot; birth_year = REFERENCE_YEAR - age
GEN_ORDER = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]


def _cols(con, tbl):
    try:
        return {r[1] for r in con.execute(f"PRAGMA table_info({tbl})").fetchall()}
    except Exception:
        return set()


def _birth_year_expr(voter_cols: set[str]) -> str | None:
    """SQL expr for birth year from whatever the VRDB carries."""
    if "birthdate" in voter_cols:
        return "EXTRACT(year FROM v.birthdate)"
    if "age" in voter_cols:
        return f"({REFERENCE_YEAR} - v.age)"
    return None


_GEN_CASE = """CASE
    WHEN {by} IS NULL THEN NULL
    WHEN {by} <= 1945 THEN 'Silent'
    WHEN {by} <= 1964 THEN 'Boomer'
    WHEN {by} <= 1980 THEN 'Gen X'
    WHEN {by} <= 1996 THEN 'Millennial'
    ELSE 'Gen Z' END"""


def analyze(code: str, statewide_path: str) -> dict | None:
    vrdb_path = statewide_path.replace("_statewide.duckdb", "_vrdb.duckdb")
    try:
        c = duckdb.connect(statewide_path, read_only=True)
    except Exception as e:
        print(f"  [{code}: statewide DB unavailable — {e}]")
        return None
    try:
        c.execute(f"ATTACH '{vrdb_path}' AS vrdb (READ_ONLY)")
    except Exception:
        print(f"  [{code}: no VRDB at {vrdb_path} — skipped]")
        c.close()
        return None

    vcols = _cols(c, "vrdb.voters")
    by = _birth_year_expr(vcols)
    if by is None:
        print(f"  [{code}: VRDB voters has neither birthdate nor age — skipped]")
        c.close()
        return None
    n_match = c.execute("SELECT COUNT(*) FROM voter_donor_affiliation").fetchone()[0]
    if not n_match:
        print(f"  [{code}: voter_donor_affiliation empty — skipped]")
        c.close()
        return None

    gen_case = _GEN_CASE.format(by=by)
    has_party = "party" in vcols

    # Roll generation distribution + matchability (unique last|initial|zip5).
    c.execute(f"""
        CREATE TEMP TABLE roll AS
        SELECT v.state_voter_id sid, {gen_case} AS gen,
               UPPER(TRIM(v.last_name)) || '|' || UPPER(SUBSTR(TRIM(v.first_name),1,1))
                 || '|' || SUBSTR(v.reg_zip,1,5) AS mkey
        FROM vrdb.voters v
    """)
    c.execute("CREATE TEMP TABLE keyn AS SELECT mkey, COUNT(*) n FROM roll GROUP BY 1")
    roll_gen = dict(c.execute(
        "SELECT gen, COUNT(*) FROM roll WHERE gen IS NOT NULL GROUP BY 1").fetchall())
    # P(matchable | gen) = share of the generation whose key is unique on the roll.
    pmatch = dict(c.execute("""
        SELECT r.gen, AVG(CASE WHEN k.n = 1 THEN 1.0 ELSE 0 END)
        FROM roll r JOIN keyn k USING (mkey)
        WHERE r.gen IS NOT NULL GROUP BY 1
    """).fetchall())

    # Matched-donor generation distribution (join match -> roll by voter id).
    don_gen = dict(c.execute("""
        SELECT r.gen, COUNT(*)
        FROM voter_donor_affiliation a JOIN roll r ON r.sid = a.state_voter_id
        WHERE r.gen IS NOT NULL GROUP BY 1
    """).fetchall())

    roll_tot = sum(roll_gen.values()) or 1
    don_tot = sum(don_gen.values()) or 1
    ipw = {g: don_gen.get(g, 0) / pmatch[g] for g in roll_gen if pmatch.get(g)}
    ipw_tot = sum(ipw.values()) or 1

    gens = {}
    for g in GEN_ORDER:
        rp = roll_gen.get(g, 0) / roll_tot * 100
        dp = don_gen.get(g, 0) / don_tot * 100
        rwt_dp = ipw.get(g, 0) / ipw_tot * 100
        gens[g] = {
            "roll_pct": round(rp, 1), "donor_pct": round(dp, 1),
            "over_rep": round(dp / rp, 2) if rp else None,
            "p_match": round(pmatch.get(g, 0), 4),
            "rwt_donor_pct": round(rwt_dp, 1),
            "rwt_over_rep": round(rwt_dp / rp, 2) if rp else None,
        }

    # $ concentration among matched donors.
    top1, top10 = c.execute("""
        WITH ranked AS (SELECT total_donated t, NTILE(100) OVER (ORDER BY total_donated DESC) p
                        FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT SUM(t) FILTER (WHERE p=1)/SUM(t), SUM(t) FILTER (WHERE p<=10)/SUM(t) FROM ranked
    """).fetchone()
    gini = c.execute("""
        WITH r AS (SELECT total_donated t, ROW_NUMBER() OVER (ORDER BY total_donated) rn,
                          COUNT(*) OVER () n, SUM(total_donated) OVER () s
                   FROM voter_donor_affiliation WHERE total_donated > 0)
        SELECT (2.0*SUM(rn*t)/(MAX(n)*MAX(s))) - (MAX(n)+1.0)/MAX(n) FROM r
    """).fetchone()[0]

    # Party skew (party-of-record states only).
    party = None
    if has_party:
        roll_p = dict(c.execute("""
            SELECT UPPER(TRIM(party)), COUNT(*) FROM vrdb.voters
            WHERE party IS NOT NULL AND TRIM(party) <> '' GROUP BY 1
        """).fetchall())
        don_p = dict(c.execute("""
            SELECT UPPER(TRIM(v.party)), COUNT(*)
            FROM voter_donor_affiliation a JOIN vrdb.voters v ON v.state_voter_id = a.state_voter_id
            WHERE v.party IS NOT NULL AND TRIM(v.party) <> '' GROUP BY 1
        """).fetchall())

        def _bucket(dist):
            dem = rep = oth = 0
            for k, n in dist.items():
                if k.startswith("DEM"):
                    dem += n
                elif k.startswith("REP"):
                    rep += n
                else:
                    oth += n
            tot = dem + rep + oth or 1
            return {"Dem": round(dem / tot * 100, 1), "Rep": round(rep / tot * 100, 1),
                    "Other": round(oth / tot * 100, 1)}

        party = {"roll": _bucket(roll_p), "donors": _bucket(don_p)}

    c.close()
    return {
        "state": code, "n_matched": int(n_match),
        "generations": gens,
        "top1_share": round(float(top1), 4) if top1 else None,
        "top10_share": round(float(top10), 4) if top10 else None,
        "gini": round(float(gini), 4) if gini is not None else None,
        "party": party,
    }


def main():
    results = []
    for code, path in region_states():
        r = analyze(code, path)
        if r:
            results.append(r)

    print("\n" + "=" * 82)
    print("DONOR AGE SKEW — matched-donor share / roll share, by generation (raw | IPW-reweighted)")
    print("=" * 82)
    hdr = f"{'gen':11}" + "".join(f"{r['state']+' raw':>11}{r['state']+' rwt':>11}" for r in results)
    print(hdr)
    print("-" * len(hdr))
    for g in GEN_ORDER:
        line = f"{g:11}"
        for r in results:
            gg = r["generations"][g]
            raw = f"{gg['over_rep']:.2f}x" if gg["over_rep"] is not None else "-"
            rwt = f"{gg['rwt_over_rep']:.2f}x" if gg["rwt_over_rep"] is not None else "-"
            line += f"{raw:>11}{rwt:>11}"
        print(line)

    print("\nDonor $ concentration (matched donors):")
    for r in results:
        print(f"  {r['state']}: matched={r['n_matched']:,}  top1%={_pct(r['top1_share'])}  "
              f"top10%={_pct(r['top10_share'])}  Gini={r['gini']}")

    party_states = [r for r in results if r["party"]]
    if party_states:
        print("\nDonor PARTY skew (party-of-record states) — electorate vs matched donors:")
        for r in party_states:
            p = r["party"]
            print(f"  {r['state']}: roll  D {p['roll']['Dem']}% / R {p['roll']['Rep']}% / "
                  f"O {p['roll']['Other']}%   ||   donors  D {p['donors']['Dem']}% / "
                  f"R {p['donors']['Rep']}% / O {p['donors']['Other']}%")

    out = write_json("cross_state_donor_representativeness.json", results)
    print(f"\nwrote {out}")


def _pct(x):
    return f"{x*100:.1f}%" if x is not None else "-"


if __name__ == "__main__":
    main()
