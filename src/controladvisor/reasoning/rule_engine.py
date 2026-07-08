"""Rule-based recommendation signals for ControlAdvisor-AI."""

from pydantic import BaseModel, ConfigDict, Field

from controladvisor.knowledge_base import MethodCardKnowledgeBase
from controladvisor.schemas.method_card import MethodCategory
from controladvisor.schemas.problem import (
    ComputePower,
    ConstraintType,
    ProblemDefinition,
    RobotDrive,
    SafetyLevel,
    SensorType,
    TaskType,
    UncertaintyType,
)


class RuleSignal(BaseModel):
    """Rule-based signals for one candidate method."""

    model_config = ConfigDict(extra="forbid")

    method_id: str
    positive_reasons: list[str] = Field(default_factory=list)
    caution_reasons: list[str] = Field(default_factory=list)
    avoid_reasons: list[str] = Field(default_factory=list)


class RuleEngineResult(BaseModel):
    """Complete rule-engine output for one problem definition."""

    model_config = ConfigDict(extra="forbid")

    problem_id: str
    signals: list[RuleSignal] = Field(default_factory=list)

    def get_signal(self, method_id: str) -> RuleSignal:
        """Return the signal for a candidate method."""

        for signal in self.signals:
            if signal.method_id == method_id:
                return signal

        raise KeyError(f"Unknown rule signal method ID: {method_id}")

    def candidate_method_ids(self) -> list[str]:
        """Return candidate method IDs in deterministic order."""

        return sorted(signal.method_id for signal in self.signals)


class _RuleSignalBuilder:
    """Internal helper that safely adds reasons only for known methods."""

    def __init__(self, knowledge_base: MethodCardKnowledgeBase) -> None:
        self._knowledge_base = knowledge_base
        self._signals_by_method_id: dict[str, RuleSignal] = {}

    def add_positive(self, method_id: str, reason: str) -> None:
        self._add_reason(method_id, "positive_reasons", reason)

    def add_caution(self, method_id: str, reason: str) -> None:
        self._add_reason(method_id, "caution_reasons", reason)

    def add_avoid(self, method_id: str, reason: str) -> None:
        self._add_reason(method_id, "avoid_reasons", reason)

    def build(self) -> list[RuleSignal]:
        return [
            self._signals_by_method_id[method_id]
            for method_id in sorted(self._signals_by_method_id)
        ]

    def _add_reason(self, method_id: str, field_name: str, reason: str) -> None:
        if not self._knowledge_base.has_method(method_id):
            return

        signal = self._signals_by_method_id.setdefault(
            method_id, RuleSignal(method_id=method_id)
        )
        reasons = getattr(signal, field_name)
        if reason not in reasons:
            reasons.append(reason)


def evaluate_problem_against_methods(
    problem: ProblemDefinition,
    knowledge_base: MethodCardKnowledgeBase,
) -> RuleEngineResult:
    """Evaluate explicit MVP rules and return recommendation signals."""

    builder = _RuleSignalBuilder(knowledge_base)
    _apply_mapping_and_slam_rules(problem, builder)
    _apply_localization_rules(problem, knowledge_base, builder)
    _apply_global_planning_rules(problem, builder)
    _apply_local_planning_rules(problem, builder)
    _apply_tracking_and_low_level_rules(problem, builder)
    _apply_safety_and_constraint_rules(problem, builder)
    _apply_compute_power_rules(problem, builder)
    _apply_uncertainty_rules(problem, builder)

    return RuleEngineResult(problem_id=problem.id, signals=builder.build())


def _has_lidar(problem: ProblemDefinition) -> bool:
    return bool(
        {
            SensorType.two_d_lidar,
            SensorType.three_d_lidar,
        }.intersection(problem.sensors)
    )


def _has_camera(problem: ProblemDefinition) -> bool:
    return bool(
        {
            SensorType.rgb_camera,
            SensorType.depth_camera,
        }.intersection(problem.sensors)
    )


def _slam_method_ids(knowledge_base: MethodCardKnowledgeBase) -> list[str]:
    return [
        method_card.id
        for method_card in knowledge_base.filter_by_category(MethodCategory.slam)
    ]


def _apply_mapping_and_slam_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if not problem.map_known and _has_lidar(problem):
        builder.add_positive(
            "graph_slam",
            "The map is not known and lidar is available, so graph-based SLAM can build or refine an indoor factory map.",
        )
        builder.add_positive(
            "ekf_slam",
            "The map is not known and lidar is available, so EKF-SLAM can provide a validated SLAM baseline.",
        )

    if not problem.map_known and not _has_lidar(problem) and not _has_camera(problem):
        builder.add_caution(
            "graph_slam",
            "The map is not known, but no lidar or camera sensor is available to support robust SLAM.",
        )
        builder.add_caution(
            "ekf_slam",
            "The map is not known, but no lidar or camera sensor is available to support landmark or feature observations.",
        )


def _apply_localization_rules(
    problem: ProblemDefinition,
    knowledge_base: MethodCardKnowledgeBase,
    builder: _RuleSignalBuilder,
) -> None:
    if TaskType.localization not in problem.tasks:
        return

    has_odometry_or_imu = (
        SensorType.wheel_encoders in problem.sensors or SensorType.imu in problem.sensors
    )
    if not has_odometry_or_imu:
        return

    for method_id in _slam_method_ids(knowledge_base):
        builder.add_positive(
            method_id,
            "The problem requires localization and has wheel encoder or IMU sensing to support state estimation.",
        )


def _apply_global_planning_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if TaskType.navigation not in problem.tasks:
        return

    builder.add_positive(
        "astar",
        "Navigation is required, and A* is a clear global planner for route generation.",
    )

    if problem.map_known:
        builder.add_positive(
            "astar",
            "The map is known, which matches A* planning on a grid map or roadmap.",
        )
    else:
        builder.add_caution(
            "astar",
            "The map is not known, so A* requires a map from SLAM, prior mapping, or another mapping process.",
        )


def _apply_local_planning_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if problem.dynamic_obstacles:
        builder.add_positive(
            "dwa",
            "Dynamic obstacles are present, and DWA can provide real-time local obstacle avoidance.",
        )
        builder.add_caution(
            "astar",
            "Dynamic obstacles are present, so global planning alone is not enough without local avoidance.",
        )

    if ConstraintType.collision_avoidance in problem.constraints:
        builder.add_positive(
            "dwa",
            "Collision avoidance is an explicit constraint, which fits a reactive local planner such as DWA.",
        )
        builder.add_positive(
            "mpc",
            "Collision avoidance is an explicit constraint, and MPC can reason about constraints over a prediction horizon.",
        )


def _apply_tracking_and_low_level_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if problem.robot_drive is RobotDrive.differential_drive:
        builder.add_positive(
            "pure_pursuit",
            "The robot is differential drive, and Pure Pursuit is a simple path-following baseline for mobile robots.",
        )
        builder.add_positive(
            "pid",
            "The robot is differential drive, and PID is suitable for low-level wheel speed or actuator loops.",
        )

    if TaskType.payload_transport in problem.tasks:
        builder.add_caution(
            "pid",
            "Payload transport can change the plant response, so PID may need retuning across payload conditions.",
        )

        constraints_or_safety_matter = (
            bool(problem.constraints)
            or problem.safety_level
            in {SafetyLevel.high, SafetyLevel.safety_critical}
        )
        if constraints_or_safety_matter:
            builder.add_positive(
                "mpc",
                "Payload transport with safety or operational constraints benefits from MPC's predictive constraint handling.",
            )


def _apply_safety_and_constraint_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if problem.safety_level is SafetyLevel.high:
        builder.add_positive(
            "mpc",
            "High safety criticality favors MPC because constraints can be represented explicitly.",
        )
        builder.add_positive(
            "dwa",
            "High safety criticality favors a local planner that can react to nearby obstacles.",
        )

    if (
        ConstraintType.velocity_limit in problem.constraints
        or ConstraintType.acceleration_limit in problem.constraints
    ):
        builder.add_positive(
            "mpc",
            "Velocity or acceleration limits are explicit constraints that MPC can handle directly.",
        )


def _apply_compute_power_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if problem.compute_power is ComputePower.low:
        builder.add_caution(
            "mpc",
            "Compute power is low, so MPC solve time may be difficult to guarantee.",
        )
        builder.add_caution(
            "graph_slam",
            "Compute power is low, so graph optimization for SLAM may be too expensive online.",
        )
        builder.add_positive(
            "pid",
            "Compute power is low, and PID has very low computational cost.",
        )
        builder.add_positive(
            "astar",
            "Compute power is low, and A* is often practical on bounded indoor planning grids.",
        )
        builder.add_positive(
            "pure_pursuit",
            "Compute power is low, and Pure Pursuit is lightweight for path tracking.",
        )

    if problem.compute_power is ComputePower.high:
        builder.add_positive(
            "mpc",
            "High compute power improves feasibility for online MPC optimization.",
        )
        builder.add_positive(
            "graph_slam",
            "High compute power improves feasibility for graph-based SLAM optimization.",
        )


def _apply_uncertainty_rules(
    problem: ProblemDefinition, builder: _RuleSignalBuilder
) -> None:
    if UncertaintyType.sensor_noise in problem.uncertainties:
        builder.add_caution(
            "ekf_slam",
            "Sensor noise is listed as an uncertainty, so EKF-SLAM performance depends on careful noise modeling.",
        )
        builder.add_caution(
            "graph_slam",
            "Sensor noise is listed as an uncertainty, so Graph SLAM needs robust measurement models and outlier handling.",
        )

    if UncertaintyType.payload_variation in problem.uncertainties:
        builder.add_caution(
            "pid",
            "Payload variation can change the dynamics, making fixed PID gains less reliable.",
        )
        builder.add_positive(
            "mpc",
            "Payload variation favors MPC because constraints and model updates can be handled explicitly.",
        )

    if UncertaintyType.wheel_slip in problem.uncertainties:
        builder.add_caution(
            "ekf_slam",
            "Wheel slip can corrupt odometry and degrade EKF-SLAM state prediction.",
        )
        builder.add_caution(
            "graph_slam",
            "Wheel slip can corrupt odometry constraints and degrade SLAM graph consistency.",
        )
        builder.add_caution(
            "pure_pursuit",
            "Wheel slip can increase path-tracking error for geometric tracking methods such as Pure Pursuit.",
        )
