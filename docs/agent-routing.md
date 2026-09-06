# Agent Routing

User-owned routing for optional Herdr handoffs. This file is a template: replace
`TODO` values you intend to use. The framework does not assign models, planners,
providers, or approval modes.

## Policy

- Do not execute placeholder values (`TODO`, empty, or other unresolved tokens).
- Do not invent a model, planner, approval flag, quota command, or fallback.
- Honor an explicit user or session choice for the current handoff without
  asking again.
- Resolve only fields this handoff actually uses. Unrelated `TODO` rows do not
  block other work.
- A handoff is blocked only when a field required by that handoff is still
  unresolved and the session did not supply it.
- Before launch, the handed-off category needs an explicit `agent_kind` and an
  explicit model decision. Fill `model` with a chosen model, or write an
  explicit user-selected CLI default such as `CLI default`. Leaving `model` as
  `TODO` is not permission to accept a silent CLI default.
- Resolve `thinking`, `native_args`, and `approval_policy` only when this
  handoff uses them. Unresolved unused fields stay `TODO` and are omitted.
- `approval_policy` has no universal default. Leave it `TODO` unless the user
  chose an approval mode.
- `quota_check` and `fallback` run only when filled. A `TODO` fallback means
  stop and report the gap; do not pick a substitute.
- Planning is proportional to task complexity. A planning row is not required
  for every change.
- Implementation handoff also requires an aligned registered plan.

Edit this file locally. Re-running initialization must not overwrite a customized
copy.

## Route table

```yaml
routes:
  planning:
    agent_kind: TODO
    model: TODO
    thinking: TODO
    native_args: TODO
    approval_policy: TODO
    quota_check: TODO
    fallback: TODO
  implementation:
    agent_kind: TODO
    model: TODO
    thinking: TODO
    native_args: TODO
    approval_policy: TODO
    quota_check: TODO
    fallback: TODO
  review:
    agent_kind: TODO
    model: TODO
    thinking: TODO
    native_args: TODO
    approval_policy: TODO
    quota_check: TODO
    fallback: TODO
```

Add more category keys if the workspace needs them. Keep the same field names.
Independent executor and evaluator instances may use the same model when they
are separate agents.
