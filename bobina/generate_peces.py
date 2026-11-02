#!/usr/bin/env python3
"""Genera els models STL de les peces del MEET Robotics Challenge.

Totes les peces són la mateixa bobina, un sòlid de revolució definit per un perfil (radi, altura)
en mil·límetres. Per canviar una mida, edita el perfil i torna a executar:

    python3 generate_peces.py

Executat amb FreeCADCmd, també genera els fitxers STEP editables.
Sense dependències externes a banda de la biblioteca estàndard.
"""
import math
import pathlib
import struct

OUT = pathlib.Path(__file__).resolve().parent
SEGMENTS = 180

# Perfil de la base al cim. El primer i el darrer punt es tanquen a l'eix.
BOBINA = [
    (24.0, 0.0),  # simètrica respecte de z = 40: no té part de sota ni de sobre
    (25.0, 1.0),  # extrem Ø 50
    (25.0, 6.0),
    (17.0, 14.0),  # cintura Ø 34; cons a 45°: s'imprimeix sense suports
    (17.0, 66.0),
    (25.0, 74.0),
    (25.0, 79.0),
    (24.0, 80.0),
]

# Massa volúmica del PLA, g/cm³, i paràmetres d'impressió de referència.
DENSITY = 1.24


def revolve(profile, segments=SEGMENTS):
    """Retorna els triangles (cares cap enfora) del sòlid de revolució."""
    ring = [
        (math.cos(2 * math.pi * i / segments), math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    ]
    tris = []
    for i in range(segments):
        c0, s0 = ring[i]
        c1, s1 = ring[(i + 1) % segments]
        r, z = profile[0]
        tris.append(((0, 0, z), (r * c1, r * s1, z), (r * c0, r * s0, z)))
        r, z = profile[-1]
        tris.append(((0, 0, z), (r * c0, r * s0, z), (r * c1, r * s1, z)))
        for (ra, za), (rb, zb) in zip(profile, profile[1:]):
            a0 = (ra * c0, ra * s0, za)
            a1 = (ra * c1, ra * s1, za)
            b0 = (rb * c0, rb * s0, zb)
            b1 = (rb * c1, rb * s1, zb)
            tris.append((a0, a1, b1))
            tris.append((a0, b1, b0))
    return tris


def write_stl(path, name, tris):
    with open(path, "wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            u = [b[k] - a[k] for k in range(3)]
            v = [c[k] - a[k] for k in range(3)]
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            size = math.sqrt(sum(x * x for x in n)) or 1.0
            f.write(struct.pack("<3f", *(x / size for x in n)))
            for p in (a, b, c):
                f.write(struct.pack("<3f", *p))
            f.write(b"\0\0")


def stats(tris):
    """Volum (mm³), superfície (mm²) i altura del centre de massa (mm)."""
    volume = area = moment = 0.0
    for a, b, c in tris:
        cross = (
            b[1] * c[2] - b[2] * c[1],
            b[2] * c[0] - b[0] * c[2],
            b[0] * c[1] - b[1] * c[0],
        )
        v = (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6
        volume += v
        moment += v * (a[2] + b[2] + c[2]) / 4
        u = [b[k] - a[k] for k in range(3)]
        w = [c[k] - a[k] for k in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        area += math.sqrt(sum(x * x for x in n)) / 2
    return volume, area, moment / volume


def estimated_mass(volume, area, wall_mm, infill):
    """Estimació: closca massissa més farciment parcial. Cal pesar el prototip."""
    shell = min(area * wall_mm, volume)
    return (shell + (volume - shell) * infill) / 1000 * DENSITY


def write_step(name, profile):
    import FreeCAD  # noqa: F401  (només disponible dins FreeCADCmd)
    import Part
    from FreeCAD import Vector

    points = [Vector(0, 0, profile[0][1])]
    points += [Vector(r, 0, z) for r, z in profile]
    points += [Vector(0, 0, profile[-1][1])]
    points.append(points[0])
    face = Part.Face(Part.makePolygon(points))
    solid = face.revolve(Vector(0, 0, 0), Vector(0, 0, 1), 360)
    Part.Shape(solid).exportStep(str(OUT / f"{name}.step"))


PIECES = (
    ("bobina", BOBINA, 1.7, 0.30),
)

for piece, outline, wall, infill in PIECES:
    triangles = revolve(outline)
    write_stl(OUT / f"{piece}.stl", piece, triangles)
    vol, surf, cz = stats(triangles)
    print(
        f"{piece}: volum {vol / 1000:.1f} cm3, massa massissa {vol / 1000 * DENSITY:.0f} g, "
        f"massa estimada {estimated_mass(vol, surf, wall, infill):.0f} g, "
        f"centre de massa a z = {cz:.1f} mm"
    )
    try:
        write_step(piece, outline)
        print(f"{piece}: STEP generat")
    except ImportError:
        pass
