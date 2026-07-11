"""Voter<->donor match-precision VALIDATION sampler.

The 382K voter<->donor match (voter_donor_affiliation) underlies every §F donor
finding, yet has no ground-truth precision check. This pulls a random,
seed-fixed sample of matched voters, reconstructs the donor record(s) that the
matcher's key would have linked, and writes a CSV with the voter side next to the
donor side plus a blank `is_same_person` column for HAND adjudication. Run it,
eyeball the CSV, fill Y/N/?, and report the precision.

It also prints two structural precision indicators that need no hand review:
  - full-first-name agreement rate (matches where the donor's full first name, not
    just the initial, equals the voter's) — higher = stronger;
  - share of matched voters whose (last, first-initial, zip5) key collides with a
    DONOR-side namesake (a distinct contributor sharing the key) — the population at
    risk of a false merge.

PII: the CSV contains voter + donor names, so it is written OUTSIDE the repo
written to data/validation/ (gitignored) and must not be committed.
"""
import csv
import os
import duckdb

VRDB = "data/wa_vrdb.duckdb"
N = 150
SEED = 42
# data/ is gitignored, so the PII sample is durable-with-the-project but NEVER committed.
OUT = "data/validation/match_validation_sample.csv"


def main():
    c = duckdb.connect("data/wa_statewide.duckdb", read_only=True)
    c.execute(f"ATTACH '{VRDB}' AS vrdb (READ_ONLY)")

    # Sampled matched voters with VRDB identity + parsed match key.
    c.execute(f"""
        CREATE TEMP TABLE samp AS
        SELECT a.state_voter_id, a.donation_count, a.total_donated, a.match_quality,
               a.donor_party,
               v.first_name, v.last_name, v.reg_zip, v.reg_city,
               UPPER(TRIM(v.last_name)) AS lk,
               UPPER(SUBSTR(TRIM(v.first_name),1,1)) AS fi,
               SPLIT_PART(UPPER(TRIM(v.first_name)),' ',1) AS ff,
               SUBSTR(v.reg_zip,1,5) AS z5
        FROM voter_donor_affiliation a
        JOIN vrdb.voters v USING (state_voter_id)
        WHERE v.first_name IS NOT NULL AND v.last_name IS NOT NULL AND v.reg_zip IS NOT NULL
        ORDER BY md5(a.state_voter_id || '{SEED}') LIMIT {N}
    """)

    # Reconstruct the donor side: contributions sharing (last, first-initial, zip5).
    # WA individual_contributions mixes FEC ("LAST, FIRST MID") and PDC
    # ("Last First Mid", no comma); parse both. Match on zip5 (the dominant tiers).
    rows = c.execute("""
        WITH ic AS (
            SELECT
              CASE WHEN contributor_name LIKE '%,%'
                   THEN UPPER(TRIM(SPLIT_PART(contributor_name,',',1)))
                   ELSE UPPER(SPLIT_PART(TRIM(contributor_name),' ',1)) END lk,
              CASE WHEN contributor_name LIKE '%,%'
                   THEN SPLIT_PART(UPPER(TRIM(SPLIT_PART(contributor_name,',',2))),' ',1)
                   ELSE UPPER(SPLIT_PART(TRIM(contributor_name),' ',2)) END ffull,
              LEFT(contributor_zip,5) z5,
              contributor_name, contribution_amount
            FROM individual_contributions
            WHERE contribution_amount > 0 AND contributor_name IS NOT NULL
              AND UPPER(contributor_name) <> 'SMALL CONTRIBUTIONS')
        SELECT s.state_voter_id, s.first_name, s.last_name, s.reg_zip, s.reg_city,
               s.donation_count, s.total_donated, s.match_quality, s.donor_party,
               STRING_AGG(DISTINCT ic.contributor_name, ' | ') donor_names,
               COUNT(ic.contributor_name) ic_rows, ROUND(SUM(ic.contribution_amount),0) ic_total,
               MAX(CASE WHEN ic.ffull = s.ff THEN 1 ELSE 0 END) full_first_agree,
               COUNT(DISTINCT ic.ffull) distinct_first_names
        FROM samp s
        LEFT JOIN ic ON ic.lk = s.lk AND ic.z5 = s.z5 AND LEFT(ic.ffull,1) = s.fi
        GROUP BY 1,2,3,4,5,6,7,8,9
    """).fetchall()
    c.close()

    cols = ["state_voter_id", "voter_first", "voter_last", "voter_zip", "voter_city",
            "donation_count", "total_donated", "match_quality", "donor_party",
            "donor_names_matching_key", "donor_contrib_rows", "donor_total",
            "full_first_name_agrees", "distinct_donor_first_names",
            "is_same_person(Y/N/?)", "notes"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(cols)
        for r in rows:
            w.writerow(list(r) + ["", ""])

    n = len(rows)
    full_agree = sum(1 for r in rows if r[12] == 1)
    multi_first = sum(1 for r in rows if (r[13] or 0) > 1)
    no_donor = sum(1 for r in rows if (r[10] or 0) == 0)
    print(f"wrote {n}-row validation sample -> {OUT}\n")
    print("Structural precision indicators (no hand review needed):")
    print(f"  full first-name agreement (donor full first == voter full first): "
          f"{full_agree}/{n} = {full_agree/n*100:.0f}%")
    print(f"  key collides with >1 distinct donor first-name (false-merge RISK): "
          f"{multi_first}/{n} = {multi_first/n*100:.0f}%")
    print(f"  sampled voters with no key-matching contribution re-found: {no_donor}/{n} "
          f"(expected small; PDC/parsing edge cases)")
    print("\nNEXT: open the CSV, fill is_same_person (Y/N/?), then precision = Y / (Y+N).")


if __name__ == "__main__":
    main()
