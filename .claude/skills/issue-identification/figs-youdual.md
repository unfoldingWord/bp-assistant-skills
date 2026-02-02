# figs-youdual

## Purpose
Identify when exactly two people are being addressed, helping translators whose languages have a dual pronoun form.

## Definition
Some languages have a **dual** form of "you" for when the word refers to only two people, in addition to singular (one person) and plural (more than two people). Hebrew, Aramaic, and Greek do not have dual forms, so the context must be examined to determine when exactly two people are being addressed.

## Categories

| Category | Example |
|----------|---------|
| Two named individuals addressed | "Since Jesus is speaking to James and John, **you** would be dual here" |
| Context indicates two people | "Jesus sent out two of his disciples and said to them" |
| Two people acting together | "the two of them went on together" |

### Common Biblical Contexts

| Context | Example |
|---------|---------|
| Genesis narratives | Abraham & Isaac, Jacob & Esau |
| Exodus | Moses & Aaron addressed together |
| Gospels | Two disciples sent out (Mark 11:1-2) |
| Judges | Simeon & Levi |

## NOT This Issue

| Situation | Use Instead |
|-----------|-------------|
| More than two people addressed | figs-yousingular |
| One person addressed | figs-yousingular |
| Singular addressing a crowd | figs-youcrowd |
| Formal register question | figs-youformal |
| General "you" clarification | figs-you |

## Recognition Process

```
Is there a second-person pronoun (you, your)?
|
+--> Does context indicate EXACTLY two people are addressed?
     |
     +--> YES - Clear that two specific people are the audience
     |    --> Use figs-youdual
     |
     +--> NO - One person, three+, or unclear number
          --> Use figs-yousingular for singular/plural distinction
```

## Common Patterns from Published Notes

| Book | Count | Examples |
|------|-------|----------|
| Exodus | 45 | Pharaoh addressing Moses and Aaron; instructions to two midwives |
| Genesis | 15 | Conversations between patriarchs; two angels visiting Lot; Abraham and Isaac traveling |
| Luke | 12 | Various dual addresses |
| Mark | - | Sending out disciples in pairs (Mark 11:1-2) |

## Key Distinction from figs-yousingular

| figs-youdual | figs-yousingular |
|--------------|------------------|
| Exactly 2 people | 1 person OR 3+ people |
| Context must clearly show two | General singular/plural distinction |
| Helps languages WITH dual forms | Helps languages distinguishing sg/pl |
