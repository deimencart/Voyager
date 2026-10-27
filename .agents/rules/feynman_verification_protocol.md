---
trigger: always_on
description: Mandatory Feynman Verification Protocol for robotics control, Ackermann kinematics, LiDAR processing, and ROS 2 algorithms.
---

# Protocolo Obligatorio Feynman (Robótica Móvil, Cinemática y Control)

Este protocolo debe ejecutarse automáticamente siempre que se diseñe, explique o implemente lógica de control cinemático, algoritmos de navegación reactiva o integración de sensores en el UGV Voyager 3:

---

## 1. 💻 Al Generar o Modificar Código de Control o Navegación
* **Cero Cajas Negras:** Describir con exactitud el modelo cinemático (modelo bicicleta Ackermann, espacios de velocidad admissible, o diagramas de cercanía ND).
* **Manejo Obligatorio de Casos Borde ($Edge\ Cases$):**
  * Vehículo en reposo absoluto ($v = 0$): asegurar que la dirección permanezca estable sin derivas numéricas.
  * Obstáculos dentro de la zona de seguridad mínima ($d < d_{\text{safety}}$): activación inmediata de maniobra de retroceso o frenado.
  * Lecturas atípicas de sensores (rayos LiDAR reflejados o ciegos): filtrado estricto de `inf` y `NaN`.
* **Mini-Test de Validación Embebido:** Incluir siempre una prueba o aserción unitaria reproducible en el bloque `if __name__ == '__main__':` que verifique la consistencia dimensional y matemática.

---

## 2. 📐 Al Explicar Conceptos de Robótica, Navegación o Control
* **Deconstrucción Desnuda (Sin Razonamientos Circulares):**
  * Explicar el fenómeno a partir de magnitudes físicas fundamentales: fuerzas de rozamiento, aceleraciones, radios de giro tangenciales y tiempos de respuesta.
* **Formalismo Matemático en LaTeX:**
  * Escribir las ecuaciones diferenciales cinemáticas y dinámicas utilizando KaTeX ($$...$$), definiendo cada variable y su unidad en el SI.
* **Grafos Conceptuales en Mermaid:**
  * Incluir obligatoriamente diagramas de flujo de datos, máquinas de estados finitos del vehículo o árboles de decisión de maniobra.

---

## 3. 📄 Al Auditar Algoritmos o Documentos Técnicos
* **Verificación de Factibilidad Física:** Auditar si el algoritmo asume capacidades no holónomas imposibles (como desplazamiento lateral directo sin radio de giro).
* **Consistencia con las Restricciones del Hardware Real:** Considerar la frecuencia de refresco del LiDAR SF40/C ($4.5 - 10\text{ Hz}$), la latencia del puerto serie UART a 921.600 bps y el tiempo de respuesta del servo de dirección.
