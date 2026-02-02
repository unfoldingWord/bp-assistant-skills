# figs-apostrophe

## Purpose
Identify apostrophe in biblical text where a speaker addresses someone or something that cannot hear them to express strong emotion.

## Definition

Apostrophe is when a speaker turns away from their actual listeners and addresses someone or something that cannot hear them - absent people, dead people, inanimate objects, places, or abstract concepts. The purpose is to express strong emotion to the actual audience.

## Key Recognition Criteria

1. **Addressed entity cannot hear**: The person/thing being spoken TO cannot receive the message
2. **Actual audience is present**: Someone else IS listening who CAN hear
3. **Shows strong emotion**: The speaker is communicating feelings ABOUT the addressed entity

## Common Apostrophe Targets

| Target Type | Examples |
|-------------|----------|
| Cities/Places | Jerusalem, Babylon, Canaan, mountains, land |
| Natural elements | Wind, earth, beasts |
| Inanimate objects | Altar |
| Abstract concepts | Death |
| Absent people | Kings, rulers, tribes not present |
| Dead people | Deceased prophets |

## Pattern Examples from Published Notes

**Cities/Places:**
- "Jerusalem, Jerusalem" (Luke 13:34, Matt 23:37) - Jesus expressing grief to disciples about Jerusalem
- "Altar! Altar!" (1 Kings 13:2) - Prophet addressing altar to warn the king
- "Mountains of Gilboa" (1 Samuel) - David expressing grief about Saul's death

**Natural Elements:**
- "Do not fear, land! Be glad and rejoice" (Joel 2:21) - Actually speaking to Judeans
- "Awake, north wind, and come, south wind" (Song 4:16) - Woman expressing desire
- "Earth, do not conceal my blood" (Job 16:18) - Expressing anguish about suffering

**Abstract:**
- "Death, where is your victory? Death, where is your sting?" (1 Cor 15:55) - Taunting death

**Absent People:**
- "Listen, kings! Give ear, rulers" (Judges 5:3) - Song addressing world leaders while speaking to Israelites
- "Increase your army and come out" (Judges 9:29) - Gaal addressing absent Abimelech to show contempt

## NOT Apostrophe

| Situation | Use Instead |
|-----------|-------------|
| Speaker addresses God (who CAN hear) | Not a figure of speech - genuine prayer |
| Speaker addresses present audience directly | Normal address |
| Personification where object IS the audience | figs-personification |
| Speaking to oneself (aside) | figs-aside |

## Recognition Process

```
Is someone speaking TO something/someone?
  |
  +-- Can the addressed entity hear? --> NOT apostrophe
  |
  +-- Cannot hear:
      |
      +-- Is there an actual audience present? --> YES = Apostrophe
      |
      +-- No audience present? --> Consider figs-aside (speaking to self)
```

## Translation Strategy

The standard approach is to convert the address to third-person speech about the entity:
- "Altar, altar!" --> "You who worship at this altar, listen!"
- "Jerusalem, Jerusalem" --> "I am very upset about Jerusalem"
- "Mountains of Gilboa, let there be no rain on you" --> "As for these mountains, let there be no rain on them"
