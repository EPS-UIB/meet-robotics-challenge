#!/usr/bin/env python3
"""Imatges del muntatge de la barrera: peces separades i conjunt muntat.

Mides en mm, coincidents amb generate_barrera.py i generate_zona.py. Origen a l'eix
de la barrera, sobre el taulell: x cap a la dreta, y cap al fons, z amunt.

    python3 render_muntatge.py [amplada] [supermostreig]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
SS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
HEIGHT = WIDTH * 5 // 8

WOOD = np.array([0.6, 0.41, 0.23])
WOOD2 = np.array([0.5, 0.33, 0.18])
PRINT = np.array([0.29, 0.11, 0.48])
STEEL = np.array([0.32, 0.33, 0.35])
FLOOR = np.array([0.62, 0.62, 0.61])

OUTLINE = np.array([(245, 10), (245, -10), (6.98, -10), (-37.47, -54.45), (-54.45, -37.47), (-6.98, 10)], float)
BLADE = np.array([(-35.39, -56.57), (-37.51, -54.45), (-58.73, -33.24), (-56.61, -35.36)], float)
WINDOWS = [(30 + i * (64.33 + 6), 64.33) for i in range(3)]
STOPS = ((-31.1, -11.3), (28.7, -16.5))


def sd_box(p, lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    q = np.abs(p - (lo + hi) / 2) - (hi - lo) / 2
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def sd_polygon(xy, poly):
    best = np.full(len(xy), 1e12)
    inside = np.zeros(len(xy), bool)
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        e = b - a
        w = xy - a
        t = np.clip((w @ e) / (e @ e), 0, 1)
        d = w - t[:, None] * e
        best = np.minimum(best, (d * d).sum(axis=1))
        if e[1] != 0:
            crosses = (a[1] <= xy[:, 1]) != (b[1] <= xy[:, 1])
            inside ^= crosses & (xy[:, 0] < a[0] + (xy[:, 1] - a[1]) * e[0] / e[1])
    return np.sqrt(best) * np.where(inside, -1, 1)


def sd_extruded(p, poly, y0, y1, oz=80.0):
    d2 = sd_polygon(np.stack([p[:, 0], p[:, 2] - oz], axis=1), poly)
    dy = np.abs(p[:, 1] - (y0 + y1) / 2) - (y1 - y0) / 2
    q = np.stack([d2, dy], axis=1)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def sd_ycyl(p, x, z, r, y0, y1):
    d2 = np.hypot(p[:, 0] - x, p[:, 2] - z) - r
    dy = np.abs(p[:, 1] - (y0 + y1) / 2) - (y1 - y0) / 2
    q = np.stack([d2, dy], axis=1)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def build(offsets):
    """Llista de (funció de distància, color), cada grup amb el seu desplaçament."""
    def shifted(group, fn):
        o = np.array(offsets.get(group, (0, 0, 0)), float)
        return lambda p: fn(p - o)

    items = []

    def box(group, lo, hi, color):
        items.append((shifted(group, lambda p, lo=lo, hi=hi: sd_box(p, lo, hi)), color))

    box("base", (-41, 2, 0), (50, 150, 3), WOOD)
    box("muntant1", (-36, 5, 3), (33, 8, 100), WOOD2)
    box("muntant2", (-36, 8, 3), (33, 11, 100), WOOD)
    box("paret", (-1.5, 11, 3), (1.5, 150, 100), WOOD2)
    box("paret", (-1.5, 5, 30), (1.5, 11, 60), WOOD2)
    box("receptacle", (53, 141, 0), (247, 144, 91), WOOD2)
    box("receptacle", (58, 56, 0), (61, 144, 91), WOOD2)
    box("receptacle", (239, 56, 0), (242, 144, 91), WOOD2)
    box("receptacle", (50, 50, 91), (250, 150, 94), WOOD)

    def moving(p):
        d = sd_extruded(p, OUTLINE, -3, 0)
        for start, length in WINDOWS:
            d = np.maximum(d, -sd_box(p, (start, -5, 74), (start + length, 2, 86)))
        d = np.maximum(d, -sd_ycyl(p, 0, 80, 2.2, -5, 2))
        return np.minimum(d, sd_extruded(p, BLADE, -50, 0))

    items.append((shifted("mobil", moving), PRINT))

    def axle(p):
        return np.minimum.reduce([
            sd_ycyl(p, 0, 80, 2, -6, 16),
            sd_ycyl(p, 0, 80, 4, -8, -5),
            sd_ycyl(p, 0, 80, 4, 11, 14),
            sd_ycyl(p, 0, 80, 4.5, 0, 5),
        ])

    items.append((shifted("eix", axle), STEEL))
    for index, (x, z) in enumerate(STOPS):
        def stop(p, x=x, z=80 + z):
            return np.minimum(sd_ycyl(p, x, z, 2, -3, 14), sd_ycyl(p, x, z, 4, 11, 14))
        items.append((shifted("topalls", stop), STEEL))
    return items


def render(offsets, camera, target, fov, name, labels):
    items = build(offsets)
    w, h = WIDTH * SS, HEIGHT * SS
    camera = np.array(camera, float)
    target = np.array(target, float)

    def scene(p):
        d = p[:, 2] + 0.0 + (offsets.get("terra", 0))
        for fn, _ in items:
            d = np.minimum(d, fn(p))
        return d

    forward = (target - camera) / np.linalg.norm(target - camera)
    right = np.cross(forward, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    focal = 1 / np.tan(np.radians(fov) / 2)
    gx, gy = np.meshgrid((np.arange(w) + 0.5) / w * 2 - 1, (1 - (np.arange(h) + 0.5) / h * 2) * h / w)
    dirs = forward * focal + gx.ravel()[:, None] * right + gy.ravel()[:, None] * up
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    key = np.array([-0.5, -0.55, 0.67])
    key /= np.linalg.norm(key)
    flat = np.zeros((h * w, 3))
    for start in range(0, len(dirs), 50000):
        d = dirs[start:start + 50000]
        t = np.zeros(len(d))
        active = np.arange(len(d))
        hit = np.zeros(len(d), bool)
        for _ in range(110):
            if not len(active):
                break
            dist = scene(camera + d[active] * t[active, None])
            done = dist < 0.03
            hit[active[done]] = True
            t[active] += dist
            active = active[~done & (t[active] < 5000)]
        c = np.tile(np.array([0.84, 0.84, 0.83]), (len(d), 1))
        if hit.any():
            p = camera + d[hit] * t[hit, None]
            n = np.zeros_like(p)
            for i in range(3):
                e = np.zeros(3)
                e[i] = 0.03
                n[:, i] = scene(p + e) - scene(p - e)
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
            dists = np.stack([fn(p) for fn, _ in items], axis=1)
            near = dists.argmin(axis=1)
            colors = np.array([col for _, col in items])
            col = colors[near]
            col[dists.min(axis=1) > 0.3] = FLOOR
            origin = p + n * 0.2
            shadow = np.ones(len(p))
            ts = np.full(len(p), 0.8)
            for _ in range(30):
                dd = scene(origin + key * ts[:, None])
                shadow = np.minimum(shadow, np.clip(12 * dd / ts, 0, 1))
                ts += np.clip(dd, 0.6, 40)
            occ = np.zeros(len(p))
            for i, s in enumerate((2, 7, 18, 40)):
                occ += (s - scene(p + n * s)) / s * 0.5 ** i
            amb = np.clip(1 - 0.55 * occ, 0.15, 1)
            light = (1.25 * np.maximum(n @ key, 0) * shadow + 0.55 * (0.55 + 0.45 * n[:, 2]) * amb)[:, None]
            c[hit] = col * light
        flat[start:start + 50000] = c
    image = flat.reshape(h, w, 3)
    if SS > 1:
        image = image.reshape(HEIGHT, SS, WIDTH, SS, 3).mean(axis=(1, 3))
    image = np.clip(image / (1 + 0.3 * image) * 1.22, 0, 1) ** (1 / 2.2)

    fig = plt.figure(figsize=(WIDTH / 100, HEIGHT / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(image)
    ax.axis("off")
    for text, point in labels:
        v = np.array(point, float) - camera
        depth = v @ forward
        sx = (v @ right) / depth * focal
        sy = (v @ up) / depth * focal
        x = (sx + 1) / 2 * WIDTH
        y = (1 - sy / (HEIGHT / WIDTH)) / 2 * HEIGHT
        ax.text(x, y, text, fontsize=WIDTH / 95, fontweight="bold", color="white", ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.3", fc="#1b1b1f", ec="white", lw=1))
    fig.savefig(OUT / name, dpi=100)
    plt.close(fig)
    print("Generat:", OUT / name)


render({}, (590, -560, 420), (85, 65, 55), 28, "barrera_muntada.png", [])

SEPARATED = {
    "base": (0, 0, -150),
    "muntant1": (0, -75, 0),
    "muntant2": (0, -40, 0),
    "paret": (0, 40, 0),
    "mobil": (0, -300, 0),
    "eix": (0, -185, 0),
    "topalls": (0, -150, 0),
    "receptacle": (130, 60, 130),
    "terra": 320.0,
}
render(
    SEPARATED, (760, -1120, 760), (130, -40, 20), 36, "barrera_peces_separades.png",
    [
        ("1", (-75, 100, -147)),
        ("2", (-62, -60, 112)),
        ("3", (-22, 125, 118)),
        ("4", (200, -300, 45)),
        ("5", (-95, -185, 85)),
        ("6", (270, 240, 240)),
    ],
)
