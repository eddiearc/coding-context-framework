# <Task ID> Task Plan

Date: YYYY-MM-DD

## Plan Status

Status: Draft - waiting for user alignment
Execution: Blocked. Do not begin implementation while questions remain.

## Goal / Scope

Describe the goal, in-scope behavior, and explicit non-goals.

## Context Sources Checked

- `AGENTS.md`
- relevant domain and target-repository rules

## Alignment Status

Status: Draft - waiting for user alignment

## Human Alignment Log

Record only questions actually asked and answers actually received.

## Task / Worktree / Branch Plan

- Task:
- Repository:
- Base branch:
- Worktree:

## Contract / Behavior

- Observable behavior:
- Compatibility:

## Validation Plan

Test Boundary: describe the boundary
Why this boundary: explain the chosen scope
Why not narrower: explain what narrower testing misses
Why not broader: explain why broader testing is unnecessary
Dependencies: list concrete dependencies
Command: list the primary validation command
Expected RED: describe the expected failing behavior
Expected GREEN: describe the expected passing behavior
Missing evidence policy: record attempts and never claim omitted evidence passed
Minimum attempts before accepting missing evidence: 2
Covered layers: list covered layers
Entry / Command / Artifact per layer: see the table
Omitted layers with reasons / risks: list omissions and residual risks

| Layer | Required | Entry / Command / Artifact | Proves | Does not prove / Risk |
| --- | --- | --- | --- | --- |
| Unit | Yes | concrete command | concrete claim | residual risk |
| Component / Module | No | explicit skip reason | omission is explicit | residual risk |
| Contract | Yes | concrete command | concrete claim | residual risk |
| Mock E2E | No | explicit skip reason | omission is explicit | residual risk |
| Real API / CLI | Yes | concrete command | concrete claim | residual risk |
| Real Backend E2E | No | explicit skip reason | omission is explicit | residual risk |
| Evidence / Demo | Yes | concrete artifact | concrete claim | residual risk |

## Evidence Plan

- Commands and outputs:
- Reports:

## Risks / Open Questions

- Blocking question:

## Implementation Recommendation

- Smallest aligned implementation:
