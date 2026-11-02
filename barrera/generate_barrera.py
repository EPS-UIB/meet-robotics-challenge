#!/usr/bin/env python3
"""Barrera fixa de la zona lila. Revisió 4.

Tipus pàrquing: una sola peça mòbil, impresa en 3D, amb el braç i una pala que
sobresurt. Un faldó sota el braç impedeix que una bobina tombada passi per sota de
la barrera tancada. Un robot empeny la pala i la barrera puja. El gir queda limitat entre
0° i 80° per dos topalls, i la barrera es tanca pel seu propi pes. El conjunt és
independent del receptacle i es col·loca al seu costat.

Executat amb python3, genera la làmina de tall. Executat amb FreeCADCmd, genera
també la peça mòbil en STL i STEP. Mides en mm. Coordenades de la peça mòbil: origen
a l'eix, x cap al braç, z amunt, amb la barrera tancada.
"""
from math import cos, hypot, pi, radians, sin
from pathlib import Path

OUT = Path(__file__).resolve().parent
T = 3.0
KERF = 0.15
SLOT = T + 0.05
ARM_LENGTH = 245.0
ARM_WIDTH = 20.0
SKIRT_START = 40.0  # distància de l'eix on comença el faldó
SKIRT_BOTTOM = 35.0  # altura del cantell inferior del faldó sobre el taulell
BOBBIN_LYING = 50.0  # altura d'una bobina tombada (diàmetre dels extrems)
BOBBIN_STANDING = 80.0
PASSAGE_START = 58.0  # distància de l'eix a la paret lateral del receptacle
WALL_FACE = 1.5  # cara de la paret fixa, a la dreta de l'eix
PADDLE_LENGTH = 65.0
PADDLE_WIDTH = 24.0
PADDLE_ANGLE = 225.0  # direcció de la pala, amb la barrera tancada
OPEN_ANGLE = 80.0
AXIS_HEIGHT = 80.0
BOLT_HOLE = 4.4
PIN_HOLE = 4.2
PIN_RADIUS = 2.0
UPRIGHT_LEFT, UPRIGHT_RIGHT = 36.0, 33.0
UPRIGHT_TOP = 100.0
BLADE_WIDTH, BLADE_HEIGHT = 50.0, 30.0
WALL_LENGTH, WALL_HEIGHT = 139.0, 100.0
WINDOW_COUNT, WINDOW_WIDTH = 3, 12.0
PRINT_DENSITY = 0.00093  # g/mm³: PLA amb 2 perímetres i 30 % de farciment, a 3 mm de gruix
BOLT_FRICTION = 0.3


def f(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def direction(degrees):
    return cos(radians(degrees)), sin(radians(degrees))


def moving_outline():
    dx, dz = direction(PADDLE_ANGLE)
    nx, nz = -dz, dx  # costat de la pala que dona al braç
    h = PADDLE_WIDTH / 2
    hw = ARM_WIDTH / 2

    def on_edge(side, z):
        t = (z - side * h * nz) / dz
        return side * h * nx + t * dx, z

    skirt = SKIRT_BOTTOM - AXIS_HEIGHT
    return [
        (ARM_LENGTH, hw),
        (ARM_LENGTH, skirt),
        (SKIRT_START, skirt),
        (SKIRT_START, -hw),
        on_edge(1, -hw),
        (h * nx + PADDLE_LENGTH * dx, h * nz + PADDLE_LENGTH * dz),
        (-h * nx + PADDLE_LENGTH * dx, -h * nz + PADDLE_LENGTH * dz),
        on_edge(-1, hw),
    ]


def stops():
    """Centres dels dos topalls: contacte amb els cantells de la pala."""
    reach, gap = 30.0, PADDLE_WIDTH / 2 + PIN_RADIUS
    closed = direction(PADDLE_ANGLE)
    closed_side = direction(PADDLE_ANGLE - 90)
    opened = direction(PADDLE_ANGLE + OPEN_ANGLE)
    opened_side = direction(PADDLE_ANGLE + OPEN_ANGLE + 90)
    return (
        (reach * closed[0] + gap * closed_side[0], reach * closed[1] + gap * closed_side[1]),
        (reach * opened[0] + gap * opened_side[0], reach * opened[1] + gap * opened_side[1]),
    )


def offset(points, distance):
    """Desplaça cap enfora un polígon de cantells rectes (sentit horari)."""
    n = len(points)
    out = []
    for i in range(n):
        ax, ay = points[i - 1]
        bx, by = points[i]
        cx, cy = points[(i + 1) % n]
        ux, uy = bx - ax, by - ay
        vx, vy = cx - bx, cy - by
        lu, lv = hypot(ux, uy), hypot(vx, vy)
        n1 = (-uy / lu, ux / lu)
        n2 = (-vy / lv, vx / lv)
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        scale = distance / (1 + n1[0] * n2[0] + n1[1] * n2[1])
        out.append((bx + mx * scale, by + my * scale))
    return out


def polygon(points, ox, oy, flip=True):
    pts = " ".join(f"{f(ox + x)},{f(oy - y if flip else oy + y)}" for x, y in points)
    return f'<polygon class="cut" points="{pts}"/>'


def rect(x, y, w, h):
    return (f'<rect class="cut" x="{f(x - KERF / 2)}" y="{f(y - KERF / 2)}" '
            f'width="{f(w + KERF)}" height="{f(h + KERF)}"/>')


def slot(cx, cy, w, h):
    return (f'<rect class="cut" x="{f(cx - w / 2 + KERF / 2)}" y="{f(cy - h / 2 + KERF / 2)}" '
            f'width="{f(w - KERF)}" height="{f(h - KERF)}"/>')


def hole(cx, cy, diameter):
    return f'<circle class="cut" cx="{f(cx)}" cy="{f(cy)}" r="{f(diameter / 2 - KERF / 2)}"/>'


def label(x, y, text):
    return f'<text class="label" x="{f(x)}" y="{f(y)}">{text}</text>'


def tabs_bottom(width, height, tabs):
    """Contorn de placa amb llengüetes inferiors. Origen a dalt a l'esquerra."""
    k = KERF / 2
    pts = [(-k, -k), (width + k, -k), (width + k, height + k)]
    for centre, w in sorted(tabs, reverse=True):
        pts += [(centre + w / 2 + k, height + k), (centre + w / 2 + k, height + T + k),
                (centre - w / 2 - k, height + T + k), (centre - w / 2 - k, height + k)]
    pts.append((-k, height + k))
    return pts


def sheet():
    a = ['''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
  <title>Barrera de la zona lila: base, muntants i paret</title>
  <metadata>Unitats: mm. Vermell = tall, blau = gravat. Kerf de 0,15 mm incorporat.</metadata>
  <style>
    .cut { fill:none; stroke:#ff0000; stroke-width:0.10; }
    .label { fill:#0066ff; font-family:Arial,sans-serif; font-size:4px; }
  </style>''']

    # Base: coordenades del taulell, en mm. Toca el receptacle (x = 1800) i el fons (y = 1000).
    def bx(x):
        return 8 + x - 1709

    def by(y):
        return 8 + 1000 - y

    outline = [(1709, 852), (1800, 852), (1800, 1000), (1709, 1000)]
    k = KERF / 2
    # Contorn en sentit horari sobre la làmina; es desplaça cap enfora.
    a.append(polygon(offset([(bx(x), by(y)) for x, y in outline], -k), 0, 0, flip=False))
    a.append(slot(bx(1750 - (UPRIGHT_LEFT - UPRIGHT_RIGHT) / 2), by(858), 30.05, 2 * T + 0.1))
    a.append(slot(bx(1750), by(861 + WALL_LENGTH / 2), SLOT, 40.05))
    a.append(label(bx(1714), by(865), "BASE"))

    # Dos muntants laminats, amb l'eix i els topalls.
    closed_stop, open_stop = stops()
    body = UPRIGHT_TOP - T
    width = UPRIGHT_LEFT + UPRIGHT_RIGHT
    axis_from_top = UPRIGHT_TOP - AXIS_HEIGHT
    for i, ux in enumerate((110.0, 195.0)):
        uy = 30.0
        pts = tabs_bottom(width, body, [(width / 2, 30.0)])
        coords = " ".join(f"{f(ux + x)},{f(uy + y)}" for x, y in pts)
        a.append(f'<polygon class="cut" points="{coords}"/>')
        ax, ay = ux + UPRIGHT_LEFT, uy + axis_from_top
        a.append(hole(ax, ay, PIN_HOLE))
        a.append(hole(ax + closed_stop[0], ay - closed_stop[1], PIN_HOLE))
        a.append(hole(ax + open_stop[0], ay - open_stop[1], PIN_HOLE))
        a.append(slot(ax, uy + 55, SLOT, 30.05))
        a.append(label(ux + 3, uy + body - 3, f"MUNTANT {i + 1}"))

    # Paret: tanca el costat del receptacle i arriostra els muntants.
    wx, wy = 104.0, 136.0
    pts = tabs_bottom(WALL_LENGTH, WALL_HEIGHT - T, [(WALL_LENGTH / 2, 40.0)])
    # Llengüeta frontal que travessa els dos muntants.
    tab = [(-k, 40 - k), (-2 * T - k, 40 - k), (-2 * T - k, 70 + k), (-k, 70 + k)]
    full = pts + list(reversed(tab))
    coords = " ".join(f"{f(wx + x)},{f(wy + y)}" for x, y in full)
    a.append(f'<polygon class="cut" points="{coords}"/>')
    a.append(label(wx + 40, wy + 15, "PARET"))
    a.append("</svg>")
    (OUT / "barrera_lamina_1a1.svg").write_text("\n".join(a), encoding="utf-8")


def windows():
    """Finestres del braç: alleugereixen la peça impresa."""
    start, end, rib = 30.0, ARM_LENGTH - 10.0, 6.0
    length = (end - start - (WINDOW_COUNT - 1) * rib) / WINDOW_COUNT
    return [(start + i * (length + rib), length) for i in range(WINDOW_COUNT)]


def skirt_box():
    """Faldó: extrem esquerre, extrem dret, z superior i z inferior, des de l'eix."""
    return SKIRT_START, ARM_LENGTH, -ARM_WIDTH / 2, SKIRT_BOTTOM - AXIS_HEIGHT


def skirt_mass():
    x0, x1, z0, z1 = skirt_box()
    return (x1 - x0) * (z0 - z1) * T * PRINT_DENSITY


def part_mass():
    """Massa (g) del braç, la pala i la superfície de contacte, impresos en 3D."""
    window_area = sum(length * WINDOW_WIDTH for _, length in windows())
    arm = (ARM_LENGTH * ARM_WIDTH - window_area) * T * PRINT_DENSITY
    paddle = PADDLE_LENGTH * PADDLE_WIDTH * T * PRINT_DENSITY
    blade = BLADE_WIDTH * BLADE_HEIGHT * T * PRINT_DENSITY
    return arm, paddle, blade


def closing_moment(angle):
    arm, paddle, blade = part_mass()
    g = 9.81e-3
    paddle_dir = direction(PADDLE_ANGLE + angle)
    arm_dir = direction(angle)
    x0, x1, z0, z1 = skirt_box()
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    skirt = skirt_mass() * (cx * arm_dir[0] - cz * arm_dir[1])
    return g * (skirt + arm * ARM_LENGTH / 2 * arm_dir[0]
                + paddle * PADDLE_LENGTH / 2 * paddle_dir[0]
                + blade * PADDLE_LENGTH * paddle_dir[0])


def report():
    arm, paddle, blade = part_mass()
    total = arm + paddle + blade + skirt_mass()
    friction = total * 9.81e-3 * BOLT_FRICTION * BOLT_HOLE / 2
    worst = float("inf")
    max_force = 0.0
    for degrees in range(0, int(OPEN_ANGLE) + 1):
        moment = closing_moment(degrees)
        worst = min(worst, moment)
        tip = direction(PADDLE_ANGLE + degrees)
        lever = PADDLE_LENGTH * abs(tip[1])
        max_force = max(max_force, moment / lever)
    closed_stop, open_stop = stops()
    print(f"Massa mòbil estimada: {total:.1f} g")
    print(f"Moment de tancament mínim: {worst:.2f} N·mm; fregament estimat de l'eix: {friction:.2f} N·mm")
    print(f"Força horitzontal màxima a la pala: {max_force:.2f} N")
    tip_closed = direction(PADDLE_ANGLE)
    tip_open = direction(PADDLE_ANGLE + OPEN_ANGLE)
    print(f"Punta de la pala: tancada x={PADDLE_LENGTH * tip_closed[0]:.0f}, z={AXIS_HEIGHT + PADDLE_LENGTH * tip_closed[1]:.0f}; "
          f"oberta x={PADDLE_LENGTH * tip_open[0]:.0f}, z={AXIS_HEIGHT + PADDLE_LENGTH * tip_open[1]:.0f}")
    print(f"Topalls: tancat ({closed_stop[0]:.1f}, {closed_stop[1]:.1f}), obert ({open_stop[0]:.1f}, {open_stop[1]:.1f})")
    x0, x1, z0, z1 = skirt_box()
    a = radians(OPEN_ANGLE)
    lowest = min(AXIS_HEIGHT + x * sin(a) + z * cos(a)
                 for x in (x0 + i * (x1 - x0) / 100 for i in range(101)) for z in (z0, z1)
                 if x * cos(a) - z * sin(a) >= PASSAGE_START)
    print(f"Faldó: de x={x0:.0f} a {x1:.0f} mm, cantell inferior a {SKIRT_BOTTOM:.0f} mm del taulell; "
          f"pas lliure entre la paret i el faldó: {x0 - WALL_FACE:.1f} mm")
    print(f"Barrera oberta: punt més baix del faldó sobre el pas del receptacle a {lowest:.0f} mm")
    if SKIRT_BOTTOM > BOBBIN_LYING - 10 or x0 - WALL_FACE > BOBBIN_LYING - 10:
        raise SystemExit("VALIDACIÓ FALLIDA: una bobina tombada pot passar per sota de la barrera")
    if hypot(x0, z0) < hypot(*open_stop) + PIN_RADIUS + 4:
        raise SystemExit("VALIDACIÓ FALLIDA: el faldó topa amb el topall d'obertura")
    if lowest < BOBBIN_STANDING + 10:
        raise SystemExit("VALIDACIÓ FALLIDA: amb la barrera oberta, el faldó no deixa passar una bobina dreta")
    if worst <= 3 * friction:
        raise SystemExit("VALIDACIÓ FALLIDA: el pes no garanteix el tancament")
    if open_stop[0] + 4 > UPRIGHT_RIGHT or -closed_stop[0] + 4 > UPRIGHT_LEFT:
        raise SystemExit("VALIDACIÓ FALLIDA: els topalls no caben al muntant")
    print("VALIDACIÓ OK")


def write_moving_part():
    """Peça mòbil en STL i STEP. Només funciona dins FreeCADCmd."""
    import Part
    from FreeCAD import Vector

    def prism(points, z0, z1):
        loop = [Vector(x, y, z0) for x, y in points]
        face = Part.Face(Part.makePolygon(loop + [loop[0]]))
        return face.extrude(Vector(0, 0, z1 - z0))

    solid = prism(moving_outline(), 0, T)
    for start, length in windows():
        h = WINDOW_WIDTH / 2
        solid = solid.cut(prism([(start, -h), (start + length, -h), (start + length, h), (start, h)], -1, T + 1))
    solid = solid.cut(Part.makeCylinder(BOLT_HOLE / 2, T + 2, Vector(0, 0, -1)))
    dx, dz = direction(PADDLE_ANGLE)
    nx, nz = -dz, dx
    half = BLADE_HEIGHT / 2
    tip = (PADDLE_LENGTH * dx, PADDLE_LENGTH * dz)
    back = (tip[0] - T * dx, tip[1] - T * dz)
    blade = [(tip[0] + half * nx, tip[1] + half * nz), (back[0] + half * nx, back[1] + half * nz),
             (back[0] - half * nx, back[1] - half * nz), (tip[0] - half * nx, tip[1] - half * nz)]
    solid = solid.fuse(prism(blade, T - BLADE_WIDTH, T)).removeSplitter()
    solid.exportStep(str(OUT / "barrera_peca_mobil.step"))
    solid.tessellate(0.05)
    import Mesh
    Mesh.Mesh(solid.tessellate(0.05)).write(str(OUT / "barrera_peca_mobil.stl"))
    print(f"Peça mòbil: {solid.Volume / 1000:.1f} cm3, sòlid vàlid: {solid.isValid()}")


report()
sheet()
try:
    write_moving_part()
except ImportError:
    pass
