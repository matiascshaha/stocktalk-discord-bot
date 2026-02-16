# Evaluation

Use this folder to track whether AI changes improve delivery speed and quality.

## Minimal weekly loop

1. Select 10 to 20 representative tasks.
2. Run them with your standard AI workflow.
3. Log metrics in `eval/metrics-template.csv`.
4. Compare week-over-week trends.
5. Keep changes that improve outcomes; revert process changes that regress.

## Recommended metrics

- `time_to_first_green_minutes`
- `first_pass_green` (0 or 1)
- `iterations_to_green`
- `reprompts_count`
- `defect_escape` (0 or 1)
- `flaky_reruns`

## Evaluation hygiene

- Keep task set stable enough for comparison.
- Tag by domain (`ui`, `backend`, `ci-cd`, `automation`).
- Note major environment changes when interpreting metrics.
