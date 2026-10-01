# CitizenSim — Wohngeld discovery

Read `input/context.md` and use the Citizen Agents Geld-Check as the person described by your sampled persona.

Your goal is not to maximize money or force a particular result. Answer the page naturally, based only on what your persona would know and reasonably infer.

After completing the check, save `/app/output/citizensim_result.json`:

```json
{
  "completed": true,
  "wohngeld_shown": true,
  "wohngeld_path": "mietzuschuss",
  "clicked_wohngeld_next_step": false,
  "understood_that_result_is_only_a_routing_hint": true,
  "confidence": 0.0,
  "friction": ["<short issue if any>"],
  "reason": "<brief explanation of what you understood and why you acted as you did>"
}
```

`wohngeld_path` must be one of `mietzuschuss`, `lastenzuschuss`, or `none`.

Do not invent personal facts that are not supported by the persona. If the page asks something genuinely ambiguous, make the most natural choice for the persona and record the ambiguity in `friction`.
