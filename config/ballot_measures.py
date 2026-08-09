"""Ballot measure metadata and issue categorization.

Maps WA State ballot measures from 2016-2024 to issue dimensions for
precinct-level issue profile scoring.  The ``BALLOT_MEASURES`` catalog
provides the classification that the analysis module needs, since the
raw SOS CSV race-name text is inconsistent across election years.

Each measure records which vote direction ("Yes"/"No"/"Approved"/
"Rejected") aligns with the progressive position, enabling the system
to compute a progressive/conservative score per precinct per issue
category.

Advisory Votes are excluded — they use reversed semantics
("Repealed"/"Maintained") and are advisory-only, providing weaker
signal.  They can be added in a future iteration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BallotMeasure:
    """Metadata for a single ballot measure."""

    year: int
    measure_id: str  # e.g. "I-2066", "R-90"
    race_name_pattern: str  # substring to match in the SOS Race column
    short_name: str  # human-readable label
    issue_category: str  # one of ISSUE_CATEGORIES
    progressive_position: str  # "Yes", "No", "Approved", or "Rejected"
    description: str  # brief description


# Issue categories for clustering.  Each ballot measure maps to exactly
# one of these.
ISSUE_CATEGORIES: list[str] = [
    "tax_economic",
    "labor_workers",
    "guns_public_safety",
    "environment",
    "social_services",
    "government_elections",
    "education",
    "law_enforcement",
]

# Human-friendly labels for display in reports.
ISSUE_CATEGORY_LABELS: dict[str, str] = {
    "tax_economic": "Tax & Economic",
    "labor_workers": "Labor & Workers",
    "guns_public_safety": "Guns & Public Safety",
    "environment": "Environment",
    "social_services": "Social Services",
    "government_elections": "Government & Elections",
    "education": "Education",
    "law_enforcement": "Law Enforcement",
}


BALLOT_MEASURES: list[BallotMeasure] = [
    # ---- 2024 ----
    BallotMeasure(
        year=2024,
        measure_id="I-2066",
        race_name_pattern="Initiative Measure No. 2066",
        short_name="Natural Gas Mandate",
        issue_category="environment",
        progressive_position="No",
        description="Require utilities to provide natural gas; repeal "
        "parts of climate legislation",
    ),
    BallotMeasure(
        year=2024,
        measure_id="I-2109",
        race_name_pattern="Initiative Measure No. 2109",
        short_name="Capital Gains Tax Repeal",
        issue_category="tax_economic",
        progressive_position="No",
        description="Repeal the state capital gains excise tax",
    ),
    BallotMeasure(
        year=2024,
        measure_id="I-2117",
        race_name_pattern="Initiative Measure No. 2117",
        short_name="Carbon Pricing Repeal",
        issue_category="environment",
        progressive_position="No",
        description="Repeal the state carbon pricing (cap-and-invest) "
        "program",
    ),
    BallotMeasure(
        year=2024,
        measure_id="I-2124",
        race_name_pattern="Initiative Measure No. 2124",
        short_name="Long-Term Care Opt-Out",
        issue_category="social_services",
        progressive_position="No",
        description="Allow opt-out of the state long-term care "
        "insurance program (WA Cares)",
    ),
    # ---- 2020 ----
    BallotMeasure(
        year=2020,
        measure_id="R-90",
        race_name_pattern="Referendum Measure No. 90",
        short_name="Sex Education",
        issue_category="education",
        progressive_position="Approved",
        description="Approve comprehensive sex education in public "
        "schools (K-12)",
    ),
    # ---- 2018 ----
    BallotMeasure(
        year=2018,
        measure_id="I-1631",
        race_name_pattern="1631",
        short_name="Carbon Fee",
        issue_category="environment",
        progressive_position="Yes",
        description="Carbon emissions fee on large emitters to fund "
        "clean energy",
    ),
    BallotMeasure(
        year=2018,
        measure_id="I-1634",
        race_name_pattern="1634",
        short_name="Grocery Tax Ban",
        issue_category="tax_economic",
        progressive_position="No",
        description="Prohibit local governments from taxing groceries",
    ),
    BallotMeasure(
        year=2018,
        measure_id="I-1639",
        race_name_pattern="1639",
        short_name="Firearms Safety",
        issue_category="guns_public_safety",
        progressive_position="Yes",
        description="Enhanced background checks, training requirements, "
        "age limits for semi-automatic rifle purchases",
    ),
    BallotMeasure(
        year=2018,
        measure_id="I-940",
        race_name_pattern="940",
        short_name="Police Use of Force",
        issue_category="law_enforcement",
        progressive_position="Yes",
        description="De-escalation training for officers, independent "
        "investigations of deadly force",
    ),
    # ---- 2016 ----
    BallotMeasure(
        year=2016,
        measure_id="I-1433",
        race_name_pattern="1433",
        short_name="Minimum Wage & Sick Leave",
        issue_category="labor_workers",
        progressive_position="Yes",
        description="Raise minimum wage to $13.50, mandatory paid sick "
        "leave",
    ),
    BallotMeasure(
        year=2016,
        measure_id="I-1464",
        race_name_pattern="1464",
        short_name="Campaign Finance Reform",
        issue_category="government_elections",
        progressive_position="Yes",
        description="Public campaign financing via democracy credits",
    ),
    BallotMeasure(
        year=2016,
        measure_id="I-1491",
        race_name_pattern="1491",
        short_name="Extreme Risk Protection Orders",
        issue_category="guns_public_safety",
        progressive_position="Yes",
        description="Allow courts to temporarily remove firearms from "
        "individuals posing a risk",
    ),
    BallotMeasure(
        year=2016,
        measure_id="I-1501",
        race_name_pattern="1501",
        short_name="Senior Protection",
        issue_category="social_services",
        progressive_position="Yes",
        description="Protect seniors and vulnerable individuals from "
        "identity theft and fraud",
    ),
    BallotMeasure(
        year=2016,
        measure_id="I-732",
        race_name_pattern="732",
        short_name="Carbon Tax",
        issue_category="tax_economic",
        progressive_position="Yes",
        description="Revenue-neutral carbon tax on fossil fuels",
    ),
]


def get_measure_by_race_name(race_name: str) -> BallotMeasure | None:
    """Find the BallotMeasure whose ``race_name_pattern`` matches *race_name*.

    Returns ``None`` if no match is found.
    """
    for measure in BALLOT_MEASURES:
        if measure.race_name_pattern in race_name:
            return measure
    return None


def get_measures_by_category(category: str) -> list[BallotMeasure]:
    """Return all ballot measures in the given *category*."""
    return [m for m in BALLOT_MEASURES if m.issue_category == category]
