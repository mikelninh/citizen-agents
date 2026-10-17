# Citizen Agents Historical-Replay Optimizer

Optimize **one watchdog at a time**.

1. Freeze a historical window and its gold set of meaningful events.
2. Enforce a strict information cutoff: the agent may only see sources available at that time.
3. Run the watchdog and record recall, false positives, source quality, citations, duplicates and relevance.
4. Inspect the largest systematic miss/noise source.
5. State one falsifiable hypothesis.
6. Change one coherent surface only.
7. Replay the entire historical benchmark.
8. Any unsupported finding, state confusion (proposal/passed/effective), future-data leak, lost audit log or bypassed human review => `REVERT`.
9. Otherwise `KEEP` only if the precision/recall frontier improves on held-out history.
10. Commit the experiment record.

Optimise for: **Would a citizen relying on this watchdog have learned about the important change in time?**

Do not optimise for number of findings, verbosity or attention-grabbing language.
