import streamlit as st
import sympy

st.set_page_config(
    page_title="Ingeniería Civil — Estructuras con SymPy",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("Ingeniería Civil — Estructuras con SymPy")

st.markdown("""
Este proyecto es una colección de herramientas interactivas para resolver problemas clásicos de ingeniería estructural usando Python, SymPy y Streamlit.

**Páginas disponibles:**
- **Viga apoyada: reacciones y diagramas**
- **Cercha plana: método de nudos**
- **Cable catenaria: tensiones y flecha**

---

### ¿Cómo usar?
1. Selecciona una página desde el menú lateral o superior.
2. Ingresa los datos solicitados en cada herramienta.
3. Visualiza resultados, diagramas y descarga ejemplos desde la sección de datos.

---

[Ver ejemplos de datos](data/ejemplos.csv)
""")

with st.sidebar:
    st.header("Verificación de versiones")
    st.write(f"**SymPy:** {sympy.__version__}")
    try:
        import streamlit as st_pkg
        st.write(f"**Streamlit:** {st_pkg.__version__}")
    except Exception:
        st.write("No se pudo verificar la versión de Streamlit.")

    st.markdown("---")
    st.info("Selecciona una página para comenzar.")
