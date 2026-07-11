"""WA adult (18+) age composition from the Census ACS 5-year, for the
"who is counted" comparison in docs/who-decides-washington.md.

Source: U.S. Census Bureau, American Community Survey 5-year, table B01001
(Sex by Age), state = Washington (FIPS 53). We sum the male + female age
brackets into the paper's four cohorts (18-29 / 30-44 / 45-64 / 65+) and
interpolate an adult-resident median age from the brackets. Also pulls table
B29001 (Citizen, Voting-Age Population by Age) for the CVAP row — the
eligible-electorate benchmark that excludes non-citizens.

Needs a free Census API key in CENSUS_API_KEY (repo .env) — sign up at
https://api.census.gov/data/key_signup.html . Run from the project root:

    python scripts/acs_wa_adult_age.py            # default vintage 2024 (2020-2024 5-year)
    python scripts/acs_wa_adult_age.py 2023       # 2019-2023 5-year
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# B01001 age brackets -> paper cohorts (male codes; female = +24).
MALE = {"18-29": [7, 8, 9, 10, 11], "30-44": [12, 13, 14],
        "45-64": [15, 16, 17, 18, 19], "65+": [20, 21, 22, 23, 24, 25]}
FEMALE = {k: [i + 24 for i in v] for k, v in MALE.items()}
COHORTS = ["18-29", "30-44", "45-64", "65+"]
# nominal bracket spans for the median interpolation (18..90 cap)
SPAN = {"18-29": (18, 30), "30-44": (30, 45), "45-64": (45, 65), "65+": (65, 90)}


def load_key():
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        return key.strip()
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*CENSUS_API_KEY\s*=\s*(.+)", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("CENSUS_API_KEY not set (env or .env)")


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    key = load_key()
    variables = [f"B01001_{i:03d}E" for grp in (MALE, FEMALE) for k in grp for i in grp[k]]
    url = (f"https://api.census.gov/data/{year}/acs/acs5?get="
           + ",".join(variables) + f"&for=state:53&key={key}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    val = {h: int(v) for h, v in zip(data[0], data[1])
           if v is not None and h.startswith("B01001")}
    counts = {k: sum(val[f"B01001_{i:03d}E"] for i in MALE[k])
                 + sum(val[f"B01001_{i:03d}E"] for i in FEMALE[k]) for k in COHORTS}
    total = sum(counts.values())

    print(f"WA adult (18+) residents — ACS {year-4}-{year} 5-year (Census B01001):")
    for k in COHORTS:
        print(f"  {k:6} {counts[k]:>10,}  {counts[k]/total*100:5.1f}%")
    print(f"  total adults {total:,}")

    # linear-interpolated median age from the brackets
    half, cum = total / 2, 0
    for k in COHORTS:
        if cum + counts[k] >= half:
            lo, hi = SPAN[k]
            median = lo + (half - cum) / counts[k] * (hi - lo)
            print(f"  interpolated adult-resident median age ~ {median:.0f} (in {k})")
            break
        cum += counts[k]

    # Citizen voting-age population by age — ACS table B29001 (the eligible benchmark)
    cvap_vars = [f"B29001_{i:03d}E" for i in (1, 2, 3, 4, 5)]
    url2 = (f"https://api.census.gov/data/{year}/acs/acs5?get="
            + ",".join(cvap_vars) + f"&for=state:53&key={key}")
    with urllib.request.urlopen(url2, timeout=60) as resp:
        d2 = json.load(resp)
    cv = {h: int(v) for h, v in zip(d2[0], d2[1]) if h.startswith("B29001")}
    ct = cv["B29001_001E"]
    cvap = dict(zip(COHORTS, (cv["B29001_002E"], cv["B29001_003E"],
                             cv["B29001_004E"], cv["B29001_005E"])))
    print(f"\nWA citizen voting-age population (CVAP) — ACS {year-4}-{year} 5-year (B29001):")
    for k in COHORTS:
        print(f"  {k:6} {cvap[k]:>10,}  {cvap[k]/ct*100:5.1f}%")
    print(f"  total CVAP {ct:,}")
    half2, cum2 = ct / 2, 0
    for k in COHORTS:
        if cum2 + cvap[k] >= half2:
            lo, hi = SPAN[k]
            print(f"  interpolated CVAP median age ~ {lo + (half2-cum2)/cvap[k]*(hi-lo):.0f} (in {k})")
            break
        cum2 += cvap[k]


if __name__ == "__main__":
    main()
