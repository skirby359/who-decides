"""Turnout decomposition (Who Decides WA, §F1 follow-up): is the gray off-year
electorate driven by differential TURNOUT (behavior/salience) or by the registered
roll's COMPOSITION (who's registered)? Symmetric (Das-Gupta-style) two-factor
decomposition of the change in the 65+ (and 18-29) share of the electorate from the
2024 presidential general to the 2025 off-year general.

For cohort i in election t: R_{i,t} = age-eligible registrants on the current roll
(age as of election t), tau_{i,t} = turnout, electorate share of i =
R_i*tau_i / sum_j R_j*tau_j. We build the four counterfactual electorates
(P-roll/P-rates, P-roll/O-rates, O-roll/P-rates, O-roll/O-rates) and split the
observed share change into a RATE effect and a COMPOSITION effect.

If the rate effect dominates and composition ~ 0, the skew is a turnout/salience
problem (fixable by on-cycle timing), not a registration problem.
"""
import argparse

import duckdb

DB = "data/wa_vrdb.duckdb"
# Defaults reproduce the body's headline pair. The dates are ARGUMENTS as of
# 2026-08-09: they used to be module constants, so the paper's 2023 and 2021
# decomposition figures had no reproducible path in the repo at all — the script
# it cited could only ever produce the 2025 pair. That is the "a load-bearing
# claim no check could fail" shape, and it is why the 2023 and 2021 figures were
# published under the wrong definition for two rounds.
PRES, OFF = "2024-11-05", "2025-11-04"
OFF_YEARS = ("2025-11-04", "2023-11-07", "2021-11-02")
BUCKETS = ["18-29", "30-44", "45-64", "65+"]


def cohort_table(c, date):
    """{cohort -> (roll, voted)} on the current roll, age as of `date`."""
    rows = c.execute(f"""
        WITH elig AS (
            SELECT v.state_voter_id,
                   CASE WHEN date_diff('year', v.birthdate, DATE '{date}') < 30 THEN '18-29'
                        WHEN date_diff('year', v.birthdate, DATE '{date}') < 45 THEN '30-44'
                        WHEN date_diff('year', v.birthdate, DATE '{date}') < 65 THEN '45-64'
                        ELSE '65+' END coh,
                   CASE WHEN h.state_voter_id IS NOT NULL THEN 1 ELSE 0 END voted
            FROM voters v
            LEFT JOIN (SELECT DISTINCT state_voter_id FROM voting_history
                       WHERE election_date = DATE '{date}') h ON h.state_voter_id = v.state_voter_id
            WHERE v.birthdate IS NOT NULL
              AND date_diff('year', v.birthdate, DATE '{date}') >= 18
              AND v.registration_date IS NOT NULL AND v.registration_date <= DATE '{date}')
        SELECT coh, COUNT(*) roll, SUM(voted) voted FROM elig GROUP BY 1
    """).fetchall()
    return {coh: (float(roll), float(voted)) for coh, roll, voted in rows}


def share(roll, rate, target):
    """65+/target share of the electorate given roll{coh} and rate{coh}."""
    voters = {c: roll[c] * rate[c] for c in BUCKETS}
    tot = sum(voters.values())
    return voters[target] / tot if tot else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pres", default=PRES, help="presidential election date (YYYY-MM-DD)")
    ap.add_argument("--off", default=None,
                    help="off-year election date; repeatable via --all-off-years")
    ap.add_argument("--all-off-years", action="store_true",
                    help=f"run every off-year in {OFF_YEARS} against --pres")
    args = ap.parse_args()

    targets = list(OFF_YEARS) if args.all_off_years else [args.off or OFF]
    c = duckdb.connect(DB, read_only=True)
    P = cohort_table(c, args.pres)
    for off in targets:
        _report(c, P, args.pres, off)
    c.close()


def _report(c, P, pres, off):
    O = cohort_table(c, off)

    rollP = {c: P[c][0] for c in BUCKETS}
    rollO = {c: O[c][0] for c in BUCKETS}
    rateP = {c: P[c][1] / P[c][0] for c in BUCKETS}
    rateO = {c: O[c][1] / O[c][0] for c in BUCKETS}

    print(f"\n{'=' * 78}\nWithin-cohort turnout and roll share, "
          f"{pres} presidential vs {off} off-year:\n")
    print(f"{'cohort':7} {'roll%P':>7} {'roll%O':>7} {'turnoutP':>9} {'turnoutO':>9} {'O/P ret.':>9}")
    tP = sum(rollP.values()); tO = sum(rollO.values())
    for c in BUCKETS:
        print(f"{c:7} {rollP[c]/tP*100:6.1f}% {rollO[c]/tO*100:6.1f}% "
              f"{rateP[c]*100:8.1f}% {rateO[c]*100:8.1f}% {rateO[c]/rateP[c]*100:8.0f}%")

    for target in ["65+", "18-29"]:
        S_PP = share(rollP, rateP, target)   # observed presidential
        S_OO = share(rollO, rateO, target)   # observed off-year
        S_OP = share(rollO, rateP, target)   # off-year roll, presidential rates
        S_PO = share(rollP, rateO, target)   # presidential roll, off-year rates
        comp = 0.5 * ((S_OP - S_PP) + (S_OO - S_PO))   # composition (roll) effect
        rate = 0.5 * ((S_PO - S_PP) + (S_OO - S_OP))   # turnout-rate effect
        print(f"\n=== {target} share of the electorate: {S_PP*100:.1f}% (pres) -> "
              f"{S_OO*100:.1f}% (off-year), change {(S_OO-S_PP)*100:+.1f}pp ===")
        print(f"   turnout-rate (behavior) effect : {rate*100:+5.1f} pp")
        print(f"   roll-composition effect        : {comp*100:+5.1f} pp")
        # TWO ratios, printed separately and named differently on purpose. They
        # coincide only when both effects share a sign. Reporting the second under
        # the first's name is the defect corrected 2026-08-09: with a negative roll
        # effect, behaviour must account for MORE than 100% of the rise, so any
        # sub-100% figure called "share of the rise" is self-contradictory.
        of_rise = rate / (S_OO - S_PP) * 100 if (S_OO - S_PP) else float("nan")
        of_move = abs(rate) / (abs(rate) + abs(comp)) * 100
        print(f"   rate effect / observed change  : {of_rise:5.0f}%"
              f"   {'(>100% because the roll effect runs the other way)' if of_rise > 100 else ''}")
        print(f"   rate share of total movement   : {of_move:5.0f}%"
              f"   |rate| / (|rate| + |roll|)")
        dom = "turnout BEHAVIOR" if abs(rate) > abs(comp) else "roll COMPOSITION"
        print(f"   -> dominated by {dom}")
    print("\nReading: the off-year electorate is older principally because the young turn "
          "out\nfar less (behaviour under low salience), not because the registered roll is "
          "older.\nThat locates the mechanism; it does NOT identify what moving the election "
          "would do —\na decomposition is an accounting identity, not a counterfactual.")


if __name__ == "__main__":
    main()
