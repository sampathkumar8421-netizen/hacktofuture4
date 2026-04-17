import argparse
import random
from pathlib import Path

import pandas as pd


APPLICATION_TYPES = [
    # Core physical
    "ocean_heat_content_timeseries",
    "mixed_layer_depth_index",
    "thermocline_depth_index",
    "anomaly_detection_core_temperature_salinity",
    "float_trajectory_spatiotemporal_track",
    # BGC / OneArgo
    "bgc_ocean_health_scores",
    "oxygen_minimum_zone_extent",
    "ocean_acidification_ph_anomaly",
    "harmful_algal_bloom_hab_support",
    # Hazard / operations
    "hurricane_ocean_initialization_metrics",
    "search_and_rescue_drift_support",
    "oil_spill_transport_forecast_inputs",
    # Defense / acoustic
    "acoustic_sound_speed_profile_inputs",
    # Retrieval/meta
    "semantic_retrieval_floats_profiles",
    "data_sufficiency_coverage_report",
    "explainability_provenance_report",
]


REGIONS = [
    ("North Atlantic", (-80, 0, 0, 65)),
    ("South Atlantic", (-70, 20, -60, 0)),
    ("Indian Ocean", (20, 120, -50, 25)),
]


def rand_year() -> int:
    return random.choice([2020, 2021, 2022, 2023, 2024, 2025])


def mk_region_phrase() -> tuple[str, dict]:
    name, bbox = random.choice(REGIONS)
    lon_min, lon_max, lat_min, lat_max = bbox
    if random.random() < 0.5:
        return (
            f"in the {name}",
            {
                "region_mode": "named",
                "region_name": name,
            },
        )
    return (
        f"in bbox lon[{lon_min},{lon_max}] lat[{lat_min},{lat_max}]",
        {"region_mode": "bbox", "bbox": [lon_min, lon_max, lat_min, lat_max]},
    )


def mk_time_phrase() -> tuple[str, dict]:
    y = rand_year()
    if random.random() < 0.5:
        return (f"during {y}", {"time_mode": "year", "year": y})
    m1 = random.randint(1, 10)
    m2 = m1 + random.randint(1, 2)
    return (f"from {y}-{m1:02d} to {y}-{m2:02d}", {"time_mode": "range", "start": f"{y}-{m1:02d}-01", "end": f"{y}-{m2:02d}-28"})


def mk_depth_phrase() -> tuple[str, dict]:
    if random.random() < 0.6:
        z = random.choice([200, 700, 1000, 2000])
        return (f"down to {z}m", {"depth_mode": "max_depth_m", "max_depth_m": z})
    pmax = random.choice([200, 1000, 2000])
    return (f"pressure up to {pmax} dbar", {"depth_mode": "max_pressure_dbar", "max_pressure_dbar": pmax})


def mk_qc_phrase() -> tuple[str, dict]:
    if random.random() < 0.5:
        return ("using adjusted/delayed-mode data only", {"qc_policy": "prefer_adjusted"})
    return ("including real-time data (warn on low QC)", {"qc_policy": "mixed_with_warnings"})


def mk_query(app: str) -> tuple[str, dict]:
    region_phrase, region_meta = mk_region_phrase()
    time_phrase, time_meta = mk_time_phrase()
    depth_phrase, depth_meta = mk_depth_phrase()
    qc_phrase, qc_meta = mk_qc_phrase()

    base_meta = {
        "application_type": app,
        **region_meta,
        **time_meta,
        **depth_meta,
        **qc_meta,
    }

    if app == "ocean_heat_content_timeseries":
        text = f"Compute ocean heat content time series {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        base_meta["required_variables"] = ["TEMP", "PRES"]
        base_meta["derived_indicators"] = ["OHC_0_700", "OHC_0_2000"]
        return text, base_meta

    if app == "bgc_ocean_health_scores":
        text = f"Assess deoxygenation and acidification risk {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        base_meta["required_variables"] = ["DOXY", "PH_IN_SITU_TOTAL", "PRES"]
        base_meta["derived_indicators"] = ["oxygen_anomaly", "pH_anomaly", "risk_score"]
        return text, base_meta

    if app == "hurricane_ocean_initialization_metrics":
        text = f"Estimate hurricane ocean initialization metrics {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        base_meta["required_variables"] = ["TEMP", "SAL", "PRES"]
        base_meta["derived_indicators"] = ["upper_ocean_heat_content_proxy", "mld", "stratification"]
        return text, base_meta

    if app == "acoustic_sound_speed_profile_inputs":
        text = f"Build sound speed profile inputs for underwater acoustics {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        base_meta["required_variables"] = ["TEMP", "SAL", "PRES"]
        base_meta["derived_indicators"] = ["sound_speed_profile_proxy"]
        return text, base_meta

    if app == "semantic_retrieval_floats_profiles":
        topic = random.choice(
            [
                "low oxygen and pH anomalies",
                "strong stratification and warm subsurface",
                "profiles near eddy-like features",
                "high salinity anomalies",
            ]
        )
        text = f"Find floats/profiles {region_phrase} {time_phrase} that match: {topic}."
        base_meta["required_variables"] = []
        base_meta["derived_indicators"] = []
        return text, base_meta

    # Generic templates
    verb = random.choice(["analyze", "compute", "summarize", "investigate", "report"])
    text = f"{verb.capitalize()} {app.replace('_', ' ')} {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
    base_meta["required_variables"] = []
    base_meta["derived_indicators"] = []
    return text, base_meta


def main() -> int:
    p = argparse.ArgumentParser(description="Generate synthetic training data for an Argo/OneArgo request router.")
    p.add_argument("--out", required=True, help="Output CSV path.")
    p.add_argument("--n", type=int, default=4000, help="Number of examples.")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)
    rows: list[dict] = []
    for _ in range(max(10, args.n)):
        app = random.choice(APPLICATION_TYPES)
        text, meta = mk_query(app)
        rows.append({"query_text": text, "application_type": app, "spec_json": str(meta)})

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote {len(rows):,} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

