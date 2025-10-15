import streamlit as st
import sympy as sp
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from utils.structural_helpers import symbols_safe, solve_positive, validar_longitud

st.set_page_config(page_title="Cercha plana: método de nudos")
st.title("Cercha plana: método de nudos")

st.header("Definición de la cercha")

# --- Entradas de nodos ---
st.subheader("Nodos (coordenadas)")
def_nodos = st.data_editor(
    pd.DataFrame({"nodo":[], "x [m]":[], "y [m]":[]}),
    num_rows="dynamic", key="nodos"
)

# --- Entradas de barras ---
st.subheader("Barras (conectividad)")
def_barras = st.data_editor(
    pd.DataFrame({"barra":[], "nodo_i":[], "nodo_j":[]}),
    num_rows="dynamic", key="barras"
)

# --- Apoyos ---
st.subheader("Apoyos")
def_apoyos = st.data_editor(
    pd.DataFrame({"nodo":[], "tipo":[]}),
    num_rows="dynamic", key="apoyos"
)

# --- Cargas puntuales ---
st.subheader("Cargas puntuales en nodos")
def_cargas = st.data_editor(
    pd.DataFrame({"nodo":[], "Fx [kN]":[], "Fy [kN]":[]}),
    num_rows="dynamic", key="cargas"
)

# --- Procesamiento de datos ---
# Nodos
nodos = {row["nodo"]: (float(row["x [m]"]), float(row["y [m]"])) for _, row in def_nodos.iterrows() if row["nodo"]}
# Barras
barras = [(row["barra"], row["nodo_i"], row["nodo_j"]) for _, row in def_barras.iterrows() if row["barra"] and row["nodo_i"] and row["nodo_j"]]
# Apoyos
apoyos = {row["nodo"]: row["tipo"] for _, row in def_apoyos.iterrows() if row["nodo"] and row["tipo"]}
# Cargas
cargas = {row["nodo"]: (float(row["Fx [kN]"] or 0), float(row["Fy [kN]"] or 0)) for _, row in def_cargas.iterrows() if row["nodo"]}

if not nodos or not barras:
    st.info("Define al menos dos nodos y una barra para continuar.")
    st.stop()

# --- Variables simbólicas para fuerzas en barras ---
N_barras = {b: symbols_safe(f'N_{b}') for b, _, _ in barras}
# Reacciones
reacciones = {}
for n, tipo in apoyos.items():
    if tipo.lower() == "pasador":
        reacciones[f"Rx_{n}"] = symbols_safe(f"Rx_{n}")
        reacciones[f"Ry_{n}"] = symbols_safe(f"Ry_{n}")
    elif tipo.lower() == "rodillo":
        reacciones[f"Ry_{n}"] = symbols_safe(f"Ry_{n}")

# --- Ensamblaje de ecuaciones de nudos ---
eqs = []
incognitas = list(N_barras.values()) + list(reacciones.values())
for n, (x0, y0) in nodos.items():
    # Barras conectadas al nodo
    barras_n = [(b, ni, nj) for b, ni, nj in barras if ni == n or nj == n]
    eq_fx = 0
    eq_fy = 0
    for b, ni, nj in barras_n:
        xi, yi = nodos[ni]
        xj, yj = nodos[nj]
        # Sentido: de i a j
        dx = xj - xi
        dy = yj - yi
        L = np.hypot(dx, dy)
        if L == 0:
            continue
        cos = (dx / L) if n == ni else (-dx / L)
        sen = (dy / L) if n == ni else (-dy / L)
        eq_fx += N_barras[b] * cos
        eq_fy += N_barras[b] * sen
    # Reacciones
    if f"Rx_{n}" in reacciones:
        eq_fx += reacciones[f"Rx_{n}"]
    if f"Ry_{n}" in reacciones:
        eq_fy += reacciones[f"Ry_{n}"]
    # Cargas
    fx, fy = cargas.get(n, (0, 0))
    eq_fx -= fx
    eq_fy -= fy
    eqs.append(eq_fx)
    eqs.append(eq_fy)

# --- Validación de isostaticidad ---
edof = 2 * len(nodos)
if len(eqs) != len(incognitas):
    st.warning(f"Sistema no isostático: ecuaciones={len(eqs)}, incógnitas={len(incognitas)}. Puede haber mecanismo o indeterminación.")

# --- Resolución simbólica ---
sols = sp.solve(eqs, incognitas, dict=True)
if not sols:
    st.error("No se pudo resolver el sistema. Revisa la geometría, apoyos y cargas.")
    st.stop()
sol = sols[0]

# --- Salidas: tabla de esfuerzos ---
data_barras = []
for b, _, _ in barras:
    Nval = sol[N_barras[b]]
    tipo = "Tensión" if Nval > 0 else "Compresión" if Nval < 0 else "Nulo"
    data_barras.append({"Barra": b, "N [kN]": float(Nval), "Tipo": tipo})
df_barras = pd.DataFrame(data_barras)

st.subheader("Esfuerzos en barras")
st.table(df_barras)

# --- Máximos ---
max_N = df_barras["N [kN]"].abs().max()
barra_max = df_barras.iloc[df_barras["N [kN]"].abs().idxmax()]["Barra"]
st.markdown(f"**Máximo |N|:** {max_N:.2f} kN en barra {barra_max}")

# --- Gráfica de la cercha ---
fig = go.Figure()
for b, ni, nj in barras:
    xi, yi = nodos[ni]
    xj, yj = nodos[nj]
    Nval = float(sol[N_barras[b]])
    color = "red" if Nval < 0 else "blue" if Nval > 0 else "gray"
    width = 2 + 6 * abs(Nval) / (max_N if max_N else 1)
    fig.add_trace(go.Scatter(
        x=[xi, xj], y=[yi, yj],
        mode="lines+markers+text",
        line=dict(color=color, width=width),
        marker=dict(size=8),
        text=[ni, nj],
        textposition="top center",
        name=f"{b}"
    ))
fig.update_layout(title="Cercha: diagrama de esfuerzos", xaxis_title="x [m]", yaxis_title="y [m]", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# --- Exportar CSV ---
if st.button("Exportar resultados a CSV"):
    df_nodos = pd.DataFrame([{"nodo": n, "x [m]": x, "y [m]": y} for n, (x, y) in nodos.items()])
    df_barras_exp = pd.DataFrame([{"barra": b, "nodo_i": ni, "nodo_j": nj} for b, ni, nj in barras])
    df_apoyos = pd.DataFrame([{"nodo": n, "tipo": t} for n, t in apoyos.items()])
    df_cargas = pd.DataFrame([{"nodo": n, "Fx [kN]": fx, "Fy [kN]": fy} for n, (fx, fy) in cargas.items()])
    df_reacciones = pd.DataFrame([{k: float(sol[v])} for k, v in reacciones.items()])
    with pd.ExcelWriter("data/ejemplo_cercha_resultados.xlsx") as writer:
        df_nodos.to_excel(writer, sheet_name="nodos", index=False)
        df_barras_exp.to_excel(writer, sheet_name="barras", index=False)
        df_apoyos.to_excel(writer, sheet_name="apoyos", index=False)
        df_cargas.to_excel(writer, sheet_name="cargas", index=False)
        df_barras.to_excel(writer, sheet_name="esfuerzos", index=False)
        df_reacciones.to_excel(writer, sheet_name="reacciones", index=False)
    st.success("Archivo exportado en data/ejemplo_cercha_resultados.xlsx")

# --- Ejemplos en data/ejemplos.csv ---
st.markdown("---")
st.markdown("Ejemplos de cerchas tipo Pratt y Howe disponibles en [data/ejemplos.csv](data/ejemplos.csv)")
