# 11. Compendio de Papers Seminales de SLAM y Visión

---

## 📚 Visión General del Acervo Científico

Este documento compendia, analiza críticamente y formaliza matemáticamente los doce artículos científicos seminales presentes en el laboratorio y bóvedas de investigación. Estos trabajos representan los pilares sobre los cuales se sostiene el SLAM moderno, desde los algoritmos clásicos de asociación de datos estocástica hasta las librerías multi-mapa del estado del arte.

---

### 1. Neira & Tardós (2001) — JCBB: Asociación Robusta de Datos

* **Título:** *Data Association in Stochastic Mapping Using the Joint Compatibility Branch and Bound Algorithm*
* **Autores:** José Neira y Juan D. Tardós.
* **Publicación:** *IEEE Transactions on Robotics and Automation*, Vol. 17, No. 2, pp. 130–141, 2001.
* **Problema Abordado:** El algoritmo ingenuo del vecino más cercano (*Nearest Neighbor - NN*) fracasa sistemáticamente en presencia de alta densidad de obstáculos (*clutter*) o cuando la incertidumbre angular del robot ($\sigma_\theta$) es significativa, introduciendo asociaciones falsas que destruyen el filtro estocástico.
* **Aporte Matemático Central:** Formulación del estadístico de compatibilidad conjunta (*Joint Compatibility*):
  $$D_{\mathcal{H}}^2 = \boldsymbol{\nu}_{\mathcal{H}}^T \left( \mathbf{H}_{\mathcal{H}} \mathbf{P} \mathbf{H}_{\mathcal{H}}^T + \mathbf{R}_{\mathcal{H}} \right)^{-1} \boldsymbol{\nu}_{\mathcal{H}} \le \chi^2_{2k, \alpha}$$
  Acompañado del algoritmo de búsqueda en árbol de interpretación con poda acotada (*Branch and Bound*):
  $$\text{length}(\mathcal{H}) + (m - i) \le \text{length}(\text{Best}) \implies \text{Podar rama}$$
* **Impacto:** Eliminó la fragilidad de asociación en EKF-SLAM en entornos no estructurados con telémetros láser y sónar.

---

### 2. Civera, Davison & Montiel (2008) — Parametrización por Profundidad Inversa

* **Título:** *Inverse Depth Parametrization for Monocular SLAM*
* **Autores:** Javier Civera, Andrew J. Davison y J. M. M. Montiel.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 24, No. 5, pp. 932–945, 2008.
* **Problema Abordado:** En SLAM monocular, cuando un punto 3D se observa por primera vez, su profundidad $Z$ es desconocida y puede tender a infinito (paralaje casi nulo). Representar el punto en coordenadas cartesianas euclidianas $(X, Y, Z)$ produce una distribución gaussiana extremadamente no lineal y aberrante que hace divergir al EKF.
* **Aporte Matemático Central:** Parametrización de un punto 3D mediante un vector de 6 parámetros que incluye la inversa de la profundidad $\rho = 1/d$:
  $$\mathbf{y} = [x_v, y_v, z_v, \theta, \phi, \rho]^T$$
  donde $(x_v, y_v, z_v)$ es el centro óptico de la cámara en el momento del avistamiento inicial, $(\theta, \phi)$ son los ángulos azimut y elevación del rayo óptico, y $\rho = 1/d$ es la profundidad inversa.
  * Cuando la profundidad tiende a infinito ($d \to \infty$), $\rho \to 0$, lo cual es **perfectamente lineal y gaussiano**.
  * Permite incorporar puntos inmediatamente al filtro desde el primer fotograma sin retrasar la inicialización.
* **Impacto:** Hizo viable el SLAM monocular en tiempo real (*MonoSLAM*) en exteriores y entornos de gran escala.

---

### 3. Paz, Tardós & Neira (2008) — Divide and Conquer SLAM

* **Título:** *Divide and Conquer SLAM*
* **Autores:** Lina M. Paz, Juan D. Tardós y José Neira.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 24, No. 5, pp. 1107–1120, 2008.
* **Problema Abordado:** La complejidad $\mathcal{O}(N^2)$ del EKF-SLAM clásico y la acumulación descontrolada de inconsistencia por linealizaciones en un mapa global único.
* **Aporte Matemático Central:** Fusión jerárquica de submapas estocásticos organizados en un árbol binario completo:
  * El coste computacional total para un mapa de $N$ marcas se reduce a $\mathcal{O}(N)$ amortizado por paso.
  * La consistencia estadística (NEES) se preserva porque cada submapa local de tamaño $k$ se calcula con errores angulares locales infinitesimales ($\Delta \theta \approx 0$).
* **Impacto:** Permitió cerrar bucles y construir mapas métricos exactos de miles de marcas en entornos kilométricos manteniendo la formulación estocástica de Kalman.

---

### 4. Strasdat, Montiel & Davison (2010) — ¿Por Qué Filtrar?

* **Título:** *Real-time Monocular SLAM: Why Filter?*
* **Autores:** Hauke Strasdat, J. M. M. Montiel y Andrew J. Davison.
* **Publicación:** *IEEE International Conference on Robotics and Automation (ICRA)*, pp. 2657–2664, 2010.
* **Problema Abordado:** Debate fundamental en la comunidad robótica: ¿Es mejor procesar cada fotograma con un Filtro de Kalman o descartar fotogramas intermedios y optimizar fotogramas clave (*Keyframes*) mediante Bundle Adjustment?
* **Aporte Matemático Central:** Demostración de que la ganancia de información por segundo está gobernada por la línea base estéreo ($\mathbf{t}$), no por la tasa de refresco en hercios.
  * El EKF gasta el $90\%$ de sus ciclos de CPU en actualizar correlaciones de fotogramas casi estáticos.
  * El Bundle Adjustment sobre Keyframes dispersos con un resolvedor de mínimos cuadrados no lineales (**Levenberg-Marquardt**) logra un error de trayectoria un orden de magnitud menor con el mismo presupuesto de cómputo.
* **Impacto:** Marcó el fin del dominio del EKF en SLAM visual puro y dio origen a las arquitecturas modernas basadas en optimización de grafos (PTAM, ORB-SLAM, SVO).

---

### 5. Gálvez-López & Tardós (2012) — DBoW2: Reconocimiento Rápido de Lugares

* **Título:** *Bags of Binary Words for Fast Place Recognition in Image Sequences*
* **Autores:** Dorian Gálvez-López y Juan D. Tardós.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 28, No. 5, pp. 1188–1197, 2012.
* **Problema Abordado:** Reconocimiento de lugares invariante a punto de vista e iluminación en tiempo real sin requerir descriptores de coma flotante lentos como SIFT o SURF.
* **Aporte Matemático Central:** 
  * Árbol de vocabulario $k$-means jerárquico discretizado para descriptores binarios (BRIEF/ORB).
  * Función de similitud $L_1$ con ponderación TF-IDF y normalización respecto a la imagen previa:
    $$s(\mathbf{v}_1, \mathbf{v}_2) = 1 - \frac{1}{2} \|\mathbf{v}_1 - \mathbf{v}_2\|_{L_1}$$
  * Estructura dual: **Índice Invertido** (consultas de candidatos en $\approx 2\text{ ms}$) e **Índice Directo** (matching de características 2D-2D en $\approx 1\text{ ms}$).
* **Impacto:** Estándar absoluto de la industria robótica para detección de cierres de bucle y relocalización global instantánea.

---

### 6. Hornung et al. (2013) — OctoMap: Mapeo Probabilístico 3D Basado en Octrees

* **Título:** *OctoMap: An Efficient Probabilistic 3D Mapping Framework Based on Octrees*
* **Autores:** Armin Hornung, Kai M. Wurm, Maren Bennewitz, Cyrill Stachniss y Wolfram Burgard.
* **Publicación:** *Autonomous Robots*, Vol. 34, No. 3, pp. 189–206, 2013.
* **Problema Abordado:** Representación volumétrica eficiente de entornos 3D continuos sin asumir un volumen predefinido ni saturar la memoria RAM.
* **Aporte Matemático Central:** Modelo de ocupación log-odds sobre un árbol jerárquico de octantes (*Octree*):
  $$L(n \mid z_{1:t}) = L(n \mid z_{1:t-1}) + L(n \mid z_t)$$
  * Poda de nodos con probabilidad de ocupación homogénea (reducción masiva de memoria).
  * Distingue de forma estricta entre espacio libre (*free space*), ocupado (*occupied*) y completamente desconocido (*unknown*).
* **Impacto:** Utilizado universalmente en ROS y navegación robótica para detección de colisiones, planificación de trayectorias 3D y filtrado de nubes de puntos de LiDAR.

---

### 7. Mur-Artal, Montiel & Tardós (2015) — ORB-SLAM Monocular

* **Título:** *ORB-SLAM: A Versatile and Accurate Monocular SLAM System*
* **Autores:** Raúl Mur-Artal, J. M. M. Montiel y Juan D. Tardós.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 31, No. 5, pp. 1147–1163, 2015.
* **Problema Abordado:** Creación de un sistema monocular completo y robusto capaz de operar en tiempo real en entornos interiores y exteriores, con recuperación ante pérdidas y cierre de bucles.
* **Aporte Matemático Central:**
  * Uso transversal de características **ORB** en todas las tareas: Tracking, Mapping, Relocalization y Loop Closing.
  * Arquitectura concurrente en tres hilos paralelos (*Tracking, Local Mapping, Loop Closing*).
  * Grafo de Covisibilidad y Grafo Esencial para optimizaciones de pose-graph instantáneas.
  * Cierre de bucle con alineación en $Sim(3)$ para corregir la deriva de escala.

---

### 8. Mur-Artal & Tardós (2017) — ORB-SLAM2

* **Título:** *ORB-SLAM2: An Open-Source SLAM System for Monocular, Stereo and RGB-D Cameras*
* **Autores:** Raúl Mur-Artal y Juan D. Tardós.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 33, No. 5, pp. 1255–1262, 2017.
* **Problema Abordado:** Extensión del framework monocular a cámaras estéreo calibradas y sensores RGB-D.
* **Aporte Matemático Central:**
  * Tratamiento unificado de mediciones estéreo y de profundidad mediante coordenadas monocular emparejadas $(u_L, v_L, u_R)$, donde $u_R = u_L - \frac{f_x \cdot b}{Z}$.
  * Inicialización métrica instantánea desde el primer fotograma (elimina la necesidad de paralaje inicial monocular).
  * Cierre de bucle en $SE(3)$ en vez de $Sim(3)$ gracias a la escala métrica intrínseca.

---

### 9. Campos et al. (2021) — ORB-SLAM3: El Estado del Arte Visual-Inercial Multi-Mapa

* **Título:** *ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM*
* **Autores:** Carlos Campos, Richard Elvira, Juan J. Gómez Rodríguez, J. M. M. Montiel y Juan D. Tardós.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 37, No. 6, pp. 1874–1890, 2021.
* **Aportes Revolucionarios:**
  1. **Inicialización Inercial en 2 Segundos:** Algoritmo de máxima verosimilitud que resuelve escala, gravedad, velocidad y biases en tiempo récord.
  2. **Arquitectura ATLAS (Multi-Map):** Gestión de submapas discontinuos activos e inactivos, permitiendo operación de por vida (*Lifelong SLAM*) ante oclusiones totales.
  3. Soporte para lentes gran angular y ojo de pez (*Fisheye*) mediante el modelo de Kannala-Brandt.

---

### 10. Forster et al. (2017) — Preintegración de IMU en Manifolds

* **Título:** *On-Manifold Preintegration for Real-Time Visual-Inertial Odometry*
* **Autores:** Christian Forster, Luca Carlone, Frank Dellaert y Davide Scaramuzza.
* **Publicación:** *IEEE Transactions on Robotics*, Vol. 33, No. 1, pp. 1–21, 2017.
* **Aporte Matemático Central:** Integración de la aceleración y velocidad angular en el marco local relativo $\mathbf{R}_i^T$, junto con el cálculo analítico de Jacobianos en el álgebra $\mathfrak{so}(3)$ para actualizar las variables frente a cambios de bias sin reintegrar las mediciones de IMU en el solver de optimización.

---

### 11. Castellanos et al. (2004) — SLAM Robocéntrico

* **Título:** *Robocentric SLAM: A Local Map Approach for Improving Efficiency and Consistency*
* **Autores:** José A. Castellanos, Ricardo Martínez-Cantín, Juan D. Tardós y José Neira.
* **Publicación:** *IFAC Symposium on Intelligent Autonomous Vehicles (IAV)*, 2004.
* **Aporte Matemático Central:** Reformulación de las ecuaciones de SLAM expresando todas las marcas del entorno con respecto al marco de referencia móvil del robot en vez de un origen mundial estático.
  * Demostró que al eliminar la referencia inercial global fija, **la falsa ganancia de información angular desaparece**, restaurando la consistencia estocástica (NEES) del filtro.

---

### 12. Barfoot (2017 / 2024) — Estimación de Estado para Robótica Móvil

* **Título:** *State Estimation for Robotics*
* **Autor:** Timothy D. Barfoot.
* **Editorial:** Cambridge University Press.
* **Aporte Pedagógico y Matemático:** Tratado definitivo sobre grupos de Lie matriciales ($SO(3), SE(3)$), ecuaciones diferenciales estocásticas, estimación por mínimos cuadrados ponderados en manifolds y optimización de grafos de factores con matrices dispersas.
