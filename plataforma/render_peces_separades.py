#!/usr/bin/env python3
"""Esquema de muntatge de la plataforma: peces separades i numerades.

Mides en mm, coincidents amb generate_zona.py. Origen a la cantonada davantera
esquerra, sobre el taulell: x cap a la dreta, y cap al fons, z amunt.

    python3 render_peces_separades.py [amplada] [supermostreig]
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
FLOOR = np.array([0.62, 0.62, 0.61])

# Peces: (mín. x, y, z), (màx. x, y, z), com a render_plataforma.py.
BOXES = {
    "posterior": ((3, 91, 0), (197, 94, 91)),
    "lateral1": ((8, 6, 0), (11, 94, 91)),
    "lateral2": ((189, 6, 0), (192, 94, 91)),
    "placa": ((0, 0, 91), (200, 100, 94)),
    "capa1": ((0, 0, 94), (200, 100, 97)),
    "capa2": ((0, 0, 97), (200, 100, 100)),
}
SEATS = ((50.0, 50.0), (150.0, 50.0))
SEAT_R = 35.0


def sd_box(p, lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    q = np.abs(p - (lo + hi) / 2) - (hi - lo) / 2
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def build(offsets):
    """Llista de (funció de distància, color), cada peça amb el seu desplaçament."""
    items = []
    for name, (lo, hi) in BOXES.items():
        o = np.array(offsets.get(name, (0, 0, 0)), float)

        def fn(p, lo=lo, hi=hi, o=o, seats=name.startswith("capa")):
            q = p - o
            d = sd_box(q, lo, hi)
            if seats:
                holes = np.minimum.reduce([np.hypot(q[:, 0] - x, q[:, 1] - y) - SEAT_R for x, y in SEATS])
                d = np.maximum(d, -holes)
            return d
        items.append((fn, WOOD if name in ("placa", "capa2", "lateral1") else WOOD2))
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



SEPARATED = {
    "posterior": (0, 90, 0),
    "lateral1": (-90, 0, 0),
    "lateral2": (90, 0, 0),
    "placa": (0, 0, 70),
    "capa1": (0, 0, 130),
    "capa2": (0, 0, 175),
    "terra": 0.0,
}
render(
    SEPARATED, (520, -760, 560), (100, 60, 120), 38, "plataforma_peces_separades.png",
    [
        ("1", (225, 185, 40)),
        ("2", (-110, 10, 95)),
        ("2", (310, 10, 95)),
        ("3", (-25, 50, 165)),
        ("4", (-25, 50, 228)),
        ("4", (-25, 50, 273)),
    ],
)
