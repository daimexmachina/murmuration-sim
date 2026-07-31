# Technical Specification: Murmuration Sim Pro

## 1. Project Overview
**Objective:** Transition from a basic Boids-style simulation to a high-fidelity, scientifically grounded model of starling (*Sturnus vulgaris*) collective behavior. The goal is to achieve "scale-free correlation"—where a change in movement by one bird propagates across the entire flock regardless of size—while maintaining a professional, cinematic aesthetic.

---

## 2. Bio-Physics & Behavioral Dynamics
The simulation will move away from metric-distance (fixed radius) interactions to **topological interaction**.

### 2.1 Behavioral Tiers
#### Tier 1: Baseline (Topological Cohesion)
- **The Rule of Seven:** Each bird tracks exactly 6-7 nearest neighbors, regardless of physical distance.
- **Interaction:** Alignment and cohesion are calculated based on the average velocity and position of these 7 neighbors.
- **Citation:** Ballerini et al. (2008), *PNAS* 105(30), 10333-10338.

#### Tier 2: Advanced (Kinematic Constraints)
- **Vision Cones:** Interactions are weighted by a $\sim 120^\circ$ field of view. Birds in the "blind spot" are ignored.
- **Angular Velocity Limits:** Rotation of the velocity vector is capped at $\omega_{max}$ to prevent instantaneous "jitter" and create sweeping, organic arcs.
- **Inertia:** Acceleration is applied as a force over time ($\vec{v}_{t+1} = \vec{v}_t + \vec{a} \Delta t$) rather than direct velocity setting.
- **Citation:** Cavagna et al. (2010), *PNAS* 107(26), 11821-11826.

#### Tier 3: High-Fidelity (Emergent Events)
- **Predator-Induced Panic:** Introduction of a predator entity that triggers a high-magnitude repulsion force $\vec{F}_{panic} \propto 1/d^2$.
- **Flash Expansion:** When local density drops below a critical threshold during a panic event, birds accelerate away from the flock's center of mass to maximize distance from the threat.
- **Citation:** Young et al. (2013), *PNAS* (Predator-induced collective motion).

---

## 3. Graphics & Rendering Pipeline
The visual goal is to move from "dots on a screen" to a cinematic representation of density and motion.

### 3.1 Rendering Tiers
| Tier | Technology | Visual Features | Hardware Req. |
| :--- | :--- | :--- | :--- |
| **Enhanced** | Pygame / SDL2 | Anti-aliased shapes, motion trails, density-based coloring (heatmaps). | Low (CPU) |
| **Professional** | ModernGL / OpenGL | Instanced rendering, 3D perspective, Bloom, basic particle effects. | Mid (GPU) |
| **Cinematic** | Compute Shaders | Volumetric lighting, Depth of Field (DoF), motion blur, 100k+ birds. | High (GPU) |

---

## 4. Performance Architecture
To maintain 60 FPS with thousands of agents, the $O(N^2)$ naive neighbor search must be eliminated.

### 4.1 Scaling Strategies
1.  **Vectorized Grid Partitioning (NumPy):** Divide the space into a grid. Only check neighbors in the current and adjacent cells.
    - **Complexity:** $O(N)$ average case.
    - **Limit:** $\sim 2,000$ birds.
2.  **Spatial Partitioning (Quadtree/KD-Tree):** Use a recursive spatial tree to query the 7 nearest neighbors.
    - **Complexity:** $O(N \log N)$.
    - **Limit:** $\sim 10,000$ birds.
3.  **GPU Spatial Hashing (Compute Shaders):** Use a GPU-side grid hash to perform neighbor lookups in parallel.
    - **Complexity:** $O(N)$ parallel.
    - **Limit:** $100,000+$ birds.

---

## 5. Self-Adversarial Review (Red Team Critique)

### 5.1 Engineering Bottlenecks
- **The "Topological Search" Trap:** Finding the *exact* 7 nearest neighbors is computationally expensive. A KD-tree helps, but at 10k+ birds, the overhead of updating the tree every frame becomes the primary bottleneck.
- **The Pygame Ceiling:** Pygame is CPU-bound. Attempting "Cinematic" visuals in Pygame is a contradiction; the project *must* migrate to a GPU-backed library (like ModernGL) to achieve the desired aesthetic.

### 5.2 Biological Assumptions
- **Simplification of 3D:** While the spec mentions 3D, real murmurations involve complex vertical diving. A 2D simulation with a "pseudo-Z" depth value is a "boring" implementation; true 3D is required for scientific fidelity.
- **The "Rule of Seven" Rigidity:** In reality, the number of neighbors is a distribution, not a constant. A fixed "7" may lead to artificial crystalline patterns in the flock.

---

## 6. Implementation Roadmap

### Wave 1: Foundation (The "Correct" Boids)
- Implement topological neighbor search (KD-Tree).
- Integrate angular velocity limits and inertia.
- **Goal:** A stable, jitter-free 2D flock of 1,000 birds.

### Wave 2: Infrastructure (The GPU Leap)
- Migrate rendering to ModernGL (Instanced Rendering).
- Implement Vision Cones and basic Predator entities.
- **Goal:** 10,000 birds with cinematic bloom and 3D perspective.

### Wave 3: Polish (The "Pro" Experience)
- Implement Flash Expansion and Predator-Prey dynamics.
- Add volumetric lighting and motion blur.
- **Goal:** A high-fidelity, research-grade simulation.
