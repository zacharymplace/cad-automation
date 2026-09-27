# Validation catalog coverage

The local runner uses `validation-catalog.example.json`: 43 explicit designs
across 28 generator types, expanded from three starter designs.
The existing policy is unchanged: five geometry checks and build-volume checks
are required, and warnings fail acceptance. The configured printer remains
Prusa MK4. Failures must be investigated, not removed merely to make CI pass.

This inventory is based on the repository scan supplied on 2026-09-26.
Generation and policy acceptance of the expanded catalog still require a local run.
No CAD exports are written by catalog validation.

## Included designs and declared-parameter coverage

The listed parameter names are recognized by the current generic profile rules.
A listed name means applicable, not passed. Other parameter names, including
`wall_mm` and `floor_thickness`, are not measured or validated by these rules.
The shared policy does not require `declared_parameters`; geometry and build
volume remain required for every design. Family-specific rules remain future work.

| Design | Generator | Recognized declared parameters |
| --- | --- | --- |
| `calibration/default-fit-coupon.json` | `fit_coupon` | None |
| `calibration/default-tolerance-coupon.json` | `tolerance_coupon` | `label_height`, `label_size` |
| `calibration/display-window-coupon.json` | `display_window_coupon` | None |
| `calibration/enclosure-fit-test.json` | `enclosure` | `floor`, `label_height`, `label_size`, `lid_clearance`, `wall` |
| `calibration/insert-boss-coupon.json` | `insert_boss_coupon` | None |
| `calibration/pico2-enclosure-fit.json` | `pico2_enclosure_fit` | None |
| `calibration/pico2-mount-coupon.json` | `pico2_mount_coupon` | None |
| `electronics/default-enclosure.json` | `enclosure` | `floor`, `label_height`, `label_size`, `lid_clearance`, `wall` |
| `example-tray.json` | `tray` | `floor`, `wall` |
| `gifts/coaster-p1.json` | `pixel_coaster` | None |
| `gifts/coaster-p2.json` | `pixel_coaster` | None |
| `gifts/creeper-block-planter.json` | `pixel_block_planter` | `floor`, `wall` |
| `gifts/extra-life-planter.json` | `pixel_heart_planter` | `floor`, `label_height`, `label_size`, `wall` |
| `gifts/gamepad-coaster.json` | `pixel_coaster` | None |
| `gifts/headphone-hook.json` | `pixel_hook` | None |
| `gifts/music-note-coaster.json` | `pixel_coaster` | None |
| `gifts/photo-stand.json` | `pixel_photo_stand` | None |
| `gifts/pixel-garden-module.json` | `pixel_garden_module` | `floor`, `wall` |
| `gifts/plant-marker-basil.json` | `pixel_plant_marker` | `label_height`, `label_size` |
| `gifts/plant-marker-chili.json` | `pixel_plant_marker` | `label_height`, `label_size` |
| `gifts/plant-marker-mint.json` | `pixel_plant_marker` | `label_height`, `label_size` |
| `gifts/plant-marker-tomato.json` | `pixel_plant_marker` | `label_height`, `label_size` |
| `gifts/player-two-planter.json` | `pixel_heart_planter` | `floor`, `label_height`, `label_size`, `wall` |
| `gifts/ring-dish.json` | `pixel_ring_dish` | `floor`, `wall` |
| `gridfinity/compatibility-fit-coupon.json` | `gridfinity_fit_coupon` | None |
| `gridfinity/empty-bin-1x1.json` | `gridfinity_bin` | `floor`, `wall` |
| `home-bar/garnish-caddy-citrus.json` | `garnish_caddy` | `wall` |
| `home-bar/garnish-caddy.json` | `garnish_caddy` | `wall` |
| `home-bar/jigger-rack.json` | `jigger_rack` | None |
| `oxo-soap-dispenser-drip-tray.json` | `drip_tray` | `wall` |
| `phone-tablet-stand.json` | `phone_stand` | None |
| `sink-sponge-caddy.json` | `sponge_caddy` | `wall` |
| `tattoo/grip-stand-dual.json` | `grip_stand` | None |
| `tattoo/grip-stand-fat-grip.json` | `grip_stand` | None |
| `tattoo/grip-stand.json` | `grip_stand` | None |
| `tattoo/ink-cap-tray-sink-edge.json` | `ink_cap_tray` | `wall` |
| `tattoo/ink-cap-tray-with-mixing-wells.json` | `ink_cap_tray` | `wall` |
| `tattoo/ink-cap-tray.json` | `ink_cap_tray` | `wall` |
| `tattoo/insert-tray.json` | `insert_tray` | None |
| `tattoo/stencil-holder-divided.json` | `stencil_holder` | `wall` |
| `tattoo/stencil-holder-high-capacity.json` | `stencil_holder` | `wall` |
| `tattoo/stencil-holder.json` | `stencil_holder` | `wall` |
| `tattoo/travel-case.json` | `travel_case` | `wall` |

## Excluded schemas

| File | Reason |
| --- | --- |
| `board-display/pico2-oled.example.json` | Registry-driven board-display schema; needs its own validation adapter. |
| `board-display/xiao-esp32s3-oled.example.json` | Registry-driven board-display schema; needs its own validation adapter. |
| `garden-assembly.example.json` | Garden assembly schema; collision/insertion checks use garden-assembly. |
| `garden-bed.json` | Garden assembly schema; collision/insertion checks use garden-assembly. |
| `garden-corner.json` | Garden assembly schema; collision/insertion checks use garden-assembly. |
| `garden-heart.json` | Garden assembly schema; collision/insertion checks use garden-assembly. |
| `validation-catalog.example.json` | Validation configuration, not a CAD design. |
| `validation-policy.example.json` | Validation configuration, not a CAD design. |

Add new designs explicitly after checking schema compatibility. This catalog is
not automatic discovery and does not claim complete repository or manufacturing
coverage. Preserve ERROR/FAIL results from the first expanded run for diagnosis.
