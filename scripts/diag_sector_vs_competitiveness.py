"""Sector x competitiveness: does Wall Street money chase Tossups while
energy/tech funds safe incumbents?

Crosses the employer/sector signatures (Section A/C) against the inflow
competitiveness bands (Section E). Uses the recipient-anchored inflow
(data/fec_inflow.duckdb), classifying each contribution's contributor_employer
into a sector, joined to each WA/NY/TX U.S. House district's competitiveness
band (this project's forecast margin: Tossup<5 / Lean5-10 / Likely10-20 /
Solid>=20), 2022-2026 (post-redistricting).

Output per sector: dollar split across bands, COMPETITIVE share
(Tossup+Lean)/total, and out-of-state share — to see which sectors target the
marginal race vs pile into safe seats, and which travel farthest.

Sector classification is keyword-on-employer (noisy, free-text); an
'unclassified' bucket carries the residue and its size is reported.
"""
import duckdb

from cross_state_common import competitiveness_bands, region_codes, write_json

# Keyword -> sector. Order matters (first match wins via the CASE below).
SECTORS = {
    # NOTE: finance is matched BEFORE tech, so finance-side names that contain a tech
    # keyword (e.g. "RENAISSANCE TECHNOLOGIES") are correctly caught here first.
    "finance": ["GOLDMAN", "BLACKSTONE", "BLACKROCK", "MORGAN STANLEY", "JPMORGAN", "JP MORGAN",
                "CITADEL", "JANE STREET", "POINT72", "BRIDGEWATER", " KKR", "CARLYLE", "APOLLO",
                "BAIN CAPITAL", "HEDGE", "PRIVATE EQUITY", "CAPITAL MANAGEMENT", "CAPITAL PARTNERS",
                "INVESTMENT", "SECURITIES", "BANK", "WELLS FARGO", "CITIGROUP", "CITIBANK",
                "CREDIT SUISSE", "UBS", "DEUTSCHE", "BARCLAYS", "FIDELITY", "VANGUARD", "SOROS FUND",
                "JEFFERIES", "LAZARD", "EVERCORE", "CASH ", "FINANCIAL", "ASSET MANAGEMENT", "VENTURE",
                # named hedge funds / asset managers / VC surfaced as unclassified blind spots
                "LONE PINE", "BAUPOST", "SESSA CAPITAL", "TWO SIGMA", "MILLENNIUM MANAGEMENT",
                "ELLIOTT MANAGEMENT", "TIGER GLOBAL", "COATUE", "VIKING GLOBAL", "D.E. SHAW",
                "DE SHAW", "RENAISSANCE TECHNOLOGIES", "SUSQUEHANNA", "PIMCO", "T. ROWE", "T ROWE",
                "STATE STREET", "PAULSON", "ANDREESSEN", "SEQUOIA CAPITAL", "GREYLOCK",
                "KLEINER PERKINS", "GENERAL ATLANTIC", "SILVER LAKE", "WARBURG PINCUS"],
    "tech": ["MICROSOFT", "AMAZON", "GOOGLE", "ALPHABET", "META PLATFORMS", "FACEBOOK", "APPLE INC",
             "APPLE COMPUTER", "ORACLE", "SALESFORCE", "NVIDIA", "INTEL", "ADOBE", "NETFLIX",
             "SOFTWARE", "TECHNOLOGIES", "TECHNOLOGY", "DATA", "AMAZON WEB", "AWS", "TESLA",
             "SEMICONDUCTOR", "CISCO", "IBM", "DELL", "HEWLETT", "QUALCOMM", "UBER", "AIRBNB",
             "STRIPE", "PALANTIR", "ZILLOW", "EXPEDIA", "ZUMIEZ",
             # AI / newer tech surfaced as unclassified blind spots
             "ANTHROPIC", "OPENAI", "DATABRICKS", "SNOWFLAKE", "COINBASE", "DOORDASH",
             "INSTACART", "DROPBOX", "PINTEREST", "SNAP INC", "SPACEX"],
    "energy": ["EXXON", "CHEVRON", "VALERO", "CONOCO", "PHILLIPS 66", "MARATHON", "OCCIDENTAL",
               "HALLIBURTON", "SCHLUMBERGER", "BAKER HUGHES", "PETROLEUM", "OIL", "GAS COMPANY",
               "NATURAL GAS", "ENERGY", "PIPELINE", "DRILLING", "REFINING", "KOCH", "DEVON",
               "PIONEER NATURAL", "ENTERPRISE PRODUCTS", "KINDER MORGAN", "COAL", "EXPLORATION"],
    "law": ["LAW FIRM", "LAW OFFICE", "LLP", "ATTORNEY", "LAW GROUP", "& ASSOCIATES",
            "LEGAL", "COUNSEL", " LAW", "LAW,",
            # named BigLaw firms surfaced as unclassified blind spots
            "PAUL WEISS", "AKIN GUMP", "SKADDEN", "KIRKLAND & ELLIS", "KIRKLAND AND ELLIS",
            "LATHAM & WATKINS", "SULLIVAN & CROMWELL", "DAVIS POLK", "SIMPSON THACHER",
            "WACHTELL", "CRAVATH", "GIBSON DUNN", "SIDLEY", "JONES DAY", "WILMERHALE",
            "WILMER CUTLER", "HOGAN LOVELLS", "ARNOLD & PORTER", "COVINGTON & BURLING",
            "DEBEVOISE", "WEIL GOTSHAL", "ROPES & GRAY", "MORGAN LEWIS", "PERKINS COIE",
            "K&L GATES", "MAYER BROWN", "WILLKIE FARR", "FRIED FRANK", "CLEARY GOTTLIEB",
            "QUINN EMANUEL", "GREENBERG TRAURIG", "DLA PIPER", "HOLLAND & KNIGHT"],
    "healthcare": ["HOSPITAL", "MEDICAL", "HEALTH", "PHARMA", "CLINIC", "PHYSICIAN", "PFIZER",
                   "MERCK", "KAISER", "UNITEDHEALTH", "BIOTECH", "GENENTECH", "AMGEN"],
    "realestate": ["REAL ESTATE", "REALTY", "REALTOR", "PROPERTIES", "DEVELOPMENT GROUP",
                   "CONSTRUCTION", "HOMEBUILD", "REAL-ESTATE"],
    "academia/public": ["UNIVERSITY", "COLLEGE", "SCHOOL DISTRICT", "STATE OF", "CITY OF",
                        "COUNTY OF", "PUBLIC SCHOOL", "GOVERNMENT", "FEDERAL"],
}


def sector_sql_column():
    """Build a CASE expression mapping UPPER(employer) -> sector."""
    parts = ["CASE",
             "WHEN e IN ('RETIRED','NOT EMPLOYED','NONE','N/A','UNEMPLOYED','SELF',"
             "'SELF-EMPLOYED','SELF EMPLOYED','HOMEMAKER','INFORMATION REQUESTED','') "
             "OR e IS NULL THEN 'non-working/none'"]
    for sector, kws in SECTORS.items():
        likes = " OR ".join(f"e LIKE '%{kw}%'" for kw in kws)
        parts.append(f"WHEN {likes} THEN '{sector}'")
    parts.append("ELSE 'unclassified' END")
    return "\n".join(parts)


def main():
    comp = competitiveness_bands()  # {(state, cd): (margin_abs, band)}
    sector_col = sector_sql_column()
    ic = duckdb.connect("data/fec_inflow.duckdb", read_only=True)
    rows = ic.execute(f"""
        WITH base AS (
            SELECT recipient_state st,
                   'cd' || LPAD(CAST(TRY_CAST(recipient_district AS INTEGER) AS VARCHAR), 2, '0') AS cd,
                   UPPER(TRIM(COALESCE(contributor_employer,''))) e,
                   contribution_amount amt,
                   CASE WHEN contributor_state <> recipient_state THEN 1 ELSE 0 END oos
            FROM inflow_contributions
            WHERE recipient_office='H' AND election_cycle >= 2022 AND contribution_amount > 0
              AND TRY_CAST(recipient_district AS INTEGER) IS NOT NULL
        )
        SELECT st, cd, ({sector_col}) AS sector,
               SUM(amt) tot, SUM(amt*oos) oos
        FROM base GROUP BY 1,2,3
    """).fetchall()
    ic.close()

    # sector -> band -> {tot, oos}
    sectors = {}
    grand = 0.0
    for st, cd, sector, tot, oos in rows:
        cinfo = comp.get((st, cd))
        if not cinfo:
            continue
        b = cinfo[1]
        tot = float(tot); oos = float(oos)
        grand += tot
        s = sectors.setdefault(sector, {bn: {"tot": 0.0, "oos": 0.0} for bn in
                                        ["Tossup", "Lean", "Likely", "Solid"]})
        s[b]["tot"] += tot
        s[b]["oos"] += oos

    order = ["finance", "tech", "energy", "law", "healthcare", "realestate",
             "academia/public", "non-working/none", "unclassified"]
    print(f"Sector x competitiveness — {'/'.join(region_codes())} U.S. House inflow, 2022-2026")
    print(f"(grand total matched to a band: ${grand/1e6:,.0f}M)\n")
    hdr = (f"{'sector':18} {'$M':>8} {'%of$':>6} | {'Tossup':>8} {'Lean':>8} {'Likely':>8} "
           f"{'Solid':>8} | {'COMPETv':>8} {'OOS%':>6}")
    print(hdr); print("-" * len(hdr))
    out = {}
    for sector in order:
        s = sectors.get(sector)
        if not s:
            continue
        tot = sum(b["tot"] for b in s.values())
        if tot <= 0:
            continue
        comp_share = (s["Tossup"]["tot"] + s["Lean"]["tot"]) / tot * 100
        oos_share = sum(b["oos"] for b in s.values()) / tot * 100
        shares = {bn: s[bn]["tot"] / tot * 100 for bn in s}
        print(f"{sector:18} {tot/1e6:7.1f} {tot/grand*100:5.1f}% | "
              f"{shares['Tossup']:7.1f}% {shares['Lean']:7.1f}% {shares['Likely']:7.1f}% "
              f"{shares['Solid']:7.1f}% | {comp_share:7.1f}% {oos_share:5.1f}%")
        out[sector] = {"total": tot, "pct_of_all": tot / grand * 100,
                       "band_share": shares, "competitive_share": comp_share,
                       "oos_share": oos_share}

    # headline contrasts
    print("\nCOMPETITIVE share (Tossup+Lean) by sector, ranked:")
    rank = sorted(((sec, d["competitive_share"]) for sec, d in out.items()
                   if sec not in ("non-working/none", "unclassified")),
                  key=lambda x: x[1], reverse=True)
    for sec, cs in rank:
        print(f"   {sec:18} {cs:5.1f}%")
    allcomp = (sum(sectors[s]["Tossup"]["tot"] + sectors[s]["Lean"]["tot"] for s in sectors)
               / grand * 100)
    print(f"   {'[ALL sectors]':18} {allcomp:5.1f}%   <- baseline")
    path = write_json("sector_competitiveness.json", out)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
