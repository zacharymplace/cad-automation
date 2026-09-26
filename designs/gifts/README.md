# Gifts: the pixel family

Wedding gifts for a friend who is into CAD, video games, engineering,
and landscaping. Every design here is 8-bit pixel art built on the
shared `zcad.generators.pixel_grid.PixelGrid` toolkit: trace a pattern
into a sharp outline, offset it exactly, score the walls and faces so
blocks read in a single colour.

| Design | Type | Parts | What it is |
| --- | --- | --- | --- |
| `player-two-planter.json` | `pixel_heart_planter` | planter, saucer | Hollow pixel heart with drainage, on an achievement plate reading "PLAYER 2 HAS JOINED". |
| `extra-life-planter.json` | `pixel_heart_planter` | planter, saucer | Same generator, mushroom pattern, "1-UP" banner. |
| `pixel-garden-module.json` | `pixel_garden_module` | main | One plantable 40 mm pixel with dovetail rails; print many, slide them into any picture. |
| `plant-marker-tomato.json` | `pixel_plant_marker` | main | Flat garden stake with a scored pixel sprout and an embossed crop name. |
| `gamepad-coaster.json` | `pixel_coaster` | main | Square coaster with a flush pixel gamepad relief; filament-swap at the recess floor for two colours. |
| `coaster-p1.json`, `coaster-p2.json`, `music-note-coaster.json` | `pixel_coaster` | main | Same coaster with P1, P2, and eighth-note reliefs. |
| `plant-marker-basil.json`, `-chili.json`, `-mint.json` | `pixel_plant_marker` | main | The marker set. |
| `photo-stand.json` | `pixel_photo_stand` | main | Low pixel heart block with a slanted slot that holds a 4x6 wedding photo or a card. |
| `creeper-block-planter.json` | `pixel_block_planter` | main | 80 mm voxel cube with a face recessed into the front wall and a drainage hole. |
| `ring-dish.json` | `pixel_ring_dish` | main | Low pixel heart tray with a centre cone for rings. |
| `headphone-hook.json` | `pixel_hook` | main | Screw-mounted J-hook with an eighth note recessed in the plate; prints on its side. |

## Patterns

Patterns are lists of strings, `X` filled and `.` empty, row 0 at the
top. Outline-based products (planter, marker) need a single connected
region without holes whose pixels touch on full edges. Reliefs (the
coaster, the block planter faces, the hook plate) accept anything,
including islands.

## Fit before committing

- Print two garden modules before nine; `rail_clearance` (0.25 mm) is
  the knob if the slide is tight or loose.
- The planter drops into its saucer with 0.5 mm per side; `clearance`
  adjusts it.

Build any design with:

```bash
zcad designs/gifts/<design>.json
```
