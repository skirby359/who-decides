"""Hardcoded national political environment data for structural forecasting.

Sources: FiveThirtyEight generic ballot averages, Gallup presidential approval,
BLS economic data, Cook Political Report PVI calculations.

District-specific historical performance is stored in district profiles
(see ``config.districts``), NOT in this module.  The ``wa05_dem_two_party_pct``
field is retained for backward compatibility with existing databases but is
deprecated in favor of ``district_historical_performance`` table.
"""

from dataclasses import dataclass, field


@dataclass
class NationalCycle:
    year: int
    election_type: str  # "presidential" or "midterm"
    # Generic congressional ballot final margin (D - R), percentage points
    generic_ballot_margin: float
    # Presidential approval on election day (Gallup)
    pres_approval: float
    # President's party
    president_party: str
    # Economic indicators (Q3 of election year)
    gdp_growth: float  # annualized real GDP growth %
    unemployment: float  # unemployment rate %
    cpi_inflation: float  # year-over-year CPI %
    consumer_sentiment: float  # U of Michigan index
    # National House popular vote margin (D - R)
    national_house_margin: float
    # Wave classification
    wave_type: str  # "blue_wave", "red_wave", "neutral"
    # DEPRECATED: District-specific results now live in district profiles.
    # Retained only for backward compat with existing DBs.
    wa05_dem_two_party_pct: float = 0.0
    # Whether this cycle's data is projected/estimated (vs actual results)
    is_projected: bool = False


# Historical data for modeling
NATIONAL_CYCLES = [
    NationalCycle(
        year=2016,
        election_type="presidential",
        generic_ballot_margin=1.1,
        pres_approval=53.0,
        president_party="Democratic",
        gdp_growth=1.9,
        unemployment=4.9,
        cpi_inflation=1.7,
        consumer_sentiment=87.2,
        national_house_margin=1.1,
        wave_type="neutral",
        wa05_dem_two_party_pct=38.6,
    ),
    NationalCycle(
        year=2018,
        election_type="midterm",
        generic_ballot_margin=8.6,
        pres_approval=40.0,
        president_party="Republican",
        gdp_growth=3.0,
        unemployment=3.7,
        cpi_inflation=2.2,
        consumer_sentiment=98.3,
        national_house_margin=8.6,
        wave_type="blue_wave",
        wa05_dem_two_party_pct=45.2,
    ),
    NationalCycle(
        year=2020,
        election_type="presidential",
        generic_ballot_margin=3.1,
        pres_approval=46.0,
        president_party="Republican",
        gdp_growth=-2.8,
        unemployment=6.7,
        cpi_inflation=1.4,
        consumer_sentiment=76.9,
        national_house_margin=3.1,
        wave_type="neutral",
        wa05_dem_two_party_pct=42.0,
    ),
    NationalCycle(
        year=2022,
        election_type="midterm",
        generic_ballot_margin=2.4,
        pres_approval=41.0,
        president_party="Democratic",
        gdp_growth=-0.6,
        unemployment=3.6,
        cpi_inflation=7.7,
        consumer_sentiment=56.8,
        national_house_margin=2.4,
        wave_type="neutral",
        wa05_dem_two_party_pct=47.6,
    ),
    NationalCycle(
        year=2024,
        election_type="presidential",
        generic_ballot_margin=0.3,
        pres_approval=38.0,
        president_party="Democratic",
        gdp_growth=2.8,
        unemployment=4.1,
        cpi_inflation=2.6,
        consumer_sentiment=73.0,
        national_house_margin=-1.0,
        wave_type="red_wave",
        wa05_dem_two_party_pct=43.8,
    ),
    # --- 2026 PROJECTED (election not yet held) ---
    # Generic-ballot re-triangulation as of June 8, 2026 (back to D+6.0; the
    # June-6 trim to D+5.5 reacted to a brief softening that has since reversed):
    #   - RealClearPolling average:         D+6.8  (48.3/41.5; up from 5.4 Jun 6)
    #   - USPollingData:                    D+6.0-7.0
    #   - Race to the WH average:           ~D+6.5 (48.1/41.1)
    #   - Silver Bulletin:                  D+5.3  (RV-adjusted, stable)
    #   - Morning Consult tracking:         D+3.0  (RV, runs low)
    # Trimmed-blend consensus ~D+6.0 (range D+3-7). Set to D+6.0.
    #
    # RE-REVIEWED June 17, 2026 (held at D+6.0): the early-June dip fully
    # reversed. RealClearPolling D+6.6 (48.9/42.3, "largest of cycle"); Silver
    # Bulletin D+6.6 (recovered from 5.3); Race to the WH ~D+6.5; FiftyPlusOne
    # D+6.0; Morning Consult D+4.0 (RV, runs low). Trimmed blend ~D+6.4, full
    # mean ~D+6.0. Within noise of the existing D+6.0 and below the threshold to
    # chase this far out (see cadence below) — NOT changed. Re-lock on this date
    # captures the open-seat→incumbent attenuation fix at a constant wave.
    #
    # RE-TRIANGULATED July 19, 2026 (D+6.0 -> D+5.5): the mid-June peak has
    # softened over six weeks, consistently across every aggregator — this is
    # the monthly-cadence review, not a 2-day move:
    #   - RealClearPolling average:         D+4.7  (48.6/43.9, 6/24-7/14 window;
    #                                       down from 6.6 at the June 17 review)
    #   - Silver Bulletin:                  D+6.1  (Jul 17; down from 7.1 peak
    #                                       Jun 1 / 6.6 Jun 17; Silver flags the
    #                                       reversion — "not massive, not nothing")
    #   - FiftyPlusOne:                     D+5.3  (49.2/43.9, Jul 18; was 6.0)
    #   - USPollingData:                    D+6.2
    #   - Morning Consult tracking:         D+3.0  (RV, runs low)
    # Recent individual polls cluster D+2 to D+6 (RCP table). Trimmed blend
    # (drop 6.2 high / 3.0 low) ~D+5.4, full mean ~D+5.1. Direction is uniform
    # and sustained, so set to D+5.5 (half-point convention). Matches the
    # wave-trajectory research lean that a summer midterm lead more often
    # softens than grows. national_house_margin kept equal to
    # generic_ballot_margin for the projected cycle, as before.
    #
    # RE-TRIANGULATION CADENCE: this value is a projection AND the dominant
    # driver of swing-seat forecasts, but it is dollar-for-dollar sampling noise
    # this far out — a 5.5<->6.0 swing between June 6 and June 8 is well inside
    # the aggregator spread. Do NOT chase 2-day moves. Recommended cadence:
    # monthly through August, biweekly in September, weekly in October, every
    # 2-3 days in the final fortnight (and after any major shock). See
    # METHODOLOGY.md §5. NOTE: pres_approval=44.0 below is now stale vs ~38.6
    # current (Trump) — left unchanged pending a check of whether it feeds the
    # forecast; the wave is driven by generic_ballot_margin, not approval.
    # After editing this file, re-push to the DB with:
    #   python main.py load --national --force
    # (analysis reads from national_environment, not from this dataclass.)
    NationalCycle(
        year=2026,
        election_type="midterm",
        generic_ballot_margin=5.5,
        pres_approval=44.0,
        president_party="Republican",
        gdp_growth=2.0,
        unemployment=4.3,
        cpi_inflation=2.5,
        consumer_sentiment=65.0,
        national_house_margin=5.5,
        wave_type="blue_wave",
        wa05_dem_two_party_pct=0.0,
        is_projected=True,
    ),
]


# Current model version tag. Bump when MODEL_PARAMS / forecast logic changes so
# recorded predictions (forecast_predictions table) and reports carry a citable
# version. History lives in METHODOLOGY.md.
MODEL_VERSION = "v-jun17"

# Political science model parameters (generic, not district-specific)
MODEL_PARAMS = {
    # Incumbency advantage (percentage points). 3.5 selected via May 14
    # grid search — see METHODOLOGY § 6 calibration history. Modern PolSci
    # estimates House incumbency advantage at 1-4 pts depending on era;
    # 3.5 sits at the higher end and lifts directional accuracy without
    # hurting bias under honest grading.
    "incumbency_advantage": 3.5,
    # Republican-incumbent penalty (dem-pct, applied as a *decrease* to
    # predicted_dem_pct). Decoupled from the shared `incumbency_advantage`
    # so R can be recalibrated without touching the D-incumbent fallback
    # (D incumbents normally use the personal-vote carryover; the flat term
    # only fires for the no-prior / post-redistricting fallback).
    # Recalibrated 3.5 -> 4.0 (v-jun4d-model). After Track 7 zeroed the
    # D-incumbent bias, R incumbents still over-predicted the Democrat
    # (+1.47 margin). R keeps the FLAT term (the prior D share is a changing
    # challenger, so a personal-vote carryover would only add noise), so the
    # flat magnitude is the lever. 4.0 cuts R-INC bias +1.47->+1.10 and lifts
    # R-INC directional accuracy 92->96% while holding CI coverage (92) and
    # nudging ALL MAE 6.89->6.87 / bias +0.94->+0.82. Bias does NOT fully
    # zero by deepening further: most R-INC cells are safe-R seats already
    # clipped by the safe-seat cap, so only competitive cells respond —
    # chasing 0 would overfit them (MAE flattens past 4.25, CI erodes 92->91).
    # Pinned by scripts/backtest_r_incumbency_sweep.py.
    "incumbency_advantage_rep": 4.0,
    # Open seat penalty (legacy single value; superseded by the directional
    # pair below, which the model now uses).
    "open_seat_penalty": -1.5,
    # Directional open-seat penalties (dem-pct), v-jun4b-model. Backtest
    # diagnosis: open seats over-predict the Democrat in BOTH retirement
    # directions (R-retired +6.25 margin / n=32, D-retired +4.55 / n=9) — the new
    # candidate loses the prior incumbent's personal vote and token Ds in safe-R
    # seats crater below the incumbent-inflated baseline. So BOTH penalties are
    # downward-on-D (the old "R retired -> +1.5 D" was empirically backwards).
    # Magnitudes pinned by scripts/backtest_open_seat_sweep.py.
    "open_seat_penalty_d_retired": -3.0,
    "open_seat_penalty_r_retired": -1.5,
    # Incumbency-conditional CI floors (dem-pct). Open-seat over/under-
    # performance is much less predictable than incumbent (Track-3 residual
    # decomposition: open RMSE ~5.0 / std 4.6 vs incumbent ~3.3-3.5), so the
    # 95% CI half-width floors higher for open seats. See national_model.py
    # confidence-interval block.
    "rmse_floor_default": 3.0,
    "rmse_floor_open_seat": 4.5,
    # Confidence-interval RMSE (dem-pct), incumbency-conditional, v-jun4c-model.
    # The 95% CI half-width = 1.96 * ci_rmse[group]. These are the model's
    # realized FULL-prediction error (RMSE) on the 163-cell backtest, by
    # incumbency — replacing the old per-district *naive*-model RMSE (which was
    # both mis-specified, the interval is centered on the full prediction, and
    # noisy, 2-4 cycles/district). D-INC is the most uncertain (4.9), R-INC the
    # most predictable (3.5; D-challenger-vs-R-incumbent races are easy calls).
    # In-sample calibration (fit + validated on the same 163 cells). See §7.1.
    # (open is set above its raw RMSE 4.4: open-seat errors are fat-tailed —
    # the Schrier/GCP-type upsets blow past 1.96*4.4 — so it's calibrated to
    # empirical ~95% coverage. D-INC 4.9 lands ~97% (slightly conservative).)
    "ci_rmse_d_inc": 4.9,
    "ci_rmse_r_inc": 3.5,
    "ci_rmse_open": 5.1,
    "ci_rmse_default": 4.4,
    # Personal-vote carryover (v-jun4-model). For a contested INCUMBENT race
    # with a clean same-map prior cycle, replace the flat incumbency + quality
    # adjustments with a shrunk version of the incumbent's realized prior-cycle
    # offset from (baseline + swing) — their persistent personal/quality vote
    # (cross-cycle r=0.85). No-look-ahead (prior cycle only). enabled/shrink are
    # backtest-gated; see METHODOLOGY §14.3.
    "personal_vote_enabled": True,
    "personal_vote_shrink": 0.7,
    "personal_vote_cap": 8.0,
    # Presidential party midterm penalty (percentage points)
    "midterm_penalty": -3.5,
    # Surge-decline: extra turnout in presidential years
    "presidential_surge_pct": 8.0,
    # Default elasticity if insufficient data
    "default_elasticity": 0.95,
    # Damping factor on (elasticity * national_swing). Backtests showed
    # the structural forecast over-reacts to national tides in WA, which
    # consistently under-shifts the national environment. 0.50 cut MAE
    # from 6.49 to 5.40 across the 2018-2024 24-prediction backtest
    # without hurting directional accuracy. Lower factors fit the
    # backtest better but risk overfitting the 24-sample set.
    # National-swing damping: 0.85 was selected via grid search against
    # the no-look-ahead backtest (see METHODOLOGY for the May 14 calibration).
    # The previous 0.50 attenuated wave signal too aggressively under
    # honest grading; 0.85 minimizes |bias| without losing MAE.
    "national_swing_damping": 0.85,
    # Down-ballot drag scale factor.
    #
    # History: this was 0.25 historically, then 0.0 after the May 14 joint
    # grid search (which found 0.0 dominant on a 46-cell evaluation grid).
    # The May 18 D-bias diagnostic on the 163-cell filtered residual matrix
    # showed the +5.74 mean bias was driven by drag=0 — the model wasn't
    # applying its data-driven district drag signal that DOES correlate
    # with bias direction (cd07 +6.46 historical drag matches its +D
    # under-prediction; LD-06 -5.92 matches its R over-prediction, etc.).
    #
    # Single-coefficient LOCO on the 163-cell filtered set:
    #   2018 held-out: train-best 0.30, held-out 9.66 vs 10.80 @0  (tuned wins)
    #   2020 held-out: train-best 0.40, held-out 6.61 vs 7.63 @0   (tuned wins)
    #   2022 held-out: train-best 0.40, held-out 7.63 vs 7.90 @0   (tuned wins)
    #   2024 held-out: train-best 0.50, held-out 7.56 vs 6.95 @0   (scale=0 wins)
    #   Aggregate: 7.85 tuned vs 8.33 @0 = 0.48 MAE reduction across folds.
    #
    # 0.40 picked as a robust single-coefficient minimum that 3 of 4 LOCO
    # folds pointed near. See memory/may18_d_bias_diagnostic.md.
    "down_ballot_drag_scale": 0.40,
    # Phase 2 of the May 18 D-bias fix: when own-district drag history
    # has < 2 cycles, fall back to a lean-bucket statewide mean drag
    # (computed across other WA districts of the same type + bucket).
    # Targets the Strong-R cell cluster that still had +11.5pt bias
    # after Phase 1 because they had n_cycles=0 for own drag.
    # Enabled May 18 evening after joint-LOCO confirmed Phase 1 holds.
    "drag_use_statewide_prior": True,
    # Recency weights for composite lean
    "lean_weights": [1.0, 0.7, 0.4, 0.2, 0.1],
    # Swing threshold (std dev of lean across elections)
    "swing_threshold": 5.0,
    # GOTV efficiency: contact-to-vote conversion rates
    "door_knock_conversion": 0.10,
    "phone_call_conversion": 0.03,
    "text_conversion": 0.01,
    # Non-voter partisan attenuation: non-voters are ~25% more moderate
    # than the precinct's voter pool (Citrin et al. 2003; Fraga 2018).
    # Applied as a discount to potential_net_votes in GOTV projections.
    "nonvoter_partisan_discount": 0.75,
    # Conversion rate ranges for confidence intervals (Green & Gerber meta-analysis)
    "door_knock_conversion_low": 0.05,
    "phone_call_conversion_low": 0.01,
    "text_conversion_low": 0.005,
    # Digital advertising conversion rate (Kalla & Broockman 2018 meta-analysis).
    # Net persuasion effect per impression-reached voter.
    "digital_ad_conversion": 0.005,
    "digital_ad_conversion_low": 0.002,
    # Fraction of registered voters reachable via digital ad targeting
    "digital_ad_reach_rate": 0.60,
    # Equivalent impressions per volunteer-hour for efficiency scoring
    "digital_ad_contacts_per_hour": 100,
    # Supplementary channel discount: when a voter is already contacted by the
    # primary method, supplementary channels have diminished incremental impact.
    "supplementary_channel_discount": 0.50,

    # --- Volunteer resource model ---
    "shift_length_hours": 3,              # hours per volunteer shift
    "shifts_per_weekend": 2,              # shifts available each weekend day (AM + PM)
    "weekday_volunteer_multiplier": 0.3,  # weekday capacity as fraction of weekend

    # --- Opponent vulnerability thresholds ---
    "opponent_weak_threshold": -3.0,      # overperformance below this = opponent weak
    "demobilization_threshold": -0.05,    # turnout decline threshold (5pp)
    "opponent_lean_threshold": -5.0,      # minimum opponent lean for demob targeting

    # --- Vote budget overlap discounts ---
    # When aggregating vote sources, discount overlapping pools to avoid double-counting.
    "undervote_gotv_overlap": 0.50,       # undervote voters partly overlap GOTV pool
    "primary_leakage_gotv_overlap": 0.60, # primary leakage overlaps GOTV non-voters
    "ballot_chase_gotv_overlap": 0.30,    # chase targets overlap GOTV universe

    # --- Tier-1 candidate quality (Jacobson 1989, Bond/Covington/Fleisher) ---
    # 0-3 score per candidate from {prior_office, funds_serious >= $500K,
    # primary_dominant >= 55%}. Adjustment uses the D-R differential.
    # Conservative vs literature (which puts each tier at 3-5 pts); start
    # small and revisit after backtest.
    # quality_pt_per_tier: 2.0 selected May 14 grid search (was 1.0).
    # The candidate-quality tier diff already saturates the ±2 cap
    # frequently in WA backtest, so per-tier weight beyond 2.0 has
    # diminishing returns. quality_max remains the binding constraint.
    "quality_pt_per_tier": 2.0,           # pts per quality-tier difference
    # quality_max: 2.0 -> 3.0 selected May 14 night after Tier-2 signals
    # (party_recruit, prominent_appointment) were wired in. At cap=2 the
    # D-R differential saturated on Schrier-class races (D tier=1 vs R
    # tier=2 already at the cap), making the Tier-2 contribution invisible.
    # Sensitivity sweep shows cap=3 lowers backtest MAE 5.98 -> 5.87 and
    # directional accuracy 70.8% -> 75.0% with bias unchanged. Further
    # raising to 4 or 5 gives no additional improvement (the cap no
    # longer binds on any backtest cycle).
    "quality_max": 3.0,                   # absolute cap on adjustment
    "quality_funds_threshold": 500000,    # USD; "serious" fundraising signal
    "quality_primary_dominant_pct": 55.0, # within-party primary share threshold
    # Primary "narrow winner" — flags a candidate who won a fragmented
    # primary with very low within-party share. Validated against
    # WA-03 2022 (Joe Kent 35% vs incumbent Herrera Beutler) where the
    # general electorate rejected an outsider who barely won the primary.
    # Narrow-winner subtracts 1 quality tier so the D-R differential can
    # extend to ±4 (vs ±3 with only positive features).
    "quality_primary_narrow_pct": 40.0,   # below this is "narrow winner"

    # --- Safe-seat adjustment cap scaling (Stage 3, May 15) ---
    # When True, the existing _TOTAL_ADJUSTMENT_CAP=8 scales down
    # quadratically with |baseline_dem_pct - 50|, but ONLY when the
    # adjustment direction matches the baseline lean. Addresses the
    # cd02/cd06/cd10 + safe-D LD over-prediction pattern surfaced by
    # the 170-cell expanded backtest. On that grid the smart cap
    # drops MAE 11.52 -> 10.13 and bias +3.46 -> +2.20.
    #
    # Production-mode impact: cd03/cd05/cd08 forecasts unchanged
    # because their adjustments don't amplify-lean (either baseline
    # close to 50 or adjustments point opposite to baseline). Safe-D
    # LDs and cd02/cd06/cd10-style suburban-D races shift R-ward
    # toward more realistic margins.
    "safe_seat_cap_scaling": True,
    "safe_seat_cap_distance_scale": 25.0,
    "safe_seat_cap_floor": 0.1,

    # --- Walkability / canvassing density tiers ---
    # Doors-per-volunteer-hour drops sharply below ~500 voters/sq mi
    # (rural, houses 1+ mile apart). The yield-floor caps the adjustment
    # so a high-density precinct gets full credit and rural precincts
    # get proportionally less. Thresholds calibrated from typical urban
    # volunteer schedules: high-tier precincts net 25-35 doors/hr, rural <5.
    "walk_high_threshold": 1500,          # voters/sq mi for "door-primary"
    "walk_medium_threshold": 300,         # voters/sq mi for "door + phone"
    "walk_low_threshold": 50,             # voters/sq mi for "phone primary"
    "walk_yield_floor_density": 500,      # density at which factor reaches 1.0

    # --- Demobilization lever (Ansolabehere & Iyengar 1995, "Going Negative") ---
    # Forward-looking effect of contrast/negative campaigning on opponent
    # turnout. Opt-in via --demob-strategy CLI flag; default is OFF so the
    # baseline forecast does not pre-bake suppression effects.
    "demob_intensity_off": 0.00,
    "demob_intensity_mild": 0.03,         # typical contrast environment
    "demob_intensity_aggressive": 0.07,   # sustained heavy negative campaign
    "demob_backlash_fraction": 0.20,      # own-side voters depressed at 20% of opponent rate
    "demob_forecast_cap": 2.0,            # hard cap on forecast adjustment, pts
    "demob_persuasion_overlap": 0.25,     # vote-budget discount for precinct overlap with persuasion
}


# Campaign finance model parameters
# Sources: Bonica (2017), Jacobson (2015), Opensecrets.org analysis
FINANCE_MODEL_PARAMS = {
    # National benchmark: points gained per $1M fundraising advantage.
    # House races show ~2-3 points per $1M, with diminishing returns.
    "points_per_million": 2.5,

    # Bayesian prior strength: weight of national benchmark vs. district data.
    # Higher = more weight on the national benchmark (important with few cycles).
    "prior_strength": 3.0,

    # Diminishing returns: fundraising advantage has log-scale impact.
    # First $1M matters far more than the fifth $1M.
    "diminishing_returns_base": 2.0,

    # Maximum forecast adjustment from fundraising (percentage points).
    # Even a 10:1 advantage rarely moves a race more than ±5 points.
    "max_adjustment_pts": 5.0,

    # Campaign health thresholds
    "healthy_burn_rate": 0.70,       # spending < 70% of receipts = healthy
    "warning_burn_rate": 0.90,       # 70-90% = caution; > 90% = danger
    "grassroots_strong_pct": 60.0,   # > 60% individual contributions = strong
    "grassroots_weak_pct": 30.0,     # < 30% = PAC-dependent

    # Dollar-to-vote scenario tiers (additional fundraising amounts)
    "scenario_tiers": [250_000, 500_000, 1_000_000, 2_000_000],
}


# Channel cost parameters for budget allocation recommendations.
# Sources: DCCC 2024 benchmarks, Civis Analytics field cost surveys,
# industry standard CPMs for digital advertising.
CHANNEL_COST_PARAMS = {
    "door_knock": {
        "cost_per_contact": 15.00,   # Includes organizer salary, materials, travel
        "label": "Door-to-Door Canvassing",
        "description": "In-person voter contact at residences",
    },
    "phone": {
        "cost_per_contact": 3.00,    # Phone bank volunteer coordination + dialer costs
        "label": "Phone Banking",
        "description": "Live phone calls to registered voters",
    },
    "text": {
        "cost_per_contact": 0.50,    # P2P texting platform + per-message fees
        "label": "Peer-to-Peer Texting",
        "description": "SMS outreach via peer-to-peer platforms",
    },
    "digital_ad": {
        "cost_per_contact": 0.50,    # ~$5 CPM, 10 impressions per voter = $0.05/impression
        "label": "Digital Advertising",
        "description": "Targeted online ads (social media, display, video)",
    },
    "mail": {
        "cost_per_contact": 1.25,    # Design, printing, postage for direct mail piece
        "label": "Direct Mail",
        "description": "Physical mailers to targeted voter households",
    },
}


# Expected turnout baselines by election cycle type.
# Sources: United States Elections Project (McDonald 2024), Census CPS Voting
# Supplement, WA Secretary of State historical data.
# Values are VEP (Voting Eligible Population) turnout fractions [0, 1].
# WA runs all-mail elections, so baseline turnout is above the national average.
EXPECTED_TURNOUT_PARAMS = {
    # National VEP turnout baselines (used when district data is insufficient)
    "national_presidential": 0.66,   # ~66% in presidential years
    "national_midterm": 0.50,        # ~50% in midterm years
    "national_off_year": 0.30,       # ~30% in odd-year / off-cycle elections
    # WA state adjustment: all-mail voting raises baseline by ~5-8pp
    "wa_mail_bonus": 0.07,
    # Minimum number of elections of a cycle type needed to use district average
    # instead of the national baseline + mail bonus
    "min_elections_for_district_avg": 2,
    # How much the cycle-type ratio adjusts vote-gap projections.
    # E.g. if the last election was presidential (high turnout) but the target
    # is a midterm, the "headroom" for GOTV shrinks.  This factor scales the
    # vote gap: adjusted_gap = raw_gap * turnout_adjustment_ratio.
    "turnout_headroom_floor": 0.25,  # never shrink gap below 25% of raw
}


# Messaging strategy parameters
MESSAGING_MODEL_PARAMS = {
    # A precinct's issue score must deviate from the district average by this
    # many percentage points to be flagged as a distinguishing issue.
    "issue_deviation_threshold": 5.0,

    # Minimum number of ballot measures that contributed to a precinct's
    # issue score for it to be considered reliable.
    "min_measures_for_score": 2,

    # Lean thresholds for messaging group classification (absolute value of
    # composite_lean).  0-4 = competitive/swing, 4-12 = lean, 12+ = base.
    "swing_lean_threshold": 4.0,
    "lean_base_threshold": 12.0,

    # Turnout percentile thresholds for mobilization classification
    "low_turnout_threshold": 0.55,
    "high_turnout_threshold": 0.70,

    # Demographic thresholds for group classification
    "high_college_threshold": 30.0,   # pct_college_degree
    "high_homeowner_threshold": 65.0,  # pct_homeowner
    "high_blue_collar_threshold": 20.0,  # pct_construction + pct_production
}


# Vote-by-mail ballot return model parameters.
# WA is 100% vote-by-mail; ballots are mailed ~18 days before Election Day.
# Return curves estimated from WA Secretary of State historical patterns and
# EAVS (Election Administration and Voting Survey) data.
VBM_RETURN_PARAMS = {
    # Days before Election Day that ballots are mailed
    "ballot_mail_day": 18,

    # Cumulative fraction of eventual returners by period.
    # Represents the share of FINAL turnout returned by end of each period.
    "base_return_curve": {
        "week_1": 0.40,       # ~40% return in first 7 days after mailing
        "week_2": 0.65,       # cumulative ~65% by day 14
        "final_days": 0.85,   # cumulative ~85% by Election Day eve
        "election_day": 1.0,  # remaining returns on/after Election Day
    },

    # Turnout-rate adjustments: high-turnout precincts return earlier
    "high_turnout_early_bonus": 0.10,   # +10pp to week_1 for top-quartile turnout
    "low_turnout_late_penalty": 0.12,   # -12pp from week_1 for bottom-quartile turnout

    # Partisan adjustments: strong partisan precincts return earlier
    "strong_partisan_early_bonus": 0.08,  # +8pp to week_1 for |lean| > 15
    "swing_late_penalty": 0.06,           # -6pp from week_1 for |lean| < 5

    # Ballot chase parameters
    "chase_window_start_day": 7,     # start chasing after day 7
    "chase_efficiency_rate": 0.15,   # 15% of chased non-returners will return
    "min_chase_precinct_size": 50,   # don't chase in tiny precincts

    # Turnout quartile thresholds (for precinct classification)
    "high_turnout_quartile": 0.75,   # top 25% of precincts
    "low_turnout_quartile": 0.25,    # bottom 25% of precincts
}


# WA campaign calendar: phase definitions for campaign timeline generation.
# Dates are computed backward from Election Day (first Tuesday in November).
WA_CAMPAIGN_CALENDAR = {
    "ballots_mailed_days_before": 18,
    # WA top-two primary: first Tuesday in August.
    # Primary results reveal actual opponent, electorate mood, and name-ID strength.
    "primary_month": 8,  # August
    "phases": [
        {
            "id": "pre_primary",
            "label": "Pre-Primary: Fundraising & Name ID",
            "relative_to": "primary",
            "months_before": (4, 1),
            "activities": [
                "Fundraising events & call time",
                "Voter registration drives",
                "Name recognition building (mailers, events, earned media)",
                "Volunteer recruitment & training",
            ],
            "priority_tiers": [4, 5],
            "message_types": ["registration"],
        },
        {
            "id": "primary_sprint",
            "label": "Primary Sprint",
            "relative_to": "primary",
            "months_before": (1, 0),
            "activities": [
                "Primary voter mobilization",
                "Candidate visibility events",
                "Top-two positioning strategy",
            ],
            "priority_tiers": [1, 2, 3],
            "message_types": ["mobilization", "persuasion"],
        },
        {
            "id": "post_primary",
            "label": "Post-Primary: Pivot & Persuasion",
            "months_before_election": (3, 2),
            "activities": [
                "Door-to-door in swing precincts",
                "Targeted digital ads",
                "Issue-based messaging deployment",
            ],
            "priority_tiers": [1, 2, 3],
            "message_types": ["persuasion"],
        },
        {
            "id": "gotv_early",
            "label": "GOTV Mobilization",
            "months_before_election": (2, 1),
            "activities": [
                "Base mobilization canvassing",
                "Phone banking blitz",
                "Early vote encouragement",
            ],
            "priority_tiers": [1, 2],
            "message_types": ["mobilization"],
        },
        {
            "id": "ballot_chase",
            "label": "Ballot Chase & Reminders",
            "days_before_election": (18, 3),
            "activities": [
                "Ballot-mailed reminder contacts",
                "Return tracking & follow-up",
                "Targeted phone/text to non-returners",
            ],
            "priority_tiers": [1, 2, 3],
            "message_types": ["mobilization"],
        },
        {
            "id": "emergency_chase",
            "label": "Emergency Chase",
            "days_before_election": (3, 0),
            "activities": [
                "Slow-return precinct contacts",
                "Ballot drop-off location reminders",
                "Last-chance GOTV push",
            ],
            "priority_tiers": [1],
            "message_types": ["mobilization"],
        },
    ],
}
