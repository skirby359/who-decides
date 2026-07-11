"""Match-bias check: is the NY donor AGE skew genuine, or a matching artifact?

The donor-class finding (48% of matched donors are 65+) could be inflated if
older voters are simply more *matchable* to FEC donor records — e.g. more
unique (name, zip) keys, more stable addresses. The matcher's dominant tier
(full-name + zip5, 87% of matches) only fires when a voter's
(last, full-first, zip5) key is UNIQUE on the roll. So we measure
P(matchable | age) = share of active voters in each age band whose Tier-0 key
is unique, then re-weight the matched-donor age distribution by 1 / P(matchable)
and check whether the skew survives.

If P(matchable) is ~flat across age bands, the raw and bias-corrected donor age
distributions coincide and the skew is genuine (this is what the WA §F
re-weighting found).

Usage:
    STATE=NY python scripts/diag_ny_match_bias.py
"""
import duckdb

NY_STATEWIDE = "data/ny_statewide.duckdb"
NY_VRDB = "data/ny_vrdb.duckdb"

BANDS = ["18-29", "30-44", "45-64", "65+"]
BAND_SQL = """
    CASE WHEN age BETWEEN 18 AND 29 THEN '18-29'
         WHEN age BETWEEN 30 AND 44 THEN '30-44'
         WHEN age BETWEEN 45 AND 64 THEN '45-64'
         WHEN age BETWEEN 65 AND 105 THEN '65+' END
"""


def main() -> int:
    con = duckdb.connect(NY_STATEWIDE, read_only=True)
    con.execute(f"ATTACH '{NY_VRDB}' AS vrdb (READ_ONLY)")

    # P(matchable | age): fraction of active, name+zip-complete voters in each
    # band whose Tier-0 key (last, full first, zip5) is UNIQUE on the roll.
    print("[1] computing P(matchable) by age band (Tier-0 key uniqueness)...")
    pm = con.execute(f"""
        WITH base AS (
            SELECT state_voter_id,
                   date_diff('year', birthdate, DATE '2024-11-05') AS age,
                   UPPER(TRIM(last_name)) AS l, UPPER(TRIM(first_name)) AS f,
                   SUBSTR(reg_zip,1,5) AS z
            FROM vrdb.voters
            WHERE status_code='A' AND birthdate IS NOT NULL
              AND first_name IS NOT NULL AND last_name IS NOT NULL AND reg_zip IS NOT NULL
              AND date_diff('year', birthdate, DATE '2024-11-05') BETWEEN 18 AND 105
        ),
        keyed AS (
            SELECT state_voter_id, age,
                   COUNT(*) OVER (PARTITION BY l, f, z) AS keycount
            FROM base
        )
        SELECT {BAND_SQL} AS band,
               count(*) AS voters,
               100.0*count(*) FILTER(WHERE keycount=1)/count(*) AS p_matchable
        FROM keyed GROUP BY band ORDER BY band
    """).df()

    # Raw matched-donor age distribution + all-voter distribution.
    donor = con.execute(f"""
        WITH d AS (
            SELECT date_diff('year', v.birthdate, DATE '2024-11-05') AS age
            FROM voter_donor_affiliation vda JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.birthdate IS NOT NULL
        )
        SELECT {BAND_SQL} AS band, count(*) n FROM d
        WHERE age BETWEEN 18 AND 105 GROUP BY band
    """).df()

    pm = pm.set_index("band").reindex(BANDS)
    donor = donor.set_index("band").reindex(BANDS)

    pm["donor_n"] = donor["n"]
    pm["donor_share"] = 100.0 * pm["donor_n"] / pm["donor_n"].sum()
    # bias-corrected = donor_n / P(matchable), renormalized.
    pm["corr_raw"] = pm["donor_n"] / (pm["p_matchable"] / 100.0)
    pm["donor_corrected"] = 100.0 * pm["corr_raw"] / pm["corr_raw"].sum()

    print("\n=== MATCH-BIAS CHECK: donor age skew, raw vs P(matchable)-corrected ===")
    print(f"  {'band':8} {'P(match)':>9} {'donor%raw':>10} {'donor%corr':>11} {'shift':>7}")
    print("  " + "-" * 50)
    for b in BANDS:
        r = pm.loc[b]
        shift = r["donor_corrected"] - r["donor_share"]
        print(f"  {b:8} {r['p_matchable']:8.1f}% {r['donor_share']:9.1f}% "
              f"{r['donor_corrected']:10.1f}% {shift:+6.1f}")
    spread = pm["p_matchable"].max() - pm["p_matchable"].min()
    g65_raw = pm.loc["65+", "donor_share"]
    g65_corr = pm.loc["65+", "donor_corrected"]
    print(f"\n  P(matchable) spread across bands: {spread:.1f} pts")
    print(f"  65+ donor share: raw {g65_raw:.1f}%  ->  corrected {g65_corr:.1f}%")
    verdict = ("GENUINE (correction barely moves the skew)"
               if abs(g65_corr - g65_raw) < 5 else
               "CHECK — matchability differs enough to matter")
    print(f"  VERDICT: donor age skew is {verdict}")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
