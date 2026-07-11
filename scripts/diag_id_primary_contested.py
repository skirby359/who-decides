"""How many Idaho primaries are actually contested? (all loaded cycles)

Qualifies the "closed primary IS the election" claim in who-decides-idaho.md §IV.
If a party's primary for a seat has only one candidate, the seat is settled at
candidate FILING — not by the primary electorate at all — so "the primary decides"
holds only for the CONTESTED share.

Source: `data/id_statewide.duckdb`, the loaded Idaho SoS canvasses (generals +
primaries, 2016-2024; see config/election_calendar.py + scripts/download_id_sos.py).
A "primary race" is one row in `races` for an election of type 'primary'; each
party's contest is a distinct race ("… REPUBLICAN" / "… DEMOCRATIC"). Contested =
>=2 distinct candidates with precinct results in that race.

Cross-validated against Ballotpedia's independent competitiveness tallies, per
cycle (contested Republican legislative primaries): 2016 ours 36 / BP 34; 2018
43 / 45; 2022 71 / 71; 2024 52 / 52 — exact on the two recent cycles, ±2 on the
older two. Total legislative filers (R+D) track BP within ~1-3% and run slightly
LOW by construction (BP counts who filed; this canvass counts who appeared on the
ballot, so post-deadline withdrawals drop out): 2016 215/217, 2018 229/231, 2022
252/259. The 2024 figure also matches a direct read of the raw SoS primary canvass.

Coverage note: the 2020 primary's *legislative* results were published by the SoS
at county level only (COVID-era mail-only cycle), with no precinct-level file, so
2020 loaded statewide-only — its legislative row is reported as n/a, not zero.

Public record, reproducible, no PII.
"""
import re
import sys

import duckdb

try:  # Windows consoles default to cp1252 and choke on the arrows/dashes below.
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

DB = "data/id_statewide.duckdb"

# Primary date per cycle (third Tuesday in May; 2020 delayed/mail-only May 19).
CYCLES = [("2016-05-17", 2016), ("2018-05-15", 2018), ("2020-05-19", 2020),
          ("2022-05-17", 2022), ("2024-05-21", 2024)]

# State-legislative race matcher, robust across the two naming conventions and
# excluding U.S. House/Senate and statewide offices:
#   2016/2018/2022  -> "LEGISLATIVE DISTRICT N ST REP A/B | ST SEN … REPUBLICAN"
#   2024            -> "REPRESENTATIVE DISTRICT N SEAT A/B …" (+ STATE SENATOR)
# The SEAT / LEGISLATIVE / STATE-SENATOR anchors keep out the 2020 archive's bare
# "REPRESENTATIVE DISTRICT 1/2" (which is actually U.S. House, sans the US prefix).
_LEG = """(UPPER(ra.race_name) LIKE '%LEGISLATIVE DISTRICT%'
   OR (UPPER(ra.race_name) LIKE '%REPRESENTATIVE DISTRICT%' AND UPPER(ra.race_name) LIKE '%SEAT%')
   OR UPPER(ra.race_name) LIKE '%STATE SENATOR%'
   OR UPPER(ra.race_name) LIKE '%SENATOR DISTRICT%')"""


# Idaho's legislature is 35 districts × {Senate, House Seat A, House Seat B} = 105
# seats every cycle. Reconciling the R-primary counts against this frame confirms
# they are exact seat tallies (not naming artifacts): each R race maps 1:1 to a
# seat, and 105 − (R races) is the number of seats where no Republican filed.
_CANON = set([(d, "SEN") for d in range(1, 36)]
             + [(d, "REP", s) for d in range(1, 36) for s in "AB"])


def _seat_key(name):
    """Parse a legislative race name to a canonical seat key, across both naming
    conventions (2016-2022 'LEGISLATIVE DISTRICT N ST SEN|ST REP A/B'; 2024
    'REPRESENTATIVE DISTRICT N SEAT A/B' + 'SENATOR DISTRICT N'). Returns None if
    no district, or ('UNPARSED', name) if the chamber/seat can't be resolved."""
    n = name.upper()
    m = re.search(r"DISTRICT (\d+)", n)
    if not m:
        return None
    d = int(m.group(1))
    if "ST SEN" in n or ("SENATOR" in n and "REPRESENTATIVE" not in n):
        return (d, "SEN")
    if "SEAT A" in n or "ST REP A" in n:
        return (d, "REP", "A")
    if "SEAT B" in n or "ST REP B" in n:
        return (d, "REP", "B")
    return ("UNPARSED", name)


def _leg_race_names(conn, date_str, party):
    return [r[0] for r in conn.execute(f"""
        SELECT ra.race_name FROM elections e
        JOIN races ra ON ra.election_id = e.election_id
        WHERE e.election_type = 'primary' AND e.election_date = DATE '{date_str}'
          AND UPPER(ra.race_name) LIKE '%{party}%' AND {_LEG}
    """).fetchall()]


def reconcile(conn):
    """Seat-frame reconciliation: R races should map 1:1 onto the 105 seats, with
    105 − count being seats no Republican contested (mostly safe-D seats Dems ran in)."""
    print("\n" + "=" * 72)
    print("Seat reconciliation vs the 105-seat frame (35 Sen + 70 House per cycle)")
    print("=" * 72)
    print(f"{'cycle':>6} {'Rraces':>7} {'Rseats':>7} {'dupes':>6} {'unparsed':>9} "
          f"{'Rless':>6} {'Rless w/ D primary':>19}")
    print("-" * 64)
    for date_str, yr in CYCLES:
        if yr == 2020:
            print(f"{yr:>6} {'—':>7} {'—':>7} {'—':>6} {'—':>9} {'—':>6}   (legislative n/a)")
            continue
        rk = [_seat_key(n) for n in _leg_race_names(conn, date_str, "REPUBLICAN")]
        dk = {k for k in (_seat_key(n) for n in _leg_race_names(conn, date_str, "DEMOCRATIC"))
              if k and k[0] != "UNPARSED"}
        unparsed = [k for k in rk if k and k[0] == "UNPARSED"]
        rseats = {k for k in rk if k and k[0] != "UNPARSED"}
        dupes = len([k for k in rk if k]) - len(set(k for k in rk if k))
        rless = _CANON - rseats
        dfiled = sum(1 for s in rless if s in dk)
        print(f"{yr:>6} {len(rk):>7} {len(rseats):>7} {dupes:>6} {len(unparsed):>9} "
              f"{len(rless):>6} {dfiled:>10} of {len(rless)}")
    print("  Reads: R races == R seats, 0 dupes/unparsed => counts are exact seat")
    print("  tallies. 105 − Rseats = seats no R contested; most are safe-D seats a")
    print("  Democrat ran in instead (the rest are single-filer seats, no primary at all).")


def counts(conn, date_str, party):
    """(#races, #contested>=2, #uncontested==1) for one party's legislative primaries."""
    q = f"""
    WITH rr AS (
        SELECT ra.race_id, COUNT(DISTINCT pr.candidate_id) AS ncand
        FROM elections e
        JOIN races ra ON ra.election_id = e.election_id
        JOIN precinct_results pr ON pr.race_id = ra.race_id
        WHERE e.election_type = 'primary' AND e.election_date = DATE '{date_str}'
          AND UPPER(ra.race_name) LIKE '%{party}%' AND {_LEG}
        GROUP BY 1
    )
    SELECT COUNT(*), COUNT(*) FILTER (WHERE ncand >= 2), COUNT(*) FILTER (WHERE ncand = 1)
    FROM rr
    """
    return conn.execute(q).fetchone()


def main():
    conn = duckdb.connect(DB, read_only=True)
    print("=" * 72)
    print("Idaho primaries — contested vs uncontested state-legislative races")
    print("(from data/id_statewide.duckdb; each party's primary is a distinct race)")
    print("=" * 72)
    print(f"{'cycle':>6} {'party':>4} {'races':>6} {'contested':>10} {'uncontested':>12} {'%contested':>11}")
    print("-" * 54)
    rep_trend = []
    for date_str, yr in CYCLES:
        for party, tag in [("REPUBLICAN", "REP"), ("DEMOCRATIC", "DEM")]:
            n, con, unc = counts(conn, date_str, party)
            if n == 0:
                # 2020: legislative not loaded (statewide-only cycle).
                print(f"{yr:>6} {tag:>4} {'—':>6} {'—':>10} {'—':>12} {'n/a':>11}")
                continue
            pc = 100.0 * con / n
            print(f"{yr:>6} {tag:>4} {n:>6} {con:>10} {unc:>12} {pc:>10.0f}%")
            if tag == "REP":
                rep_trend.append((yr, n, con, pc))

    print("\nRepublican legislative-primary contestation over time:")
    print("  " + " → ".join(f"{yr} {pc:.0f}%" for yr, n, con, pc in rep_trend))
    print("  The 'decisive' Republican primary is increasingly a real contest — the")
    print("  contested share roughly doubled across the decade, peaking in 2022 (the")
    print("  first post-redistricting cycle) — even as the primary stays closed to the")
    print("  unaffiliated quarter of the electorate. Democratic primaries are almost")
    print("  never contested (a one-party state fields few Democrats). 2020 legislative")
    print("  is n/a: the SoS published that cycle at county level only (no precinct file).")

    reconcile(conn)
    conn.close()


if __name__ == "__main__":
    main()
