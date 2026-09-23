"""Constant-molar-overflow ternary column with a replaceable bubble-state surface.

Order: sec-butyl alcohol, sec-butyl acetate, DMF. Stage N is the reboiler;
the total condenser is excluded. Both feeds have q=1. Flows are mol/s.
"""

import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

F = 1.0
Z = np.array([0.5, 0.5, 0.0])
P = 101.3
S = 32 * ((74.1216 + 116.15828) / 2) / 73.09378
D = 0.5 * 0.98 / 0.995


def xs(rs):
    r, s = np.asarray(rs).T
    return np.c_[(1 - r) * (1 - s), r * (1 - s), s]


def rs_from_x(x):
    return np.c_[x[:, 1] / np.maximum(x[:, 0] + x[:, 1], 1e-30), x[:, 2]]


def flows(N, nf, ns, R, Sflow=S, Dflow=D):
    feeds = np.zeros((N, 3))
    feeds[nf - 1] += Z * F
    feeds[ns - 1] += np.array([0, 0, Sflow])
    L = R * Dflow + np.cumsum(feeds.sum(axis=1))
    V = (R + 1) * Dflow
    B = F + Sflow - Dflow
    return feeds, L, V, B


def residual(rs, surf, N, nf, ns, R, Sflow=S, Dflow=D, full=False):
    x, y, T = surf.state(np.asarray(rs).reshape(N, 2))
    feeds, L, V, B = flows(N, nf, ns, R, Sflow, Dflow)
    bal = feeds - L[:, None] * x - V * y
    bal[1:] += L[:-1, None] * x[:-1]
    bal[:-1] += V * y[1:]
    bal[0] += R * Dflow * y[0]
    bal[-1] += (L[-1] - B) * x[-1]
    if full:
        return bal, x, y, T
    return bal[:, [0, 2]].ravel()


def solve(surf, N, nf, ns, R, Sflow=S, Dflow=D, init=None, maxeval=250):
    if init is None:
        r = np.linspace(0.96, 0.018, N)
        feeds, L, V, B = flows(N, nf, ns, R, Sflow, Dflow)
        s = np.where(np.arange(N) < ns - 1, 0.001, Sflow / (L + 1e-10))
        s = np.clip(s, 1e-6, 0.99)
        init = np.c_[r, s]
    elif len(init) != N:
        init = np.c_[
            [
                np.interp(
                    np.linspace(0, 1, N), np.linspace(0, 1, len(init)), init[:, k]
                )
                for k in range(2)
            ]
        ].T
    # Damped sparse Newton on two independent stage component balances.
    # Derivatives are local, obtained by simultaneously perturbing each
    # independent stage state; neighboring-stage flow derivatives assembled.
    init = np.clip(init, 1e-10, 1 - 1e-10)
    for iteration in range(100):
        bal, x, y, T = residual(init, surf, N, nf, ns, R, Sflow, Dflow, True)
        f = bal[:, [0, 2]].ravel()
        if np.max(abs(f)) < 2e-10:
            break
        feeds, L, V, B = flows(N, nf, ns, R, Sflow, Dflow)
        dx = np.zeros((N, 2, 2))
        dy = np.zeros_like(dx)
        for k in range(2):
            up = init.copy()
            dn = init.copy()
            up[:, k] += 1e-6
            dn[:, k] -= 1e-6
            xp, yp, _ = surf.state(up)
            xm, ym, _ = surf.state(dn)
            dx[:, :, k] = (xp - xm)[:, [0, 2]] / 2e-6
            dy[:, :, k] = (yp - ym)[:, [0, 2]] / 2e-6
        jac = lil_matrix((2 * N, 2 * N))
        for j in range(N):
            diag = -(B if j == N - 1 else L[j]) * dx[j] - V * dy[j]
            if j == 0:
                diag += R * Dflow * dy[j]
            jac[2 * j : 2 * j + 2, 2 * j : 2 * j + 2] = diag
            if j > 0:
                jac[2 * j : 2 * j + 2, 2 * j - 2 : 2 * j] = L[j - 1] * dx[j - 1]
            if j < N - 1:
                jac[2 * j : 2 * j + 2, 2 * j + 2 : 2 * j + 4] = V * dy[j + 1]
        step = spsolve(jac.tocsr(), -f).reshape(N, 2)
        if not np.all(np.isfinite(step)):
            break
        frac = np.minimum(
            np.where(step > 0, (1 - 1e-12 - init) / np.maximum(step, 1e-100), np.inf),
            np.where(step < 0, (init - 1e-12) / np.maximum(-step, 1e-100), np.inf),
        )
        a = min(1.0, 0.99 * float(frac.min()))
        old = np.linalg.norm(f)
        for backtrack in range(18):
            trial = init + a * step
            ff = residual(trial, surf, N, nf, ns, R, Sflow, Dflow)
            if np.linalg.norm(ff) < old:
                break
            a *= 0.5
        if a < 1e-10:
            break
        init = trial
    sp = lil_matrix((2 * N, 2 * N), dtype=int)
    for j in range(N):
        sp[2 * j : 2 * j + 2, 2 * max(0, j - 1) : 2 * min(N, j + 2)] = 1
    scale = (R + 1) * Dflow + Sflow + F

    def fun(v):
        return residual(v, surf, N, nf, ns, R, Sflow, Dflow) / scale

    sol = least_squares(
        fun,
        np.clip(init, 1e-10, 1 - 1e-10).ravel(),
        bounds=(1e-12, 1 - 1e-12),
        jac_sparsity=sp.tocsr(),
        xtol=2e-11,
        ftol=2e-11,
        gtol=1e-11,
        max_nfev=maxeval,
        tr_options={"atol": 1e-12, "btol": 1e-12},
    )
    rs = sol.x.reshape(N, 2)
    bal, x, y, T = residual(rs, surf, N, nf, ns, R, Sflow, Dflow, True)
    mass = np.max(np.abs(bal))
    globalbal = (
        F * Z + Sflow * np.array([0, 0, 1]) - Dflow * y[0] - (F + Sflow - Dflow) * x[-1]
    )
    return dict(
        N=N,
        nf=nf,
        ns=ns,
        R=R,
        S=Sflow,
        D=Dflow,
        B=F + Sflow - Dflow,
        xD=y[0].tolist(),
        xB=x[-1].tolist(),
        recovery=Dflow * y[0, 1] / 0.5,
        mass_residual=float(mass),
        global_residual=float(np.max(abs(globalbal))),
        nfev=sol.nfev,
        success=bool(mass < 1e-7),
        rs=rs.tolist(),
        x=x.tolist(),
        y=y.tolist(),
        T=T.tolist(),
    )
