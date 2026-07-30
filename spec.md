# Specification: Murmuration Sim Pro

## 1. Project Overview
**Objective:** Transform a basic "Rule of Seven" flocking demonstration into a high-fidelity, scientifically accurate, and visually striking simulation of starling murmurations.
**Target Goal:** 10,000+ birds at 60 FPS with professional-grade visuals and a research-oriented configuration interface.

---

## 2. Behavioral Accuracy (The Bio-Fidelity Layer)

### Tier 1: Baseline (Current State)
- **Rule of Seven:** Each bird tracks the 7 nearest neighbors regardless of distance.
- **Core Forces:** Basic Alignment, Cohesion, and Separation.
- **Topology:** Simple distance-based sorting.

### Tier 2: Advanced (The "Realism" Layer)
- **Vision Cones:** Interaction is limited to a $\sim 120^\circ$ field of view. Birds do not react to neighbors behind them.
- **Kinematic Constraints:** 
    - **Inertia:** Velocity changes are smoothed over time.
    - **Angular Velocity Limit:** Maximum turn rate per frame to prevent "jitter."
- **Scale-Free Correlation:** Validation that a change in one bird's direction propagates across the flock without decaying over distance.

### Tier 3: High-Fidelity (The "Emergent" Layer)
- **Predator-Prey Dynamics:** Introduction of a "Predator" entity that triggers high-magnitude repulsion.
- **Flash Expansion:** Implementation of the "critical density" trigger where a local panic causes a rapid, synchronized expansion of the entire flock.
- **3D Spatiality:** Transition from 2D $\rightarrow$ 3D coordinates $(x, y, z)$ to allow for diving and overlapping maneuvers.

---

## 3. Rendering Pipeline (The Aesthetic Layer)

### Tier 1: Enhanced Pygame
- **Visuals:** Improved bird shapes (anti-aliased polygons), simple motion trails.
- **Dynamic Coloring:** Bird color shifts based on local density (e.g., Blue $\rightarrow$ White $\rightarrow$ Yellow).
- **Hardware:** CPU-bound, standard GPU.

### Tier 2: ModernGL / OpenGL
- **Instanced Rendering:** Use a single vertex buffer to draw thousands of birds in one draw call.
- **3D Perspective:** Implementation of a perspective camera with zoom and pan.
- **Post-Processing:** Basic Bloom and Glow effects to simulate light reflecting off feathers.
- **Hardware:** Dedicated GPU (OpenGL 3.3+).

### Tier 3: Cinematic (GPU-Driven)
- **Compute Shaders:** Physics and state updates moved entirely to the GPU.
- **Advanced Effects:** 
    - **Motion Blur:** Per-particle velocity-based blurring.
    - **Volumetric Lighting:** Soft light shafts and atmospheric haze.
    - **Depth of Field:** Dynamic focus based on the flock's center of mass.
- **Hardware:** High-end GPU (OpenGL 4.3+ / Vulkan).

---

## 4. Performance & Scaling (The Engineering Layer)

### Tier 1: Optimized Python
- **Vectorization:** Use NumPy for all position/velocity updates.
- **Grid Partitioning:** Divide the world into a coarse grid to limit neighbor searches.
- **Complexity:** $O(N \cdot (\text{grid\_cell\_size}))$.
- **Limit:** $\sim 500\text{--}1,000$ birds.

### Tier 2: Engineering Grade
- **Spatial Partitioning:** Implementation of a **Quadtree** (2D) or **Octree** (3D) for $O(N \log N)$ neighbor lookups.
- **Multi-threading:** Parallelize the "force calculation" phase across CPU cores.
- **Memory Layout:** Use contiguous arrays (Structure of Arrays) to improve cache locality.
- **Limit:** $\sim 5,000\text{--}10,000$ birds.

### Tier 3: Extreme Scale
- **GPU Physics:** All neighbor searches and steering calculations performed in a Compute Shader.
- **Zero-Copy Buffers:** Physics data stays on the GPU and is fed directly into the render pipeline without CPU read-back.
- **Complexity:** $O(N)$ parallel.
- **Limit:** $100,000+$ birds.

---

## 5. Configuration & UX (The Lab Layer)

### Tier 1: File-Based
- **Presets:** YAML/JSON files defining species-specific weights (e.g., `starling.yaml`).
- **Workflow:** Edit file $\rightarrow$ Restart App.

### Tier 2: Interactive Lite
- **Real-time Tuning:** On-screen sliders for Alignment, Cohesion, and Separation weights.
- **Dynamic Neighbor Count:** Ability to change the "Rule of N" on the fly.

### Tier 3: Professional Lab
- **Dashboard:** Full ImGui/Dear PyGui interface.
- **Analytics:** Real-time graphing of flock density, average velocity, and stability metrics.
- **Event Timeline:** A programmable sequence of events (e.g., "T+10s: Spawn Predator at (500, 200)").
- **Snapshotting:** Ability to save and load the exact state of a murmuration.
