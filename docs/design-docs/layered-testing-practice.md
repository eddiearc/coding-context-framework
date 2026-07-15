# Layered Validation Practice

This document defines a shared vocabulary for validation evidence. Each layer
must be reported only for what actually ran: a mock result is not a real API
result, and a screenshot is not a complete acceptance test.

The terms below do not replace the plan structure in
`.agents/skills/task-plan/SKILL.md`. That skill and its checker are the single source
of truth for task-plan sections, alignment, missing-evidence policy, and
commands.

## 1. Unit

Scope: individual functions, parsers, state transitions, configuration reads,
and hierarchy helpers.

Proves: local logic produces the expected result for representative and edge
inputs.

Does not prove: command wiring, file-system integration, or a complete user
workflow.

## 2. Component / Module

Scope: one cohesive module or CLI command with controlled dependencies and a
temporary board.

Proves: the module behaves correctly across its internal branches and error
paths.

Does not prove: cross-module wiring or compatibility with an independently
deployed dependency.

## 3. Contract

Scope: JSON Schema, YAML artifact shape, command options, output formats, exit
codes, plan structure, and field semantics.

Proves: producers and consumers agree on a stable interface and invalid input
is rejected.

Does not prove: that a complete workflow executed or that any external system
is available.

## 4. Mock E2E

Scope: a complete workflow whose service, network, or runtime dependencies are
replaced by mocks, fixtures, or interception.

Proves: the workflow and expected state transitions are coherent under
controlled inputs. Test fixtures are generated in temporary workspaces and
must be labeled Mock E2E when dependencies are simulated.

Does not prove: real authentication, private data access, deployed services,
or production behavior.

## 5. Real API / CLI

Scope: the actual public API or CLI entry point with its real parser,
filesystem, schema, and mutation path. For this template, initializing a fresh
temporary workspace and running `scripts/task` is real local CLI validation.

Proves: the shipped entry point accepts the documented inputs and produces the
documented local effects.

Does not prove: a UI path, a hosted service, or a runtime integration that was
not invoked.

## 6. Real Backend E2E

Scope: a complete client workflow connected to a real backend, real
authentication, and real dependencies in a named environment.

Proves: the tested user path crosses those real components successfully.

Does not prove: untested edge cases or parity with another environment.

Coding Context Framework v0.1.0 ships no backend integration. Reports must mark this
layer `Omitted` with a reason unless a consuming repository adds and actually
runs such a test.

## 7. Evidence / Demo

Scope: reports, command summaries, screenshots, traces, or other reviewable
artifacts tied to a validation run.

Proves: the named command or path ran and its result can be reviewed when the
artifact records the environment and outcome.

Does not prove: a higher validation layer than the underlying run. A mock demo
remains Mock E2E evidence; a command transcript remains Real API / CLI evidence
only for the command that ran.

## Synthetic, mock, and real labels

- `Synthetic` describes the data. It may be used in a real local CLI run.
- `Mock` describes a replaced dependency.
- `Real` means the named entry point and named dependencies actually ran.
- `Not run` and `Omitted` are valid outcomes when paired with a reason and
  residual risk.

Never infer a higher layer from a lower one. Record expected and actual results
separately, and do not paste credentials, private identifiers, private paths,
or large raw logs into evidence.

## Delivery summary

Use the templates under `docs/generated/evidence/templates/` and report all
seven layers, including omitted ones:

```text
Validated:
- Layer, command, environment, actual result, evidence path

Not validated:
- Layer, reason, residual risk

Conclusion:
- What is supported by the evidence
- What remains uncertain
```
