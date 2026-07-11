"""Load the NYSVOTER statewide FOIL voter file into a standalone ny_vrdb.duckdb.

This is the flagship party-of-record dataset the electoral-health study was
gated on (TODO #1): unlike WA, New York publishes individual *party
enrollment* (ENROLLMENT, field 22) plus full DOB and per-event voting
history. Loading it unblocks the party-resolved re-run of the §F playbook
(turnout-by-age x party, donor-class x party, individual crossover).

Source: data/raw/ny/ALLNYVOTERS20260629.zip
  -> ALLNYVOTERS20260629/ALLNYVOTERS20260629.txt  (~6.26 GB, ~14M rows)
Layout: FOIL_VOTER_LIST_LAYOUT.pdf v2.6 — 47 CSV fields, all double-quoted,
  comma-delimited, CR-LF, NO header row.

Writes a standalone data/ny_vrdb.duckdb (parallel to wa_vrdb.duckdb) so it
never lock-conflicts with ny_statewide.duckdb. The huge .txt is extracted to
local temp (off the Dropbox tree) and deleted afterward unless --keep-files.

Usage:
    PYTHONPATH=src python scripts/load_ny_voters.py
    PYTHONPATH=src python scripts/load_ny_voters.py --keep-files
"""
import argparse
import os
import sys
import zipfile

import duckdb

ZIP_PATH = "data/raw/ny/ALLNYVOTERS20260629.zip"
INNER_TXT = "ALLNYVOTERS20260629/ALLNYVOTERS20260629.txt"
TMP_DIR = "data/_ny_voters"
TMP_TXT = f"{TMP_DIR}/ALLNYVOTERS20260629.txt"
NY_VRDB = "data/ny_vrdb.duckdb"

# Field order per FOIL_VOTER_LIST_LAYOUT.pdf v2.6 (positions 1-47).
RAW_COLS = [
    "last_name", "first_name", "middle_name", "name_suffix",
    "r_add_number", "r_halfcode", "r_predirection", "r_streetname",
    "r_postdirection", "r_apt_type", "r_apt", "r_addr_nonstd",
    "r_city", "r_zip5", "r_zip4",
    "mailadd1", "mailadd2", "mailadd3", "mailadd4",
    "dob", "gender", "enrollment", "otherparty",
    "county_code", "ed", "ld", "town_city", "ward",
    "cd", "sd", "ad",
    "last_voter_date", "prev_year_voted", "prev_county", "prev_address",
    "prev_name", "county_vr_number", "reg_date", "vr_source",
    "id_required", "id_met", "status", "reason_code", "inact_date",
    "purge_date", "sboeid", "voter_history",
]

# Appendix A — 2-digit county code -> name.
COUNTY = {
    "01": "ALBANY", "02": "ALLEGANY", "03": "BRONX", "04": "BROOME",
    "05": "CATTARAUGUS", "06": "CAYUGA", "07": "CHAUTAUQUA", "08": "CHEMUNG",
    "09": "CHENANGO", "10": "CLINTON", "11": "COLUMBIA", "12": "CORTLAND",
    "13": "DELAWARE", "14": "DUTCHESS", "15": "ERIE", "16": "ESSEX",
    "17": "FRANKLIN", "18": "FULTON", "19": "GENESEE", "20": "GREENE",
    "21": "HAMILTON", "22": "HERKIMER", "23": "JEFFERSON", "24": "KINGS",
    "25": "LEWIS", "26": "LIVINGSTON", "27": "MADISON", "28": "MONROE",
    "29": "MONTGOMERY", "30": "NASSAU", "31": "NEW YORK", "32": "NIAGARA",
    "33": "ONEIDA", "34": "ONONDAGA", "35": "ONTARIO", "36": "ORANGE",
    "37": "ORLEANS", "38": "OSWEGO", "39": "OTSEGO", "40": "PUTNAM",
    "41": "QUEENS", "42": "RENSSELAER", "43": "RICHMOND", "44": "ROCKLAND",
    "45": "SARATOGA", "46": "SCHENECTADY", "47": "SCHOHARIE", "48": "SCHUYLER",
    "49": "SENECA", "50": "ST.LAWRENCE", "51": "STEUBEN", "52": "SUFFOLK",
    "53": "SULLIVAN", "54": "TIOGA", "55": "TOMPKINS", "56": "ULSTER",
    "57": "WARREN", "58": "WASHINGTON", "59": "WAYNE", "60": "WESTCHESTER",
    "61": "WYOMING", "62": "YATES",
}


def extract_txt() -> None:
    """Extract the inner .txt to local temp (skipped if already present)."""
    if os.path.exists(TMP_TXT) and os.path.getsize(TMP_TXT) > 6_000_000_000:
        print(f"[extract] reusing existing {TMP_TXT}")
        return
    os.makedirs(TMP_DIR, exist_ok=True)
    print(f"[extract] {ZIP_PATH} :: {INNER_TXT} -> {TMP_TXT}")
    with zipfile.ZipFile(ZIP_PATH) as zf, open(TMP_TXT, "wb") as out:
        with zf.open(INNER_TXT) as fh:
            while True:
                chunk = fh.read(1 << 24)  # 16 MB
                if not chunk:
                    break
                out.write(chunk)
    print(f"[extract] done ({os.path.getsize(TMP_TXT) / 1e9:.2f} GB)")


def load() -> None:
    con = duckdb.connect(NY_VRDB)
    cols_sql = ", ".join(f"'{c}': 'VARCHAR'" for c in RAW_COLS)
    txt = TMP_TXT.replace("\\", "/")

    print("[load] staging raw CSV (DuckDB read_csv, all VARCHAR)...")
    con.execute("DROP TABLE IF EXISTS _ny_raw;")
    con.execute(f"""
        CREATE TABLE _ny_raw AS
        SELECT * FROM read_csv(
            '{txt}',
            header = false,
            delim = ',',
            quote = '"',
            escape = '"',
            columns = {{{cols_sql}}},
            ignore_errors = true,
            null_padding = true
        );
    """)
    raw_n = con.execute("SELECT count(*) FROM _ny_raw").fetchone()[0]
    print(f"[load] staged {raw_n:,} rows")

    # County code -> name lookup table (for the typed projection).
    con.execute("DROP TABLE IF EXISTS _ny_county;")
    con.execute("CREATE TABLE _ny_county (code VARCHAR, name VARCHAR);")
    con.executemany(
        "INSERT INTO _ny_county VALUES (?, ?)", list(COUNTY.items())
    )

    print("[load] building typed voters table...")
    con.execute("DROP TABLE IF EXISTS voters;")
    con.execute("""
        CREATE TABLE voters AS
        SELECT
            r.sboeid                                   AS state_voter_id,
            UPPER(TRIM(r.last_name))                   AS last_name,
            UPPER(TRIM(r.first_name))                  AS first_name,
            UPPER(TRIM(r.middle_name))                 AS middle_name,
            NULLIF(TRIM(r.name_suffix), '')            AS name_suffix,
            TRY_STRPTIME(r.dob, '%Y%m%d')::DATE        AS birthdate,
            NULLIF(TRIM(r.gender), '')                 AS gender,
            UPPER(NULLIF(TRIM(r.enrollment), ''))      AS party,
            UPPER(NULLIF(TRIM(r.otherparty), ''))      AS other_party,
            r.county_code                              AS county_code,
            c.name                                     AS county_name,
            NULLIF(TRIM(r.ed), '')                     AS election_district,
            NULLIF(TRIM(r.ld), '')                     AS legislative_district_local,
            UPPER(NULLIF(TRIM(r.town_city), ''))       AS town_city,
            NULLIF(TRIM(r.ward), '')                   AS ward,
            NULLIF(TRIM(r.cd), '')                     AS congressional_district,
            NULLIF(TRIM(r.sd), '')                     AS senate_district,
            NULLIF(TRIM(r.ad), '')                     AS assembly_district,
            UPPER(NULLIF(TRIM(r.r_streetname), ''))    AS reg_street_name,
            NULLIF(TRIM(r.r_add_number), '')           AS reg_street_num,
            UPPER(NULLIF(TRIM(r.r_city), ''))          AS reg_city,
            NULLIF(TRIM(r.r_zip5), '')                 AS reg_zip,
            TRY_STRPTIME(r.reg_date, '%Y%m%d')::DATE   AS registration_date,
            TRY_STRPTIME(r.last_voter_date, '%Y%m%d')::DATE AS last_voted,
            NULLIF(TRIM(r.status), '')                 AS status_code,
            NULLIF(TRIM(r.reason_code), '')            AS reason_code,
            r.voter_history                            AS voter_history
        FROM _ny_raw r
        LEFT JOIN _ny_county c ON r.county_code = c.code;
    """)
    con.execute("DROP TABLE _ny_raw;")
    con.execute("DROP TABLE _ny_county;")

    n = con.execute("SELECT count(*) FROM voters").fetchone()[0]
    print(f"\n[done] voters table: {n:,} rows in {NY_VRDB}\n")

    print("--- party-of-record (ENROLLMENT) breakdown ---")
    for party, cnt in con.execute("""
        SELECT COALESCE(party, '(null)') AS party, count(*) AS n
        FROM voters GROUP BY 1 ORDER BY n DESC
    """).fetchall():
        print(f"  {party:>8} {cnt:>12,}  ({100.0 * cnt / n:5.2f}%)")

    print("\n--- status breakdown ---")
    for status, cnt in con.execute("""
        SELECT COALESCE(status_code, '(null)') AS s, count(*) AS n
        FROM voters GROUP BY 1 ORDER BY n DESC LIMIT 12
    """).fetchall():
        print(f"  {status:>6} {cnt:>12,}")

    print("\n--- coverage of key analysis fields ---")
    cov = con.execute("""
        SELECT
            100.0 * count(birthdate)              / count(*) AS dob_pct,
            100.0 * count(party)                  / count(*) AS party_pct,
            100.0 * count(NULLIF(voter_history,'')) / count(*) AS hist_pct,
            100.0 * count(congressional_district) / count(*) AS cd_pct,
            count(DISTINCT county_name)                      AS counties
        FROM voters
    """).fetchone()
    print(f"  DOB present:            {cov[0]:5.2f}%")
    print(f"  party present:          {cov[1]:5.2f}%")
    print(f"  voter_history present:  {cov[2]:5.2f}%")
    print(f"  CD present:             {cov[3]:5.2f}%")
    print(f"  distinct counties:      {cov[4]}")

    con.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-files", action="store_true",
                    help="keep the extracted .txt in temp afterward")
    args = ap.parse_args()

    if not os.path.exists(ZIP_PATH):
        print(f"ERROR: {ZIP_PATH} not found", file=sys.stderr)
        return 1

    extract_txt()
    load()

    if not args.keep_files and os.path.exists(TMP_TXT):
        os.remove(TMP_TXT)
        print(f"[cleanup] removed {TMP_TXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
