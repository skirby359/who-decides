"""Cross-state STATE-LEVEL campaign money comparison (state-agnostic).

The federal cuts (docs/cross-state-fec-money.md Sections A-I) all run on FEC
data. This is the first analysis over the STATE-disclosure layer now loaded
for every region state in ``candidate_finance``:

    WA  PDC        rows prefixed ``PDC:``       (legislative + curated locals ONLY)
    NY  NYSBOE     rows prefixed ``NY:``        (full filer universe)
    TX  TEC        rows prefixed ``TX:``        (full filer universe)
    ID  Sunshine   rows prefixed ``SUNSHINE:``  (full filer universe, no office/party)

Apples-to-apples core = STATE-HOUSE candidate money (office='SR'), because
every state's lower chamber is fully up each cycle (senates are staggered
heterogeneously: NY/ID 2-yr all-up, WA/TX 4-yr staggered). District joins are
restricted to the 2021-2024 window (elections on post-2022-redistricting maps;
odd years grouped into the following even cycle). 2026 is in-cycle (incomplete)
and excluded from money cuts.

Per-state gap-filling, mirroring the donor-side backfills:
  * TX legislative party is mostly Unknown -> joined to the ``candidates``
    roster (last name + chamber + district; unique-party guard).
  * ID Sunshine rows carry NO office/district/party -> person-name rows
    (``LAST, FIRST``) joined to the roster on (last, first-initial) with a
    unique-party guard; org-name rows are the PAC/party-committee layer.

Outputs reports/cross_state_state_money.json + a printed comparison.
"""
import duckdb

from cross_state_common import band, region_states, write_json

STATES = region_states()

# Per-state spec: state-row prefix, house forecast-district prefix, whether
# party comes native from the disclosure feed, and what the filer universe is.
SPEC = {
    "WA": dict(prefix="PDC:", house_fc="ld", native_party=True,
               universe="legislative + curated local candidates only (no statewide execs, no PACs/party cmtes)"),
    "NY": dict(prefix="NY:", house_fc="ad", native_party=True,
               universe="full filer universe (candidates + party cmtes + PACs)"),
    "TX": dict(prefix="TX:", house_fc="hd", native_party=False,
               universe="full filer universe (candidates + PACs; statewide execs mostly office-unclassified)"),
    "ID": dict(prefix="SUNSHINE:", house_fc="ld", native_party=False,
               universe="full filer universe (candidates + PACs + ballot cmtes; office/party via roster join)"),
}

HOUSE_SEATS = {"WA": 98, "NY": 150, "TX": 150, "ID": 70}

# District-cut window: elections fought on current (post-2022) maps, complete
# cycles only. Odd years (ID/WA locals, off-year filing) group into the next
# even cycle.
WINDOW = "((election_cycle + (election_cycle % 2)) IN (2022, 2024))"


def _id_backfill_sql() -> str:
    """CTEs classifying ID SUNSHINE rows via the SoS candidates roster.

    Produces ``fin`` with (office, dist, party) columns matching the shape the
    other states get natively. Only person-name rows (``LAST, FIRST``) are
    join-eligible; the unique-party guard drops ambiguous (last, initial) keys.
    """
    return r"""
    roster AS (
      SELECT UPPER(TRIM(REGEXP_EXTRACT(cd.candidate_name, '(\S+)$', 1))) lastn,
             UPPER(LEFT(TRIM(cd.candidate_name), 1)) fi,
             CASE WHEN UPPER(r.office) LIKE 'REPRESENTATIVE DISTRICT%' THEN 'SR'
                  WHEN UPPER(r.office) LIKE 'SENATOR DISTRICT%' THEN 'SS' END office,
             TRY_CAST(REGEXP_EXTRACT(r.office, '(\d+)', 1) AS INT) dist,
             cd.party_normalized p
      FROM candidates cd JOIN races r USING (race_id)
      WHERE cd.party_normalized IN ('Democratic', 'Republican')
    ),
    uniq AS (
      SELECT lastn, fi, MIN(p) p, MIN(office) office, MIN(dist) dist
      FROM roster WHERE office IS NOT NULL AND dist IS NOT NULL
      GROUP BY 1, 2 HAVING COUNT(DISTINCT p) = 1
    ),
    fin AS (
      SELECT f.election_cycle, f.total_receipts,
             f.total_individual_contributions, f.total_pac_contributions,
             u.office, u.dist, COALESCE(u.p, 'Unknown') party,
             (f.candidate_name LIKE '%,%') is_person
      FROM candidate_finance f
      LEFT JOIN uniq u
        ON u.lastn = UPPER(TRIM(SPLIT_PART(f.candidate_name, ',', 1)))
       AND u.fi = UPPER(LEFT(TRIM(SPLIT_PART(f.candidate_name, ',', 2)), 1))
       AND f.candidate_name LIKE '%,%'
      WHERE f.fec_candidate_id LIKE 'SUNSHINE:%'
    )
    """


def _tx_party_sql() -> str:
    """CTEs adding roster-joined party to TX legislative rows (native rows for
    everything else). Join key = last name + chamber + district, unique-party
    guarded; TLC roster names are last-name-only."""
    return r"""
    roster AS (
      SELECT UPPER(TRIM(REGEXP_REPLACE(cd.candidate_name, '\s*\[.*\]$', ''))) lastn,
             CASE WHEN UPPER(r.race_name) LIKE 'REPRESENTATIVE HOUSE DISTRICT%' THEN 'SR'
                  WHEN UPPER(r.race_name) LIKE 'SENATOR SENATE DISTRICT%' THEN 'SS' END office,
             TRY_CAST(REGEXP_EXTRACT(r.race_name, '(\d+)$', 1) AS INT) dist,
             cd.party_normalized p
      FROM candidates cd JOIN races r USING (race_id)
      WHERE cd.party_normalized IN ('Democratic', 'Republican')
    ),
    uniq AS (
      SELECT lastn, office, dist, MIN(p) p
      FROM roster WHERE office IS NOT NULL AND dist IS NOT NULL
      GROUP BY 1, 2, 3 HAVING COUNT(DISTINCT p) = 1
    ),
    fin AS (
      SELECT f.election_cycle, f.total_receipts,
             f.total_individual_contributions, f.total_pac_contributions,
             f.office, TRY_CAST(f.district AS INT) dist,
             CASE WHEN f.party IN ('Democratic', 'Republican') THEN f.party
                  ELSE COALESCE(u.p, 'Unknown') END party,
             (f.candidate_name LIKE '%,%') is_person
      FROM candidate_finance f
      LEFT JOIN uniq u
        ON u.lastn = UPPER(TRIM(SPLIT_PART(f.candidate_name, ',', 1)))
       AND u.office = f.office AND u.dist = TRY_CAST(f.district AS INT)
      WHERE f.fec_candidate_id LIKE 'TX:%'
    )
    """


def _native_sql(prefix: str) -> str:
    """fin CTE for states whose disclosure feed already carries office/party."""
    return f"""
    fin AS (
      SELECT election_cycle, total_receipts,
             total_individual_contributions, total_pac_contributions,
             office, TRY_CAST(district AS INT) dist, party,
             (candidate_name LIKE '%,%') is_person
      FROM candidate_finance WHERE fec_candidate_id LIKE '{prefix}%'
    )
    """


def _fin_cte(st: str) -> str:
    if st == "ID":
        return _id_backfill_sql()
    if st == "TX":
        return _tx_party_sql()
    return _native_sql(SPEC[st]["prefix"])


def _house_margins(path: str, fc_prefix: str) -> dict[int, float]:
    """{district_number: abs_margin} from the latest Democratic house-chamber
    forecast in this state's DB."""
    c = duckdb.connect(path, read_only=True)
    try:
        rows = c.execute(
            "WITH r AS (SELECT district_id, predicted_margin, "
            "ROW_NUMBER() OVER (PARTITION BY district_id ORDER BY as_of_date DESC) rn "
            f"FROM forecast_predictions WHERE party='Democratic' AND district_id LIKE '{fc_prefix}%') "
            "SELECT district_id, predicted_margin FROM r WHERE rn=1"
        ).fetchall()
    finally:
        c.close()
    out = {}
    for did, m in rows:
        try:
            out[int(did[len(fc_prefix):])] = abs(float(m))
        except ValueError:
            continue
    return out


def analyze(st: str, path: str) -> dict:
    spec = SPEC.get(st)
    if spec is None:
        return {"skipped": f"no state-finance spec for {st}"}
    c = duckdb.connect(path, read_only=True)
    cte = _fin_cte(st)
    res: dict = {"universe": spec["universe"]}

    # ---- J0 inventory --------------------------------------------------
    inv = c.execute(
        f"WITH {cte} SELECT COUNT(*), ROUND(SUM(total_receipts)/1e6, 1), "
        "MIN(election_cycle), MAX(election_cycle), "
        "ROUND(SUM(total_receipts) FILTER (WHERE office IN ('SR','SS'))/1e6, 1), "
        "ROUND(SUM(total_receipts) FILTER (WHERE party IN ('Democratic','Republican'))/1e6, 1) "
        "FROM fin"
    ).fetchone()
    res["inventory"] = dict(zip(
        ["rows", "total_m", "cycle_min", "cycle_max", "legislative_m", "party_resolved_m"], inv))

    # ---- J1 price of a house seat (2022+2024 cycles, current maps) -----
    j1 = c.execute(
        f"WITH {cte} SELECT ROUND(SUM(total_receipts)/1e6, 1), COUNT(*), "
        "ROUND(MEDIAN(total_receipts), 0), ROUND(AVG(total_receipts), 0) "
        f"FROM fin WHERE office='SR' AND {WINDOW} AND total_receipts > 0"
    ).fetchone()
    seats = HOUSE_SEATS[st]
    res["house_seat"] = dict(
        total_m=j1[0], candidates=j1[1], median_raise=j1[2], mean_raise=j1[3],
        seats=seats,
        per_seat_cycle=round(float(j1[0] or 0) * 1e6 / (seats * 2), 0),
    )

    # ---- J2 house money vs competitiveness -----------------------------
    margins = _house_margins(path, spec["house_fc"])
    dist_money = c.execute(
        f"WITH {cte} SELECT dist, SUM(total_receipts) "
        f"FROM fin WHERE office='SR' AND {WINDOW} AND dist IS NOT NULL GROUP BY 1"
    ).fetchall()
    bands: dict[str, dict] = {}
    for d, tot in dist_money:
        if d not in margins:
            continue
        b = band(margins[d])
        e = bands.setdefault(b, {"districts": 0, "total": 0.0})
        e["districts"] += 1
        e["total"] += float(tot)
    # districts with a forecast but NO money rows still belong in the denominator
    moneyed = {d for d, _ in dist_money}
    for d, m in margins.items():
        if d not in moneyed:
            e = bands.setdefault(band(m), {"districts": 0, "total": 0.0})
            e["districts"] += 1
    for b, e in bands.items():
        e["per_district_m"] = round(e["total"] / max(e["districts"], 1) / 1e6, 2)
        e["total"] = round(e["total"] / 1e6, 2)
    res["money_vs_competitiveness"] = bands
    comp = [e for b, e in bands.items() if b in ("Tossup", "Lean")]
    solid = bands.get("Solid")
    if comp and solid and solid["per_district_m"]:
        comp_d = sum(e["districts"] for e in comp)
        comp_m = sum(e["total"] for e in comp)
        res["competitive_premium"] = round(
            (comp_m / comp_d) / solid["per_district_m"], 2)

    # ---- J3 party split (legislative rows, complete cycles) ------------
    j3 = c.execute(
        f"WITH {cte} SELECT party, COUNT(*), ROUND(SUM(total_receipts)/1e6, 1) "
        f"FROM fin WHERE office IN ('SR','SS') AND {WINDOW} "
        "GROUP BY 1 ORDER BY 3 DESC"
    ).fetchall()
    res["party_split"] = {p: dict(n=n, total_m=m) for p, n, m in j3}
    dm = res["party_split"].get("Democratic", {}).get("total_m") or 0
    rm = res["party_split"].get("Republican", {}).get("total_m") or 0
    if dm + rm:
        res["party_split"]["dem_share_of_resolved"] = round(dm / (dm + rm), 3)

    # ---- J4 individual vs PAC composition (legislative rows) -----------
    j4 = c.execute(
        f"WITH {cte} SELECT SUM(total_individual_contributions), "
        "SUM(total_pac_contributions), SUM(total_receipts) "
        f"FROM fin WHERE office IN ('SR','SS') AND {WINDOW}"
    ).fetchone()
    ind, pac, tot = (float(x or 0) for x in j4)
    res["composition"] = dict(
        individual_share=round(ind / tot, 3) if tot else None,
        pac_share=round(pac / tot, 3) if tot else None,
        other_share=round((tot - ind - pac) / tot, 3) if tot else None,
    )

    # ---- J5 panorama: top filers + person/org layer --------------------
    pfx = spec["prefix"]
    res["top_filers"] = [
        dict(name=nm, total_m=m, cycles=cy)
        for nm, m, cy in c.execute(
            "SELECT candidate_name, ROUND(SUM(total_receipts)/1e6, 1), "
            "COUNT(DISTINCT election_cycle) "
            f"FROM candidate_finance WHERE fec_candidate_id LIKE '{pfx}%' "
            "AND election_cycle <= 2025 "
            "GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
        ).fetchall()
    ]
    # Person-vs-org split is only derivable where filer names follow the
    # "LAST, FIRST" convention (TEC/Sunshine). WA is candidates-only by
    # construction; NY filers are ALL committee names (incl. candidate cmtes).
    if st in ("TX", "ID"):
        j5 = c.execute(
            f"WITH {cte} SELECT is_person, COUNT(*), ROUND(SUM(total_receipts)/1e6, 1) "
            "FROM fin WHERE election_cycle <= 2025 GROUP BY 1"
        ).fetchall()
        res["person_vs_org"] = {
            ("person" if k else "org"): dict(n=n, total_m=m) for k, n, m in j5}

    c.close()
    return res


def main() -> None:
    out = {}
    for st, path in STATES:
        print(f"=== {st} ===")
        out[st] = analyze(st, path)
        for k, v in out[st].items():
            print(f"  {k}: {v}")
    path = write_json("cross_state_state_money.json", out)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
