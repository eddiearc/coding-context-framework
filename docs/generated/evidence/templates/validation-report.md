# Validation Report: <synthetic scope>

- Version or revision: `<revision>`
- Date: `<YYYY-MM-DD>`
- Environment: `<local | synthetic fixture | named real environment>`
- Data classification: `synthetic`
- Preconditions: `<tools and setup>`

## Results

| Layer | Case | Entry / Command | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|---|
| Unit | `<case>` | `<command>` | `<expected>` | `<actual>` | `<Pass / Fail / Not run>` | `<relative path>` |
| Component / Module | `<case>` | `<command>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |
| Contract | `<case>` | `<command>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |
| Mock E2E | `<case>` | `<command>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |
| Real API / CLI | `<case>` | `<command>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |
| Real Backend E2E | `<case>` | `<command>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |
| Evidence / Demo | `<case>` | `<artifact>` | `<expected>` | `<actual>` | `<status>` | `<relative path>` |

## Commands executed

```sh
<exact reproducible commands>
```

## Not validated

- `<layer>`: `<reason and impact>`

## Residual risks

- `<risk or none identified>`

## Publication check

- [ ] Evidence contains no credentials or private identifiers.
- [ ] Paths are repository-relative.
- [ ] Mock, synthetic, and real labels match what ran.
- [ ] Raw logs are summarized rather than pasted.
