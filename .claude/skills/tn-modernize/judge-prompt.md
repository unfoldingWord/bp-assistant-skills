# Is each claim still in the rewritten note?

You get a JSON array of items. Each has an `ID`, a rewritten translation note (`note`) and a list of `claims` taken from the note it replaced.

For each claim, give the probability that the rewritten note still states it or clearly implies it. Wording may differ; the information must be the same, with the same certainty (a claim that something "may" be so is not met by a note that says it is so). General template wording does not count as stating a specific claim. A claim that is only in the alternate translations does not count as stated unless the prose explains it. If the note says something different or leaves it out, the probability is low.

Return only one JSON object, no other text, with one probability (0 to 1) per claim in claim order:

```json
{"present": {"ab12": [0.97, 0.12], "cd34": []}}
```
