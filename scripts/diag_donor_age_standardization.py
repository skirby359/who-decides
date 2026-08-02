"""Age-standardized party and turnout cuts for docs/donor-class-and-the-electorate.md.

Answers two asks from the 2026-07-29 external review. Both have the same shape: the
paper's strongest compositional finding is that matched donors are much OLDER than the
roll, and two other findings are stated on raw (age-unadjusted) comparisons, so part of
each could be age composition rather than the thing being claimed.

  R3  party, age-standardized      Registered Democrats are over-represented among
                                   matched donors. Is that still true comparing donors
                                   to registrants of the SAME age? Reported three ways:
                                   party shares WITHIN each age band, donation
                                   PREVALENCE by party within band (donors per 1,000
                                   registrants — the cleanest "who gives" measure, since
                                   it needs no share-of-donors denominator), and a
                                   directly age-standardized donor party share using the
                                   registration age distribution as the standard.
  R4  turnout, age-standardized    Donors vote far more than non-donors. Older
                                   registrants vote more and have longer histories, so
                                   the raw gap mixes the giving<->voting association
                                   with the donor pool's age skew. Reported within age
                                   bands, then directly standardized to a common age
                                   distribution, then standardized jointly on age AND
                                   registration tenure (a 22-year-old cannot have a
                                   four-election history).

Direct standardization, stated exactly. With age bands b, standard weights w_b taken
from the ACTIVE registration roll (the universe the matcher draws from), and a
within-band statistic x_b for the group being standardized, the standardized statistic
is sum_b w_b * x_b. For party shares the within-band statistic is the group's share of
that band's donors, so the standardized shares still sum to 100% by construction. For
the joint age x tenure version, cells where either group is empty carry no weight and
the retained share of the standard population is printed, because a standardization that
silently drops cells is not comparable to one that does not.

This is a compositional adjustment, not a causal one. It answers "is the raw gap merely
the age skew restated?" and nothing further: standardizing on age does not address
current-roll survivorship, party-of-record timing, or linkage error, all of which are
carried as limitations in the paper.

Read-only; aggregate output only (the voter files carry PII).

Run:  python scripts/diag_donor_age_standardization.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"

FED = "voter_donor_affiliation_fec"
STATE = "voter_donor_affiliation_state"

# Finer than the paper's four display bands. Standardization residual-confounds less
# with narrower strata, and the four-band version is printed alongside so the choice is
# visible rather than assumed.
BANDS_FINE = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
BANDS_COARSE = ["18-29", "30-44", "45-64", "65+"]

TENURE = ["<2y", "2-5y", "6-10y", "11-20y", "20y+"]


def band_sql(age_expr: str, fine: bool) -> str:
    if fine:
        return (f"CASE WHEN {age_expr}<25 THEN '18-24' WHEN {age_expr}<35 THEN '25-34' "
                f"WHEN {age_expr}<45 THEN '35-44' WHEN {age_expr}<55 THEN '45-54' "
                f"WHEN {age_expr}<65 THEN '55-64' WHEN {age_expr}<75 THEN '65-74' "
                f"ELSE '75+' END")
    return (f"CASE WHEN {age_expr}<30 THEN '18-29' WHEN {age_expr}<45 THEN '30-44' "
            f"WHEN {age_expr}<65 THEN '45-64' ELSE '65+' END")


def tenure_sql(reg_expr: str) -> str:
    y = f"date_diff('year', {reg_expr}, DATE '2024-11-05')"
    return (f"CASE WHEN {y}<2 THEN '<2y' WHEN {y}<6 THEN '2-5y' WHEN {y}<11 THEN '6-10y' "
            f"WHEN {y}<21 THEN '11-20y' ELSE '20y+' END")


def rule(title: str, char: str = "=") -> None:
    print("\n" + char * 78)
    print(title)
    print(char * 78)


# --------------------------------------------------------------------------
# R3 — party composition, age-standardized
# --------------------------------------------------------------------------
def report_party_standardized(con, state: str, panels: dict[str, str], age_expr: str,
                             party_case: str, order: list[str], fine: bool = True) -> None:
    bands = BANDS_FINE if fine else BANDS_COARSE
    band = band_sql(age_expr, fine)
    tag = "fine bands" if fine else "four display bands"
    rule(f"R3  {state}: donor party composition, age-standardized ({tag})")
    print("  Universe: ACTIVE registrants with a known age of 18+ (the matcher's own")
    print("  universe, minus records with no usable age). Standard population for the")
    print("  direct standardization = that roll's age distribution.")

    # Standard population: active registrants by band x party.
    reg = {(b, p): n for b, p, n in con.execute(f"""
        SELECT {band} b, {party_case} p, COUNT(*)
        FROM vrdb.voters v
        WHERE status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18
        GROUP BY 1, 2""").fetchall()}
    reg_band = {b: sum(n for (bb, _), n in reg.items() if bb == b) for b in bands}
    reg_total = sum(reg_band.values())
    reg_party = {p: sum(n for (_, pp), n in reg.items() if pp == p) for p in order}
    w = {b: reg_band[b] / reg_total for b in bands}

    print(f"\n  roll age distribution (n={reg_total:,})")
    print("    " + "".join(f"{b:>9}" for b in bands))
    print("    " + "".join(f"{w[b]*100:8.1f}%" for b in bands))

    for label, panel in panels.items():
        don = {(b, p): n for b, p, n in con.execute(f"""
            SELECT {band} b, {party_case} p, COUNT(*)
            FROM {panel} a JOIN vrdb.voters v USING (state_voter_id)
            WHERE v.status_code='A' AND {age_expr} IS NOT NULL AND {age_expr} >= 18
            GROUP BY 1, 2""").fetchall()}
        don_band = {b: sum(n for (bb, _), n in don.items() if bb == b) for b in bands}
        don_total = sum(don_band.values())
        if not don_total:
            print(f"\n  {label} panel: no rows with usable age — skipped")
            continue

        print(f"\n  {label} panel (n={don_total:,})")
        print("    donor party share WITHIN each age band, and (roll share) beneath")
        print(f"    {'party':9}" + "".join(f"{b:>9}" for b in bands))
        for p in order:
            row = "".join(
                f"{(don.get((b, p), 0)/don_band[b]*100 if don_band[b] else float('nan')):8.1f}%"
                for b in bands)
            print(f"    {p:9}{row}")
            row_r = "".join(f"{reg.get((b, p), 0)/reg_band[b]*100:8.1f}%" for b in bands)
            print(f"    {'  (roll)':9}{row_r}")

        print("\n    donation PREVALENCE — matched donors per 1,000 registrants of the")
        print("    same party AND age band (needs no donor-share denominator)")
        print(f"    {'party':9}" + "".join(f"{b:>9}" for b in bands) + f"{'all':>9}")
        for p in order:
            row = "".join(
                f"{(don.get((b, p), 0)/reg[(b, p)]*1000 if reg.get((b, p)) else float('nan')):9.1f}"
                for b in bands)
            allp = (sum(n for (_, pp), n in don.items() if pp == p) / reg_party[p] * 1000
                    if reg_party.get(p) else float("nan"))
            print(f"    {p:9}{row}{allp:9.1f}")

        print("\n    RAW vs AGE-STANDARDIZED donor party share, against registration")
        print(f"    {'party':9}{'roll%':>8}{'raw%':>8}{'std%':>8}{'raw skew':>10}"
              f"{'std skew':>10}{'age-expl':>10}")
        for p in order:
            roll_p = reg_party.get(p, 0) / reg_total * 100
            raw = sum(n for (_, pp), n in don.items() if pp == p) / don_total * 100
            std = sum(w[b] * (don.get((b, p), 0) / don_band[b]) for b in bands
                      if don_band[b]) * 100
            raw_skew, std_skew = raw - roll_p, std - roll_p
            expl = ((raw_skew - std_skew) / raw_skew * 100
                    if abs(raw_skew) > 1e-9 else float("nan"))
            print(f"    {p:9}{roll_p:7.1f}%{raw:7.1f}%{std:7.1f}%{raw_skew:+9.1f}"
                  f"{std_skew:+9.1f}{expl:9.1f}%")


# --------------------------------------------------------------------------
# R4 — turnout, age-standardized (and age x tenure standardized)
# --------------------------------------------------------------------------
def report_turnout_standardized(con, state: str, roll_sql: str, panels: dict[str, str],
                                measure: str = "super-voter",
                                tenure_is_endogenous: bool = False) -> None:
    """roll_sql must yield (state_voter_id, band, tenure, super) over the comparison
    universe, with `super` a 0/1 flag. Donor status is joined per panel.

    tenure_is_endogenous marks an outcome whose DEFINITION already contains registration
    tenure. Washington's `voter_scores.is_super_voter` is such a measure — it is
    (last_voted >= 2022-01-01 AND years registered >= 8), so every registrant of under
    eight years' standing is FALSE by construction. Standardizing that outcome on tenure
    conditions on a component of the outcome itself, which is not an adjustment; the row
    is still printed, labelled, and must not be read as one.
    """
    rule(f"R4  {state}: donor vs non-donor turnout, age- and tenure-standardized"
         f"  [{measure}]")
    print("  Standard population = the whole comparison universe (both groups pooled),")
    print("  so 'standardized' means: what each group's rate would be if its age (or")
    print("  age x tenure) composition matched the roll's. The non-donor rate barely")
    print("  moves — non-donors ARE nearly the whole roll — so the adjustment lands")
    print("  almost entirely on the donor side, which is the point.")
    con.execute(f"CREATE OR REPLACE TEMP TABLE _roll AS {roll_sql}")

    for label, panel in panels.items():
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE _cmp AS
            SELECT r.*, CASE WHEN a.state_voter_id IS NOT NULL THEN 1 ELSE 0 END d
            FROM _roll r LEFT JOIN {panel} a USING (state_voter_id)""")
        raw = {d: (n, s) for d, n, s in con.execute(
            "SELECT d, COUNT(*), AVG(super) FROM _cmp GROUP BY 1").fetchall()}
        if 1 not in raw or 0 not in raw:
            print(f"\n  {label} panel: one side empty — skipped")
            continue
        n_d, r_d = raw[1][0], float(raw[1][1])
        n_n, r_n = raw[0][0], float(raw[0][1])
        print(f"\n  {label} panel — RAW: donors {r_d*100:.1f}% (n={n_d:,}) vs "
              f"non-donors {r_n*100:.1f}% (n={n_n:,}), gap {(r_d-r_n)*100:+.1f} pts")

        # within-band rates
        rows = con.execute("""
            SELECT band, d, COUNT(*) n, AVG(super) s FROM _cmp GROUP BY 1, 2""").fetchall()
        cell = {(b, d): (n, float(s)) for b, d, n, s in rows}
        std_pop = {b: sum(n for (bb, _), (n, _) in cell.items() if bb == b)
                   for b in BANDS_FINE}
        tot = sum(std_pop.values())
        print(f"    {'band':8}{'roll wt':>9}{'donor n':>10}{'donor%':>9}"
              f"{'non-donor%':>12}{'gap':>8}")
        for b in BANDS_FINE:
            if not std_pop.get(b):
                continue
            dn, ds = cell.get((b, 1), (0, float("nan")))
            nn, ns = cell.get((b, 0), (0, float("nan")))
            print(f"    {b:8}{std_pop[b]/tot*100:8.1f}%{dn:>10,}{ds*100:8.1f}%"
                  f"{ns*100:11.1f}%{(ds-ns)*100:+8.1f}")

        # age-standardized, both groups, to the pooled roll distribution
        def std_rate(d: int) -> float:
            num = sum(std_pop[b] / tot * cell[(b, d)][1] for b in BANDS_FINE
                      if std_pop.get(b) and (b, d) in cell)
            wt = sum(std_pop[b] / tot for b in BANDS_FINE
                     if std_pop.get(b) and (b, d) in cell)
            return num / wt if wt else float("nan")

        sd, sn = std_rate(1), std_rate(0)
        print(f"    AGE-standardized: donors {sd*100:.1f}% vs non-donors {sn*100:.1f}%,"
              f" gap {(sd-sn)*100:+.1f} pts  (raw gap {(r_d-r_n)*100:+.1f})")

        # joint age x tenure
        jrows = con.execute("""
            SELECT band, tenure, d, COUNT(*) n, AVG(super) s
            FROM _cmp WHERE tenure IS NOT NULL GROUP BY 1, 2, 3""").fetchall()
        jcell = {(b, t, d): (n, float(s)) for b, t, d, n, s in jrows}
        jpop: dict[tuple[str, str], int] = {}
        for (b, t, _), (n, _) in jcell.items():
            jpop[(b, t)] = jpop.get((b, t), 0) + n
        jtot = sum(jpop.values())
        keys = [k for k in jpop if (k[0], k[1], 1) in jcell and (k[0], k[1], 0) in jcell]
        retained = sum(jpop[k] for k in keys) / jtot if jtot else 0.0

        def jstd(d: int) -> float:
            num = sum(jpop[k] * jcell[(k[0], k[1], d)][1] for k in keys)
            return num / sum(jpop[k] for k in keys) if keys else float("nan")

        jd, jn = jstd(1), jstd(0)
        warn = "  ** NOT an adjustment — tenure is inside this outcome's definition **" \
            if tenure_is_endogenous else ""
        print(f"    AGE x TENURE-standardized: donors {jd*100:.1f}% vs non-donors "
              f"{jn*100:.1f}%, gap {(jd-jn)*100:+.1f} pts "
              f"({retained*100:.1f}% of the standard population retained)")
        if warn:
            print(warn)


def main() -> int:
    NY_PARTY = ("CASE WHEN v.party='DEM' THEN 'DEM' WHEN v.party='REP' THEN 'REP' "
                "WHEN v.party='BLK' THEN 'NOPARTY' ELSE 'OTHER' END")
    NY_ORDER = ["DEM", "REP", "NOPARTY", "OTHER"]
    NY_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    ID_PARTY = ("CASE WHEN v.party='REP' THEN 'REP' WHEN v.party='DEM' THEN 'DEM' "
                "WHEN v.party='UNA' THEN 'UNAFF' ELSE 'OTHER' END")
    ID_ORDER = ["REP", "DEM", "UNAFF", "OTHER"]
    PANELS = {"federal": FED, "state": STATE}

    rule("NEW YORK  (ny_statewide + ny_vrdb)", "#")
    ny = duckdb.connect(str(DATA / "ny_statewide.duckdb"), read_only=True)
    ny.execute(f"ATTACH '{DATA / 'ny_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_party_standardized(ny, "NY", PANELS, NY_AGE, NY_PARTY, NY_ORDER, fine=True)
    report_party_standardized(ny, "NY", PANELS, NY_AGE, NY_PARTY, NY_ORDER, fine=False)
    # NY turnout: generals voted of the last four; super-voter = >=3 of 4.
    ny_roll = f"""
        WITH gen AS (
            SELECT state_voter_id, COUNT(DISTINCT election_year) g
            FROM vrdb.voter_participation
            WHERE kind='GENERAL' AND election_year IN (2018,2020,2022,2024)
            GROUP BY 1)
        SELECT v.state_voter_id,
               {band_sql(NY_AGE, True)} band,
               {tenure_sql('v.registration_date')} tenure,
               CASE WHEN COALESCE(gen.g,0) >= 3 THEN 1.0 ELSE 0.0 END super
        FROM vrdb.voters v LEFT JOIN gen USING (state_voter_id)
        WHERE v.status_code='A' AND {NY_AGE} IS NOT NULL AND {NY_AGE} >= 18"""
    report_turnout_standardized(ny, "NY", ny_roll, PANELS)
    ny.close()

    rule("IDAHO  (id_statewide + id_vrdb)", "#")
    idc = duckdb.connect(str(DATA / "id_statewide.duckdb"), read_only=True)
    idc.execute(f"ATTACH '{DATA / 'id_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    report_party_standardized(idc, "ID", PANELS, "v.age", ID_PARTY, ID_ORDER, fine=True)
    report_party_standardized(idc, "ID", PANELS, "v.age", ID_PARTY, ID_ORDER, fine=False)
    print("\n  (Idaho turnout is reported as COMPOSITION not rates — current-roll")
    print("   denominators make ID rates survivorship-unreliable, Appendix C — so the")
    print("   turnout standardization is run for WA and NY only.)")
    idc.close()

    rule("WASHINGTON  (wa_statewide + wa_vrdb)", "#")
    wa = duckdb.connect(str(DATA / "wa_statewide.duckdb"), read_only=True)
    wa.execute(f"ATTACH '{DATA / 'wa_vrdb.duckdb'}' AS vrdb (READ_ONLY)")
    print("\n  (WA publishes no party of record, so R3 has no WA cut.)")
    WA_AGE = "date_diff('year', v.birthdate, DATE '2024-11-05')"
    wa_roll = f"""
        WITH roll AS (SELECT state_voter_id, is_super_voter
                      FROM donor_paper_wa_roll)
        SELECT r.state_voter_id,
               {band_sql(WA_AGE, True)} band,
               {tenure_sql('v.registration_date')} tenure,
               CASE WHEN r.is_super_voter THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        WHERE {WA_AGE} IS NOT NULL AND {WA_AGE} >= 18 AND v.status_code = 'A'"""
    report_turnout_standardized(wa, "WA", wa_roll, PANELS,
                                measure="voter_scores.is_super_voter (published)",
                                tenure_is_endogenous=True)

    # A tenure-free WA measure, so the tenure standardization means something. WA's VRDB
    # voting_history carries a rolling window that reaches only the 2022 and 2024
    # generals, so this is 2-of-2 rather than NY's 3-of-4 — a different measure, reported
    # as its own row and never compared to NY's number.
    print("\n  WA has no four-general history in the VRDB export (voting_history holds")
    print("  the 2022 and 2024 generals only), so the tenure-free measure below is")
    print("  'voted BOTH the 2022 and 2024 generals'. It is not comparable to NY's")
    print("  3-of-4 super-voter rate; it exists so that a tenure standardization can be")
    print("  run on an outcome that does not already contain tenure.")
    wa_roll2 = f"""
        WITH roll AS (SELECT state_voter_id
                      FROM donor_paper_wa_roll),
        gen AS (SELECT state_voter_id, COUNT(DISTINCT YEAR(election_date)) g
                FROM vrdb.voting_history
                WHERE MONTH(election_date)=11 AND YEAR(election_date) IN (2022, 2024)
                GROUP BY 1)
        SELECT r.state_voter_id,
               {band_sql(WA_AGE, True)} band,
               {tenure_sql('v.registration_date')} tenure,
               CASE WHEN COALESCE(gen.g,0) >= 2 THEN 1.0 ELSE 0.0 END super
        FROM roll r JOIN vrdb.voters v USING (state_voter_id)
        LEFT JOIN gen ON gen.state_voter_id = r.state_voter_id
        WHERE {WA_AGE} IS NOT NULL AND {WA_AGE} >= 18 AND v.status_code = 'A'"""
    report_turnout_standardized(wa, "WA", wa_roll2, PANELS,
                                measure="voted both 2022 and 2024 generals (tenure-free)")
    wa.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
