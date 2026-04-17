import argparse
import random
import json
from pathlib import Path

import pandas as pd
from hyperpipeline.schemas import ApplicationSpec, ExecutionPlan


APPLICATION_TYPES = [
    # Core physical
    "ocean_heat_content_timeseries",
    "mixed_layer_depth_index",
    "thermocline_depth_index",
    # BGC / OneArgo
    "bgc_ocean_health_scores",
    "oxygen_minimum_zone_extent",
    # Hazard / operations
    "hurricane_ocean_initialization_metrics",
    # Defense / acoustic
    "acoustic_sound_speed_profile_inputs",
    # Meta
    "semantic_retrieval_floats_profiles",
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
            {"region_mode": "named", "region_name": name}
        )
    return (
        f"in bounding box lon[{lon_min},{lon_max}] lat[{lat_min},{lat_max}]",
        {"region_mode": "bbox", "bbox": [lon_min, lon_max, lat_min, lat_max]}
    )

def mk_time_phrase() -> tuple[str, dict]:
    y = rand_year()
    if random.random() < 0.5:
        return (f"during {y}", {"time_mode": "year", "year": y})
    m1 = random.randint(1, 10)
    m2 = m1 + random.randint(1, 2)
    return (f"from {y}-{m1:02d} to {y}-{m2:02d}", {"time_mode": "range", "start_date": f"{y}-{m1:02d}-01", "end_date": f"{y}-{m2:02d}-28"})

def mk_depth_phrase() -> tuple[str, dict]:
    if random.random() < 0.6:
        z = random.choice([200, 700, 1000, 2000])
        return (f"down to {z}m depth", {"depth_mode": "max_depth_m", "max_depth_m": z})
    pmax = random.choice([200, 1000, 2000])
    return (f"up to {pmax} dbar pressure", {"depth_mode": "max_pressure_dbar", "max_pressure_dbar": pmax})

def mk_qc_phrase() -> tuple[str, dict]:
    if random.random() < 0.5:
        return ("using adjusted/delayed-mode data only", {"qc_policy": "prefer_adjusted"})
    return ("including real-time data", {"qc_policy": "mixed_with_warnings"})

def build_execution_plan(app: str) -> dict:
    steps = ["retrieval_chunk"]
    
    if app not in ["semantic_retrieval_floats_profiles", "data_sufficiency_coverage_report"]:
        steps.append("feature_composer_chunk")
        steps.append("domain_metric_chunk")
        
    steps.append("evidence_and_reporting_chunk")
    
    return ExecutionPlan(steps=steps).model_dump()

def mk_query(app: str) -> tuple[str, dict, dict]:
    region_phrase, region_meta = mk_region_phrase()
    time_phrase, time_meta = mk_time_phrase()
    depth_phrase, depth_meta = mk_depth_phrase()
    qc_phrase, qc_meta = mk_qc_phrase()

    spec_dict = {
        "application_type": app,
        **region_meta,
        **time_meta,
        **depth_meta,
        **qc_meta,
        "output_format": "table",
        "evidence_policy": "intermediate_artifacts" if random.random() < 0.3 else "raw_only"
    }

    if app == "ocean_heat_content_timeseries":
        text = f"Compute ocean heat content time series {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        spec_dict["required_variables"] = ["TEMP", "PRES"]
        spec_dict["derived_indicators"] = ["OHC_0_700", "OHC_0_2000"]
        spec_dict["output_format"] = "timeseries"
    elif app == "bgc_ocean_health_scores":
        text = f"Assess deoxygenation and acidification risk {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        spec_dict["required_variables"] = ["DOXY", "PH_IN_SITU_TOTAL", "PRES"]
        spec_dict["derived_indicators"] = ["oxygen_anomaly", "pH_anomaly", "risk_score"]
    elif app == "hurricane_ocean_initialization_metrics":
        text = f"Estimate hurricane ocean initialization metrics {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        spec_dict["required_variables"] = ["TEMP", "SAL", "PRES"]
        spec_dict["derived_indicators"] = ["upper_ocean_heat_content_proxy", "mld", "stratification"]
    elif app == "acoustic_sound_speed_profile_inputs":
        text = f"Build sound speed profile inputs for underwater acoustics {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        spec_dict["required_variables"] = ["TEMP", "SAL", "PRES"]
        spec_dict["derived_indicators"] = ["sound_speed_profile_proxy"]
    elif app == "semantic_retrieval_floats_profiles":
        topic = random.choice([
            "low oxygen and pH anomalies",
            "strong stratification and warm subsurface",
            "profiles near eddy-like features",
            "high salinity anomalies",
        ])
        text = f"Find floats/profiles {region_phrase} {time_phrase} that match: {topic}."
        spec_dict["required_variables"] = []
        spec_dict["derived_indicators"] = []
        spec_dict["output_format"] = "ranked_list"
    else:
        # Default fallback
        verb = random.choice(["Analyze", "Compute", "Investigate", "Report"])
        text = f"{verb} {app.replace('_', ' ')} {region_phrase} {time_phrase} {depth_phrase} {qc_phrase}."
        spec_dict["required_variables"] = []
        spec_dict["derived_indicators"] = []

    # Validate with Pydantic
    spec = ApplicationSpec(**spec_dict)
    plan = build_execution_plan(app)
    
    return text, spec.model_dump(), plan

def main() -> int:
    p = argparse.ArgumentParser(description="Generate synthetic training data (Inputs -> ApplicationSpec & ExecutionPlan).")
    p.add_argument("--out", required=True, help="Output CSV path.")
    p.add_argument("--n", type=int, default=1000, help="Number of examples.")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)
    rows: list[dict] = []
    
    for _ in range(max(10, args.n)):
        app = random.choice(APPLICATION_TYPES)
        text, spec_meta, plan_meta = mk_query(app)
        rows.append({
            "query_text": text,
            "application_type": app,
            "application_spec_json": json.dumps(spec_meta),
            "execution_plan_json": json.dumps(plan_meta)
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote {len(rows):,} rows to {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
