# Is it worth building further? Cost, price and reliability simulations

Run from `viability.py` (40,000 Monte Carlo draws per case; `viability_results.json` has the raw table). Every input is an **assumption**, not data, and is listed below so you can argue with it. The simulations cannot tell you whether anyone will buy this. They tell you what price it would need, how many units that takes, and where the design is weak.

## Short answer

- **As a hand-made consumer product at festival-gadget prices: no.** A hand-assembled kit costs more to make and sell than commodity festival items sell for, by roughly 5 to 10 times.
- **As a small, lean, niche accessibility product, or as plans you sell: possible, unproven.** The numbers work if costs are lean and customers pay roughly $200 for the bare collar, $300 for glow and $500 for the full kit.
- **There is a reason to take the next small step** (the Stage 1 print, a design fix and a demand test, a few hundred dollars in cash) **and no reason yet to spend money on inventory, certification or tooling.**
- **The simulations found a design problem:** the glued bar failed in about one in four units over a season under the assumed handling. I changed it (30 mm glued flange plus two barbed locating pegs through the skin), which brings that to about 2-3% on the central assumptions, but it is still 10-40% if the glue is weaker or handling harsher than I assumed. Stage 1 has to measure the real glue strength and peg pull-out force before anyone trusts the number.

## What it costs to make and sell one (size M)

Per unit, in US dollars, median with the 10th to 90th percentile. "Make cost" is filament, purchased parts, printer time, print attendance and assembly labour, with failed prints and scrapped units included. "Landed cost" adds packaging, shipping, returns, payment fees and the cost of finding the customer.

| Kit | Print hours | Make cost | Landed cost | Price to cover landed cost | Price for a 40% margin |
|---|---|---|---|---|---|
| core | 16 | 162 (136-193) | about 250 | **250** (211-294) | **424** (360-500) |
| glow | 20 | 297 (252-352) | about 395 | **403** (346-472) | **686** (588-802) |
| carry | 28 | 386 (327-456) | about 490 | 502 (430-588) | 853 (732-999) |
| comfort | 25 | 365 (310-432) | about 470 | 479 (411-559) | 815 (698-951) |
| full | 34 | 473 (402-560) | about 590 | **602** (515-705) | **1,023** (876-1,198) |

Size XXL costs about 10-25% more once everything is counted (core 306 to cover cost, full 676).

**The plastic is not the problem.** Filament is $4-15 per kit and the purchased parts are $10-157. What drives the price is labour (assembly takes 85 minutes for the bare collar and about 4 hours for the full kit), printer time, and the fixed costs of selling one unit: shipping about $14, finding the customer about $30, returns, fees.

## What would change the answer

Median price needed to cover cost (and for a 40% margin) when one assumption is changed:

| Change | core | full |
|---|---|---|
| baseline | 249 / 424 | 601 / 1,021 |
| assembly time halved (design for assembly) | 222 / 378 | 517 / 879 |
| labour cost halved | 217 / 370 | 514 / 873 |
| printers owned and written off | 214 / 363 | 526 / 895 |
| no paid ads (community, partners) | 218 / 371 | 570 / 970 |
| parts 30% cheaper at 100+ units | 244 / 416 | 564 / 959 |
| **all of the above (a lean operation)** | **120 / 203** | **308 / 523** |
| sold as a self-assembly kit | 217 / 369 | 500 / 850 |

No single lever is enough; they all have to move together.

## How many units a lean operation needs

Prices a lean operation could plausibly charge, and the units per year to cover fixed costs (insurance, testing spread over 3 years, web and tools: about $7,000 a year for the bare collar and $13,000 for anything with a battery):

| Kit | Price | Margin per unit | Break-even units per year |
|---|---|---|---|
| core | 149 / 199 / 249 | 29 / 77 / 126 | 239 / **90** / 55 |
| glow | 249 / 299 / 349 | 51 / 100 / 148 | 266 / **137** / 92 |
| full | 399 / 499 / 599 | 89 / 186 / 283 | 153 / **73** / 48 |

For scale: the five largest US festivals drew roughly 2.8 million attendances in 2025, and about 27% of US adults report a disability. Even 100 units a year is a tiny share of that pool. But **whether people with those needs would pay $200-500 for this is exactly what the numbers cannot say.**

## Selling the files and instructions instead

No stock, no assembly, no shipping. Assumed: support of 15-70 minutes per sale, finding the customer $5-45, 3-15% refunds, about $3,000 a year fixed.

| Price | Margin per sale | Break-even sales per year |
|---|---|---|
| 29 | -14 | not reachable |
| 49 | 4 | 375 |
| **79** | **31** | **113** |

This carries far less risk, and an open, hackable design may suit the people it is for. It earns less per sale and does not scale like a physical product.

## The price problem

What people pay for the single functions today (from listings I found, October 2026): neck fans $10-20 retail, sensory ear defenders about $14-17, hydration packs about $27-58, festival LED novelties about $13-29 in bulk. Added together the separate items come to roughly $60-120. This product is priced as an integrated, accessibility-fitted system, and the price premium has to be earned by that fit. The "sensory-friendly wearables" market I found is small (about $72 million a year worldwide in one report), so do not assume a big pool.

## Lowering the cost without losing function or quality

I added these as levers in `viability.py` (`cost_levers`). Median price to cover cost / price for a 40% margin, size M. Savings are from my assumptions, and the sheet price is a guess because I could not find one.

| Change | core | glow | full |
|---|---|---|---|
| baseline (printed detent already included) | 250 / 424 | 397 / 675 | 559 / 950 |
| print TPU on a 0.6 mm nozzle at about 5 mm3/s (my baseline assumed about 1.8) | 209 / 355 | 357 / 606 | 519 / 883 |
| gluing and fitting jig (the pegs already locate the bar) | 241 / 410 | 380 / 646 | 536 / 912 |
| buy parts at 100+ units | 244 / 415 | 371 / 632 | 529 / 900 |
| ship the flat skin in an envelope | 240 / 408 | 387 / 657 | 549 / 934 |
| print the lip with the skin (no lip parts, no lip gluing; needs a redesign) | 240 / 408 | 387 / 659 | 550 / 935 |
| cut the skin from 2 mm TPU sheet instead of printing it | 245 / 416 | 392 / 666 | 554 / 943 |
| **all of the above except cutting** | **178 / 302** | **297 / 504** | **449 / 764** |
| all of the above with cutting | 212 / 360 | 332 / 564 | 483 / 821 |
| all of the above with cutting, plus a lean operation | 144 / 245 | 228 / 388 | 328 / 557 |

The spring plungers were a lever in the previous version of this table; the printed detent is now the design, so it is in the baseline (it took about $40 off the full kit). Its force (about 1.9 N) and strain (about 0.33%) are hand calculations, not tested.

**What this says.** Together the changes cut the price needed by about 28% with no loss of function, and with a lean operation as well the bare collar could cover its cost at about $145 and the full kit at about $330. The biggest single levers are printing the TPU faster (about $40 a kit), a fitting jig, and buying parts in bulk.

**Cutting the skin from sheet is a wash on cost on my numbers**, because the sheet and the cutting service (about $30-120 a set, assumed) cost about what the 15 hours of printing does. It would still give a cleaner, stronger, layer-free skin and free the printers, so it is worth quoting. I found waterjet, knife and pulsed CO2 laser cutting of TPU (waterjet is cold, so no fumes); I did not find a sheet price.

**Injection moulding the flat skin pays off once volume is proven.** The skin is nearly flat, with no undercuts, so it moulds well. On assumed figures (aluminium tool about $10,000, parts about $9 a kit) it saves about $88 a kit against printing, and the tool pays back after about 120 kits (range 77 to 180). Generic guides put aluminium tools at $3,000-12,000 and break-even against printing at 400-800 parts; none of that was TPU-specific. Do this only after the demand test.

**What I would not cut:** the skin thickness, the slots, the 30 mm flange and pegs, the fan guards, the LED cover, or any of the safety items. They are the margin the strength and safety checks rely on.

**Costs design cannot fix:** about $85 a sale goes on finding the customer, shipping, returns and payment fees. A good size guide (the five-measurement check) cuts wrong-size returns, and community or partner sales cut the acquisition cost.

## Reliability: the glue joint

I simulated the weakest joint, a cup (402 g, 91 mm out) peeling its bar off the skin. Inputs: peak acceleration per use (median 1.3 g, 95th percentile 4.5 g, lognormal) and adhesive peel strength (median 2.0 N/mm, 35% scatter). A barbed peg is assumed to hold 15 N before it pulls back through the 2 mm TPU. All three are guesses until the Stage 1 tests measure them.

| Design | Chance of failure per peak | Per season (30 peaks) |
|---|---|---|
| 20 mm flange, glue only (the previous design) | 1.0% | **26%** |
| same, adhesive scatter 50% | 1.5% | 37% |
| 30 mm flange, glue only | 0.3% | 8% |
| **30 mm flange + 2 pegs (current design)** | **0.1%** | **2.6%** |
| same, weak glue (1.0 N/mm) | 0.9% | 23% |
| same, weak pegs (6 N each) and weak glue | 1.8% | 41% |
| 30 mm flange + 4 pegs, weak glue | 0.4% | 10% |
| 30 mm flange + 2 pegs, harsh handling (95th percentile 7 g) | 0.8% | 21% |
| 30 mm flange + 4 pegs, harsh handling | 0.5% | 15% |

**The change helps a lot on the central assumptions (26% to 2.6%) but does not make the joint safe by itself.** If the real glue is half as strong, or handling is harsher, the failure rate is back above 20%. If Stage 1 shows that, the next step is a mechanical fixing (a screw through the bar and skin into a small backing plate) instead of relying on glue. A cup spilling on the wearer is not a minor failure.

## Do the stages pay for themselves?

My own probabilities, not data: Stage 1 passes 55% (cone holds, glue holds, clip slides, cover snaps), Stage 2 70% (sits well on a body, one-handed), Stage 3 80% (modules under load), Stage 4 85% (battery bench test). The chance the whole product works as designed is **about 26%.**

If you spend about $25,000 (median) on inventory, testing, insurance and tooling before knowing, Stage 1 alone is expected to avoid about **$11,000 of losses** for a cost of about $700 (mostly your time). The four stages together cost about $3,900. Testing first is clearly right; this is the one conclusion that does not depend on demand.

## What would make me stop

- The flat TPU skin does not hold a cone on the body (Stage 1 or 2).
- The glue cannot be made to hold with the wider flange and pegs.
- No one will commit money at or above the lean-case price (below).
- Real assembly takes more than twice the time assumed (core 85 minutes, full about 4 hours), or the lean levers (own printers, community sales) are not available to you.

## What would make me continue

1. Stage 1 passes, with a measured glue strength that makes the bar failure rate under 2% per season.
2. A demand test: a page describing the product and its price, with refundable deposits. **A reasonable bar is 25-30 deposits at $199 for the bare collar or $299 for glow within three months**, roughly a quarter to a third of one year's break-even volume. Talk to disabled festival-goers before building more.
3. Tests with real users and their own mobility aids and seating.
4. Quotes for the battery system and a product-liability policy that match the assumed $13,000 a year.

## What the model does not know

Demand, price sensitivity, regulation, the real labour time, the real failure rate, and everything about the people who would use it. Fixed costs (insurance, testing, set-up) are my rough ranges, not quotes. Injection moulding at scale would change the economics completely but needs tens of thousands of dollars of tooling; it is not modelled.

## Sources for the anchors

[LED neck fans, retail and bulk](https://uchangepromo.com/products/neck-fan-with-led-light) · [FDM machine rates: 1.5-5 EUR per hour](https://sinterit.com/3d-printing-guide/costs-of-a-3d-printing/how-to-calculate-3d-printing-cost) · [US adults with a disability: 27%](https://www.cdc.gov/ncbddd/disabilityandhealth/infographic-disability-impacts-all.html) · [largest US festivals by attendance](https://www.statista.com/chart/amp/36070/music-festivals-with-the-largest-total-attendance-in-the-us) · [sensory ear defenders](https://www.inclusive.com/sensory-ear-defenders.html) · [sensory-friendly wearables market](https://www.gii.tw/report/smrc1836396-sensory-friendly-wearables-clothing-market.html). Prices and market reports vary by source and date.
