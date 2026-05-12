# 8-Puzzle Solver — Búsqueda A\* con Heurística Manhattan

> Proyecto de la asignatura **Inteligencia Artificial**  
> Implementación interactiva del algoritmo A\* para resolver el clásico 8-puzzle.

---

## Demo

Abre `8puzzle_astar_solver.html` directamente en cualquier navegador moderno — no requiere servidor ni dependencias locales.

---

## ¿Qué es el 8-Puzzle?

El **8-puzzle** es un tablero de 3×3 con 8 fichas numeradas (1–8) y un espacio vacío. El objetivo es alcanzar el estado meta **S\*** mediante deslizamientos de fichas adyacentes al hueco:

```
Estado inicial (ejemplo)     Estado objetivo S*
┌───┬───┬───┐                ┌───┬───┬───┐
│ 2 │   │ 3 │                │ 1 │ 2 │ 3 │
├───┼───┼───┤                ├───┼───┼───┤
│ 1 │ 5 │ 6 │   ──A*──►      │ 4 │ 5 │ 6 │
├───┼───┼───┤                ├───┼───┼───┤
│ 4 │ 7 │ 8 │                │ 7 │ 8 │   │
└───┴───┴───┘                └───┴───┴───┘
```

---

## Algoritmo A\*

A\* es un algoritmo de búsqueda informada que garantiza encontrar la solución **óptima** (menor número de movimientos) siempre que la heurística sea **admisible**.

### Función de evaluación

```
f(n) = g(n) + h(n)
```

| Término | Significado                                               |
| ------- | --------------------------------------------------------- |
| `g(n)`  | Costo acumulado desde el estado inicial hasta el nodo `n` |
| `h(n)`  | Estimación heurística del costo restante hasta S\*        |
| `f(n)`  | Prioridad total del nodo (menor = explorar primero)       |

### Heurística: Distancia Manhattan

Para cada ficha `t` en posición `(r, c)` y posición objetivo `(gr, gc)`:

```
h(n) = Σ |r - gr| + |c - gc|   para todo t ≠ 0
```

Esta heurística es **admisible** (nunca sobreestima el costo real) y **consistente**, lo que garantiza que A\* encuentre la solución óptima sin re-expandir nodos.

### Complejidad

| Caso                           | Estados posibles   |
| ------------------------------ | ------------------ |
| 8-puzzle resoluble             | 9!/2 = **181,440** |
| Peor caso (nodos explorados)   | ~**180,000** nodos |
| Profundidad máxima de solución | **31 movimientos** |

---

## Características

- **Resolución automática** con A\* y heurística Manhattan admisible
- **Visualización paso a paso** — navega forward/backward por la solución
- **Reproducción automática** con control de velocidad (slider)
- **Movimiento manual** — haz clic en las fichas adyacentes al hueco
- **Teclado** — usa las flechas ← → ↑ ↓ para mover fichas
- **Métricas en tiempo real** — h(n), g(n), f(n) y nodos explorados
- **Timeline de movimientos** con barra de progreso
- **Modo oscuro / claro** con toggle
- **Diseño responsive** — funciona en móvil y escritorio
- **Sin dependencias** — un solo archivo HTML estático

---

## Estructura del Proyecto

```
.
├── 8puzzle_astar_solver.html   # Solver interactivo (HTML + CSS + JS)
├── astar_8puzzle_graph.html    # Árbol de búsqueda A* paso a paso
├── 8puzzle_state_space.html    # Grafo del espacio de estados completo (181,440 nodos)
└── README.md                   # Este archivo
```

---

## Visualizador del Espacio de Estados Completo

`8puzzle_state_space.html` renderiza **los 9!/2 = 181,440 estados resolubles** del 8-puzzle conectados por sus transiciones válidas (movimientos del hueco). Se enumeran por **BFS** desde el estado objetivo S\*, y se distribuyen mediante un **layout force-directed** (atracción por aristas + repulsión local en grilla espacial uniforme + gravedad hacia el centro).

| Métrica            | Valor       |
| ------------------ | ----------- |
| Estados (nodos)    | **181,440** |
| Transiciones       | **241,920** |
| Diámetro del grafo | **31**      |
| Iteraciones layout | 250         |

Controles: rueda del mouse para zoom, arrastrar para desplazar, botones para pausar/reanudar/reiniciar el layout y togglear nodos/aristas. Permite observar visualmente:

- El **núcleo denso** (estados cerca de S\*) y la dispersión hacia profundidades altas.
- La estructura de "explosión combinatoria" del espacio de búsqueda.
- Por qué heurísticas como Manhattan son críticas: un BFS ingenuo sobre este grafo es prohibitivo.

---

## Uso

### Opción 1: Abrir directamente

```bash
# Linux
xdg-open 8puzzle_astar_solver.html

# macOS
open 8puzzle_astar_solver.html

# Windows
start 8puzzle_astar_solver.html
```

### Opción 2: Servidor local (opcional)

```bash
python3 -m http.server 8080
# Luego abre: http://localhost:8080/8puzzle_astar_solver.html
```

### Flujo de uso

1. **Barajar** — genera un estado inicial aleatorio y resoluble
2. **Resolver A\*** — ejecuta el algoritmo y muestra la solución óptima
3. Usa **← Atrás / Adelante →** para recorrer los pasos manualmente
4. Usa **▶ Auto** para reproducir automáticamente con la velocidad deseada
5. Haz clic en cualquier ficha adyacente al hueco para moverla manualmente
6. **Reiniciar** — vuelve al estado objetivo S\*

---

## Implementación Técnica

### Estructura de datos

```javascript
// Nodo del árbol de búsqueda
{ s: [1,2,3,4,5,6,7,8,0],   // estado (array de 9 enteros)
  g: 4,                       // costo desde inicio
  h: 6,                       // heurística Manhattan
  f: 10,                      // f = g + h
  par: <nodo_padre>,          // referencia para reconstruir camino
  m: "→ Derecha"              // movimiento que generó este nodo
}
```

### Cola de prioridad (Min-Heap)

Se usa un heap binario mínimo para extraer eficientemente el nodo con menor `f(n)` en cada iteración:

```javascript
class Heap {
  push(x) {
    /* sift-up  O(log n) */
  }
  pop() {
    /* sift-down O(log n) */
  }
}
```

### Verificación de resolubilidad

Un estado es resoluble si y solo si el número de **inversiones** (pares desordenados) es **par**:

```javascript
function solvable(s) {
  const a = s.filter((x) => x);
  let inv = 0;
  for (let i = 0; i < a.length; i++)
    for (let j = i + 1; j < a.length; j++) if (a[i] > a[j]) inv++;
  return inv % 2 === 0;
}
```

---

## Tecnologías

| Tecnología            | Uso                                       |
| --------------------- | ----------------------------------------- |
| **HTML5**             | Estructura semántica                      |
| **CSS3**              | Variables CSS, Grid, Flexbox, animaciones |
| **JavaScript (ES6+)** | Lógica A\*, UI reactiva, min-heap         |
| **Google Fonts**      | Inter + JetBrains Mono                    |
| **Sin frameworks**    | Aplicación vanilla 100% portable          |

---

## Conceptos de IA Aplicados

Este proyecto ilustra los siguientes conceptos del programa de Inteligencia Artificial:

- **Agente resolvedor de problemas** — el sistema percibe un estado y actúa para alcanzar el objetivo
- **Espacio de estados** — representación implícita del grafo de búsqueda
- **Búsqueda informada (Best-First)** — A\* como instancia de búsqueda con heurística
- **Admisibilidad y consistencia** — propiedades que garantizan optimalidad
- **Comparativa de heurísticas** — Manhattan domina sobre Hamming (piezas fuera de lugar)

---

## Referencia Bibliográfica

> Russell, S. & Norvig, P. (2021). _Artificial Intelligence: A Modern Approach_ (4ª ed.).  
> Capítulo 3: Solving Problems by Searching — §3.5 Informed (Heuristic) Search Strategies.

---

## Autor

Desarrollado como proyecto práctico de la asignatura **Inteligencia Artificial** por Nicolás Malebrán (nmalebran.c@gmail.com) y Joselyn Montaño.

---

## Licencia

MIT License — libre para uso educativo.

---

## Nota técnica para el profesor

Hay dos caminos. Antes de elegir te explico el problema técnico clave: con 181K nodos no podemos repulsar TODOS contra TODOS (sería O(N²) = 33 mil millones de operaciones). Por eso uso una grilla local de rango 7 — pero eso significa que nodos lejanos NO se repelen, así que tienden a colapsar al centro (bola) o a su anillo (dona).
