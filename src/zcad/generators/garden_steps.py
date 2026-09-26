"""Offline step-through schematics from checked assembly reports."""

from copy import deepcopy
from html import escape
from xml.etree.ElementTree import fromstring, tostring

from zcad.generators.garden_preview import assembly_preview_svg


def assembly_steps_html(report: dict) -> str:
    """Render every checked step; blocked reports never offer playback."""
    base = fromstring(assembly_preview_svg(report))  # Shared report validation.
    for element in base.iter():
        element.tag = element.tag.removeprefix("{http://www.w3.org/2000/svg}")
    base.set("xmlns", "http://www.w3.org/2000/svg")
    order = report["insertion_check"]["assembly_order"]
    passed = report["insertion_check"]["status"] == "PASS"
    frames = []
    for installed_count in range(len(order) + 1 if passed else 1):
        installed = set(order[:installed_count])
        next_name = order[installed_count] if installed_count < len(order) else None
        svg = deepcopy(base)
        mating = set()
        for link in svg.iter():
            if "data-connection" not in link.attrib:
                continue
            ends = {link.get("data-male"), link.get("data-female")}
            active = next_name in ends and bool(ends & installed)
            if active:
                mating.update(ends - {next_name})
            link.set("opacity", "1" if active or ends <= installed else "0.12")
            if active:
                link.set("stroke", "#c04f00")
                link.set("stroke-width", "6")
        for group in svg.iter():
            name = group.get("data-module")
            if name is None:
                continue
            state = (
                "blocked"
                if not passed
                else "next"
                if name == next_name
                else "installed"
                if name in installed
                else "pending"
            )
            group.set("data-stage", state)
            group.set("opacity", "0.18" if state == "pending" else "1")
            if state == "next":
                rect = group.find("{*}rect")
                rect.set("fill", "#ffdeb8")
                rect.set("stroke", "#c04f00")
                rect.set("stroke-width", "4")
            for connector in group:
                mate = connector.get("data-mate")
                if mate and (
                    (name == next_name and mate in installed)
                    or (name in installed and mate == next_name)
                ):
                    connector.set("data-active-mate", "true")
                    polygon = connector.find("{*}polygon")
                    polygon.set("stroke", "#c04f00")
                    polygon.set("stroke-width", "5")
        if not passed:
            heading = "BLOCKED — no complete assembly sequence"
            detail = "See report.json for blocked moves and unresolved modules."
        elif next_name:
            heading = f"{installed_count} installed · Next: {next_name}"
            detail = "Mate with installed: " + (", ".join(sorted(mating)) or "none")
        else:
            heading = f"Complete — {len(order)} modules installed"
            detail = "All modules are in their checked final positions."
        counts_html = ""
        if passed:
            pairs = [{c["male"], c["female"]} for c in report["connections"]]
            engaged = sum(ends <= installed for ends in pairs)
            waiting = sum(len(ends & installed) == 1 for ends in pairs)
            exposed = 4 * installed_count - 2 * engaged - waiting
            counts = (
                ("engaged", "Engaged pairs", engaged),
                ("next", "Pairs added by next", len(mating)),
                ("waiting", "Installed connectors awaiting mates", waiting),
                ("exposed", "Installed permanently exposed edges", exposed),
            )
            counts_html = (
                '<dl class="counts">'
                + "".join(
                    f'<div><dt>{label}</dt><dd data-count="{key}">{value}</dd></div>'
                    for key, label, value in counts
                )
                + "</dl>"
            )
        for label in svg.iter("text"):
            if label.text and "connected pairs ·" in label.text:
                label.text = "Final layout: " + label.text
        frames.append(
            f'<section data-frame="{installed_count}"'
            + (" hidden" if installed_count else "")
            + f"><h2>{escape(heading)}</h2><p>{escape(detail)}</p>"
            + counts_html
            + tostring(svg, encoding="unicode")
            + "</section>"
        )
    controls = (
        f'<nav aria-label="Assembly steps"><button id="back">Back</button> '
        f'<label>Installed <input id="step" type="range" min="0" '
        f'max="{len(order)}" value="0"></label> '
        '<button id="next">Install next</button> '
        '<button id="reset">Reset</button></nav>'
        if passed
        else ""
    )
    return (
        """<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garden assembly — step through</title>
<style>
body{margin:0;background:#f5f7f5;color:#183329;font:16px system-ui,sans-serif}
main{max-width:1000px;margin:auto;padding:20px}h1{font-size:26px}h2{font-size:20px}
nav{display:flex;flex-wrap:wrap;gap:12px;align-items:center;padding:12px 0}
button{padding:10px 16px;font:inherit;cursor:pointer}input{vertical-align:middle}
svg{width:100%;height:auto}section[hidden]{display:none}
.counts{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.counts div{background:#fff;border:1px solid #cad8ce;border-radius:8px;padding:12px}
.counts dt{font-size:14px}.counts dd{font-size:26px;font-weight:600;margin:6px 0 0}
</style><main><h1>Garden / step through</h1>
<p>Green = installed · Orange = next module and mates · Faint = future modules.
Lower the next module from +Z at its shown XY position.</p>
<p>Nominal checked sequence. Tools, hands, friction and physical fit unverified.</p>
<noscript>Enable JavaScript to advance. The initial frame is shown below.</noscript>
"""
        + controls
        + '<div aria-live="polite">'
        + "".join(frames)
        + """</div></main>
<script>
const frames = Array.from(document.querySelectorAll('[data-frame]'));
const slider = document.getElementById('step');
if (slider) {
  const back = document.getElementById('back');
  const next = document.getElementById('next');
  function show(value) {
    const step = Math.max(0, Math.min(frames.length - 1, Number(value)));
    slider.value = step;
    slider.setAttribute('aria-valuetext', step + ' modules installed');
    frames.forEach((frame, i) => { frame.hidden = i !== step; });
    back.disabled = step === 0;
    next.disabled = step === frames.length - 1;
  }
  back.onclick = () => show(Number(slider.value) - 1);
  next.onclick = () => show(Number(slider.value) + 1);
  document.getElementById('reset').onclick = () => show(0);
  slider.oninput = () => show(slider.value);
  show(0);
}
</script></html>
"""
    )
