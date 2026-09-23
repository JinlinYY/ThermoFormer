"""Binary McCabe--Thiele calculations for SI Section S7.2."""

import math
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

F, Z, XD, RECOVERY = 1.0, 0.466, 0.995, 0.98
D = F * Z * RECOVERY / XD
B = F - D
XB = (F * Z - D * XD) / B


def curve(x, y, kind):
    x, y = np.asarray(x), np.asarray(y)
    assert np.all(np.diff(x) > 0) and np.all(np.diff(y) > 0)
    if kind == "pchip":
        return PchipInterpolator(x, y, extrapolate=False)
    return lambda a: np.interp(a, x, y)


def inverse(eq, y):
    return brentq(lambda x: float(eq(x)) - y, 0, 1, xtol=1e-13)


def minimum_reflux(eq):
    # q=1. Check possible pinches in BOTH sections, not only at the feed.
    xr = np.linspace(Z, XD - 1e-10, 50001)
    xs = np.linspace(XB + 1e-10, Z, 50001)
    rect = (XD - eq(xr)) / (XD - xr)
    ymax_feed = XB + (eq(xs) - XB) * (Z - XB) / (xs - XB)
    strip = (XD - ymax_feed) / (XD - Z)
    slope = max(0.0, float(rect.max()), float(strip.max()))
    if slope >= 1:
        raise ValueError("Requested separation infeasible under these assumptions")
    return slope / (1 - slope)


def stages(eq, reflux):
    total = math.isinf(reflux)
    if total:
        rect = strip = lambda x: x
    else:
        lr, vr = reflux * D, (reflux + 1) * D
        ls, vs = lr + F, vr  # saturated-liquid feed q=1

        def rect(x):
            return (lr * x + D * XD) / vr

        def strip(x):
            return (ls * x - B * XB) / vs

        assert abs(rect(Z) - strip(Z)) < 1e-12
        grid = np.linspace(XB, XD, 10001)
        lines = np.where(grid >= Z, rect(grid), strip(grid))
        if np.min(eq(grid) - lines) <= 0:
            raise ValueError("Pinch or operating line above equilibrium curve")
    y, previous = XD, XD
    path, rows, feed = [(XD, XD)], [], None
    for n in range(1, 501):
        x = inverse(eq, y)
        if x >= previous - 1e-12:
            raise ValueError("No stagewise separation progress")
        section = "rectifying" if x > Z else "stripping"
        if feed is None and section == "stripping":
            feed = n
        rows.append(
            {
                "stage_from_top": n,
                "x_liquid_heptane": x,
                "y_vapor_heptane": y,
                "section": section,
                "equilibrium_interpolation_residual": abs(float(eq(x)) - y),
            }
        )
        path.append((x, y))
        if x <= XB:
            return {
                "integer_equilibrium_stages_including_reboiler": n,
                "feed_stage_from_top": None if total else feed,
                "stage_profile": rows,
                "path": path,
            }
        y = float(rect(x) if section == "rectifying" else strip(x))
        path.append((x, y))
        previous = x
    raise ValueError("Stage limit exceeded")


def tests():
    # Independent analytical constant-alpha total-reflux reference.
    alpha = 2.5

    def eq(x):
        return alpha * np.asarray(x) / (1 + (alpha - 1) * np.asarray(x))

    analytic = math.log((XD / (1 - XD)) / (XB / (1 - XB))) / math.log(alpha)
    assert stages(eq, math.inf)[
        "integer_equilibrium_stages_including_reboiler"
    ] == math.ceil(analytic)
    expected_rmin = (XD - float(eq(Z))) / (float(eq(Z)) - Z)
    rmin = minimum_reflux(eq)
    assert abs(rmin - expected_rmin) < 1e-8
    low = stages(eq, 1.2 * rmin)["integer_equilibrium_stages_including_reboiler"]
    high = stages(eq, 2 * rmin)["integer_equilibrium_stages_including_reboiler"]
    assert low >= high
    try:
        stages(eq, 0.99 * rmin)
    except ValueError:
        pass
    else:
        raise AssertionError("Subminimum reflux was not rejected")
    assert abs(D + B - F) < 1e-12 and abs(D * XD + B * XB - F * Z) < 1e-12
    assert abs(D * XD / (F * Z) - RECOVERY) < 1e-12
    return [
        "constant-alpha Fenske stage count",
        "analytical minimum reflux",
        "reflux versus stage trend",
        "reject subminimum reflux",
        "product material balances",
    ]
