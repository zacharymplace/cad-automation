# Safety review: festival-yoke (size M, full kit)

This is a design review done before anything is built. It finds hazards and says what the design does about each, what it does not, and what has to be tested before anyone wears it. It is not a certification, and nothing here has been printed, assembled or tested. Geometry numbers come from `safety.py`, `strength.py`, `balance.py` and `donning.py`.

## Do not wear it until these pass

1. **The battery system is built and bench-tested off the body** (section A). No cell or board has been chosen yet.
2. **A pull test on every glued bar and lip** at several times the module's weight. The strength check puts the glue joint at a safety factor of 1.8 at a 5 g bump with the 20 mm flange: that is not much margin, and the adhesive figure is an assumption.
3. **Every printed edge a person or a neighbour can touch is deburred.** The CAD kernel crashed trying to round the modules' edges, so modules have sharp box edges (see B4).
4. **The LED firmware cannot flash.** Steady light or a slow fade only (A3).
5. **Hot drinks are not carried in the cup cradle** unless it has a lid (B6).

## Hazards

Severity is the worst plausible outcome; "open" means the design does not close the risk by itself.

### A. Battery and electronics

| # | Hazard | How it happens | Severity | What the design does | Open |
|---|---|---|---|---|---|
| A1 | Lithium cell fire or thermal runaway | Puncture, crush, short circuit, overcharge, heat, a bad cell | High | The pod sits behind the neck, 100 mm from the neck axis (44 mm from the neck's surface), with its lowest point 14 mm below the neck edge and its top 16 mm above it. The tray is a rigid PETG box with a screwed lid. | **Open.** No cell or board chosen. Use a protected pouch cell (built-in protection circuit) and a boost board with overcurrent and short-circuit protection, add a 2 A resettable fuse in the cell lead, never charge it inside the collar or while worn, and charge in a fire-safe bag. PETG softens at about 70-80 C and is flammable: it is not a fire barrier. |
| A2 | Water ingress | Rain, a spilled drink, sweat. The lid is vented, so it is not sealed. | Medium | Pod is at the back, away from the cup at the front. | **Open.** No ingress rating. Do not wear it in heavy rain; consider a drip lip on the lid and conformal-coated boards. |
| A3 | Photosensitive seizure | An LED strip flashing at 3-30 Hz, or strobing patterns, in a festival crowd | High for the few it affects | None yet: no firmware exists. | **Open.** Rule: steady light or a fade slower than 1 Hz, no strobe or chase effects, with a brightness cap. Others in the crowd can be affected, not just the wearer. |
| A4 | Short circuit, chafed leads | Loose wiring in the channel, leads through the pod floor slots | Medium | Two lead slots in the pod floor feed the channel; the strip is 5 V. | **Open.** Add strain relief and insulate every joint. |
| A5 | Heat on skin | Pod or strip warm against the neck, back or arm | Low | The pod is 44 mm off the neck's surface; the strip lies in the channel under a cover, away from skin. | Measure the pod's surface temperature in the bench run. |

### B. Mechanical, crowd and fit

| # | Hazard | How it happens | Severity | What the design does | Open |
|---|---|---|---|---|---|
| B1 | Protrusions hit other people | Modules stand out from the collar edge: **dock 119 mm, cup 106 mm, phone 64 mm, ID 34 mm, fan 40 mm, pod 19 mm** (full kit, beyond the collar rim). In a crush these are hard plastic at chest and hip height. | Medium | Nothing rises above the shoulder line except the fan, at jaw height (98 mm above the neck edge), so nobody's view is blocked. The core and glow kits have no side protrusions. | **Open.** The dock and cup are the worst. Bumpers in soft TPU, a smaller cup ring, or fitting them only in low-crowd use. Modules cannot pop off sideways: they only slide along the bar. |
| B2 | Snagging and strangulation | A bag strap, a tether, a hydration tube or a lanyard catching on the collar and pulling it | High | The collar is an open C with a 70 mm front gap and 30-39 mm of clearance all round the neck, so it cannot close on the neck. Pulling from the back lifts it clear. | **Open.** The ID pouch and the dock have tether eyelets and the tube clip holds a hydration tube. Any tether must be a breakaway (a clip that parts at a few newtons), and the tube must not be looped around the neck. |
| B3 | Fan: fingers, hair | Fingers or loose hair reaching the blades. The fan sits at jaw height. | Medium | Grid guards on both faces: 7.4 mm gaps, too small for a finger or a hair bundle to reach the blades. The outlet guard is screwed on. | Confirm the fan's stall current is safe and keep loose hair away from the intake. |
| B4 | Sharp edges | Printed modules have sharp box edges. The CAD kernel crashed trying to round them. The skin and cover edges are rounded or thin-wall TPU. | Low to medium | Skin edges rounded (0.6 mm). | **Open.** Deburr and chamfer every module edge by hand, or add a printed fillet to the model. |
| B5 | Pinch points | Fan frame corners, bowl rim, the clip sliding on its bar | Low | The clip's slot has 0.3 mm of slack each side: no finger gap. | Check by hand in the first print. |
| B6 | Falling objects and hot drinks | A cup, phone or defender dropping from chest height. A hot drink spilling at the chest or onto a neighbour. | Medium (scald) | The cup ring's open side lets the cup slide out, and the bar holds modules from lifting off. | **Open.** The ring is not a lid. Carry cold drinks only unless the cup has a lid. The phone cradle's snap-in is not tested. |
| B7 | Glued parts coming off | A heavy module peels its bar off the skin | Medium | 30 mm wide glue flange on each bar plus two barbed locating pegs that snap through holes in the skin. | **Open.** Pull test (above). Simulated failure is about 3% a season on central assumptions and still above 20% if the glue is half as strong: measure it, and fall back to a screwed backing plate if it is weak. |
| B8 | Printed-part failure | A cup or dock arm snapping under a bump | Medium | Arm thickness raised to 11 mm: 5 g safety factor 4.5 on the cup arm, 6.3 on the dock arm (hand calculation). | Verify in the load test; layers are the weak direction. |

### C. Body, comfort and materials

| # | Hazard | How it happens | Severity | What the design does | Open |
|---|---|---|---|---|---|
| C1 | Load on neck and shoulders | Up to 1.4 kg loaded (full kit) on the trapezius | Low to medium | Four foam seats spread the load: about 4.5 kPa at full load, under typical backpack-strap pressure. The load stays inside the foam-seat rectangle (36 mm margin, full kit). | The carry kit is on the edge (3 mm margin with a full cup): a full cup pitches it forward. Limit wearing time and ask about neck or shoulder conditions. |
| C2 | Skin contact and allergy | TPU and PETG against skin, adhesive residue | Low | Foam seats under the skin; no metal on the skin side. | Cure adhesive fully and keep it off skin. Use a skin-safe filament if possible. |
| C3 | Heat | Dark plastic in direct sun, PETG softening in a hot car | Low | None. | Do not leave it in a hot car or direct sun. |
| C4 | Hearing | The fan is noisy next to the ear. The defender dock only parks defenders: it is not hearing protection. | Low | Dock keeps defenders at hand. | State clearly that the dock is storage. |
| C5 | Seating and mobility aids | The pod sits 17 mm behind the collar rim and rises 16 mm above the neck edge. Backrests, headrests, car seats or a wheelchair joystick may not clear it. | Low to medium | Core kit has no rear module. | **Open.** Test with the actual wheelchair or seat, and take the collar off to lie back. |
| C6 | Putting on and taking off | Weak grip or limited reach | Medium | Open-front C needs only about 2-3 N per front tip to spread by 45 mm (estimate), and modules slide onto bars with about 5 N. | Measure the spread force with a spring scale. |

### D. Not covered here

- **Small parts and age.** The spring plungers, screws and diffuser pieces are choking hazards. Not for children.
- **Selling it.** Selling a wearable with a battery brings product-safety, electrical and battery-transport rules (UN 38.3 for the cell), labelling and liability. Get proper advice before any sale.
- **Real users.** Nobody has tried it. The people it is for need to test it, with their own mobility aids, seating and routines. That matters more than anything above.

## Before-wear test list (in order)

1. Bench-test the pod: cell, board, strip and fan on a bench for an hour in a fire-safe container, watching temperature, and short-circuit it deliberately behind the fuse.
2. Pull-test each bar and lip at 5 times its module's weight.
3. Spring-scale the front opening force and the clip push force.
4. Deburr everything; run a finger and a cloth over every edge.
5. Drop test the phone and cup cradles over a soft surface.
6. Wear the bare collar for ten minutes, then the glow kit, then add one module at a time.
7. Only then the full kit, and only with someone else watching the first time.
