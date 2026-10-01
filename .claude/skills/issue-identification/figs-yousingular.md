# figs-yousingular

## Purpose
Identify when "you" requires clarification of singular/plural number for translators whose languages distinguish these forms.

## Definition
Some languages have a **singular** form of "you" for when the word refers to just one person, and a **plural** form for when it refers to more than one person. The Bible was written in Hebrew, Aramaic, and Greek, which all have both forms. English has only one form ("you"), so translators need help knowing the original number.

## IMPORTANT: Name vs. Function
**Despite its name "yousingular," this issue is used to mark when "you" is PLURAL**, not singular. The name refers to the TA article title "Forms of 'You' - Singular" which covers the singular/plural distinction.

## Categories

| Category | Description | Example |
|----------|-------------|---------|
| Plural "you" addressing a group | Most common case | "Since Jesus is speaking to many people, the command **Repent** is plural" |
| Singular "you" to specific individual | When context might be unclear | "Since Jesus is speaking to John, the command **Permit** is singular here" |
| Number switches within a passage | Track who is being addressed | "The first **you** is plural, but the second is singular" |
| Commands with implicit "you" | Plural/singular verb forms | "The commands **search** and **report** are plural" |

Hebrew second-person forms also carry gender, which English "you" cannot show (editors added 36 of these in ISA, 2026, against 40 first-pass rows in the reviewed books). Consider a note whenever the number or gender of the addressee is something a translator needs and English does not show: plural addressees ("You will conceive chaff" to Judah's enemies, ISA 33:11; "your flocks" to the Israelites, ISA 61:5), feminine singular to a city or nation spoken of as a woman ("Sing joyfully, barren one", ISA 54:1; "the merchant of Sidon ... filled you", ISA 23:2), masculine singular to one person ("Call out in the throat" to Isaiah, ISA 58:1; "this trust that you trust" to Hezekiah, ISA 36:4), and especially a switch of number or gender inside a verse or passage (feminine singular "hide" after masculine "enter your rooms", ISA 26:20; singular "you" to an official and then plural "yourselves", ISA 36:7). Editors usually write one note at the first occurrence in a passage and name the verses it covers ("here and in verses 2-7"). They use figs-yousingular for these, and relabeled 17 of 20 figs-you rows to it.

## NOT This Issue (Use Instead)

| Situation | Use Instead |
|-----------|-------------|
| Singular pronoun addressing a crowd | figs-youcrowd |
| Exactly two people addressed | figs-youdual |
| Formal vs informal register | figs-youformal |
| General clarification of who "you" refers to | figs-you |
| Exclusive/inclusive "we" | figs-exclusive |

## Recognition Process

```
Is there a second-person pronoun (you, your, yourself)?
|
+--> Is the number (singular/plural) clear from context?
     |
     +--> YES, and readers could easily identify it
     |    --> No note needed
     |
     +--> NO, or the number might surprise readers
          |
          +--> Is the speaker addressing exactly 2 people?
          |    --> Use figs-youdual
          |
          +--> Is singular "you" addressing a crowd?
          |    --> Use figs-youcrowd
          |
          +--> Is this about formal/informal register?
          |    --> Use figs-youformal
          |
          +--> Otherwise
               --> Use figs-yousingular
```

## Common Patterns

| Context | Pattern |
|---------|---------|
| Epistles | Frequent plural "you" addressing churches |
| Jesus teaching | Often plural when addressing disciples or crowds |
| Direct dialogue | Singular when one person speaks to another |
| OT law | Singular addressing collective Israel (may need figs-youcrowd) |
| Prayers | Singular addressing God |

## Note
Per Issues Resolved (Jul 31, 2024): figs-yousingular notes typically do NOT need alternate translations. The note itself tells translators what form to use.
