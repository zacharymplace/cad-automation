# Pico 2 USB cable plug geometry

The cable plug is optional in Pico enclosure design JSON under
`parameters.usb_plug`. If omitted, the acceptance report keeps plug fit and
insertion as NOT_CHECKED while retaining the Pico receptacle envelope check.

Example structure (all dimensions in millimeters):

```json
"usb_plug": {
  "identifier": "maker-and-cable-part-number",
  "width_mm": 12.5,
  "height_mm": 5.8,
  "housing_length_mm": 12.0,
  "center_height_offset_mm": 0.0,
  "clearance_mm": 0.3,
  "nose_width_mm": 8.2,
  "nose_height_mm": 2.8,
  "nose_length_mm": 5.0,
  "nose_center_height_offset_mm": 0.0,
  "evidence_status": "measured",
  "evidence_source": "manufacturer drawing URL/revision or measurement record"
}
```

Measure the cable's molded housing width and height at its widest/thickest point,
and its length from the cable exit face to the connector-facing shoulder. Record
housing-center offset relative to the metal nose center. Measure the mating nose
width and height, projection from the housing shoulder to the tip, and its
vertical offset relative to the housing center. Measure the fit clearance per
side for the print process; when unknown, label the chosen value as an untested
assumption and calibrate it physically. Keep strain relief and cable bend radius
as separate measurements; this geometry does not model the flexible cable.

`evidence_status` is `measured`, `vendor_drawing`, or `test_envelope`; the source
string is descriptive and is not independently authenticated. Check the cable's
connector orientation and board port before using the negative-Y path in this
Pico fixture. Nose length must reach from the enclosure's outside wall to the
modeled receptacle face. A nose that is too short is rejected.

The acceptance report represents the overmold as a box outside the wall and its
mating nose as a narrower box through the wall. It enlarges the port opening to
fit the nose plus clearance, then checks the seated overmold, nose-to-receptacle
engagement, wall and component interference, and continuous straight insertion
sweep. The USB receptacle overlap is intentional at the seated nose; the nose
must stay within its modeled width/height bounds. A pass covers these rectangular
nominal envelopes. It does not cover chamfers, latch details, cable bend, flex,
sideways/angled insertion, manufacturing variation, or a real measured cable.

Use the synthetic fixture to exercise the workflow, not to identify a cable:
`designs/calibration/pico2-oled-clips-usb-test-envelope.json` declares
`test_envelope` geometry and says it has not been measured. The cable bend check
will remain NOT_CHECKED until a bend envelope is explicitly modeled.
