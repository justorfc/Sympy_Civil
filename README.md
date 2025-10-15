## Cómic: Confirma, sincroniza y actualiza tu repositorio en GitHub

---

**Viñeta 1:**  
👩‍💻 (Pensando): “¡Listo! Terminé de ajustar el código y corregir los errores.”

**Viñeta 2:**  
💻 (Terminal):  
```bash
git status
```
👩‍💻: “Primero, reviso los cambios pendientes…”

**Viñeta 3:**  
💻 (Terminal):  
```bash
git add .
git commit -m "Correcciones y mejoras finales"
```
👩‍💻: “Confirmo los cambios con un buen mensaje.”

**Viñeta 4:**  
💻 (Terminal):  
```bash
git pull origin main
```
👩‍💻: “Sincronizo para evitar conflictos.”

**Viñeta 5:**  
💻 (Terminal):  
```bash
git push origin main
```
👩‍💻: “¡Actualizo el repositorio en GitHub y comparto mi trabajo!”

---
# Ingeniería Civil — Estructuras con SymPy

## Propósito
Aplicación interactiva para resolver problemas clásicos de ingeniería estructural (vigas, cerchas y cables) usando Python, SymPy y Streamlit. Permite análisis simbólico y numérico, visualización de resultados y exportación de datos.

## Requisitos
- Python 3.8+
- streamlit
- sympy
- numpy
- pandas
- plotly
- scipy

## Instalación y ejecución

### Local
1. Clona el repositorio y entra al directorio:
	 ```bash
	 git clone https://github.com/justorfc/Sympy_Civil.git
	 cd Sympy_Civil
	 ```
2. Crea y activa un entorno virtual:
	 ```bash
	 python3 -m venv .venv
	 source .venv/bin/activate
	 ```
3. Instala dependencias:
	 ```bash
	 pip install -r requirements.txt
	 ```

4. Ejecuta la app:
	 ```bash
	 # Opción recomendada (VS Code/Codespaces):
	 # Usa la tarea "Run Streamlit App" (Ctrl+Shift+B o paleta de comandos)
	 # O manualmente:
	 streamlit run app.py --server.port=8501 --server.address=0.0.0.0
	 ```
5. Abre el navegador en la URL pública que se muestra en la terminal (en Codespaces, usa el botón "Open in Browser").

### Recarga y diagnóstico
- Para recargar la app tras cambios, usa el botón "Rerun" de Streamlit o recarga la página.
- Si hay errores o cálculos lentos, busca mensajes de estado en la interfaz (st.status o st.info).

### Codespaces
- El entorno y dependencias se configuran automáticamente.
- Solo ejecuta:
	```bash
	streamlit run app.py
	```

## Descripción de páginas

### 1. Viga apoyada: reacciones y diagramas
- **Ecuaciones base:**
	- Equilibrio: $\sum F_y = 0$, $\sum M = 0$
	- Cortante: $V(x) = V_0 - \int_0^x w(x) dx - \sum P_i H(x-a_i)$
	- Momento: $M(x) = M_0 + \int_0^x V(x) dx - \sum M_i H(x-a_i)$
- **Supuestos:** viga isostática, apoyos simples, cargas verticales.

### 2. Cercha plana: método de nudos
- **Ecuaciones base:**
	- Para cada nudo: $\sum F_x = 0$, $\sum F_y = 0$
	- Fuerzas axiales: $N_{ij}$ positivas (tensión), negativas (compresión)
- **Supuestos:** cercha plana, barras biarticuladas, cargas en nodos, sistema isostático.

### 3. Cable catenaria: tensiones y flecha
- **Ecuaciones base:**
	- Catenaria: $y(x) = a \cosh\left(\frac{x-x_0}{a}\right) + C$, $a = H/w$
	- Parábola: $y(x) \approx 4f/L^2 \cdot x(L-x) + \Delta h/L \cdot x$
- **Supuestos:** cable flexible, peso propio, sin rigidez a flexión.

## Guía de entrada de datos
- **Viga:**
	- Longitud, tipo de apoyos, cargas puntuales (P, posición), distribuidas (intervalo, expresión), momentos, peso propio.
- **Cercha:**
	- Nodos (nombre, x, y), barras (conectividad), apoyos (tipo y nodo), cargas nodales.
- **Cable:**
	- Separación horizontal, diferencia de altura, peso por unidad, flecha objetivo o tensión horizontal.
- Usa el archivo `data/ejemplos.csv` como referencia de formato.

## Exportación de resultados
- Cada página permite exportar resultados y tablas a archivos `.csv` o `.xlsx` en la carpeta `data/`.

## Resolución de problemas típicos
- **No se resuelve el sistema:** verifica que el número de ecuaciones coincida con el de incógnitas y que los datos sean físicamente posibles.
- **Advertencias de equilibrio:** revisa las cargas y apoyos, y que las posiciones estén dentro del rango.
- **Resultados inesperados:** revisa unidades y signos de cargas.

## Referencias breves
- Beer, F.P., Johnston, E.R. (2015). "Mecánica Vectorial para Ingenieros: Estática".
- Hibbeler, R.C. (2016). "Análisis Estructural".
- Timoshenko, S.P., Young, D.H. (1965). "Elements of Strength of Materials".
