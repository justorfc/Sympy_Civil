import pytest
import sympy as sp
import numpy as np
from utils.structural_helpers import integrate_shear_moment

# --- Test integrate_shear_moment ---
def test_integrate_shear_moment_uniform():
    x = sp.symbols('x')
    w = 5  # carga uniforme
    Vx, Mx = integrate_shear_moment(w, x)
    assert Vx.has(sp.Symbol('C1'))
    assert Mx.has(sp.Symbol('C2'))
    # Deben ser expresiones finitas
    assert sp.oo not in Vx.atoms()
    assert sp.oo not in Mx.atoms()

def test_integrate_shear_moment_piecewise():
    x = sp.symbols('x')
    w = sp.Piecewise((2, (x>=0)&(x<=2)), (0, True))
    Vx, Mx = integrate_shear_moment(w, x)
    assert Vx.has(sp.Symbol('C1'))
    assert Mx.has(sp.Symbol('C2'))
    assert sp.oo not in Vx.atoms()
    assert sp.oo not in Mx.atoms()

# --- Test cercha: esfuerzos consistentes ---
def test_cercha_signos():
    # Ejemplo simple tipo triángulo
    nodos = {'A': (0,0), 'B': (4,0), 'C': (2,3)}
    barras = [('AB','A','B'),('AC','A','C'),('BC','B','C')]
    apoyos = {'A': 'pasador', 'B': 'rodillo'}
    cargas = {'C': (0, -10)}
    from utils.structural_helpers import symbols_safe
    N_barras = {b: symbols_safe(f'N_{b}') for b,_,_ in barras}
    reacciones = {'Rx_A': sp.Symbol('Rx_A'), 'Ry_A': sp.Symbol('Ry_A'), 'Ry_B': sp.Symbol('Ry_B')}
    eqs = []
    for n, (x0, y0) in nodos.items():
        barras_n = [(b, ni, nj) for b, ni, nj in barras if ni == n or nj == n]
        eq_fx = 0
        eq_fy = 0
        for b, ni, nj in barras_n:
            xi, yi = nodos[ni]
            xj, yj = nodos[nj]
            L = np.hypot(xj-xi, yj-yi)
            if L == 0:
                continue
            cos = (xj-xi)/L if n==ni else -(xj-xi)/L
            sen = (yj-yi)/L if n==ni else -(yj-yi)/L
            eq_fx += N_barras[b]*cos
            eq_fy += N_barras[b]*sen
        if f'Rx_{n}' in reacciones:
            eq_fx += reacciones[f'Rx_{n}']
        if f'Ry_{n}' in reacciones:
            eq_fy += reacciones[f'Ry_{n}']
        fx, fy = cargas.get(n, (0,0))
        eq_fx -= fx
        eq_fy -= fy
        eqs.append(eq_fx)
        eqs.append(eq_fy)
    incognitas = list(N_barras.values()) + list(reacciones.values())
    sol = sp.solve(eqs, incognitas, dict=True)[0]
    # Tensiones y compresiones coherentes
    Nvals = [float(sol[N_barras[b]]) for b in N_barras]
    assert all(np.isfinite(Nvals))
    # Al menos una barra en tensión y una en compresión
    assert any(n > 0 for n in Nvals)
    assert any(n < 0 for n in Nvals)

# --- Test cable: flecha y tensiones positivas ---
def test_cable_flecha_tensiones():
    L = 20
    delta_h = 0
    w = 1.2
    f_obj = 2.5
    x, a, x0, C = sp.symbols('x a x0 C')
    from scipy.optimize import brentq
    def flecha_a(a_num):
        x0_num = sp.nsolve(a_num*sp.cosh((L-x0)/a_num) - a_num*sp.cosh(x0/a_num) - delta_h, x0, L/2)
        C_num = -a_num*sp.cosh(-x0_num/a_num)
        return float(a_num*sp.cosh(-x0_num/a_num) + C_num - f_obj)
    a_min = 0.01
    a_max = 10*L
    a_val = brentq(flecha_a, a_min, a_max)
    x0_sol = sp.nsolve(a_val*sp.cosh((L-x0)/a_val) - a_val*sp.cosh(x0/a_val) - delta_h, x0, L/2)
    C_val = -a_val*sp.cosh(-x0_sol/a_val)
    y_expr = a_val*sp.cosh((x-x0_sol)/a_val) + C_val
    f_max = y_expr.subs(x, x0_sol)
    T_left = w*a_val*sp.cosh(x0_sol/a_val)
    T_right = w*a_val*sp.cosh((L-x0_sol)/a_val)
    H_val = a_val * w
    # Todas las tensiones y flecha deben ser positivas y finitas
    for val in [f_max, T_left, T_right, H_val]:
        assert float(val) > 0
        assert np.isfinite(float(val))
