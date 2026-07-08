"""Method card schema for ControlAdvisor-AI."""

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class MethodCategory(str, Enum):
    """High-level category for a control, robotics, or navigation method."""

    low_level_control = "low_level_control"
    trajectory_tracking = "trajectory_tracking"
    global_planning = "global_planning"
    local_planning = "local_planning"
    localization = "localization"
    mapping = "mapping"
    slam = "slam"
    state_estimation = "state_estimation"
    robust_control = "robust_control"
    optimal_control = "optimal_control"


class MethodRequirement(str, Enum):
    """Required inputs, resources, or assumptions for a method."""

    system_model = "system_model"
    linear_model = "linear_model"
    nonlinear_model = "nonlinear_model"
    optimization_solver = "optimization_solver"
    sufficient_compute_power = "sufficient_compute_power"
    odometry = "odometry"
    lidar = "lidar"
    camera = "camera"
    imu = "imu"
    encoder = "encoder"
    map = "map"
    tuning_effort = "tuning_effort"
    training_data = "training_data"


class MethodStrength(str, Enum):
    """Strengths that can support method selection."""

    simple = "simple"
    interpretable = "interpretable"
    low_compute_cost = "low_compute_cost"
    handles_constraints = "handles_constraints"
    good_tracking_performance = "good_tracking_performance"
    robust_to_uncertainty = "robust_to_uncertainty"
    suitable_for_real_time = "suitable_for_real_time"
    suitable_for_indoor_navigation = "suitable_for_indoor_navigation"
    handles_dynamic_obstacles = "handles_dynamic_obstacles"
    widely_used = "widely_used"


class MethodLimitation(str, Enum):
    """Limitations or risks that may reduce method suitability."""

    requires_tuning = "requires_tuning"
    requires_accurate_model = "requires_accurate_model"
    computationally_expensive = "computationally_expensive"
    weak_with_strong_nonlinearity = "weak_with_strong_nonlinearity"
    weak_with_dynamic_obstacles = "weak_with_dynamic_obstacles"
    sensitive_to_noise = "sensitive_to_noise"
    may_oscillate = "may_oscillate"
    local_minima_risk = "local_minima_risk"
    implementation_complexity = "implementation_complexity"


class MethodMetric(str, Enum):
    """Metrics commonly used to evaluate a method."""

    tracking_error = "tracking_error"
    settling_time = "settling_time"
    overshoot = "overshoot"
    control_effort = "control_effort"
    computation_time = "computation_time"
    path_length = "path_length"
    collision_count = "collision_count"
    constraint_violation = "constraint_violation"
    localization_error = "localization_error"
    mapping_accuracy = "mapping_accuracy"
    robustness_score = "robustness_score"


class MethodTag(str, Enum):
    """Domain tags used for lightweight retrieval and filtering."""

    mobile_robot = "mobile_robot"
    differential_drive = "differential_drive"
    indoor_factory = "indoor_factory"
    agv = "agv"
    amr = "amr"
    safety_critical = "safety_critical"
    payload_transport = "payload_transport"
    dynamic_obstacles = "dynamic_obstacles"
    static_obstacles = "static_obstacles"
    nonlinear_system = "nonlinear_system"
    mimo_system = "mimo_system"
    uncertain_system = "uncertain_system"


class MethodCard(BaseModel):
    """Structured description of a candidate control or robotics method."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1)
    category: MethodCategory
    summary: str = Field(min_length=1)
    requirements: list[MethodRequirement] = Field(default_factory=list)
    strengths: list[MethodStrength] = Field(default_factory=list)
    limitations: list[MethodLimitation] = Field(default_factory=list)
    metrics: list[MethodMetric] = Field(default_factory=list)
    tags: list[MethodTag] = Field(default_factory=list)
    suitable_when: list[str] = Field(default_factory=list)
    avoid_when: list[str] = Field(default_factory=list)
    typical_use_cases: list[str] = Field(default_factory=list)
    related_methods: list[str] = Field(default_factory=list)
    notes: str | None = None


def load_method_card_from_yaml(path: str | Path) -> MethodCard:
    """Load and validate a method card from a YAML file."""

    yaml_path = Path(path)
    data: Any = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in method card file: {yaml_path}")

    return MethodCard.model_validate(data)
