"""Monte Carlo economics and reliability for festival-yoke: what it costs to make, what it would have to sell for, how many
units that takes, and whether the open technical risks are worth testing. Every distribution below is an ASSUMPTION
(labelled), not data: the point is to see which assumptions the answer depends on.
Run: uv run --no-project --with numpy python viability.py
"""
import json
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
N = 40000
rng = np.random.default_rng(2026)
RATE = {"TPU": 8.0, "PETG": 16.0, "NAT": 14.0}   # g/h, from print_plan.py


def tri(lo, mode, hi, n=N):
    return rng.triangular(lo, mode, hi, n)


def parse_bom(path):
    """kit -> printed grams per material and the BOM's own filament and parts ranges (USD)."""
    text = path.read_text()
    kits = {}
    for m in re.finditer(r"^\| (core|glow|carry|comfort|full) \| ([^|]*) \| (\d+) \| (\d+)-(\d+) \| (\d+)-(\d+) \| (\d+)-(\d+) \|", text, re.M):
        kit, mods, g, fl, fh, pl, ph, tl, th = m.groups()
        kits[kit] = dict(modules=[x.strip() for x in mods.split(",") if x.strip() and x.strip() != "none"], printed_g=int(g),
                         fil=(int(fl), int(fh)), parts=(int(pl), int(ph)))
    for m in re.finditer(r"^\| (core|glow|carry|comfort|full) \| (\d+) \| (\d+) \| (\d+) \|$", text, re.M):
        kit, t, p, nat = m.groups()
        kits[kit]["g"] = dict(TPU=int(t), PETG=int(p), NAT=int(nat))
    return kits


def unit_cost(k, price, size_label, lev=None):
    """Per-unit cost distribution for one kit at a selling price. Returns dict of arrays (USD)."""
    lev = lev or {}
    g = k["g"]
    hours = g["TPU"] / RATE["TPU"] + g["PETG"] / RATE["PETG"] + g["NAT"] / RATE["NAT"]
    mods = len(k["modules"])
    has_pod = "pod" in k["modules"]
    # print and yield (assumption: beta-distributed; mean about 12% of prints fail, range 5-30%)
    p_fail = rng.beta(2.2, 16, N).clip(0.03, 0.4)
    qa_scrap = rng.beta(2, 22, N).clip(0.02, 0.3)       # about 8% of assembled units are scrapped or heavily reworked
    redo = 1 / ((1 - p_fail) * (1 - qa_scrap))
    machine_rate = tri(1.5, 3.0, 5.0) * lev.get("machine", 1.0)                    # USD/h, from the FDM costing guides found (1.5-5 EUR/h)
    machine = hours * machine_rate * redo
    jobs = 4 + 1.6 * mods                                 # build plates per unit
    attend = jobs * 0.12 * tri(20, 28, 40)               # 7 minutes per job at the print operator's rate
    # assembly labour minutes (assumption): deburr, form, glue lip and bars, foam, QA; each module and the electronics add time
    minutes = 60 + 14 * mods + (75 if has_pod else 0) + 25
    minutes = minutes * tri(0.7, 1.0, 1.7) * lev.get("minutes", 1.0)
    labour_rate = tri(18, 26, 40) * lev.get("wage", 1.0)
    assembly = minutes / 60 * labour_rate * (1 / (1 - qa_scrap))
    support = 0.3 * labour_rate                           # warranty and customer service, hours per unit
    filament = tri(k["fil"][0], k["fil"][0] + 0.4 * (k["fil"][1] - k["fil"][0]), k["fil"][1]) * redo
    parts = lev.get("parts", 1.0) * tri(k["parts"][0], k["parts"][0] + 0.4 * (k["parts"][1] - k["parts"][0]), k["parts"][1]) * (1 / (1 - qa_scrap))
    packaging = tri(3, 5, 9)
    shipping = tri(9, 14, 30) * lev.get("ship", 1.0)
    cac = tri(10, 30, 90) * lev.get("cac", 1.0)                                 # paid customer acquisition per sale, niche product
    returns_rate = tri(0.03, 0.08, 0.18) * lev.get("returns", 1.0)
    base = filament + machine + attend + assembly + support + parts + packaging
    returns = returns_rate * (base + 2 * shipping)
    fee = 0.029 * price + 0.30
    variable = base + shipping + returns + fee + cac
    return dict(hours=hours, minutes=minutes, filament=filament, machine=machine, labour=attend + assembly + support, parts=parts,
                packaging=packaging, shipping=shipping, returns=returns, fee=fee, cac=cac, variable=variable, make=base)


def fixed_cost(k):
    """Annual fixed cost (USD): insurance, testing amortised over 3 years, web, tools, accounts. ASSUMPTIONS, not researched."""
    electronics = "pod" in k["modules"]
    base = tri(3000, 5500, 9000)                          # web shop, accounts, storage, tool consumables, basic liability cover
    extra = tri(2500, 6000, 15000) if electronics else tri(0, 800, 2500)   # product liability for a battery wearable, EMC/LVD and safety testing amortised
    return base + extra


def pct(a, q): return float(np.percentile(a, q))


def sensitivity():
    kits = parse_bom(ROOT / "BOM.md")
    scenarios = [
        ("baseline (assumptions above)", {}),
        ("assembly time halved (design for assembly)", {"minutes": 0.5}),
        ("labour cost halved (cheap local labour or your own time at half value)", {"wage": 0.5}),
        ("machine time halved (own printers, fully written off)", {"machine": 0.5}),
        ("no paid ads: acquisition cost cut to 30% (community, partners, word of mouth)", {"cac": 0.3}),
        ("shipping 30% cheaper", {"ship": 0.7}),
        ("parts 30% cheaper (bulk buying, 100+ units)", {"parts": 0.7}),
        ("returns halved", {"returns": 0.5}),
        ("all of the above together (a lean operation)", {"minutes": 0.5, "wage": 0.5, "machine": 0.5, "cac": 0.3, "ship": 0.7, "parts": 0.7, "returns": 0.5}),
        ("sold as a self-assembly kit (assembly time x0.3, returns x1.4, no QA scrap on assembly)", {"minutes": 0.3, "returns": 1.4}),
    ]
    print("\n================ what moves the price (size M): median price to cover variable cost / price for a 40% margin ================")
    print(f"{'scenario':<92}{'core':>12}{'full':>14}")
    rows = {}
    for label, lev in scenarios:
        cells = []
        for kit in ("core", "full"):
            vv = unit_cost(kits[kit], 200, "M", lev)
            nofee = vv["variable"] - vv["fee"]
            p0 = (nofee + 0.30) / (1 - 0.029)
            p40 = (nofee + 0.30) / (1 - 0.029 - 0.40)
            cells.append((pct(p0, 50), pct(p40, 50)))
        rows[label] = cells
        print(f"{label:<92}{cells[0][0]:>5.0f}/{cells[0][1]:<5.0f}{cells[1][0]:>7.0f}/{cells[1][1]:<5.0f}")
    return rows


def lean_breakeven():
    """Break-even volumes for a lean operation at plausible prices."""
    kits = parse_bom(ROOT / "BOM.md")
    lev = {"minutes": 0.5, "wage": 0.5, "machine": 0.5, "cac": 0.3, "ship": 0.7, "parts": 0.7, "returns": 0.5}
    print("\n================ a lean operation: break-even units per year (size M) ================")
    for kit, prices in (("core", (149, 199, 249)), ("glow", (249, 299, 349)), ("full", (399, 499, 599))):
        F = fixed_cost(kits[kit])
        for price in prices:
            vv = unit_cost(kits[kit], price, "M", lev)
            margin = price - vv["variable"]
            be = np.where(margin > 0, F / np.maximum(margin, 1e-9), np.inf)
            ok = np.isfinite(be)
            print(f"  {kit:<5} at {price}: margin per unit median {pct(margin, 50):5.0f}; P(margin>0) {float((margin > 0).mean()) * 100:3.0f}%; break-even units/yr median {pct(be[ok], 50) if ok.any() else math.inf:>7,.0f} (p90 {pct(be[ok], 90) if ok.any() else math.inf:,.0f})")


def digital_model():
    """Selling the design files, instructions and a parts list: no stock, no labour, no shipping (ASSUMPTIONS)."""
    print("\n================ selling the files and instructions instead (no stock) ================")
    for price in (19, 29, 49, 79):
        support = tri(0.25, 0.5, 1.2) * tri(18, 26, 40)           # support hours per sale
        cac = tri(5, 15, 45)
        fee = 0.029 * price + 0.30
        refunds = tri(0.03, 0.07, 0.15) * price
        margin = price - fee - cac - support - refunds
        fixed = tri(1500, 3000, 6000)                              # hosting, docs, a bit of testing and insurance
        be = fixed / np.maximum(margin, 1e-9)
        be = np.where(margin > 0, be, np.inf)
        print(f"  price {price:>3}: margin per sale median {pct(margin, 50):5.1f} (p10 {pct(margin, 10):5.1f}); P(margin>0) {float((margin > 0).mean()) * 100:3.0f}%; break-even sales per year median {pct(be[np.isfinite(be)], 50) if np.isfinite(be).any() else math.inf:,.0f}")


def main():
    sensitivity()
    lean_breakeven()
    digital_model()
    out = {}
    for size, fn in (("M", "BOM.md"), ("XXL", "BOM_XXL.md")):
        kits = parse_bom(ROOT / fn)
        print(f"\n================ size {size} ================")
        print(f"{'kit':<8}{'print h':>8}{'make cost':>11}{'landed var. cost (at $150/$250 price)':>40}{'':>2}")
        for name, k in kits.items():
            r = unit_cost(k, 150, size)
            mk = r["make"]
            print(f"{name:<8}{r['hours']:>8.0f}{pct(mk, 50):>7.0f} ({pct(mk, 10):.0f}-{pct(mk, 90):.0f}){pct(unit_cost(k, 150, size)['variable'], 50):>14.0f}{pct(unit_cost(k, 250, size)['variable'], 50):>12.0f}")
        out[size] = {}
        for name, k in kits.items():
            F = fixed_cost(k)
            rows = []
            for price in (79, 99, 129, 159, 199, 249, 299, 399):
                v = unit_cost(k, price, size)
                margin = price - v["variable"]
                units_be = np.where(margin > 0, F / np.maximum(margin, 1e-9), np.inf)
                share_pos = float((margin > 0).mean())
                rows.append((price, pct(v["variable"], 50), pct(margin, 50), share_pos, pct(units_be[np.isfinite(units_be)], 50) if np.isfinite(units_be).any() else math.inf,
                             pct(units_be[np.isfinite(units_be)], 90) if np.isfinite(units_be).any() else math.inf))
            out[size][name] = dict(fixed_median=pct(F, 50), fixed_p10=pct(F, 10), fixed_p90=pct(F, 90), rows=rows)
            # price needed for a 40% contribution margin after all variable costs (CAC and fees included): solve per draw
            need = []
            vv = unit_cost(k, 200, size)
            nofee = vv["variable"] - vv["fee"]
            price40 = (nofee + 0.30) / (1 - 0.029 - 0.40)
            price0 = (nofee + 0.30) / (1 - 0.029)
            out[size][name]["price_breakeven_per_unit"] = (pct(price0, 10), pct(price0, 50), pct(price0, 90))
            out[size][name]["price_40pct_margin"] = (pct(price40, 10), pct(price40, 50), pct(price40, 90))
            print(f"\n{name}: fixed cost per year median {pct(F, 50):,.0f} (p10 {pct(F, 10):,.0f}, p90 {pct(F, 90):,.0f}); price to cover variable cost alone {pct(price0, 50):.0f} ({pct(price0, 10):.0f}-{pct(price0, 90):.0f}); price for a 40% contribution margin {pct(price40, 50):.0f} ({pct(price40, 10):.0f}-{pct(price40, 90):.0f})")
            print(f"   {'price':>6}{'var cost':>10}{'margin':>9}{'P(margin>0)':>13}{'break-even units/yr: median':>30}{'p90':>8}")
            for price, vc, m, ps, ubm, ub9 in rows:
                print(f"   {price:>6}{vc:>10.0f}{m:>9.0f}{ps * 100:>12.0f}%{ubm:>30,.0f}{ub9:>8,.0f}")
    json.dump(out, open(ROOT / "viability_results.json", "w"), indent=1, default=lambda x: x if not isinstance(x, float) or math.isfinite(x) else None)

    # reliability: the bar's glue joint under random peaks, for design variants
    print("\n================ reliability of the glued bar (cup, 402 g at 91 mm) ================")
    mass, lever = 0.402, 0.091
    peaks = rng.lognormal(math.log(1.3), 0.755, N)         # peak g in a season: median 1.3 g, 95th percentile 4.5 g (ASSUMPTION)
    for label, flange, strength_med, cv in (("20 mm flange, flexible adhesive (current)", 20, 2.0, 0.35),
                                              ("20 mm flange, adhesive scatter 50%", 20, 2.0, 0.5),
                                              ("30 mm flange", 30, 2.0, 0.35),
                                              ("20 mm flange + 2 pegs (strength x1.8)", 20, 3.6, 0.35),
                                              ("30 mm flange + 2 pegs", 30, 3.6, 0.35)):
        strength = rng.lognormal(math.log(strength_med), math.sqrt(math.log(1 + cv ** 2)), N)   # N/mm peel
        couple = mass * 9.81 * lever * peaks               # N*m
        line = couple / (flange / 1000) / 80               # N/mm over the 80 mm bar
        pf = float((line > strength).mean())
        # per-unit risk over a season: 30 independent peak events
        season = 1 - (1 - pf) ** 30
        print(f"  {label:<44} P(fail) per peak {pf * 100:5.2f}%   per season of 30 peaks {season * 100:5.1f}%")
    mild = rng.lognormal(math.log(1.0), math.log(3.0 / 1.0) / 1.645, N)     # a gentler season: median 1 g, 95th percentile 3 g
    strength = rng.lognormal(math.log(2.0), math.sqrt(math.log(1 + 0.35 ** 2)), N)
    line = mass * 9.81 * lever * mild / 0.020 / 80
    pf = float((line > strength).mean())
    print(f"  (gentler peaks, 95th percentile 3 g, current 20 mm flange)       P(fail) per peak {pf * 100:5.2f}%   per season of 30 peaks {(1 - (1 - pf) ** 30) * 100:5.1f}%")
    # joint technical success of the staged plan (SUBJECTIVE probabilities)
    print("\n================ stage gates (SUBJECTIVE probabilities, my judgement, not data) ================")
    stages = [("Stage 0-1: flat TPU forms and holds a cone, glue holds 90 N, clip slides, cover snaps", 0.55, 700),
              ("Stage 2: bare collar sits well on a body and goes on one-handed", 0.70, 500),
              ("Stage 3: modules work under load and survive handling", 0.80, 1500),
              ("Stage 4: battery system passes a bench test and the safety list", 0.85, 1200)]
    cum = 1.0
    spent = 0.0
    commit = tri(14000, 22000, 40000)                      # inventory, testing, tooling, launch if you commit before knowing
    print(f"  commitment cost if you launch (testing, insurance set-up, tooling, first inventory): median {pct(commit, 50):,.0f} (p10 {pct(commit, 10):,.0f}, p90 {pct(commit, 90):,.0f})")
    for text, p, cost in stages:
        cum *= p
        spent += cost
        print(f"  {text:<86} p={p:.2f}  cumulative {cum:.2f}  cost {cost:>5,} (running total {spent:,.0f})")
    p1 = stages[0][1]
    total_dev = sum(c for _, _, c in stages)
    print(f"  Expected loss avoided by running Stage 1 before committing: {(1 - p1) * pct(commit, 50):,.0f} against a Stage 1 cost of {stages[0][2]:,}")
    print(f"  Chance the whole thing works as designed (product of the four): {cum * 100:.0f}%")


if __name__ == "__main__":
    main()
