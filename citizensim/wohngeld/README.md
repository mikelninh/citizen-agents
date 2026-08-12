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

## Run

```bash
python evaluate.py
```

The script writes `results/baseline.json` and `results/candidate.json` and asserts that the candidate does not regress the fixture.

## MatrAIx

`matraix-task/` contains the browser-evaluation scaffold. Copy it into MatrAIx as `application/tasks/citizensim-wohngeld-discovery/`, register the web task, and begin with 10–20 personas before scaling.
