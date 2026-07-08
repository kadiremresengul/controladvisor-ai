"""Problem definition schema for ControlAdvisor-AI."""

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class SystemType(str, Enum):
    """High-level engineered system category."""

    mobile_robot = "mobile_robot"
    agv_amr = "agv_amr"
    industrial_robot_arm = "industrial_robot_arm"
    autonomous_vehicle = "autonomous_vehicle"
    drone_uav = "drone_uav"
    process_control = "process_control"


class RobotDrive(str, Enum):
    """Mobile robot drive or locomotion type."""

    differential_drive = "differential_drive"
    ackermann = "ackermann"
    mecanum = "mecanum"
    omnidirectional = "omnidirectional"
    tracked = "tracked"
    legged = "legged"
    aerial_multirotor = "aerial_multirotor"


class EnvironmentType(str, Enum):
    """Operating environment category."""

    indoor_factory = "indoor_factory"
    indoor_warehouse = "indoor_warehouse"
    indoor_office = "indoor_office"
    outdoor_structured = "outdoor_structured"
    outdoor_unstructured = "outdoor_unstructured"
    mixed_indoor_outdoor = "mixed_indoor_outdoor"


class SensorType(str, Enum):
    """Available sensing modalities."""

    wheel_encoders = "wheel_encoders"
    imu = "imu"
    two_d_lidar = "two_d_lidar"
    three_d_lidar = "three_d_lidar"
    rgb_camera = "rgb_camera"
    depth_camera = "depth_camera"
    ultrasonic = "ultrasonic"
    gps = "gps"
    fiducial_markers = "fiducial_markers"
    safety_scanner = "safety_scanner"


class TaskType(str, Enum):
    """Primary autonomy or control tasks."""

    localization = "localization"
    mapping = "mapping"
    navigation = "navigation"
    path_planning = "path_planning"
    trajectory_tracking = "trajectory_tracking"
    obstacle_avoidance = "obstacle_avoidance"
    payload_transport = "payload_transport"
    docking = "docking"
    fleet_coordination = "fleet_coordination"
    manipulation = "manipulation"
    process_regulation = "process_regulation"


class SafetyLevel(str, Enum):
    """Qualitative safety criticality."""

    low = "low"
    medium = "medium"
    high = "high"
    safety_critical = "safety_critical"


class UncertaintyType(str, Enum):
    """Known sources of uncertainty in the problem."""

    sensor_noise = "sensor_noise"
    wheel_slip = "wheel_slip"
    payload_variation = "payload_variation"
    localization_drift = "localization_drift"
    dynamic_obstacles = "dynamic_obstacles"
    map_changes = "map_changes"
    model_mismatch = "model_mismatch"
    communication_latency = "communication_latency"


class ComputePower(str, Enum):
    """Available onboard or edge compute budget."""

    low = "low"
    medium = "medium"
    high = "high"
    edge_cloud = "edge_cloud"


class ConstraintType(str, Enum):
    """Engineering constraints that affect method selection."""

    real_time = "real_time"
    low_cost = "low_cost"
    limited_compute = "limited_compute"
    explainability_required = "explainability_required"
    deterministic_behavior = "deterministic_behavior"
    safety_certification = "safety_certification"
    energy_efficiency = "energy_efficiency"
    narrow_aisles = "narrow_aisles"
    human_shared_space = "human_shared_space"
    collision_avoidance = "collision_avoidance"
    velocity_limit = "velocity_limit"
    acceleration_limit = "acceleration_limit"


class ProblemDefinition(BaseModel):
    """Structured engineering problem definition."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    system_type: SystemType
    robot_drive: RobotDrive | None = None
    environment: EnvironmentType
    map_known: bool
    dynamic_obstacles: bool
    safety_level: SafetyLevel
    compute_power: ComputePower
    sensors: list[SensorType] = Field(min_length=1)
    tasks: list[TaskType] = Field(min_length=1)
    uncertainties: list[UncertaintyType]
    constraints: list[ConstraintType]
    notes: str | None = None


def load_problem_from_yaml(path: str | Path) -> ProblemDefinition:
    """Load and validate a problem definition from a YAML file."""

    yaml_path = Path(path)
    data: Any = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in problem file: {yaml_path}")

    return ProblemDefinition.model_validate(data)
