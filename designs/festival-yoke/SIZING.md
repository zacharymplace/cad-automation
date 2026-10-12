# Checking the size presets against survey data

I checked the S/M/L/XL presets against the **ANSUR II** survey: measurements of 4,082 men and 1,986 women in the US Army, taken in 2010-2012 and published by the Army and Penn State OpenLab ([the public CSVs](https://www.openlab.psu.edu/ansur2/); summary report TR-15/007). I computed the statistics from the raw files. All figures are millimetres.

## What the survey says (the five dimensions the yoke uses)

| Measure | Men: mean (5th-95th) | Women: mean (5th-95th) | Pooled 50/50: 5th / median / 95th |
|---|---|---|---|
| Head circumference | 574 (548-601) | 561 (532-597) | 537 / 568 / 600 |
| Head breadth | 154 (146-163) | 148 (140-156) | 141 / 151 / 162 |
| Head length | 200 (188-211) | 190 (178-202) | 180 / 195 / 209 |
| Neck circumference at the base | 435 (395-479) | 371 (340-405) | 345 / 399 / 480 |
| Neck circumference at the Adam's apple | 398 (360-443) | 330 (302-363) | 307 / 361 / 433 |
| Biacromial breadth (the yoke's "shoulder width") | 416 (384-447) | 365 (335-396) | 342 / 391 / 441 |
| Chest depth (the closest thing to "shoulder depth") | 254 (211-298) | 247 (205-296) | 207 / 249 / 297 |
| Neck-base-to-shoulder-tip drop (C7 to acromion height) | 77 (54-100) | 61 (39-82) | 43 / 69 / 94 |

## What I found and changed

1. **The head is smaller than my model assumed.** I had fitted an ellipse to the head circumference. Real heads are 152 x 196 mm at a 570 mm circumference, not 161 x 201, because a circumference measure includes the brow and back-of-head bumps. The head model now uses the survey's ratios (breadth 0.267, length 0.343 of the circumference). To keep the opening the same size I raised the allowance to 19 mm each side (ease plus about 10 mm of hair) and the depth factor to 0.87. Size M's opening is 190 x 170 mm, as before.
2. **The neck numbers were too small for what I told people to measure.** The guide says to measure at the base of the neck, where a shirt collar sits; the survey's median there is 399 mm, and I had 350 for size M. The neck presets (used for the fit report and the mannequin) are now 365 / 380 / 425 / 450, the median of the people each size serves.
3. **Head presets** moved to 550 / 570 / 580 / 590. People with a given shoulder width have heads that vary much less than my presets spread (the correlation between head circumference and shoulder width is only 0.48), so L and XL were too large.
4. **Shoulder drop** now follows the slope. The population's shoulder slope (the trapezius line) has a median of about 24 degrees, with a 5th-95th range of 15 to 32. The collar is built at 24, so the drop scales with its width: 36 / 40 / 45 / 51 (it was 38 / 40 / 42 / 45, too shallow for L and XL).
5. **Shoulder depth is the least supported number.** The survey has no shoulder front-to-back dimension. Chest depth varies little with shoulder width (medians of 242 to 263 mm across the four sizes), so my 230-300 mm range probably grows too fast. I left it: it needs a real shoulder measurement, and you can set it yourself in the `custom` table.
6. **Shoulder width presets already match the population.** The survey's 12th, 40th, 70th and 92nd percentiles are 353, 379, 411 and 435 mm; the presets are 350, 380, 410 and 440. No change.

## How well it covers

I tested each of 10,000 people (5,000 men and 5,000 women resampled): give them the size nearest their shoulder width, then ask whether (a) their shoulders are within 25 mm of the yoke, (b) their head and 10 mm of hair pass through the opening, (c) the front gap does not need to open more than 60 mm beyond its 70 mm, and (d) the opening is not more than 55 mm wider than their neck. **The presets pass for 98.4% of the sample**, with sizes S, M, L and XL used by 25%, 30%, 31% and 15%. The only real misses are people whose shoulders are more than 25 mm from any size (about 1%). A set of sizes placed exactly on population percentiles did no better. Those four criteria are mine: change them and the number moves.

## XXL

The survey says 5.2% of the pooled sample has shoulders wider than 440 mm (XL), 1.1% wider than 455 and 0.2% wider than 470; among men, 10.4% are above 440. People with shoulders of 455 mm or more in the sample have a median head circumference of 588 mm, neck base 470 mm and chest depth 288 mm. **XXL** (head 595, neck base 480, shoulders 470, depth 320, drop 57, at the usual 24 degree slope) extends the range to about 485 mm of shoulder. It rests on extrapolation, because the survey has few such people; larger civilians and older adults are likely to need it more than the Army sample shows. For XXL the front-to-back clearance to the neck base is only about 13 mm (22 mm at the sides), tighter than the other sizes, and the flat skin pieces are up to 246 x 189 mm, so it needs a printer bed of about 250 mm (XL needs about 232 mm; the lip segments are split in two for L and up, so they are not the limit). An earlier version of the bed check compared sizes the wrong way round and wrongly passed L, XL and XXL on a 220 mm bed.

## Limits

- **It is a US Army sample**: adults aged roughly 17-51, selected for fitness, with few very large bodies, no children and few older adults. The people this is for may not match it. **Larger neck and shoulder dimensions than XL are likely among civilians and older people**; that is why XXL is now there, but it is the least verified size.
- **No seated or wheelchair posture**: the survey measures standing and sitting bodies, not rounded shoulders, forward head posture or spinal conditions, all of which change how a collar sits.
- **One slope per size**: the collar is built at 24 degrees, but people's shoulders range from 15 to 32. At a 32 degree slope (about one person in twenty) the rim will lift, and at 15 degrees the skin will crease, because the TPU can only take up so much. If your slope is far from 24, set `shoulder_drop` yourself from your own measurement.
- **Head and shoulders do not travel together**: someone with broad shoulders and a small head, or the reverse, will fit one size's shoulders and another's opening. Use `size = "custom"`.
- **Hair**: the 10 mm hair allowance is a guess. Large hair, buns, hats and headwear will not pass the opening.
