import streamlit as st
import sympy as sp
import numpy as np
import pandas as pd
from utils.structural_helpers import (
    symbols_safe, solve_positive, piecewise_load_to_expr,
    integrate_shear_moment, plot_piecewise,
    validar_longitud, validar_area, validar_modulo_elastico, UNIDADES
)

st.set_page_config(page_title="Viga apoyada: reacciones y diagramas")
st.title("Viga apoyada: reacciones y diagramas")

# --- Entradas ---
st.header("Datos de la viga")
col1, col2 = st.columns(2)
with col1:
    L = st.number_input("Longitud L [m]", min_value=0.01, value=6.0, step=0.1, format="%.2f")
    try:
        validar_longitud(L, "longitud de viga")
    except ValueError as e:
        st.error(str(e))
        st.stop()
with col2:
    tipo_apoyos = st.selectbox("Tipo de apoyos", ["simple-simple"], index=0)

st.subheader("Cargas puntuales")
cargas_puntuales = st.data_editor(
    pd.DataFrame({"P [kN]":[], "a [m]":[]}),
    num_rows="dynamic", key="puntuales"
)

st.subheader("Cargas distribuidas por tramos")
def_cargas = st.text_area(
    "Definición de cargas distribuidas (ejemplo: 0 3 5 uniforme; 3 6 2x+1 triangular)",
    value=""
)

st.subheader("Momentos aplicados")
momentos = st.data_editor(
    pd.DataFrame({"M [kN·m]":[], "a [m]":[]}),
    num_rows="dynamic", key="momentos"
)

peso_propio = st.checkbox("Incluir peso propio (γ=25 kN/m³, sección 0.3x0.5 m²)", value=False)

# --- Procesamiento de cargas ---
x = symbols_safe('x')
cargas_pw = []

# Cargas distribuidas por tramos
if def_cargas.strip():
    for linea in def_cargas.strip().split(';'):
        partes = linea.strip().split()
        if len(partes) >= 4:
            a, b = float(partes[0]), float(partes[1])
            expr = partes[2]
            tipo = partes[3].lower()
            if tipo == "uniforme":
                expr_pw = float(expr)
            elif tipo == "triangular":
                expr_pw = sp.sympify(expr)
            else:
                st.warning(f"Tipo de carga no reconocido: {tipo}")
                continue
            cargas_pw.append(((a, b), expr_pw, 'x'))

# Peso propio
if peso_propio:
    gamma = 25  # kN/m³
    b = 0.3
    h = 0.5
    w_pp = gamma * b * h  # kN/m
    cargas_pw.append(((0, L), w_pp, 'x'))

w_expr = piecewise_load_to_expr(cargas_pw) if cargas_pw else 0

# Cargas puntuales y momentos
puntuales = [(float(P), float(a)) for P, a in zip(cargas_puntuales["P [kN]"], cargas_puntuales["a [m]"]) if P and a]
moms = [(float(M), float(a)) for M, a in zip(momentos["M [kN·m]"], momentos["a [m]"]) if M and a]

# Validación de posiciones
for _, a in puntuales + moms:
    if not (0 <= a <= L):
        st.warning(f"Carga o momento fuera del rango [0, L]: posición {a}")

# --- Ensamblaje de ecuaciones de equilibrio ---
RA, RB = symbols_safe('RA RB')

eqs = []
# Equilibrio vertical
sum_puntuales = sum(P for P, _ in puntuales)
sum_w = sp.integrate(w_expr, (x, 0, L)) if w_expr != 0 else 0
sum_momentos = sum(M for M, _ in moms)

eqs.append(RA + RB - sum_puntuales - sum_w)
# Momento en A
mom_puntuales = sum(P * (a) for P, a in puntuales)
mom_w = sp.integrate(w_expr * (x), (x, 0, L)) if w_expr != 0 else 0
mom_moms = sum(M for M, a in moms)
eqs.append(RB * L - mom_puntuales - mom_w - mom_moms)

# --- Resolución de reacciones ---
sols = solve_positive(eqs, [RA, RB])
if not sols:
    st.error("No se pudo resolver el sistema de reacciones. Verifica las cargas y apoyos.")
    st.stop()
reacciones = sols[0]

st.subheader("Reacciones de apoyo")
st.latex(f"R_A = {sp.latex(reacciones[RA])} \,\text{{kN}}")
st.latex(f"R_B = {sp.latex(reacciones[RB])} \,\text{{kN}}")

# --- Construcción de V(x) y M(x) ---
# Suma de Heaviside para puntuales y momentos
Vx = reacciones[RA]
Mx = reacciones[RA]*x
for P, a in puntuales:
    Vx -= P * sp.Heaviside(x - a, 0)
    Mx -= P * sp.Heaviside(x - a, 0) * (x - a)
for M, a in moms:
    Mx -= M * sp.Heaviside(x - a, 0)
if w_expr != 0:
    Vw, Mw = integrate_shear_moment(w_expr, x)
    Vx -= (Vw.subs(x, x) - Vw.subs(x, 0))
    Mx -= (Mw.subs(x, x) - Mw.subs(x, 0))
Mx += reacciones[RB]*(0)  # Momento en B=0 para viga simple-simple

st.subheader("Expresiones simbólicas")
st.markdown("**Cortante V(x):**")
st.latex(f"V(x) = {sp.latex(Vx)}")
st.markdown("**Momento M(x):**")
st.latex(f"M(x) = {sp.latex(Mx)}")

# --- Cálculo de posiciones de V=0 y máximos de |M| ---
Vx_s = sp.simplify(Vx)
Mx_s = sp.simplify(Mx)
V0_pos = sp.solve(Vx_s, x)
M_abs = sp.Abs(Mx_s)
M_max_pos = sp.solve(sp.diff(M_abs, x), x)

# Filtrar soluciones reales y dentro de [0, L]
V0_pos = [float(p.evalf()) for p in V0_pos if p.is_real and 0 <= p.evalf() <= L]
M_max_pos = [float(p.evalf()) for p in M_max_pos if p.is_real and 0 <= p.evalf() <= L]

# --- Evaluación numérica y gráficos ---
N = 400
x_vals = np.linspace(0, L, N)
V_func = sp.lambdify(x, Vx_s, modules=["numpy"])
M_func = sp.lambdify(x, Mx_s, modules=["numpy"])
V_vals = V_func(x_vals)
M_vals = M_func(x_vals)

fig_v = plot_piecewise(Vx_s, x, (0, L), num=N, title="Diagrama de cortante V(x)")
fig_m = plot_piecewise(Mx_s, x, (0, L), num=N, title="Diagrama de momento M(x)")

st.subheader("Diagramas")
st.plotly_chart(fig_v, use_container_width=True)
st.plotly_chart(fig_m, use_container_width=True)

# --- Tabla de máximos ---
max_V = np.max(np.abs(V_vals))
pos_max_V = x_vals[np.argmax(np.abs(V_vals))]
max_M = np.max(np.abs(M_vals))
pos_max_M = x_vals[np.argmax(np.abs(M_vals))]

df_max = pd.DataFrame({
    "Magnitud": ["|V| máximo", "|M| máximo"],
    "Valor": [max_V, max_M],
    "Posición [m]": [pos_max_V, pos_max_M]
})
st.subheader("Máximos absolutos")
st.table(df_max)

# --- Exportar CSV ---
if st.button("Exportar resultados a CSV"):
    df_export = pd.DataFrame({
        "x [m]": x_vals,
        "V(x) [kN]": V_vals,
        "M(x) [kN·m]": M_vals
    })
    df_export.to_csv("data/ejemplo_viga_resultados.csv", index=False)
    st.success("Archivo exportado en data/ejemplo_viga_resultados.csv")

# --- Validación de equilibrio ---
sum_reacciones = float(reacciones[RA] + reacciones[RB])
sum_cargas = float(sum_puntuales + sum_w)
if abs(sum_reacciones - sum_cargas) > 1e-3:
    st.warning(f"Advertencia: el equilibrio vertical no se cumple exactamente (ΣR={sum_reacciones:.3f}, ΣCargas={sum_cargas:.3f})")
if sum_reacciones < 0:
    st.warning("Advertencia: la suma de reacciones es negativa, revisa las cargas aplicadas.")
