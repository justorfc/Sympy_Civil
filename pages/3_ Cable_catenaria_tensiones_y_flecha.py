import streamlit as st
import sympy as sp
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from utils.structural_helpers import symbols_safe, validar_longitud

st.set_page_config(page_title="Cable catenaria: tensiones y flecha")
st.title("Cable catenaria: tensiones y flecha")

st.header("Datos del cable")
col1, col2 = st.columns(2)
with col1:
    L = st.number_input("Separación horizontal entre apoyos L [m]", min_value=0.01, value=20.0, step=0.1, format="%.2f")
    w = st.number_input("Peso por unidad horizontal w [kN/m]", min_value=0.001, value=1.0, step=0.01, format="%.3f")
with col2:
    delta_h = st.number_input("Diferencia de altura Δh [m] (positivo si apoyo derecho más alto)", value=0.0, step=0.1, format="%.2f")
    f_obj = st.number_input("Flecha máxima objetivo f_obj [m] (opcional)", min_value=0.0, value=0.0, step=0.1, format="%.2f")
    H_in = st.number_input("Tensión horizontal H en punto bajo [kN] (opcional)", min_value=0.0, value=0.0, step=0.1, format="%.2f")

try:
    validar_longitud(L, "separación entre apoyos")
    validar_longitud(w, "peso por unidad horizontal")
except ValueError as e:
    st.error(str(e))
    st.stop()

# --- Modelo simbólico ---
x, a, x0, C, H = symbols_safe('x a x0 C H')

# Catenaria exacta: y(x) = a·cosh((x−x0)/a) + C, a = H/w
# Apoyos en (0,0) y (L, Δh)
# Condiciones: y(0)=0, y(L)=Δh

# Resolver x0 y C en función de a, L, Δh
# y(0) = a*cosh(-x0/a) + C = 0
# y(L) = a*cosh((L-x0)/a) + C = Δh

C_expr = -a*sp.cosh(-x0/a)
yL_expr = a*sp.cosh((L-x0)/a) + C_expr

# Ecuación para x0: yL_expr = Δh
# Resolver x0 numéricamente para a dado

# Si H_in dado, a=H_in/w
if H_in > 0:
    a_val = H_in / w
    # Resolver x0
    eq_x0 = a_val*sp.cosh((L-x0)/a_val) - a_val*sp.cosh(x0/a_val) - delta_h
    x0_sol = sp.nsolve(eq_x0, x0, L/2)
    C_val = -a_val*sp.cosh(-x0_sol/a_val)
    y_expr = a_val*sp.cosh((x-x0_sol)/a_val) + C_val
    # Flecha máxima
    f_max = y_expr.subs(x, x0_sol)
    # Tensiones
    T_left = w*a_val*sp.cosh(x0_sol/a_val)
    T_right = w*a_val*sp.cosh((L-x0_sol)/a_val)
    H_val = a_val * w
elif f_obj > 0:
    # Buscar a que cumpla flecha máxima
    def flecha_a(a_num):
        x0_num = sp.nsolve(a_num*sp.cosh((L-x0)/a_num) - a_num*sp.cosh(x0/a_num) - delta_h, x0, L/2)
        C_num = -a_num*sp.cosh(-x0_num/a_num)
        return float(a_num*sp.cosh(-x0_num/a_num) + C_num - f_obj)
    try:
        from scipy.optimize import brentq
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
    except Exception:
        st.error("No se pudo encontrar una solución para la flecha objetivo con los parámetros dados.")
        st.stop()
else:
    # Caso general: a desconocido, pero se puede graficar para H arbitrario
    a_val = L/4  # valor arbitrario para graficar
    x0_sol = L/2
    C_val = -a_val*sp.cosh(-x0_sol/a_val)
    y_expr = a_val*sp.cosh((x-x0_sol)/a_val) + C_val
    f_max = y_expr.subs(x, x0_sol)
    T_left = w*a_val*sp.cosh(x0_sol/a_val)
    T_right = w*a_val*sp.cosh((L-x0_sol)/a_val)
    H_val = a_val * w

# --- Parábola aproximada ---
parab = st.checkbox("Mostrar comparación con parábola (flechas pequeñas)", value=True)
if parab:
    # y(x) = 4*f_max/L**2 * x*(L-x) + delta_h/L*x
    y_parab = 4*float(f_max)/L**2 * x*(L-x) + delta_h/L*x

# --- Gráfica del perfil ---
N = 400
x_vals = np.linspace(0, L, N)
y_func = sp.lambdify(x, y_expr, modules=["numpy"])
y_vals = y_func(x_vals)
fig = go.Figure()
fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="Catenaria exacta"))
if parab:
    y_parab_func = sp.lambdify(x, y_parab, modules=["numpy"])
    y_parab_vals = y_parab_func(x_vals)
    fig.add_trace(go.Scatter(x=x_vals, y=y_parab_vals, mode="lines", name="Parábola"))
fig.add_trace(go.Scatter(x=[0, L], y=[0, delta_h], mode="markers", name="Apoyos"))
fig.update_layout(title="Perfil del cable", xaxis_title="x [m]", yaxis_title="y [m]", legend_title="Modelo")
st.plotly_chart(fig, use_container_width=True)

# --- Tabla de resultados ---
st.subheader("Resultados")
df_res = pd.DataFrame({
    "Magnitud": ["Flecha máxima", "Tensión horizontal H", "Tensión en apoyo izquierdo", "Tensión en apoyo derecho"],
    "Valor": [float(f_max), float(H_val), float(T_left), float(T_right)],
    "Unidades": ["m", "kN", "kN", "kN"]
})
st.table(df_res)

# --- Exportar CSV ---
if st.button("Exportar resultados a CSV"):
    df_export = pd.DataFrame({
        "x [m]": x_vals,
        "y_catenaria [m]": y_vals
    })
    if parab:
        df_export["y_parabola [m]"] = y_parab_vals
    df_export.to_csv("data/ejemplo_catenaria_resultados.csv", index=False)
    st.success("Archivo exportado en data/ejemplo_catenaria_resultados.csv")

# --- Validaciones y advertencias ---
if L <= 0 or w <= 0:
    st.warning("L y w deben ser mayores que cero.")
if abs(delta_h) > L:
    st.warning("La diferencia de alturas es mayor que la separación horizontal, puede no haber solución física.")
if f_obj > 0 and (not (0 < float(f_max) <= f_obj + 1e-3)):
    st.warning("No se pudo cumplir la flecha objetivo con los parámetros dados.")

st.markdown("---")
st.markdown("Ver ejemplos de catenaria en [data/ejemplos.csv](data/ejemplos.csv)")
