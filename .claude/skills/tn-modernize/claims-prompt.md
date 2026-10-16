# List the claims a translation note makes

You get a JSON array of translation notes (`ID`, `note`). For each note, list the separate pieces of information it gives about the Bible text, as short, self-contained statements a checker can look for in a rewritten version of the note.

Include:

- what a word or phrase means, or what or whom it refers to;
- who is speaking or being addressed, and to whom a pronoun refers;
- what kind of expression it is (a metaphor, an idiom, a rhetorical question, a passive form, ...);
- reasons, background or cultural facts the note gives;
- each possible meaning, when the note gives more than one;
- a specific translation suggestion tied to this verse ("you could say clearly that this message is about the people").

Leave out:

- the alternate translations themselves (they are checked separately, word for word);
- generic advice that every note of this kind gives ("use a natural form in your language", "if it would be helpful");
- links and "See also" references.

Write each claim in plain words, without quoting the note's whole sentence, and without bold or markdown. Use as many claims as the note has, usually one to five. A note with no specific information gets an empty list.

Return only one JSON object, no other text:

```json
{"claims": {"xm1w": ["The word vision means a message from Yahweh.", "..."], "jdr3": []}}
```
