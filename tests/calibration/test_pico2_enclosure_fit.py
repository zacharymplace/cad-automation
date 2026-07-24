import cadquery as cq

from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    build_pico2_enclosure_fit,
)


def test_enclosure_fit_is_valid() -> None:
    model = build_pico2_enclosure_fit(Pico2EnclosureFitParameters())

    assert isinstance(model, cq.Workplane)
    assert model.val().isValid()
    assert model.val().Volume() > 0
