# Bill of materials and rough cost (size M)

Prices are my estimates in US dollars, anchored on a few listings seen in October 2026. They are not quotes, they exclude shipping, tax and tools, and they swing a lot by seller and country. Check every line before buying. Printed masses come from the CAD; the filament line adds a 25% allowance for supports, purge and a failed print.

## Cost per kit

Filament is shown pro rata for the grams used. Add the spool minimum: you buy 1 kg of each material, so the first build costs more (see below).

| Kit | Modules | Printed g | Filament USD | Parts USD | Total USD |
|---|---|---|---|---|---|
| core | none | 138 | 4-6 | 10-20 | 14-26 |
| glow | pod | 194 | 5-8 | 43-105 | 48-113 |
| carry | cup, phone, id, pod | 319 | 7-12 | 47-126 | 54-138 |
| comfort | dock, fan, pod | 275 | 6-10 | 50-133 | 56-143 |
| full | cup, phone, dock, fan, pod, id, tube | 415 | 9-15 | 54-157 | 63-172 |

First build, buying whole spools (1 kg TPU, 1 kg PETG, 1 kg natural PETG for the cover): **55-88 USD** for filament alone, then the parts column above. A second kit costs only the grams.

## Printed parts by kit (grams, before the 25% allowance)

| Kit | TPU 95A | PETG | natural PETG |
|---|---|---|---|
| core | 120 | 17 | 0 |
| glow | 120 | 45 | 28 |
| carry | 120 | 170 | 28 |
| comfort | 120 | 127 | 28 |
| full | 120 | 267 | 28 |

## Purchased parts

| Part | Per unit (USD) | Notes |
|---|---|---|
| foam seat pads | 2-5 | 3 mm EVA or neoprene foam, adhesive-backed, cut to the four 36 x 24 mm ovals |
| flexible adhesive | 8-15 | flexible cyanoacrylate or MS polymer for PETG to TPU; one tube is plenty |
| spring plunger M3 | 1-6 | stainless, ball tip, about 2 N, 6-7 mm; one per module. Cheapest in packs of 10-20 |
| protected pouch cell 3.7 V ~4000 mAh | 11-25 | built-in protection circuit, JST connector; about 60 x 40 x 10 mm |
| USB-C charge and 5 V boost board | 4-12 | with overcurrent and short-circuit protection; about 32 x 22 x 6 mm. Take a reputable one, not the cheapest |
| resettable fuse 2 A, slide switch, JST plug | 3-6 | fuse in the cell lead |
| LED strip 5 V COB, 8 mm, 1 m | 3-12 | needs about 0.85 m; 5 mm on size S. Prices range from about $1 to a few dollars per metre on marketplaces to far more at retail |
| PWM dimmer or MOSFET driver | 2-6 | so the firmware can cap brightness and cannot flash |
| wire, heat shrink, solder | 5-10 | if you do not already have them |
| M2 x 6 self-tapping screws (8) | 4-8 | four for the pod lid, four for the fan guard |
| 80 x 80 x 15 mm 5 V fan | 3-10 | brushless, about 0.16 A; USB or 2-pin |
| hook-and-loop strap 20 mm | 1-3 | for the defender dock |
| breakaway tether clip | 1-3 | parts at a few newtons; for the dock and ID pouch eyelets |

## Which kit needs what

| Part | core | glow | carry | comfort | full |
|---|---|---|---|---|---|
| foam seat pads | 1 | 1 | 1 | 1 | 1 |
| flexible adhesive | 1 | 1 | 1 | 1 | 1 |
| spring plunger M3 | - | 1 | 4 | 3 | 7 |
| protected pouch cell 3.7 V ~4000 mAh | - | 1 | 1 | 1 | 1 |
| USB-C charge and 5 V boost board | - | 1 | 1 | 1 | 1 |
| resettable fuse 2 A, slide switch, JST plug | - | 1 | 1 | 1 | 1 |
| LED strip 5 V COB, 8 mm, 1 m | - | 1 | 1 | 1 | 1 |
| PWM dimmer or MOSFET driver | - | 1 | 1 | 1 | 1 |
| wire, heat shrink, solder | - | 1 | 1 | 1 | 1 |
| M2 x 6 self-tapping screws (8) | - | 1 | 1 | 1 | 1 |
| 80 x 80 x 15 mm 5 V fan | - | - | - | 1 | 1 |
| hook-and-loop strap 20 mm | - | - | - | 1 | 1 |
| breakaway tether clip | - | - | 1 | 1 | 1 |

## Tools and test gear (once)

- Soldering iron, multimeter, calipers, flush cutters, sandpaper and a deburring tool.
- A spring scale (to measure the front opening force and pull-test the bars).
- A fire-safe LiPo charging bag or box, for every charge and for the bench test.
- A printer that prints TPU 95A reliably (direct drive helps) and PETG, with at least a 220 mm bed (size XL needs about 235 mm).

## Price anchors I looked at (October 2026, not quotes)

- 3.7 V 4000 mAh protected pouch cells: about 10-23 EUR across [OpenELAB](https://openelab.io/a/s/products/openelab-805080-4000mah-polymer-lithium-battery), [Soldered](https://soldered.com/products/li-ion-battery-4000mah-3-7v) and [Melopero](https://www.melopero.com/?p=185001). Check that the cell has a protection circuit.
- 5 V COB LED strip, 8 mm: marketplace listings from about 1 to 6 USD per metre before shipping; one retail listing was over 40 GBP for a metre. See the [ManoMano listing](https://www.manomano.co.uk/p/cob-led-strip-320-leds-m-flexible-8mm-cuttable-5v-usb-for-tv-cabinet-bedroom-227965546).
- M3 ball plungers: about 1.5 AUD each in a [pack of 20 from Minibearings](https://minibearings.com.au/products/m3-6-plungers-plbt030m060s3005), versus about 6 GBP each singly from [Essentra](https://essentracomponents.com/en-gb/p/spring-plungers-ball-slotted/20253370).
- TPU 95A: about 21 GBP per kg ([eSUN via YPC](https://www.ypc.co.uk/product/esun-tpu-95a-filament-1-75mm-flexible-3d-printer-filament-1kg-2-2-lbs-black/)); PETG about 12-21 USD per kg on Amazon and Elegoo listings.
- 80 mm 8015 5 V fans: about 3-9 USD each depending on seller and connector.

## What this does not include

The printer, your time, shipping, tax, a spare for each part you will break while tuning, and anything for selling it (certification, insurance, packaging, support). Test prints and failures usually double the filament cost of the first kit.
