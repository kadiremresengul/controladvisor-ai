# ControlAdvisor-AI Agent Guide

## Project Purpose

ControlAdvisor-AI is an explainable engineering assistant that recommends
control, robotics, and navigation algorithms for autonomous and industrial
systems. The current MVP targets indoor differential-drive AGV/AMR use cases in
factory and warehouse environments.

## Build And Test Commands

- Create a virtual environment: `python -m venv .venv`
- Install dependencies: `python -m pip install -r requirements.txt`
- Run tests before completion: `python -m pytest -q`

When using the checked-out local virtual environment on Windows, the equivalent
test command is `.\.venv\Scripts\python -m pytest -q`.

## Coding Conventions

- Use Python 3.11+ syntax and keep the project in a clean `src/` layout.
- Keep Pydantic schemas strongly typed and explicit.
- Store method cards and example problems as readable YAML files.
- Prefer small, focused modules over broad abstractions.
- Keep enums and schema values stable because they are part of the project data
  contract.
- Do not implement future-day features unless the task explicitly asks for
  them.

## Review Expectations

- Prioritize correctness, schema validation behavior, test coverage, and clean
  repository hygiene.
- Check that examples remain valid against the schemas.
- Flag missing tests, unclear enum semantics, or data-contract changes.
- Avoid tracking local environments, caches, generated outputs, or Codex
  workspace metadata.

## Handoff Protocol

Every task must update `docs/assistant_handoff.md` before completion. The
handoff should include the current status, changed files, test command, test
result, known issues, and the next planned step.

Every task must run `python -m pytest -q` before completion. If the active shell
does not have the project environment activated, run the equivalent command via
the local virtual environment and record that exact command in the handoff.
