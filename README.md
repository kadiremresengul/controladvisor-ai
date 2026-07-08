# ControlAdvisor-AI

ControlAdvisor-AI is an explainable engineering assistant for recommending
control, robotics, and navigation algorithms for autonomous and industrial
systems.

## MVP Scope

The initial MVP focuses on an indoor differential-drive AGV/AMR operating in a
factory or warehouse. The assistant will eventually accept a structured problem
definition and recommend a control and navigation architecture with supporting
explanations.

This repository is currently a clean, testable Python project skeleton. The
full reasoning engine, simulation tooling, schemas, and application surfaces are
intentionally not implemented yet.

## Requirements

- Python 3.11+
- Pydantic for structured schemas
- YAML files for method cards and example problems
- pytest for tests

## Quickstart

```bash
python -m venv .venv
python -m pip install -r requirements.txt
pytest
```

For editable development installs:

```bash
python -m pip install -e ".[dev]"
pytest
```

## Project Layout

```text
data/
  method_cards/
  example_problems/
docs/
src/
  controladvisor/
    app/
    cli/
    explanation/
    knowledge_base/
    reasoning/
    schemas/
    simulation/
tests/
```

## Status

Skeleton only. Next steps should define the Pydantic problem schemas, method
card schema, and the first narrow recommendation flow for indoor
differential-drive AGV/AMR systems.
