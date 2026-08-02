"""Review-#3 diagnostics for docs/donor-class-and-the-electorate.md.

Three of the four actions the 2026-07-29 external review required, plus the denominator
discrepancy it found. Read-only; aggregate output only (the voter files carry PII).

  R3-1  party-specific matchability   The party incidence table reports matched donors per
                                      1,000 registrants OF THE SAME PARTY. That statistic
                                      confounds donation incidence with the probability that
                                      a party's registrants are uniquely matchable under the
                                      full-name + ZIP5 rule — parties differ in surname
                                      concentration, ZIP concentration and county
                                      distribution. Measured here three ways: P(matchable)
                                      by party, by party x age band, and by party x county;
                                      then incidence re-based on uniquely-matchable
                                      registrants; then incidence standardized on age and
                                      on joint age x county, since giving is geographically
                                      concentrated and party registration is geographically
                                      structured.
  R3-2  exact election eligibility    The age x tenure turnout standardization used five
                                      broad tenure bands. A 2-5 year band mixes registrants
                                      who could have voted in three of the four elections
                                      with registrants who could have voted in one. Redone
                                      by RESTRICTING to registrants who existed before the
                                      first election in each window, which equalizes
                                      opportunity by construction, and additionally as
                                      elections-voted / elections-eligible.
  (R3-3, Appendix G's cap simulation, lives in `diag_contribution_limits.py`, which
  already reads the contribution table — see the aggregate-level variant there.)
  R3-4  all-tier denominator          Appendix F reports WA's all-tier state panel as 269,204
                                      in two tables and 268,741 in the precision table. This
                                      reproduces both and identifies which filter differs.

Run:  python scripts/diag_donor_review3.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"

BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]


def band_sql(age_expr: str) -> str:
    return (f"CASE WHEN {age_expr}<25 THEN '18-24' WHEN {age_expr}<35 THEN '25-34' "
            f"WHEN {age_expr}<45 THEN '35-44' WHEN {age_expr}<55 THEN '45-54' "
            f"WHEN {age_expr}<65 THEN '55-64' WHEN {age_expr}<75 THEN '65-74' "
            f"ELSE '75+' END")


def rule(title: str, char: str = "=") -> None:
    print("\n" + char * 78)
    print(title)
    print(char * 78)


# --------------------------------------------------------------------------
# R3-1 — party-specific matchability, and incidence re-based / standardized
# --------------------------------------------------------------------------
def report_party_matchability(con, state: str, panels: dict[str, str], age_expr: str,
                              party_case: str, parties: list[str]) -> None:
    rule(f"R3-1  {state}: full-name-key matchability BY PARTY")
    print("  P(matchable) has two components and both can vary by party:")
    print("    complete  — has a first name, last name and ZIP at all (a record missing")
    print("                any of the three can never match, and is excluded from the")
    print("                uniqueness denominator, so it must be reported separately)")
    print("    unique    — among complete records, the (last, full first, zip5) key")
    print("                identifies exactly one registrant")
    print("  P(matchable) = complete x unique. Reported for the ACTIVE roll, age 18+.")
    band = band_sql(age_expr)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _roll AS
        WITH base AS (
            SELECT v.state_voter_id, {party_case} AS party, {band} AS band,
                   v.county_name,
                   (v.first_name IS NOT NULL AND v.last_name IS NOT NULL
                    AND v.reg_zip IS NOT NULL) AS complete,
                   UPPER(TRIM(v.last_name)) l, UPPER(TRIM(v.first_name)) f,
                   SUBSTR(v.reg_zip, 1, 5) z
            FROM vrdb.voters v
            WHERE v.status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18)
        SELECT state_voter_id, party, band, county_name, complete,
               CASE WHEN complete
                    THEN COUNT(*) FILTER (WHERE complete) OVER (PARTITION BY l, f, z)
                    END AS keycount
        FROM base""")

    print(f"\n  by party\n    {'party':10}{'registrants':>13}{'complete':>10}"
          f"{'unique|compl':>14}{'P(matchable)':>14}")
    pm: dict[str, float] = {}
    for p, n, cpl, uniq, pmatch in con.execute("""
        SELECT party, COUNT(*),
               100.0*COUNT(*) FILTER (WHERE complete)/COUNT(*),
               100.0*COUNT(*) FILTER (WHERE keycount=1)
                   /NULLIF(COUNT(*) FILTER (WHERE complete), 0),
               100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _roll GROUP BY 1""").fetchall():
        pm[p] = float(pmatch)
        print(f"    {p:10}{n:>13,}{float(cpl):9.1f}%{float(uniq):13.1f}%"
              f"{float(pmatch):13.1f}%")
    if pm:
        spread = max(pm.values()) - min(pm.values())
        print(f"    spread across parties: {spread:.1f} pts")

    print(f"\n  by party x age band — P(matchable)\n    {'party':10}"
          + "".join(f"{b:>9}" for b in BANDS))
    cells = {(p, b): float(v) for p, b, v in con.execute("""
        SELECT party, band, 100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _roll GROUP BY 1, 2""").fetchall()}
    for p in parties:
        print(f"    {p:10}" + "".join(
            f"{cells.get((p, b), float('nan')):8.1f}%" for b in BANDS))
    within = [max(cells.get((p, b), 0) for p in parties)
              - min(cells.get((p, b), 0) for p in parties) for b in BANDS]
    print(f"    max party spread within a band: {max(within):.1f} pts")

    print("\n  by party x county — P(matchable), spread across the 8 largest counties")
    top = [c for (c,) in con.execute(
        "SELECT county_name FROM _roll GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 8"
    ).fetchall()]
    # Computed for every county and filtered in Python. Interpolating county names into an
    # IN-list means hand-quoting values, which is both unreadable and the wrong habit even
    # when the values come from this same database.
    ccells = {(p, c): float(v) for p, c, v in con.execute("""
        SELECT party, county_name, 100.0*COUNT(*) FILTER (WHERE keycount=1)/COUNT(*)
        FROM _roll GROUP BY 1, 2""").fetchall() if c in set(top)}
    print(f"    {'county':16}" + "".join(f"{p:>10}" for p in parties))
    for c in top:
        print(f"    {c[:15]:16}" + "".join(
            f"{ccells.get((p, c), float('nan')):9.1f}%" for p in parties))

    # ---- incidence: raw, re-based on matchable, age-standardized, age x county
    for tag, panel in panels.items():
        rule(f"R3-1  {state} {tag}: donation incidence per 1,000 registrants", "-")
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _don AS
            SELECT r.* FROM _roll r
            WHERE r.state_voter_id IN (SELECT state_voter_id FROM {panel})""")
        print(f"    {'party':10}{'per 1,000 all':>15}{'per 1,000 matchable':>21}")
        raw, reb = {}, {}
        for p, n_all, n_uniq, n_don in con.execute("""
            SELECT r.party, COUNT(*), COUNT(*) FILTER (WHERE r.keycount=1),
                   (SELECT COUNT(*) FROM _don d WHERE d.party = r.party)
            FROM _roll r GROUP BY 1""").fetchall():
            raw[p] = n_don / n_all * 1000 if n_all else float("nan")
            reb[p] = n_don / n_uniq * 1000 if n_uniq else float("nan")
            print(f"    {p:10}{raw[p]:14.1f}{reb[p]:20.1f}")

        # direct standardization of INCIDENCE (not shares): age, then age x county
        for label, keys in (("age", ["band"]), ("age x county", ["band", "county_name"])):
            cols = ", ".join(f"r.{k}" for k in keys)
            rows = con.execute(f"""
                WITH pop AS (SELECT {cols}, r.party, COUNT(*) n,
                                    COUNT(*) FILTER (WHERE r.keycount=1) nu
                             FROM _roll r GROUP BY ALL),
                dn AS (SELECT {cols.replace('r.', 'd.')}, d.party, COUNT(*) nd
                       FROM _don d GROUP BY ALL),
                j AS (SELECT pop.*, COALESCE(dn.nd, 0) nd
                      FROM pop LEFT JOIN dn USING ({', '.join(keys)}, party)),
                -- standard population = the stratum's TOTAL registrants, applied to every
                -- party's within-stratum incidence. Strata where a party has no
                -- registrants carry no weight for that party, and the retained share of
                -- the standard population is reported so nothing is dropped silently.
                w AS (SELECT {', '.join(keys)}, SUM(n) wn FROM j GROUP BY ALL)
                SELECT j.party,
                       1000.0*SUM(w.wn * j.nd / j.n)/SUM(w.wn) std_rate,
                       100.0*SUM(w.wn)/(SELECT SUM(wn) FROM w) kept
                FROM j JOIN w USING ({', '.join(keys)})
                WHERE j.n > 0 GROUP BY 1""").fetchall()
            print(f"\n    standardized on {label}:")
            for p, sr, kept in rows:
                print(f"    {p:10}{float(sr):14.1f}   ({float(kept):.1f}% of the "
                      f"standard population retained)")


# --------------------------------------------------------------------------
# R3-2 — turnout with exact election eligibility
# --------------------------------------------------------------------------
def report_eligibility_turnout(con, state: str, panels: dict[str, str], age_expr: str,
                               roll_sql: str, first_election: str,
                               n_elections: int) -> None:
    rule(f"R3-2  {state}: turnout with EXACT election eligibility")
    print(f"  Restriction: registered before {first_election}, the first election in the")
    print(f"  window, so every retained registrant could have voted in all {n_elections}.")
    print("  This equalizes opportunity by construction rather than by tenure band.")
    print("  Also reported: elections voted / elections eligible on the UNRESTRICTED roll,")
    print("  which keeps late registrants at the cost of a ratio denominator.")
    con.execute(f"CREATE OR REPLACE TEMP TABLE _t AS {roll_sql}")
    n_tot, n_pre = con.execute(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE eligible_all) FROM _t").fetchone()
    print(f"\n  roll {n_tot:,} -> {n_pre:,} registered before {first_election} "
          f"({n_pre / n_tot * 100:.1f}%)")

    # `roll_sql` already exposes the computed age as a plain column, so callers pass the
    # temp-table-qualified expression directly.
    band = band_sql(age_expr)
    for tag, panel in panels.items():
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _tc AS
            SELECT t.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END dn
            FROM _t t LEFT JOIN {panel} a USING (state_voter_id)""")
        print(f"\n  {tag} panel")
        for label, where in (("unrestricted (as published)", "1=1"),
                             ("eligible for all elections", "eligible_all")):
            rows = {int(dn): (int(n), float(s), float(v))
                    for dn, n, s, v in con.execute(f"""
                        SELECT dn, COUNT(*), AVG(super), AVG(voted)
                        FROM _tc WHERE {where} GROUP BY 1""").fetchall()}
            if 0 not in rows or 1 not in rows:
                continue
            gap = (rows[1][1] - rows[0][1]) * 100
            print(f"    {label:30} donors {rows[1][1]*100:5.1f}% "
                  f"(n={rows[1][0]:>9,})  non-donors {rows[0][1]*100:5.1f}%  "
                  f"gap {gap:+6.1f}")
            # age-standardized within the same restriction
            cell = {(b, int(dn)): (int(n), float(s)) for b, dn, n, s in con.execute(f"""
                SELECT {band}, dn, COUNT(*), AVG(super) FROM _tc t
                WHERE {where} GROUP BY 1, 2""").fetchall()}
            pop = {b: sum(n for (bb, _), (n, _) in cell.items() if bb == b) for b in BANDS}

            def _std(who: int) -> float:
                num = sum(pop[b] * cell[(b, who)][1] for b in BANDS
                          if pop.get(b) and (b, who) in cell)
                den = sum(pop[b] for b in BANDS if pop.get(b) and (b, who) in cell)
                return num / den if den else float("nan")
            print(f"    {'  age-standardized':30} donors {_std(1)*100:5.1f}%"
                  f"{'':13}  non-donors {_std(0)*100:5.1f}%  "
                  f"gap {(_std(1)-_std(0))*100:+6.1f}")
        # elections voted / eligible, unrestricted
        for dn, r in con.execute("""
            SELECT dn, AVG(voted*1.0/NULLIF(n_eligible,0)) FROM _tc
            WHERE n_eligible > 0 GROUP BY 1 ORDER BY 1""").fetchall():
            print(f"    {'voted / eligible ratio':30} "
                  f"{'donors' if dn else 'non-donors':11} {float(r)*100:5.1f}%")


# --------------------------------------------------------------------------
# R3-4 — the all-tier denominator discrepancy
# --------------------------------------------------------------------------
def report_alltier_denominator(con, state: str) -> None:
    rule(f"R3-4  {state}: all-tier state panel — which denominator is which")
    for tbl in (STATE + "_alltier", STATE):
        try:
            n, npos, nz = con.execute(f"""
                SELECT COUNT(*), COUNT(*) FILTER (WHERE total_donated > 0),
                       COUNT(*) FILTER (WHERE total_donated IS NULL)
                FROM {tbl}""").fetchone()
        except duckdb.Error:
            print(f"    {tbl:44} absent")
            continue
        joined, = con.execute(f"""
            SELECT COUNT(*) FROM {tbl} a JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.status_code='A'""").fetchone()
        print(f"    {tbl:44} rows {n:>9,}  positive {npos:>9,}  "
              f"null {nz:>6,}  active-joined {joined:>9,}")


def main() -> int:
    NY_PARTY = ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
                "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
    NY_ORDER = ["DEM", "REP", "NOPARTY", "OTHER"]
    NY_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    ID_PARTY = ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
                "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
    ID_ORDER = ["REP", "DEM", "UNAFF", "OTHER"]
    PANELS = {"federal": FED, "state": STATE}

    rule("NEW YORK", "#")
    ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
    ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_party_matchability(ny, "NY", PANELS, NY_AGE, NY_PARTY, NY_ORDER)
    # NY: four federal generals 2018-2024; eligible-for-all = registered before the 2018 GE.
    ny_roll = f"""
        WITH gen AS (SELECT state_voter_id, COUNT(DISTINCT election_year) g
                     FROM vrdb.voter_participation
                     WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
                     GROUP BY 1)
        SELECT v.state_voter_id,
               {NY_AGE} age,
               COALESCE(gen.g, 0) voted,
               CASE WHEN COALESCE(gen.g,0) >= 3 THEN 1.0 ELSE 0.0 END super,
               (v.registration_date <= DATE '2018-11-06') eligible_all,
               (CASE WHEN v.registration_date <= DATE '2018-11-06' THEN 4
                     WHEN v.registration_date <= DATE '2020-11-03' THEN 3
                     WHEN v.registration_date <= DATE '2022-11-08' THEN 2
                     WHEN v.registration_date <= DATE '2024-11-05' THEN 1
                     ELSE 0 END) n_eligible
        FROM vrdb.voters v LEFT JOIN gen USING (state_voter_id)
        WHERE v.status_code='A' AND {NY_AGE} IS NOT NULL AND {NY_AGE} >= 18"""
    report_eligibility_turnout(ny, "NY", PANELS, "t.age", ny_roll, "2018-11-06", 4)
    ny.close()

    rule("IDAHO", "#")
    idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
    idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_party_matchability(idc, "ID", PANELS, "v.age", ID_PARTY, ID_ORDER)
    idc.close()

    rule("WASHINGTON", "#")
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    WA_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    wa_roll = f"""
        WITH roll AS (SELECT state_voter_id
                      FROM donor_paper_wa_roll),
        gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                FROM vrdb.voting_history
                WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022,2024)
                GROUP BY 1)
        SELECT r.state_voter_id,
               {WA_AGE} age,
               COALESCE(gen.g, 0) voted,
               CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END super,
               (v.registration_date <= DATE '2022-11-08') eligible_all,
               (CASE WHEN v.registration_date <= DATE '2022-11-08' THEN 2
                     WHEN v.registration_date <= DATE '2024-11-05' THEN 1
                     ELSE 0 END) n_eligible
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
        WHERE {WA_AGE} IS NOT NULL AND {WA_AGE} >= 18 AND v.status_code = 'A'"""
    report_eligibility_turnout(wa, "WA", PANELS, "t.age", wa_roll, "2022-11-08", 2)
    report_alltier_denominator(wa, "WA")
    wa.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
