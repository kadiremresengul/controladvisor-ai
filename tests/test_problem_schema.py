from pathlib import Path

from controladvisor.schemas.problem import (
    ConstraintType,
    EnvironmentType,
    SensorType,
    TaskType,
    load_problem_from_yaml,
)


EXAMPLE_PROBLEM_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "example_problems"
    / "indoor_diff_drive_agv.yaml"
)


def test_example_problem_yaml_loads_successfully() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert problem.id == "indoor_diff_drive_agv_factory_mvp"


def test_example_problem_environment_is_indoor_factory() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert problem.environment is EnvironmentType.indoor_factory


def test_example_problem_map_is_not_known() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert problem.map_known is False


def test_example_problem_includes_two_d_lidar_sensor() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert SensorType.two_d_lidar in problem.sensors


def test_example_problem_includes_navigation_task() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert TaskType.navigation in problem.tasks


def test_example_problem_includes_payload_transport_task() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert TaskType.payload_transport in problem.tasks


def test_example_problem_includes_collision_avoidance_constraint() -> None:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)

    assert ConstraintType.collision_avoidance in problem.constraints
