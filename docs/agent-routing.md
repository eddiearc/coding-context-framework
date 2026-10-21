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
- Implementation handoff also requires an aligned registered plan.

## Planning, quota, and fallback

- The current agent writes the plan by default. Fill `planning` only when
  complexity or missing expertise makes that separate handoff useful. A `TODO`
  planning row does not start a planner and does not block another category.
- Run a filled `quota_check` before launching that route, resuming it, and
  integrating its result. Exhausted quota means the command ran and reported no
  remaining capacity. Unavailable metering means the command did not run or its
  result could not be read. Record those outcomes separately. Unavailable
  metering does not count as exhaustion and does not switch routes. Continue
  the already authorized route with the unknown reading recorded, unless an
  existing explicit policy requires successful metering. Do not add a launch
  gate or another confirmation solely because the reading is unavailable.
- A `TODO` `quota_check` or `fallback` is not a command and not a substitute.
  Choose remaining capacity only among explicitly filled routes. A filled
  `fallback` applies only to its own route. Do not invent a route, model, or
  fallback. Do not replace `review.model` because another category is
  exhausted; replace it only with that review route's filled `fallback` or a
  new explicit session choice. A field the session names overrides that same
  field for this handoff. Other filled fields, including that route's
  `fallback`, still apply.

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
