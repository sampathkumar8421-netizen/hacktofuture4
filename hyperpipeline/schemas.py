import json
from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field


class ApplicationSpec(BaseModel):
    """
    The structured specification for the application required by the downstream pipeline.
    This acts as the main contract between the orchestrator and the execution chunks.
    """
    application_type: str = Field(..., description="The specific application type (e.g. hurricane_ocean_initialization_metrics)")
    
    # Required core or BGC variables
    required_variables: List[str] = Field(default_factory=list, description="Variables to query, e.g. TEMP, SAL, PRES, DOXY")
    
    # Filter contract (spatial, temporal, depth, qc)
    region_mode: Optional[Literal["named", "bbox", "point_radius"]] = None
    region_name: Optional[str] = None
    bbox: Optional[List[float]] = Field(None, description="[lon_min, lon_max, lat_min, lat_max]")
    point: Optional[List[float]] = Field(None, description="[lon, lat]")
    radius_km: Optional[float] = None
    
    time_mode: Optional[Literal["year", "range", "event_window"]] = None
    year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    depth_mode: Optional[Literal["max_depth_m", "max_pressure_dbar", "fixed_bins"]] = None
    max_depth_m: Optional[float] = None
    max_pressure_dbar: Optional[float] = None
    
    qc_policy: Optional[Literal["prefer_adjusted", "mixed_with_warnings", "adjusted_only"]] = None
    
    # Derived parameters and indicators
    derived_indicators: List[str] = Field(default_factory=list, description="List of computational indicators required")
    
    # Output and evidence contracts
    output_format: Optional[Literal["timeseries", "table", "ranked_list", "map_tiles", "text"]] = "table"
    file_format: Optional[Literal["csv", "json", "markdown"]] = None
    evidence_policy: Optional[Literal["raw_only", "intermediate_artifacts", "benchmark_citations"]] = "raw_only"


class ExecutionPlan(BaseModel):
    """
    The orchestrated chunks to run in sequential order.
    """
    steps: List[str] = Field(..., description="List of pipeline step handlers to execute (e.g. ['retrieval_chunk', 'feature_chunk', 'domain_metric_chunk', 'reporting_chunk'])")
