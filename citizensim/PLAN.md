# CitizenSim — population evaluation layer

CitizenSim turns Citizen Agents into an evidence-driven product loop:

**build → simulate → find failures → fix → rerun → validate with real people**

## v1 target

Berlin Wohngeld discovery in `geld-check.html`.

This is deliberately a **routing** evaluation, not a legal eligibility calculator. The question is whether a citizen is sent to the appropriate official next step without obvious false positives or obvious misses.

## Metrics

1. routing precision
2. routing recall
3. exclusion safety
4. renter + owner-occupier coverage
5. completion and comprehension in browser simulation

## Evaluation ladder

### 0. Deterministic fixtures
Use small, explicit citizen cases to catch rule regressions.

### 1. MatrAIx browser cohort
Start with 10–20 personas to debug trajectories, then move to 50–200 heterogeneous personas.

Track completion, whether Wohngeld is surfaced, whether the official next step is clicked, disclaimer comprehension, and friction.

### 2. Fixed-cohort regression
Keep the same cohort across product changes so before/after results are comparable.

### 3. Human pilot
Run 10–20 real users after synthetic testing. Synthetic results are stress tests and hypotheses, never proof of real-world impact.

## Portfolio output

Expose a compact public panel with:
- simulated citizens tested
- precision / recall on deterministic routing fixtures
- completion / comprehension on MatrAIx runs
- largest failure cohorts
- issues fixed
- human-pilot status

Never label synthetic results as real-user evidence.
