#!/usr/bin/env python3
"""Plataforma de les zones vermella i blava, per a tall làser. Revisió 1.

Totes les mides són en mil·límetres. La geometria vermella és la línia central
de tall i ja incorpora el kerf: no s'ha d'afegir cap compensació a la màquina.
Cada zona necessita un joc complet de les dues làmines.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class P:
    length: float = 200.0
    depth: float = 100.0
    height: float = 100.0
    thickness: float = 3.0
    kerf: float = 0.15
    fit_clearance: float = 0.05
    seat_diameter: float = 70.0
    seat_centres: tuple = (50.0, 150.0)
    seat_layers: int = 2
    bobina_diameter: float = 50.0
    wall_inset: float = 6.0      # de la vora de la placa a la cara exterior del posterior
    wall_end: float = 3.0        # de la vora de la placa a l'extrem del posterior
    side_inset: float = 8.0      # de la vora de la placa a la cara exterior del lateral
    plate_tab: float = 30.0
    side_tab: float = 15.0
    side_tab_centres: tuple = (22.0, 66.0)  # des de la base del cos de la paret

    @property
    def body(self):
        # Les parets arriben al taulell: no hi ha base, i una bobina pot entrar a sota.
        return self.height - (1 + self.seat_layers) * self.thickness

    @property
    def wall_length(self):
        return self.length - 2 * self.wall_end

    @property
    def side_body(self):
        # Del cantell lliure, a la banda oberta, fins a la cara interior del posterior.
        return self.depth - 2 * self.wall_inset - self.thickness

    @property
    def slot(self):
        return self.thickness + self.fit_clearance


CFG = P()
OUT = Path(__file__).resolve().parent


def f(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def header(width, height, title):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{f(width)}mm" height="{f(height)}mm" viewBox="0 0 {f(width)} {f(height)}">
  <title>{title}</title>
  <metadata>Unitats: mm. Vermell = tall, blau = gravat. Kerf de {f(CFG.kerf)} mm incorporat.</metadata>
  <style>
    .cut {{ fill:none; stroke:#ff0000; stroke-width:0.10; }}
    .label {{ fill:#0066ff; font-family:Arial,sans-serif; font-size:4px; }}
  </style>
'''


def outer_rect(x, y, w, h):
    k = CFG.kerf
    return f'<rect class="cut" x="{f(x-k/2)}" y="{f(y-k/2)}" width="{f(w+k)}" height="{f(h+k)}"/>'


def inner_rect(cx, cy, w, h):
    """Obertura interior centrada, amb mides acabades w × h."""
    k = CFG.kerf
    return (f'<rect class="cut" x="{f(cx-w/2+k/2)}" y="{f(cy-h/2+k/2)}" '
            f'width="{f(w-k)}" height="{f(h-k)}"/>')


def hole(cx, cy, diameter):
    return f'<circle class="cut" cx="{f(cx)}" cy="{f(cy)}" r="{f(diameter/2-CFG.kerf/2)}"/>'


def label(x, y, text):
    return f'<text class="label" x="{f(x)}" y="{f(y)}">{text}</text>'


def plate_with_slots(x, y):
    """Placa massissa: ranures per a les llengüetes de les tres parets."""
    p = CFG
    out = [outer_rect(x, y, p.length, p.depth)]
    wall_y = p.depth - p.wall_inset - p.thickness / 2
    for u in (p.wall_length / 4, 3 * p.wall_length / 4):
        out.append(inner_rect(x + p.wall_end + u, y + wall_y, p.plate_tab + p.fit_clearance, p.slot))
    for side_x in (p.side_inset + p.thickness / 2, p.length - p.side_inset - p.thickness / 2):
        out.append(inner_rect(x + side_x, y + p.depth / 2, p.slot, p.plate_tab + p.fit_clearance))
    return "\n".join(out)


def plate_with_seats(x, y):
    p = CFG
    out = [outer_rect(x, y, p.length, p.depth)]
    for cx in p.seat_centres:
        out.append(hole(x + cx, y + p.depth / 2, p.seat_diameter))
    return "\n".join(out)


def tabbed_outline(x, y, width, tabs_u, tab_w, side_tabs=False):
    """Paret amb llengüetes a dalt; opcionalment també al costat dret. La base és plana.

    (x, y) és la cantonada superior esquerra del cos de la paret.
    """
    p = CFG
    k2 = p.kerf / 2
    t, h = p.thickness, p.body
    pts = [(-k2, -k2)]
    for u in tabs_u:
        a, b = u - tab_w / 2, u + tab_w / 2
        pts += [(a - k2, -k2), (a - k2, -t - k2), (b + k2, -t - k2), (b + k2, -k2)]
    pts.append((width + k2, -k2))
    if side_tabs:
        for c in sorted(h - v for v in p.side_tab_centres):
            a, b = c - p.side_tab / 2, c + p.side_tab / 2
            pts += [(width + k2, a - k2), (width + t + k2, a - k2), (width + t + k2, b + k2), (width + k2, b + k2)]
    pts += [(width + k2, h + k2), (-k2, h + k2)]
    coords = " ".join(f"{f(x+px)},{f(y+py)}" for px, py in pts)
    return f'<polygon class="cut" points="{coords}"/>'


def long_wall(x, y):
    """Posterior: ranures per a les llengüetes dels laterals."""
    p = CFG
    out = [tabbed_outline(x, y, p.wall_length, (p.wall_length / 4, 3 * p.wall_length / 4), p.plate_tab)]
    offset = p.side_inset - p.wall_end + p.thickness / 2
    for u in (offset, p.wall_length - offset):
        for v in p.side_tab_centres:
            out.append(inner_rect(x + u, y + p.body - v, p.slot, p.side_tab + p.fit_clearance))
    return "\n".join(out)


def side_wall(x, y):
    p = CFG
    # El centre de la llengüeta coincideix amb el de la ranura, a y = depth / 2.
    return tabbed_outline(x, y, p.side_body, (p.depth / 2 - p.wall_inset,), p.plate_tab, side_tabs=True)


def sheet_plates():
    p = CFG
    w, h = 420.0, 230.0
    a = [header(w, h, "Zona de color - làmina 1 de 2: plaques")]
    positions = [
        (plate_with_slots, 8, 8, "PLACA MASSISSA"),
        (plate_with_seats, 8, 116, "CAPA AMB FORATS 1"),
        (plate_with_seats, 212, 116, "CAPA AMB FORATS 2"),
    ]
    for make, x, y, name in positions:
        a.append(make(x, y))
        a.append(label(x + 80, y + 5, name))
    a.append("</svg>")
    (OUT / "zona_lamina1_plaques_1a1.svg").write_text("\n".join(a), encoding="utf-8")


def sheet_walls():
    p = CFG
    w, h = 420.0, 230.0
    a = [header(w, h, "Zona de color - làmina 2 de 2: parets")]
    y1, y2 = 8 + p.thickness, 8 + p.thickness + p.body + 8 + p.thickness
    a.append(long_wall(8, y1))
    a.append(label(88, y1 + p.body / 2, "POSTERIOR"))
    for x, name in ((12, "LATERAL 1"), (108, "LATERAL 2")):
        a.append(side_wall(x, y2))
        a.append(label(x + 20, y2 + p.body / 2, name))
    a.append("</svg>")
    (OUT / "zona_lamina2_parets_1a1.svg").write_text("\n".join(a), encoding="utf-8")


def validate():
    p = CFG
    t = p.thickness
    checks = {
        "l'altura total tanca": p.body + (1 + p.seat_layers) * t == p.height,
        "una bobina de 80 mm entra a sota": p.body > 80,
        "la bobina cap al forat": p.seat_diameter > p.bobina_diameter,
        "els forats no toquen la vora": p.seat_diameter < p.depth - 2 * t,
        "els forats no es toquen": p.seat_centres[1] - p.seat_centres[0] > p.seat_diameter + 2 * t,
        "el primer forat no toca la vora": p.seat_centres[0] - p.seat_diameter / 2 > 2 * t,
        "les llengüetes dels laterals caben": max(p.side_tab_centres) + p.side_tab / 2 < p.body,
        "la llengüeta del posterior no toca el lateral":
            p.wall_length / 4 - p.plate_tab / 2 > p.side_inset - p.wall_end + t,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("VALIDACIÓ FALLIDA: " + "; ".join(failed))
    print("VALIDACIÓ OK")
    print(f"Cos de les parets: {f(p.body)} mm; fondària de l'allotjament: {f(p.seat_layers*t)} mm")
    print(f"Joc de la bobina a l'allotjament: {f((p.seat_diameter-p.bobina_diameter)/2)} mm per costat")


if __name__ == "__main__":
    validate()
    sheet_plates()
    sheet_walls()
