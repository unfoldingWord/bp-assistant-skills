# List the claims a translation note makes

You get a JSON array of translation notes (`ID`, `issue`, `note`). `issue` is the translation issue the note is filed under (its tA article name, such as `figs-abstractnouns`). For each note, list the separate pieces of information it gives about the Bible text, as short, self-contained statements a checker can look for in a rewritten version of the note.

Include:

- what a word or phrase means, or what or whom it refers to;
- who is speaking or being addressed, and to whom a pronoun refers;
- what kind of expression it is, when that is something other than `issue` (a figs-metonymy note that also calls the phrase an idiom);
- reasons, background or cultural facts the note gives;
- each possible meaning, when the note gives more than one;
- a specific translation suggestion tied to this verse ("you could say clearly that this message is about the people").

Leave out:

- the alternate translations themselves (they are checked separately, word for word);
- generic advice that every note of this kind gives ("use a natural form in your language", "if it would be helpful");
- the statement that the expression is the kind named by `issue` ("pride is an abstract noun" in a figs-abstractnouns note, "this is a metaphor" in a figs-metaphor note): the issue label already records it;
- links and "See also" references (a pointer such as "see how you translated this in 1:9" is kept by a separate check).

Write each claim in plain words, without quoting the note's whole sentence, and without bold or markdown. Use as many claims as the note has, usually one to five. A note with no specific information gets an empty list.

Return only one JSON object, no other text:

```json
{"claims": {"xm1w": ["The word vision means a message from Yahweh.", "..."], "jdr3": []}}
```
