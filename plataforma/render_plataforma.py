#!/usr/bin/env python3
"""Imatge realista de la plataforma muntada.

Traçador de raigs propi amb numpy: distàncies amb signe, ombres suaus i oclusió
ambiental. Les mides coincideixen amb generate_zona.py. Unitats: mm.

    python3 render_plataforma.py [amplada] [supermostreig]
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib import image as mpimg

OUT = Path(__file__).resolve().parent / "plataforma_muntada.png"
WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 1400
SS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
HEIGHT = WIDTH * 5 // 8
T = 3.0

# Peces: (mín. x, y, z), (màx. x, y, z). L'eix y va del davant cap al fons.
BOXES = {
    "posterior": ((3, 91, 0), (197, 94, 91)),
    "lateral1": ((8, 6, 0), (11, 94, 91)),
    "lateral2": ((189, 6, 0), (192, 94, 91)),
    "placa": ((0, 0, 91), (200, 100, 94)),
    "capa1": ((0, 0, 94), (200, 100, 97)),
    "capa2": ((0, 0, 97), (200, 100, 100)),
}
NAMES = ["terra"] + list(BOXES)
SEATS = ((50.0, 50.0), (150.0, 50.0))
SEAT_R = 35.0


def sd_box(p, lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    q = np.abs(p - (lo + hi) / 2) - (hi - lo) / 2
    outside = np.linalg.norm(np.maximum(q, 0), axis=1)
    return outside + np.minimum(q.max(axis=1), 0)


def parts(p):
    """Distància a cada peça, en l'ordre de NAMES."""
    out = [p[:, 2]]
    holes = None
    for name, (lo, hi) in BOXES.items():
        d = sd_box(p, lo, hi)
        if name.startswith("capa"):
            if holes is None:
                holes = np.minimum.reduce(
                    [np.hypot(p[:, 0] - x, p[:, 1] - y) - SEAT_R for x, y in SEATS]
                )
            d = np.maximum(d, -holes)
        out.append(d)
    return np.stack(out, axis=1)


def scene(p):
    return parts(p).min(axis=1)


def normals(p):
    e = 0.02
    n = np.zeros_like(p)
    for i in range(3):
        step = np.zeros(3)
        step[i] = e
        n[:, i] = scene(p + step) - scene(p - step)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def march(origin, dirs, far=4000.0):
    t = np.zeros(len(dirs))
    hit = np.zeros(len(dirs), bool)
    active = np.arange(len(dirs))
    for _ in range(130):
        if not len(active):
            break
        d = scene(origin + dirs[active] * t[active, None])
        done = d < 0.02
        hit[active[done]] = True
        t[active] += d
        active = active[~done & (t[active] < far)]
    return t, hit


def soft_shadow(p, light, k=14.0):
    res = np.ones(len(p))
    t = np.full(len(p), 0.6)
    active = np.arange(len(p))
    for _ in range(45):
        if not len(active):
            break
        d = scene(p[active] + light * t[active, None])
        res[active] = np.minimum(res[active], np.maximum(k * d / t[active], 0))
        t[active] += np.clip(d, 0.4, 30)
        active = active[(res[active] > 0.005) & (t[active] < 700)]
    return np.clip(res, 0, 1)


def ambient(p, n):
    occ = np.zeros(len(p))
    for i, h in enumerate((1.5, 5, 12, 26, 50)):
        occ += (h - scene(p + n * h)) / h * 0.5 ** i
    return np.clip(1 - 0.62 * occ, 0.12, 1)


def grain(u, v, seed):
    warp = 0.9 * np.sin(v * 0.05 + seed) + 0.6 * np.sin(u * 0.011 + v * 0.03 + 2 * seed)
    rings = np.sin((v + 9 * warp) * 0.28 + seed)
    fine = np.sin(v * 3.1 + 2.5 * np.sin(u * 0.017 + seed)) * np.sin(v * 7.7 + seed)
    pores = np.sin(u * 0.9 + v * 19 + seed) * np.sin(v * 31 + seed)
    tone = np.clip(0.55 + 0.27 * rings + 0.12 * fine + 0.04 * pores, 0, 1)
    light = np.array([0.66, 0.44, 0.24])
    dark = np.array([0.44, 0.26, 0.13])
    return dark + tone[:, None] * (light - dark)


def cut_edge(height):
    """Cantell cremat pel làser, amb les capes del contraplacat."""
    layers = 0.75 + 0.25 * np.sin(height * 2 * np.pi / 0.75)
    return np.array([0.13, 0.075, 0.04]) * layers[:, None]


def shade(p, n, ids, view):
    col = np.zeros_like(p)
    spec_power = np.full(len(p), 30.0)
    spec_amount = np.full(len(p), 0.03)
    for index, name in enumerate(NAMES):
        m = ids == index
        if not m.any():
            continue
        q, nn = p[m], n[m]
        if name == "terra":
            c = np.tile(np.array([0.6, 0.6, 0.59]), (len(q), 1))
            tape = ((np.abs(q[:, 0] - 100) < 9.5) & (q[:, 1] < 0)) | (np.abs(q[:, 1] - 100) < 9.5)
            c[tape] = (0.012, 0.012, 0.013)
            spec_amount[np.where(m)[0][tape]] = 0.09
        elif name == "posterior":
            big = np.abs(nn[:, 1]) > 0.7
            c = grain(q[:, 0], q[:, 2], 3.4)
            c[~big] = cut_edge(q[~big, 1])
        elif name.startswith("lateral"):
            big = np.abs(nn[:, 0]) > 0.7
            c = grain(q[:, 1], q[:, 2], 2.2 if name.endswith("1") else 4.7)
            c[~big] = cut_edge(q[~big, 0])
        else:
            big = np.abs(nn[:, 2]) > 0.7
            seed = {"placa": 6.1, "capa1": 3.9, "capa2": 1.9}[name]
            c = grain(q[:, 0], q[:, 1], seed)
            c[~big] = cut_edge(q[~big, 2])
        col[m] = c

    key_dir = np.array([-0.5, -0.55, 0.67])
    key_dir /= np.linalg.norm(key_dir)
    origin = p + n * 0.15
    shadow = soft_shadow(origin, key_dir)
    occlusion = ambient(p, n)
    diffuse = np.maximum(n @ key_dir, 0)
    sky = 0.55 + 0.45 * n[:, 2]
    light = (1.25 * diffuse * shadow)[:, None] * np.array([1.0, 0.96, 0.9]) + (
        0.5 * sky * occlusion
    )[:, None] * np.array([0.93, 0.97, 1.0])
    half = key_dir - view
    half /= np.linalg.norm(half, axis=1, keepdims=True)
    spec = (spec_amount * np.maximum((n * half).sum(axis=1), 0) ** spec_power * shadow)[:, None]
    return col * light + spec


def render():
    w, h = WIDTH * SS, HEIGHT * SS
    camera = np.array([430.0, -590.0, 340.0])
    target = np.array([100.0, 45.0, 45.0])
    forward = target - camera
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    focal = 1 / np.tan(np.radians(24) / 2)
    image = np.zeros((h, w, 3))
    step = 40000
    px = (np.arange(w) + 0.5) / w * 2 - 1
    py = 1 - (np.arange(h) + 0.5) / h * 2
    gx, gy = np.meshgrid(px, py * h / w)
    dirs = forward * focal + gx.ravel()[:, None] * right + gy.ravel()[:, None] * up
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    flat = np.zeros((h * w, 3))
    for start in range(0, len(dirs), step):
        d = dirs[start:start + step]
        t, hit = march(camera, d)
        c = np.tile(np.array([0.82, 0.83, 0.84]), (len(d), 1))
        if hit.any():
            p = camera + d[hit] * t[hit, None]
            ids = parts(p).argmin(axis=1)
            c[hit] = shade(p, normals(p), ids, d[hit])
        flat[start:start + step] = c
    image = flat.reshape(h, w, 3)
    if SS > 1:
        image = image.reshape(HEIGHT, SS, WIDTH, SS, 3).mean(axis=(1, 3))
    tone = image / (1 + 0.32 * image)
    tone = np.clip(tone * 1.2, 0, 1) ** (1 / 2.2)
    mpimg.imsave(OUT, (tone * 255).astype(np.uint8))
    print("Generat:", OUT)


if __name__ == "__main__":
    render()
