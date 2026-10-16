# Is each claim still in the rewritten note?

You get a JSON array of items. Each has an `ID`, a rewritten translation note (`note`) and a list of `claims` taken from the note it replaced.

For each claim, give the probability that the rewritten note still states it or clearly implies it. Wording may differ; the information must be the same. A claim that is only in the alternate translations does not count as stated unless the prose explains it. If the note says something different or leaves it out, the probability is low.

Return only one JSON object, no other text, with one probability (0 to 1) per claim in claim order:

```json
{"present": {"xm1w": [0.97, 0.12], "jdr3": []}}
```
