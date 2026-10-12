"""Hand-calculation strength checks for the parts that carry load or flex. These are first estimates from beam
formulas, not FEA: they find the weak spots worth redesigning before anything is printed.
Run: uv run --no-project --with cadquery strength.py
"""
import math

import balance
import build
import layout
import module
import power

G = 9.81
SHOCK = 5.0   # g, a crowd bump or a stumble; sustained load is 1 g

# material assumptions (printed, along the layers unless noted): conservative, check your filament's datasheet
PETG_YIELD = 40.0        # MPa, tension along layers
PETG_ZBOND = 20.0        # MPa, across layers
PETG_SNAP_STRAIN = 0.035  # permissible one-off flex strain for a snap hook
TPU_YIELD = 8.0          # MPa, 95A, practical working stress before large creep
SCREW_PULLOUT = 100.0    # N, M3 self-tapping into 5 mm of printed PETG wall (rough)


def sf(allow, stress):
    return float("inf") if stress == 0 else allow / stress


def main():
    printed, fixed, local, pay_l, strip_com = balance.setup()
    rows = []   # name, load g, lever mm, critical section, stress MPa, allowable MPa, note

    def beam(name, payload_g, printed_g, lever, w, t, note):
        F = (payload_g + printed_g) / 1000 * G
        Z = w * t * t / 6
        stress = F * lever / Z
        rows.append((name, payload_g + printed_g, lever, f"{w:g} x {t:g} mm beam", stress, PETG_ZBOND, note))

    arm_w = 20
    for n, pay in balance.PAYLOAD.items():
        if n not in local:
            continue
        g, lc = local[n]
        lever = abs(pay_l.get(n, lc)[0])
        arm_t = module.ARM_T if n in ("cup", "dock") else 8
        beam(f"{n} arm", pay, g, lever, arm_w, arm_t, "arm root, bending across layers is the weak direction")
    cup_post = (10, 14)
    g, _ = local.get("cup", (0, None))
    if "cup" in local:
        beam("cup post", balance.PAYLOAD["cup"], g, module.CUP_ID / 2 + module.WALL, *sorted(cup_post), "post root")

    print(f"{'part':<14}{'load g':>7}{'lever':>7}  {'section':<18}{'stress MPa':>11}{'SF 1 g':>8}{'SF 5 g':>8}")
    worst = 1e9
    for name, load, lever, section, stress, allow, note in rows:
        a, b = sf(allow, stress), sf(allow, stress * SHOCK)
        worst = min(worst, b)
        print(f"{name:<14}{load:>7.0f}{lever:>6.0f}  {section:<18}{stress:>11.2f}{a:>8.1f}{b:>8.1f}")

    # docking bar: the couple from the heaviest load tries to lift the inner edge of the clip against the bar's cap and
    # peel the bar's flange off the skin
    heavy = max(((n, pay + local[n][0], abs(pay_l.get(n, local[n][1])[0])) for n, pay in balance.PAYLOAD.items() if n in local), key=lambda r: r[1] * r[2], default=None)
    if heavy:
        import dock
        n, load, lever = heavy
        M = load / 1000 * G * lever / 1000                        # N*m about the bar line
        width = dock.FLANGE_W                                      # the bar's flange width, mm: the peel force is the couple over this lever
        F = M / (width / 1000)                                    # N, peeling the bar's inner edge off the skin
        cap_over = (build.R["cap_width"] - build.R["stem_width"]) / 2
        line = F / module.LENGTH                                  # N per mm of clip length on the cap
        Z = build.R["cap_height"] ** 2 / 6
        cap_stress = line * cap_over / Z
        print(f"\ndocking bar under the worst load ({n}, {load:.0f} g at {lever:.0f} mm): couple {M:.2f} N*m, lift force {F:.0f} N")
        print(f"  PETG cap overhang {cap_over:.1f} mm x {build.R['cap_height']} mm: root stress {cap_stress:.2f} MPa at 1 g, {cap_stress * SHOCK:.1f} MPa at {SHOCK:.0f} g (PETG {PETG_YIELD:.0f} MPa: SF {sf(PETG_YIELD, cap_stress * SHOCK):.1f})")
        peel = F / dock.BAR_LENGTH                                # N per mm of bar along the flange edge
        PEEL_STRENGTH = 2.0                                       # N/mm, flexible adhesive on TPU, rough
        print(f"  glue peel line load on the bar's flange: {peel:.2f} N/mm at 1 g, {peel * SHOCK:.2f} N/mm at {SHOCK:.0f} g vs about {PEEL_STRENGTH} N/mm for a flexible adhesive on TPU: SF {sf(PEEL_STRENGTH, peel * SHOCK):.1f} at {SHOCK:.0f} g")
        print("  => the glue joint, not the plastic, is the weak link. Widen the flange, add two locating pegs through the skin per bar, or both")

    # diffuser snap hook: a PETG cantilever pushed out by the bead
    t = build.G["lip_width"] / 2 + 1.5 - (build.G["lip_width"] / 2 + 0.1)   # hook thickness, mm
    L = build.D["hook"]
    defl = build.BEAD_STEP                                        # bead step protrusion, mm
    eps = 3 * defl * t / (2 * L * L)
    print(f"\ndiffuser snap hook: {t} mm thick, {L} mm long, bead {defl} mm: flex strain {eps * 100:.1f}% vs {PETG_SNAP_STRAIN * 100:.1f}% allowed (SF {PETG_SNAP_STRAIN / eps:.1f})")

    # lip groove in the TPU lip
    w = build.G["lip_width"]
    print(f"TPU lip: {w} mm wide, groove {build.SNAP_DEPTH} mm deep leaves {w - build.SNAP_DEPTH:.1f} mm: it compresses rather than breaks, but check for tearing at the groove corners")
    print(f"\nlowest 5 g safety factor on the arms and posts: {worst:.1f} (want >= 2 for printed parts)")


if __name__ == "__main__":
    main()
