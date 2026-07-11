"""Donor-side match-ceiling pre-test: of distinct donors, what fraction have a
UNIQUE match key (so they COULD be 1:1 matched to a voter)? Upper bound on the
voter<->donor match rate, computed without any voter file.

Key A = (last, first-initial, zip5)  -- the WA matcher's documented key.
Key B = (last, first-word, zip5)      -- a fuller key (uses the whole first name).
"""
import duckdb

STATES = [
    ("WA-FEC", "data/wa_statewide.duckdb", "regexp_matches(COALESCE(fec_candidate_id,''),'^[CPHS][0-9]') AND contributor_state='WA'"),
    ("NY",     "data/ny_statewide.duckdb", "contributor_state='NY'"),
    ("TX",     "data/tx_statewide.duckdb", "contributor_state='TX'"),
    ("ID",     "data/id_statewide.duckdb", "1=1"),
]

print(f"{'donors':>10} {'keyA-uniq':>10} {'keyB-uniq':>10}  state   (keyA=last+initial+zip5, keyB=last+firstword+zip5)")
for name, f, where in STATES:
    c = duckdb.connect(f, read_only=True)
    # distinct donors (full name + zip5), with parsed last / first-initial / first-word
    c.execute(f"""
        CREATE TEMP TABLE d AS
        SELECT DISTINCT UPPER(TRIM(contributor_name)) nm, LEFT(COALESCE(contributor_zip,''),5) z
        FROM individual_contributions
        WHERE {where} AND contribution_amount > 0 AND contributor_name IS NOT NULL
              AND contributor_name LIKE '%,%'          -- comma 'LAST, FIRST' format
    """)
    c.execute("""
        CREATE TEMP TABLE k AS
        SELECT nm, z,
          UPPER(TRIM(SPLIT_PART(nm, ',', 1))) || '|' ||
            SUBSTR(UPPER(TRIM(SPLIT_PART(nm, ',', 2))), 1, 1) || '|' || z AS keyA,
          UPPER(TRIM(SPLIT_PART(nm, ',', 1))) || '|' ||
            SPLIT_PART(UPPER(TRIM(SPLIT_PART(nm, ',', 2))), ' ', 1) || '|' || z AS keyB
        FROM d
    """)
    tot = c.execute("SELECT COUNT(*) FROM k").fetchone()[0]
    uniqA = c.execute("""WITH g AS (SELECT keyA, COUNT(*) c FROM k GROUP BY keyA)
                         SELECT SUM(CASE WHEN g.c=1 THEN 1 ELSE 0 END) FROM k JOIN g USING(keyA)""").fetchone()[0]
    uniqB = c.execute("""WITH g AS (SELECT keyB, COUNT(*) c FROM k GROUP BY keyB)
                         SELECT SUM(CASE WHEN g.c=1 THEN 1 ELSE 0 END) FROM k JOIN g USING(keyB)""").fetchone()[0]
    c.execute("DROP TABLE k"); c.execute("DROP TABLE d")
    c.close()
    a = uniqA / tot * 100 if tot else 0
    b = uniqB / tot * 100 if tot else 0
    print(f"{tot:>10,} {a:>9.1f}% {b:>9.1f}%  {name}")
