"""Shared helpers for the render scripts."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import module
import sizing

COLORS = {"skin": "#ff7a59", "rail": "#2bb5a6", "lip": "#f2c230", "pad": "#4c8dff", "module": "#b794f4", "diffuser": "#fff2a8", "strip": "#7ef0ff"}
LIGHT = np.array([0.4, -0.5, 0.8]); LIGHT /= np.linalg.norm(LIGHT)


def tris_of(shape, tol=0.5):
    v, t = shape.val().tessellate(tol)
    p = np.array([[x.x, x.y, x.z] for x in v])
    return p[np.array(t)]


def shade(tris, color, alpha=1.0):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    k = 0.45 + 0.55 * np.abs(n @ LIGHT)
    return [(*(np.array(to_rgb(color)) * kk), alpha) for kk in k]


def mannequin(ax):
    hp, hq = sizing.head_axes(build.W["head_circumference"])
    neck_r = build.W["neck_circumference"] / (2 * np.pi)
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:24j]
    ax.plot_surface(hp * np.cos(u) * np.sin(v), 6 + hq * np.sin(u) * np.sin(v), 190 + 115 * hq / 98 * np.cos(v), color="#9aa0b4", alpha=0.35, linewidth=0)
    z = np.linspace(-60, 90, 2); th = np.linspace(0, 2 * np.pi, 40)
    T, Z = np.meshgrid(th, z)
    ax.plot_surface(neck_r * np.cos(T), neck_r * np.sin(T), Z, color="#9aa0b4", alpha=0.35, linewidth=0)
    th = np.linspace(0, 2 * np.pi, 60); z = np.linspace(-45, -200, 2)
    T, Z = np.meshgrid(th, z)
    ax.plot_surface((build.AO - 5) * np.cos(T), (build.BO - 10) * np.sin(T), Z, color="#9aa0b4", alpha=0.3, linewidth=0)


