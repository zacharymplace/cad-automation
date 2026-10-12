"""Bill of materials and rough cost per kit, size M. Printed masses come from the CAD (print_plan.parts); prices are my
estimates in USD, anchored on a handful of listings found in Oct 2026, NOT quotes: check them before buying.
Run: uv run --no-project --with cadquery bom.py   (writes BOM.md for size M, BOM_<size>.md for the others; FESTIVAL_YOKE_SIZE=XXL picks a size)
"""
import json
from collections import defaultdict

import math

import build
import layout
import power
import print_plan

KITS = layout.KITS
WASTE = 1.25   # supports, purge, a failed print or two

# price per kg of filament, USD (low, high)
FILAMENT = {"TPU 95A": (22, 35), "PETG": (15, 25), "PETG (natural)": (18, 28)}

# purchased parts: name -> (unit low, unit high, note)
PARTS = {
    "foam seat pads": (2, 5, "3 mm EVA or neoprene foam, adhesive-backed, cut to the four 36 x 24 mm ovals"),
    "flexible adhesive": (8, 15, "flexible cyanoacrylate or MS polymer for PETG to TPU; one tube is plenty"),
    "protected pouch cell 3.7 V ~4000 mAh": (11, 25, "built-in protection circuit, JST connector; about 60 x 40 x 10 mm"),
    "USB-C charge and 5 V boost board": (4, 12, "with overcurrent and short-circuit protection; about 32 x 22 x 6 mm. Take a reputable one, not the cheapest"),
    "resettable fuse 2 A, slide switch, JST plug": (3, 6, "fuse in the cell lead"),
    "LED strip 5 V COB, 8 mm, per metre": (3, 12, "length depends on the size (see the strip line below); 4-5 mm on size S. Prices range from about $1 to a few dollars per metre on marketplaces to far more at retail"),
    "PWM dimmer or MOSFET driver": (2, 6, "so the firmware can cap brightness and cannot flash"),
    "wire, heat shrink, solder": (5, 10, "if you do not already have them"),
    "M2 x 6 self-tapping screws (8)": (4, 8, "four for the pod lid, four for the fan guard"),
    "80 x 80 x 15 mm 5 V fan": (3, 10, "brushless, about 0.16 A; USB or 2-pin"),
    "hook-and-loop strap 20 mm": (1, 3, "for the defender dock"),
    "breakaway tether clip": (1, 3, "parts at a few newtons; for the dock and ID pouch eyelets"),
}


def kit_purchases(kit):
    mods = KITS[kit]["modules"]
    items = defaultdict(int)
    items["foam seat pads"] = 1
    items["flexible adhesive"] = 1
    if "pod" in mods:
        for k in ("protected pouch cell 3.7 V ~4000 mAh", "USB-C charge and 5 V boost board", "resettable fuse 2 A, slide switch, JST plug",
                  "LED strip 5 V COB, 8 mm, per metre", "PWM dimmer or MOSFET driver", "wire, heat shrink, solder"):
            items[k] = 1
        items["M2 x 6 self-tapping screws (8)"] = 1
    if "fan" in mods:
        items["80 x 80 x 15 mm 5 V fan"] = 1
        items["M2 x 6 self-tapping screws (8)"] = 1
    if "dock" in mods:
        items["hook-and-loop strap 20 mm"] = 1
        items["breakaway tether clip"] = 1
    if "id" in mods:
        items["breakaway tether clip"] = 1
    return items


def kit_prints(parts, kit):
    """Printed grams per material for this kit, from the full-kit parts table."""
    mods = KITS[kit]["modules"]
    leds = "pod" in mods
    grams = defaultdict(float)
    for name, (shape, material, fill, note) in parts.items():
        if name.endswith("coupon"):
            continue
        if name.startswith("flat_skin") or name.startswith("hoop_lip"):
            pass
        elif name.startswith("hoop_bar_"):
            if name.removeprefix("hoop_bar_") not in mods:
                continue
        elif name.startswith("diffuser_fitted"):
            if not leds:
                continue
        elif name == "module_pod_lid":
            if not leds:
                continue
        elif name == "module_fan_guard":
            if "fan" not in mods:
                continue
        elif name.startswith("module_"):
            if name.removeprefix("module_") not in mods:
                continue
        grams[material] += shape.val().Volume() / 1000 * build.P["density_g_cc"] * fill
    return grams


def main():
    parts = print_plan.parts()
    strip_mm = 2 * power.strip_length()
    strip_metres = max(1, math.ceil(strip_mm / 1000))
    rows = []
    out = [f"# Bill of materials and rough cost (size {build.SIZE})", "",
           f"The LED strip for size {build.SIZE} is about {strip_mm:.0f} mm in two halves, so buy {strip_metres} m. " + "Prices are my estimates in US dollars, anchored on a few listings seen in October 2026. They are not quotes, they exclude shipping, tax and tools, and they swing a lot by seller and country. Check every line before buying. Printed masses come from the CAD; the filament line adds a 25% allowance for supports, purge and a failed print.", ""]
    for kit in KITS:
        grams = kit_prints(parts, kit)
        items = kit_purchases(kit)
        fil_lo = sum(g * WASTE / 1000 * FILAMENT[m][0] for m, g in grams.items())
        fil_hi = sum(g * WASTE / 1000 * FILAMENT[m][1] for m, g in grams.items())
        if "LED strip 5 V COB, 8 mm, per metre" in items:
            items["LED strip 5 V COB, 8 mm, per metre"] = strip_metres
        qty = lambda k, n: n if k == "LED strip 5 V COB, 8 mm, per metre" else 1
        buy_lo = sum(PARTS[k][0] * qty(k, n) for k, n in items.items())
        buy_hi = sum(PARTS[k][1] * qty(k, n) for k, n in items.items())
        rows.append((kit, KITS[kit]["modules"], grams, fil_lo, fil_hi, buy_lo, buy_hi, items))
    out += ["## Cost per kit", "", "Filament is shown pro rata for the grams used. Add the spool minimum: you buy 1 kg of each material, so the first build costs more (see below).", "",
            "| Kit | Modules | Printed g | Filament USD | Parts USD | Total USD |", "|---|---|---|---|---|---|"]
    for kit, mods, grams, fl, fh, bl, bh, _ in rows:
        total_g = sum(grams.values())
        out.append(f"| {kit} | {', '.join(mods) or 'none'} | {total_g:.0f} | {fl:.0f}-{fh:.0f} | {bl:.0f}-{bh:.0f} | {fl + bl:.0f}-{fh + bh:.0f} |")
    spool_lo = FILAMENT["TPU 95A"][0] + FILAMENT["PETG"][0] + FILAMENT["PETG (natural)"][0]
    spool_hi = FILAMENT["TPU 95A"][1] + FILAMENT["PETG"][1] + FILAMENT["PETG (natural)"][1]
    out += ["", f"First build, buying whole spools (1 kg TPU, 1 kg PETG, 1 kg natural PETG for the cover): **{spool_lo}-{spool_hi} USD** for filament alone, then the parts column above. A second kit costs only the grams.", ""]
    out += ["## Printed parts by kit (grams, before the 25% allowance)", "", "| Kit | TPU 95A | PETG | natural PETG |", "|---|---|---|---|"]
    for kit, mods, grams, *_ in rows:
        out.append(f"| {kit} | {grams.get('TPU 95A', 0):.0f} | {grams.get('PETG', 0):.0f} | {grams.get('PETG (natural)', 0):.0f} |")
    out += ["", "## Purchased parts", "", "| Part | Per unit (USD) | Notes |", "|---|---|---|"]
    for name, (lo, hi, note) in PARTS.items():
        out.append(f"| {name} | {lo}-{hi} | {note} |")
    out += ["", "## Which kit needs what", "", "| Part | " + " | ".join(r[0] for r in rows) + " |", "|---|" + "---|" * len(rows)]
    for name in PARTS:
        cells = []
        for r in rows:
            n = r[7].get(name, 0)
            cells.append(str(n) if n else "-")
        out.append(f"| {name} | " + " | ".join(cells) + " |")
    out += ["", "## Tools and test gear (once)", "",
            "- Soldering iron, multimeter, calipers, flush cutters, sandpaper and a deburring tool.",
            "- A spring scale (to measure the front opening force and pull-test the bars).",
            "- A fire-safe LiPo charging bag or box, for every charge and for the bench test.",
            "- A printer that prints TPU 95A reliably (direct drive helps) and PETG, with at least a 220 mm bed (size XL needs about 235 mm).", "",
            "## Price anchors I looked at (October 2026, not quotes)", "",
            "- 3.7 V 4000 mAh protected pouch cells: about 10-23 EUR across [OpenELAB](https://openelab.io/a/s/products/openelab-805080-4000mah-polymer-lithium-battery), [Soldered](https://soldered.com/products/li-ion-battery-4000mah-3-7v) and [Melopero](https://www.melopero.com/?p=185001). Check that the cell has a protection circuit.",
            "- 5 V COB LED strip, 8 mm: marketplace listings from about 1 to 6 USD per metre before shipping; one retail listing was over 40 GBP for a metre. See the [ManoMano listing](https://www.manomano.co.uk/p/cob-led-strip-320-leds-m-flexible-8mm-cuttable-5v-usb-for-tv-cabinet-bedroom-227965546).",
            "- TPU 95A: about 21 GBP per kg ([eSUN via YPC](https://www.ypc.co.uk/product/esun-tpu-95a-filament-1-75mm-flexible-3d-printer-filament-1kg-2-2-lbs-black/)); PETG about 12-21 USD per kg on Amazon and Elegoo listings.",
            "- 80 mm 8015 5 V fans: about 3-9 USD each depending on seller and connector.", "",
            "## What this does not include", "",
            "The printer, your time, shipping, tax, a spare for each part you will break while tuning, and anything for selling it (certification, insurance, packaging, support). Test prints and failures usually double the filament cost of the first kit."]
    name = "BOM.md" if build.SIZE == "M" else f"BOM_{build.SIZE}.md"
    (build.ROOT / name).write_text("\n".join(out) + "\n")
    print("\n".join(out[:20]))


if __name__ == "__main__":
    main()
