# LLM Cost Optimiser

A CPU-only Python CLI that chooses the cheapest supplied model meeting a supplied quality threshold for each task. It makes no model calls, predictions, or network requests. Costs and quality must already exist in the input. Python 3.10 or later is required; runtime dependencies are empty.

## Quickstart

```powershell
python -m pip install --no-deps --no-build-isolation -e .
lco fixtures --out demo
lco run --input demo
lco report --format md
python -m pytest -q
```

If Windows does not put the user scripts directory on PATH, use `python -m llm_cost_optimiser.cli` in place of `lco` in every command, or add the scripts directory reported by pip to PATH. Installation needs a locally available setuptools build backend and uses no dependency downloads.

For a five-record example: `lco run --input examples`, then `lco report --format md`. The five records are explicitly synthetic. Empty directories are valid and produce zero totals. Results default to `.lco/result.json` in the current directory. Use `--state` on run and report to choose another location. Reports contain every decision and SHA-256 input hashes.

## Input format

Directories contain UTF-8 JSONL files or JSON files containing one record or a list of records. JSONL permits header lines beginning with `#`. `expectations.json` is fixture metadata and is excluded from routing. Other formats are rejected with a schema error. No CSV or YAML parser is claimed.

```json
{
  "id": "task-001",
  "synthetic": true,
  "evidence": "hypothetical",
  "min_quality": "0.8",
  "baseline": "premium",
  "candidates": [
    {"model": "economy", "cost": "1", "quality": "0.9"},
    {"model": "premium", "cost": "3", "quality": "0.95"}
  ]
}
```

This example is synthetic and illustrative. For Henry's manually entered real data, set `synthetic` to false. `evidence` must be `measured` or `hypothetical`; measured means the user declares the candidate figures to be observations. The tool does not independently verify them. Never mark predicted quality or list prices as measured trial results.

All six top-level fields are required. Optional fields are `description` and `observed_on`. Unknown fields are rejected. IDs are unique across files, and model names are unique within each task. Strings allow Unicode and Windows paths, must contain 1 to 10000 characters, and cannot contain control characters or an em dash. Candidate lists allow zero to 1000 entries. Costs are nonnegative decimals, at most 1 billion, with at most six decimal places. All costs in one run must use the same currency unit; the tool does not convert currencies. Quality and minimum quality range from zero to one inclusive. NaN, infinity, booleans, negative values, and excess precision are rejected. Decimal strings are recommended for exact arithmetic.

`baseline` is a candidate name or null. A supplied baseline permits comparison for selected tasks only. Baseline quality need not meet the constraint; this enables comparison to an existing policy, and negative deltas remain visible. Infeasible tasks have null cost and null delta and do not contribute to cost or baseline totals. Optional `observed_on` uses ISO YYYY-MM-DD and cannot exceed the fixed evidence cutoff 2026-09-30. This fixed cutoff makes validation deterministic; updating the evidence window requires an explicit contract change.

Selection uses quality >= threshold, lowest cost, then ascending model name to break ties. No eligible candidate yields `infeasible`. This establishes eligibility from supplied evidence, not future output quality. Duplicate IDs and malformed records abort the whole run; nothing is silently dropped. JSON parse errors name file and line; schema errors identify offending fields. A duplicate ID is a run-level schema error naming the ID. Missing input gives a usage hint and exit code 2. Errors have no tracebacks. Reports and state use temporary files plus atomic replacement; failed writes remove temporary files and preserve any prior destination.

## Commands

| Command | Purpose | Example |
| --- | --- | --- |
| fixtures | Generate 200 labelled synthetic records and expectations | `lco fixtures --out demo` |
| run | Compute decisions and save state | `lco run --input examples --state trial.json` |
| report | Render saved decisions and provenance | `lco report --state trial.json --format json --out trial-report.json` |
| route | Print per-task decisions, totals, and provenance without saving | `lco route --input examples` |
| audit | Validate the schema and expose infeasible tasks with full traceability | `lco audit --input examples` |

Every subcommand supports `--help` and includes an example. `audit` validates supplied evidence structure, not the truth of quality observations. Report state is a generated local artifact, not a separate supported input schema.

## Architecture

```text
JSON / JSONL directory -> cli.read_inputs -> core.validate
                                            |
                                            v
                                      core.optimise
                                            |
                      atomic state JSON <- decisions -> report.render
                                                          |
                                                   Markdown / JSON
fixtures.generate -> labelled records + independent expectations
```

The core has no I/O. Decimal arithmetic provides exact cost reconciliation. File ordering, ID ordering, tie-breaking and serialization are stable. No randomness is used, so no seed is required. Identical inputs give byte-identical state and reports. Runtime timing is recorded in evidence, never embedded in deterministic outputs.

## Honesty boundary and fixture labels

The tool computes only from explicit inputs. Quality is supplied evidence, not an inferred score or a guarantee. Synthetic and hypothetical figures are labelled in CLI messages, report banners, decision provenance, and separate totals. No time saved is claimed. Cost deltas are computed only for explicit baseline comparisons. Synthetic baseline deltas are illustrative, hypothetical real-input deltas are hypothetical, and measured deltas rely on user-declared measured candidate costs. No money saved in production is claimed by the demo. Mixed runs retain separate totals; no synthetic amount is combined with measured savings.

Every JSONL fixture begins with a SYNTHETIC header comment and each record contains `synthetic: true`. JSON expectation metadata carries `synthetic: true` and a synthetic label since JSON does not permit comments. Trial results from Henry's real use are local, ignored by git, and are not shipped. Put trial directories outside the repository or add them to local git exclusions.

## Hypothesis and acceptance evidence

Hypothesis: deterministic selection from explicit cost and quality observations can provide a trustworthy routing decision under the stated input constraints. The planted ground truth tests validate the computation, not whether a given model delivers quality in production.

The fixture consists of 50 repeats of four independently specified cases: economy passes (cost 1), only premium passes (cost 3), neither passes, and economy exactly meets the threshold (cost 1). This yields 200 records, 150 selections, 50 infeasible cases, selected cost 50*(1+3+0+1)=250, 150 baseline comparisons, and baseline delta 50*(2+0+0+2)=200. All amounts are synthetic illustrative currency units. The infeasible IDs are 2, 6, ..., 198. Tests compare every choice and exact totals, and deliberately changing supplied quality changes the result. Expectations are never read by the engine.

See EVIDENCE.md for the recorded test and CLI demo measurements. Tests cover malformed input, schema drift, missing paths, failed writes, empty input, duplicates, invalid values, Unicode, long text, deterministic bytes and provenance. Neither GPU packages nor network clients are used.

## Improvement hook and verdict

After two weeks of real use, Henry should hand-check all decisions in a sample of at least 20 tasks (or all tasks if fewer) against their original supplied candidate observations. Primary metric: incorrect routing decisions / checked decisions. Record run count, checked count, errors, error rate, observed quality limitations and paid use in a private trial log. Synthetic test accuracy is not real-use accuracy. If errors exceed 10 percent, fix the top measured cause and rerun the sample, or kill with the reason. If there is no actual use, record that finding and kill rather than decorating the portfolio.

The evidence window has not occurred. No final verdict is claimed. After that window record the dated verdict and reason in VERDICT.md: expand for daily use or revenue; integrate for substantial sibling-project overlap; commercialise for a buyer willing to pay as-is; maintain as portfolio evidence otherwise; kill for no use or failed acceptance. The current build passes local synthetic acceptance only.
