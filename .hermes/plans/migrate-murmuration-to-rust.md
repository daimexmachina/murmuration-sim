# Plan: Migrating Murmuration Simulation to Rust

## Objective
Migrate the `murmuration.py` simulation to Rust to achieve high-performance flocking (thousands of birds instead of hundreds) and enhanced visual fidelity with a robust configuration system.

## Current State Analysis
- **Language:** Python (Pygame)
- **Complexity:** $O(N^2)$ per frame due to all-pairs distance calculation and sorting for the "Rule of Seven".
- **Visuals:** Basic 2D polygons.
- **Config:** Hardcoded Python constants.

## Proposed Technical Stack
- **Language:** Rust
- **Graphics/Engine:** `Bevy` (ECS is ideal for agent-based simulations) or `Macroquad` (for lean, fast 2D). Given the "visually impressive" goal, Bevy's renderer and plugin system provide more headroom.
- **Spatial Optimization:** Implement a **Spatial Hash Grid** or **KD-Tree** to reduce neighbor search complexity from $O(N^2)$ to roughly $O(N \log N)$ or $O(N)$.
- **Configuration:** `serde` + `toml` for a separate `config.toml` file.

## Implementation Phases

### Phase 1: Foundation & Performance (The Rust Core)
- [ ] Initialize Rust project with a chosen graphics backend.
- [ ] Port the `Bird` state (position, velocity, acceleration) into a Bevy Component/ECS structure.
- [ ] Implement the "Rule of Seven" logic in Rust.
- [ ] **Optimization:** Implement a spatial partitioning system to replace the global sort.
- [ ] Verify performance: Target $10,000+$ birds at $60$ FPS.

### Phase 2: Visual Enhancement
- [ ] Replace basic triangles with more dynamic shapes or high-quality sprites.
- [ ] **Motion Trails:** Implement a fading trail system to visualize the flow of the murmuration.
- [ ] **Dynamic Coloring:** Map bird speed or neighborhood density to color gradients (e.g., heat-map style).
- [ ] **Smooth Interpolation:** Ensure sub-frame movement for fluid visuals.

### Phase 3: Configurability & Interaction
- [ ] Create a `config.toml` including:
    - `num_birds`, `max_speed`, `max_force`.
    - `alignment_weight`, `cohesion_weight`, `separation_weight`.
    - Visual parameters (trail length, colors).
- [ ] Implement live-reloading of the config file (via `notify` crate).
- [ ] Add basic mouse interaction (e.g., a "predator" that pushes birds away).

### Phase 4: Verification & Polish
- [ ] Compare Rust behavior against Python original to ensure the "feel" is preserved.
- [ ] Profile the Rust implementation to identify any further bottlenecks.
- [ ] Final UI/UX polish (full-screen toggle, FPS counter).

## Success Criteria
1. **Performance:** Ability to simulate $\sim 10\text{k}$ birds without frame drops.
2. **Visuals:** Distinct improvement over Pygame (trails, color, fluid motion).
3. **Config:** All simulation weights adjustable via an external file without recompiling.
