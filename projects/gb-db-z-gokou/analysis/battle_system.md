# Battle-system analysis

This document records the evidence-backed model of the fixed-bank battle code. CPU addresses
in Bank 0 are also ROM file offsets. Game-facing names are used only where the UI or data flow
supports them; unresolved HP/ki ordering and command IDs remain explicitly unknown.

## Confirmed entry points

| Address | Role | Evidence |
|---|---|---|
| `00:0F45` / ROM `$00F45` | Battle-session initialization | Clears battle-global state at `$DA18+`, initializes both fighter records, prepares the HUD, and enters the battle loop. |
| `00:141F` / ROM `$0141F` | Initiative-meter cell calculation | Reads the 16-bit value supplied at `DE`, scales it against `$DA39`, and returns the filled/partial/empty composition for a five-cell meter. |
| `00:1474` / ROM `$01474` | Render a 16-bit value | Reads a little-endian word from `DE`, converts it to numeric tiles, and advances `DE` by two bytes. |
| `00:1485` / ROM `$01485` | Render `BP` and its value | Writes literal tile IDs `$9C,$97` (`B`,`P`), then converts three bytes from `DE` and copies five digit tiles. |
| `00:208C` / ROM `$0208C` | Select active fighter record | Returns `$D9B8` when `$DA31 == 0`, otherwise `$D9E8`. |
| `00:20D9` / ROM `$020D9` | Wait for a ready fighter | Repeatedly updates initiative, waits a frame, and exits when one fighter reaches the threshold. |
| `00:2116` / ROM `$02116` | Update initiative and choose fighter | Updates both mirrored accumulators, compares their high bytes with the shared threshold, and writes the selected slot to `$DA31`. |
| `00:247A` / ROM `$0247A` | Initialize both fighter records | Loads two 18-byte templates, initializes timed/status pairs, applies persistent player modifiers, and creates current-resource, initiative, and BP fields. |
| `00:24D2` / ROM `$024D2` | Load an 18-byte fighter template | Resolves a Bank 1 template pointer through the table at `01:5529` and copies `$12` bytes. |
| `00:24E7` / ROM `$024E7` | Initialize current stats and BP | Copies four bytes from the record's first two base fields, clears the next word, and appends a derived three-byte BP value. |
| `00:2577` / ROM `$02577` | Compute BP | Sums three little-endian base words, divides by two, and multiplies by the factor selected by `$D8C3`. |
| `00:2F47` / ROM `$02F47` | Convert 24-bit value to five digits | Produces digit tiles using decimal place values 10,000, 1,000, 100, and 10. |

## Transient fighter records

The two records are exactly `$30` bytes apart:

| Slot | WRAM range |
|---|---|
| Fighter 0 | `$D9B8-$D9E7` |
| Fighter 1 | `$D9E8-$DA17` |

`00:208C` selects between the two bases from battle-global slot field `$DA31`. Mirrored direct
references and identical initialization establish that these are parallel records.

| Offset | Slot 0 | Slot 1 | Current interpretation | Confidence |
|---:|---:|---:|---|---|
| `+$00` | `$D9B8` | `$D9E8` | First 16-bit base/max resource stat. Copied to `+$1C` at battle start. Likely HP or ki, but ordering is not yet dynamically proven. | Confirmed structure; semantic order unknown |
| `+$02` | `$D9BA` | `$D9EA` | Second 16-bit base/max resource stat. Copied to `+$1E` at battle start. Likely the other of HP/ki. | Confirmed structure; semantic order unknown |
| `+$04` | `$D9BC` | `$D9EC` | 16-bit speed-like stat. It directly feeds initiative accumulation and is the third input to BP. | Strong inference |
| `+$12` | `$D9CA` | `$D9FA` | First of five two-byte timed/status pairs. Its first byte is initialized to 100 and scales the speed-like stat during initiative updates. | Confirmed mechanics; status meaning unknown |
| `+$1C` | `$D9D4` | `$DA04` | Current first resource, rendered as a number on the HUD. | Confirmed structure; HP/ki order unknown |
| `+$1E` | `$D9D6` | `$DA06` | Current second resource, rendered as a number on the HUD. | Confirmed structure; HP/ki order unknown |
| `+$20` | `$D9D8` | `$DA08` | 16-bit initiative/readiness accumulator and source for the five-cell HUD meter. | Confirmed |
| `+$22` | `$D9DA` | `$DA0A` | 24-bit little-endian BP value rendered as five digits. | Confirmed |

The 18-byte template occupies offsets `+$00-$11`. `00:24DC` then initializes five pairs at
`+$12-$1B` to `{100, 0}`. For the player-side record, `00:250A` applies three persistent
modifiers from `$D8D5`, `$D8D7`, and `$D8D9` to the first three 16-bit fields. This matches the
observed persistent training categories (HP, ki, and speed), but the exact ordering of the first
two fields still requires a controlled HP/ki mutation trace.

## HUD data flow

The HUD setup beginning near `00:139C` uses `DE=$D9D4` for fighter 0 and `DE=$DA04` for fighter
1. For each fighter it performs the same sequence:

1. Render the 16-bit value at `+$1C`.
2. Render the 16-bit value at `+$1E`.
3. Build a five-cell meter from the 16-bit value at `+$20` using tile IDs `$92-$95`.
4. Write literal `B` and `P` tiles (`$9C,$97`).
5. Convert the 24-bit value at `+$22` into exactly five numeric tiles.

This confirms that BP is stored as a binary integer rather than five preformatted digits.

## BP calculation

`00:2577` computes the initial per-battle BP as:

```text
base_sum = word[+$00] + word[+$02] + word[+$04]
BP = floor(base_sum / 2) * factor[$D8C3]
```

The factor table at `00:259C` begins:

```text
1, 1, 1, 1, 2, 6, 5, 3
```

The multiply helper returns a 24-bit result, stored little-endian at `+$22..+$24`. The renderer
at `00:2F47` converts that value to five decimal digits. The exact scenario identities associated
with the factor-table indexes, and how active Kaioken modifies or replaces this value, remain to
be traced.

## Initiative model

For each fighter, `00:2116` performs arithmetic equivalent to:

```text
scaled_speed = floor(word[+$04] * byte[+$12] / 100)
increment = floor(scaled_speed * 120 / 100)
word[+$20] += increment
```

It then compares the high byte of each accumulator against `$DA39 - 1`. `$DA39` is initialized
by `00:2562` from the larger of two values derived from each fighter's speed-like stat, providing
a shared gauge scale/threshold. If fighter 0 crosses first, `$DA31` becomes 0; otherwise fighter
1 becomes selected. When neither crosses, the caller waits one frame and updates again.

At `00:20D9`, after a fighter is selected, the selected accumulator word is cleared before action
selection begins. That static behavior does **not** show fixed-threshold subtraction with excess
retained. The reported in-game observation of retained excess therefore remains an explicit
runtime question: it may involve another accumulator, another battle mode, or a later restoration
path. No source label should claim retained remainder until this discrepancy is traced.

## Commands, resources, and Kaioken

The orchestration range `00:1203-$20D3` clearly contains command selection, nested selection
screens, action dispatch, and resource mutation. However, broad-command IDs, individual technique
IDs/costs, the exact HP/ki field ordering, and Kaioken levels/multipliers are not yet established
well enough for permanent semantic labels.

Next runtime checkpoints should watch both records at battle entry and across:

- one technique confirmation and its ki deduction;
- one received hit and its HP deduction;
- the dedicated ki-recovery command;
- consecutive initiative updates and the transition into the command menu; and
- each available Kaioken level, including BP before activation, while active, and after expiry.