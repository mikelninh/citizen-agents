# CitizenSim v1 — Berlin Wohngeld routing

This folder contains the first repeatable CitizenSim evaluation.

## Baseline

The old `geld-check.html` surfaced Wohngeld from only two signals:

- pays rent
- low-to-middle income

On the 12-case regression fixture this produced:

- precision: **62.5%**
- recall: **83.33%**
- false positives: **3**
- false negatives: **1**

The misses exposed three important routing gaps: transfer-benefit exclusions, all-household BAföG/BAB exclusions, and owner-occupier Lastenzuschuss coverage.

## Candidate rule

The revised discovery rule uses:

- main residence in Berlin
- renter **or** self-occupied owner
- low-to-middle income signal
- no housing-cost transfer-benefit exclusion
- not an all-household BAföG/BAB-entitled case

On this deliberately constructed regression fixture the candidate scores 100% precision/recall. **That is not a real-world accuracy claim.** The fixture was designed around these known failure modes.

## Run the deterministic regression

```bash
python evaluate.py
```

The script writes `results/baseline.json` and `results/candidate.json` and asserts that the candidate does not regress the fixture.

## Run a real MatrAIx cohort

`matraix-task/` contains the browser-evaluation task. The repository also includes the manual GitHub Actions workflow `.github/workflows/citizensim-matraix.yml`.

The workflow:

1. checks out this branch
2. clones the current MatrAIx repository
3. installs the task as a Playwright web task
4. samples a fixed cohort with seed `42`
5. runs the cohort against the PR #39 Vercel preview
6. uploads the MatrAIx `jobs/` output as a workflow artifact

Before the first run, add an Actions repository secret named `OPENAI_API_KEY`.
Then open **Actions → CitizenSim MatrAIx → Run workflow**. Start with `10` personas and the default `openai/gpt-4o-mini` model. Keep seed `42` fixed between product iterations so before/after comparisons use the same sampled citizens.

Synthetic users are for stress testing and hypothesis generation. They do not replace legal validation or real-user research.
