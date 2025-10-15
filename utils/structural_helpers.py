import sympy as sp
import numpy as np
import plotly.graph_objs as go
from sympy import Piecewise, symbols, Symbol
from typing import List, Tuple, Dict, Any, Union


def symbols_safe(names: Union[str, List[str]], **kwargs) -> Union[Symbol, Tuple[Symbol, ...]]:
    """
    Crea símbolos de SymPy con nombres LaTeX legibles para expresiones matemáticas.
    Args:
        names: Nombre o lista de nombres de los símbolos.
        **kwargs: Argumentos adicionales para sympy.symbols.
    Returns:
        Símbolo o tupla de símbolos de SymPy.
    """
    if isinstance(names, str):
        names = [n.strip() for n in names.replace(',', ' ').split()]
    return symbols(names, **kwargs)


def solve_positive(system, vars_target):
    """
    Resuelve un sistema usando sympy.solve y filtra solo soluciones reales y positivas.
    Args:
        system: Ecuación o lista de ecuaciones.
        vars_target: Variable o lista de variables a resolver.
    Returns:
        Lista de soluciones reales y positivas.
    """
    sols = sp.solve(system, vars_target, dict=True)
    filtered = []
    for sol in sols:
        if all(sp.im(sol[v]) == 0 and sp.re(sol[v]) > 0 for v in vars_target):
            filtered.append({v: sp.re(sol[v]) for v in vars_target})
    return filtered


def piecewise_load_to_expr(definicion: List[Tuple[Tuple[float, float], Any, str]]) -> Piecewise:
    """
    Convierte una definición de carga distribuida por tramos a una expresión Piecewise de SymPy.
    Args:
        definicion: Lista de tuplas ((a, b), expr, var), donde (a, b) es el intervalo,
                    expr es la expresión de la carga, var es el nombre de la variable.
    Returns:
        Expresión Piecewise de SymPy.
    """
    piezas = []
    for (a, b), expr, var in definicion:
        x = symbols_safe(var)
        piezas.append((expr, (x >= a) & (x <= b)))
    return Piecewise(*piezas)


def integrate_shear_moment(w_expr, x=None):
    """
    Calcula V(x) y M(x) a partir de una carga distribuida w(x) por integración simbólica.
    Args:
        w_expr: Expresión de carga (puede ser Piecewise).
        x: Variable de integración (opcional).
    Returns:
        Tuple (V(x), M(x))
    """
    if x is None:
        x = list(w_expr.free_symbols)[0]
    Vx = -sp.integrate(w_expr, x) + sp.Symbol('C1')
    Mx = sp.integrate(Vx, x) + sp.Symbol('C2')
    return Vx, Mx


def plot_piecewise(expr, x, dominio: Tuple[float, float], num=400, title=""):
    """
    Grafica una función por tramos (Piecewise o similar) usando plotly.
    Args:
        expr: Expresión simbólica (Piecewise o función de x).
        x: Variable simbólica.
        dominio: (xmin, xmax) del eje x.
        num: Número de puntos.
        title: Título del gráfico.
    Returns:
        Figura de plotly.
    """
    x_vals = np.linspace(dominio[0], dominio[1], num)
    f_lambd = sp.lambdify(x, expr, modules=["numpy"])
    y_vals = f_lambd(x_vals)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=str(expr)))
    fig.update_layout(title=title, xaxis_title=str(x), yaxis_title="y")
    return fig

# Validadores físicos

def validar_longitud(valor, nombre="longitud"):
    """
    Valida que una longitud sea positiva.
    Args:
        valor: Valor a validar.
        nombre: Nombre de la variable (para mensajes).
    Raises:
        ValueError: Si el valor no es positivo.
    """
    if valor <= 0:
        raise ValueError(f"{nombre.capitalize()} debe ser mayor que cero. Valor recibido: {valor}")
    return valor

def validar_modulo_elastico(valor, nombre="módulo elástico"):
    """
    Valida que el módulo elástico sea positivo.
    Args:
        valor: Valor a validar.
        nombre: Nombre de la variable (para mensajes).
    Raises:
        ValueError: Si el valor no es positivo.
    """
    if valor <= 0:
        raise ValueError(f"{nombre.capitalize()} debe ser mayor que cero. Valor recibido: {valor}")
    return valor

def validar_area(valor, nombre="área"):
    """
    Valida que el área sea positiva.
    Args:
        valor: Valor a validar.
        nombre: Nombre de la variable (para mensajes).
    Raises:
        ValueError: Si el valor no es positivo.
    """
    if valor <= 0:
        raise ValueError(f"{nombre.capitalize()} debe ser mayor que cero. Valor recibido: {valor}")
    return valor

# Unidades informativas (no conversión, solo referencia)
UNIDADES = {
    "longitud": "m",
    "fuerza": "N",
    "momento": "N·m",
    "módulo_elástico": "Pa",
    "área": "m²",
    "carga_lineal": "N/m",
}
