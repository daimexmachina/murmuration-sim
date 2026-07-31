use macroquad::prelude::*;
use ::rand::Rng;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::fs;
use std::time::SystemTime;

#[derive(Serialize, Deserialize, Clone)]
struct InteractionConfig {
    predator_radius: f32,
    predator_force: f32,
}

#[derive(Serialize, Deserialize, Clone)]
struct Config {
    num_birds: usize,
    bird_radius: f32,
    neighbor_count: usize,
    max_speed: f32,
    max_force: f32,
    alignment_weight: f32,
    cohesion_weight: f32,
    separation_weight: f32,
    separation_radius: f32,
    trail_length: usize,
    interaction: InteractionConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            num_birds: 1000,
            bird_radius: 2.0,
            neighbor_count: 7,
            max_speed: 4.0,
            max_force: 0.15,
            alignment_weight: 1.0,
            cohesion_weight: 1.0,
            separation_weight: 1.5,
            separation_radius: 20.0,
            trail_length: 15,
            interaction: InteractionConfig {
                predator_radius: 100.0,
                predator_force: 0.5,
            },
        }
    }
}

fn load_config() -> Config {
    match fs::read_to_string("config.toml") {
        Ok(content) => toml::from_str(&content).unwrap_or_else(|_| Config::default()),
        Err(_) => Config::default(),
    }
}

#[derive(Clone)]
struct Bird {
    pos: Vec2,
    vel: Vec2,
    acc: Vec2,
    history: VecDeque<Vec2>,
}

impl Bird {
    fn new(width: f32, height: f32, max_speed: f32, trail_length: usize) -> Self {
        let mut rng = ::rand::thread_rng();
        let mut vel = Vec2::new(
            rng.gen_range(-max_speed..max_speed),
            rng.gen_range(-max_speed..max_speed),
        );
        if vel.length() > 0.0 {
            vel = vel.normalize() * rng.gen_range(2.0..max_speed);
        }

        let pos = Vec2::new(rng.gen_range(0.0..width), rng.gen_range(0.0..height));
        let mut history = VecDeque::with_capacity(trail_length);
        for _ in 0..trail_length {
            history.push_back(pos);
        }

        Self {
            pos,
            vel,
            acc: Vec2::ZERO,
            history,
        }
    }

    fn apply_force(&mut self, force: Vec2) {
        self.acc += force;
    }

    fn update(&mut self, width: f32, height: f32, max_speed: f32, trail_length: usize) {
        self.vel += self.acc;
        if self.vel.length() > max_speed {
            self.vel = self.vel.normalize() * max_speed;
        }
        self.pos += self.vel;
        self.acc = Vec2::ZERO;

        self.history.push_front(self.pos);
        if self.history.len() > trail_length {
            self.history.pop_back();
        }

        if self.pos.x < 0.0 { self.pos.x = width; }
        if self.pos.x > width { self.pos.x = 0.0; }
        if self.pos.y < 0.0 { self.pos.y = height; }
        if self.pos.y > height { self.pos.y = 0.0; }
    }
}

struct SpatialHashGrid {
    cell_size: f32,
    grid: std::collections::HashMap<(i32, i32), Vec<usize>>,
}

impl SpatialHashGrid {
    fn new(cell_size: f32) -> Self {
        Self {
            cell_size,
            grid: std::collections::HashMap::new(),
        }
    }

    fn clear(&mut self) {
        self.grid.clear();
    }

    fn insert(&mut self, id: usize, pos: Vec2) {
        let cx = (pos.x / self.cell_size).floor() as i32;
        let cy = (pos.y / self.cell_size).floor() as i32;
        self.grid.entry((cx, cy)).or_insert_with(Vec::new).push(id);
    }

    fn get_nearby(&self, pos: Vec2, radius: f32) -> Vec<usize> {
        let mut nearby = Vec::new();
        let min_cx = ((pos.x - radius) / self.cell_size).floor() as i32;
        let max_cx = ((pos.x + radius) / self.cell_size).floor() as i32;
        let min_cy = ((pos.y - radius) / self.cell_size).floor() as i32;
        let max_cy = ((pos.y + radius) / self.cell_size).floor() as i32;

        for cx in min_cx..=max_cx {
            for cy in min_cy..=max_cy {
                if let Some(cell) = self.grid.get(&(cx, cy)) {
                    nearby.extend(cell);
                }
            }
        }
        nearby
    }
}

fn flock(bird_idx: usize, birds: &[Bird], grid: &SpatialHashGrid, config: &Config) -> Vec2 {
    let bird = &birds[bird_idx];
    
    let mut search_radius = config.separation_radius * 2.0;
    let mut nearby_ids = grid.get_nearby(bird.pos, search_radius);
    
    while nearby_ids.len() < config.neighbor_count + 1 && search_radius < 1000.0 {
        search_radius *= 2.0;
        nearby_ids = grid.get_nearby(bird.pos, search_radius);
    }

    let mut distances: Vec<(f32, usize)> = nearby_ids
        .into_iter()
        .filter(|&id| id != bird_idx)
        .map(|id| {
            let d_sq = bird.pos.distance_squared(birds[id].pos);
            (d_sq, id)
        })
        .collect();

    distances.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    
    let neighbors: Vec<&Bird> = distances
        .iter()
        .take(config.neighbor_count)
        .map(|(_, id)| &birds[*id])
        .collect();

    if neighbors.is_empty() {
        return Vec2::ZERO;
    }

    let mut alignment = Vec2::ZERO;
    let mut cohesion = Vec2::ZERO;
    let mut separation = Vec2::ZERO;

    for neighbor in &neighbors {
        alignment += neighbor.vel;
        cohesion += neighbor.pos;
        
        let dist = bird.pos.distance(neighbor.pos);
        if dist < config.separation_radius {
            let diff = (bird.pos - neighbor.pos).normalize();
            separation += diff / (dist + 0.1);
        }
    }

    let n_len = neighbors.len() as f32;
    
    alignment /= n_len;
    if alignment.length() > 0.0 {
        alignment = (alignment.normalize() * config.max_speed) - bird.vel;
    }
    
    cohesion /= n_len;
    cohesion -= bird.pos;
    if cohesion.length() > 0.0 {
        cohesion = (cohesion.normalize() * config.max_speed) - bird.vel;
    }

    if separation.length() > 0.0 {
        separation = (separation.normalize() * config.max_speed) - bird.vel;
    }

    let mut steer = alignment * config.alignment_weight 
              + cohesion * config.cohesion_weight 
              + separation * config.separation_weight;
    
    if steer.length() > config.max_force {
        steer = steer.normalize() * config.max_force;
    }
    
    steer
}

#[macroquad::main("Murmuration Rust")]
async fn main() {
    let width = screen_width();
    let height = screen_height();
    
    let mut config = load_config();
    let mut birds: Vec<Bird> = (0..config.num_birds)
        .map(|_| Bird::new(width, height, config.max_speed, config.trail_length))
        .collect();
    
    let mut grid = SpatialHashGrid::new(50.0);
    let mut last_config_load = SystemTime::now();

    loop {
        clear_background(Color::from_rgba(15, 15, 25, 255));

        if last_config_load.elapsed().unwrap_or_default().as_secs() >= 2 {
            config = load_config();
            last_config_load = SystemTime::now();
            
            if birds.len() < config.num_birds {
                for _ in birds.len()..config.num_birds {
                    birds.push(Bird::new(width, height, config.max_speed, config.trail_length));
                }
            } else if birds.len() > config.num_birds {
                birds.truncate(config.num_birds);
            }
        }

        grid.clear();
        for (i, bird) in birds.iter().enumerate() {
            grid.insert(i, bird.pos);
        }

        let mouse_pos = Vec2::new(mouse_position().0, mouse_position().1);
        
        let forces: Vec<Vec2> = (0..birds.len())
            .map(|i| {
                let mut f = flock(i, &birds, &grid, &config);
                
                let bird_pos = birds[i].pos;
                let dist_to_mouse = bird_pos.distance(mouse_pos);
                if dist_to_mouse < config.interaction.predator_radius {
                    let escape_force = (bird_pos - mouse_pos).normalize() * config.interaction.predator_force;
                    f += escape_force;
                }
                
                f
            })
            .collect();

        for (i, bird) in birds.iter_mut().enumerate() {
            bird.apply_force(forces[i]);
            bird.update(width, height, config.max_speed, config.trail_length);
        }

        for bird in &birds {
            let speed = bird.vel.length();
            let t = ((speed - 2.0) / (config.max_speed - 2.0)).clamp(0.0, 1.0);
            let color = Color::new(
                0.7 + 0.3 * t, 
                0.8 + 0.2 * t, 
                1.0, 
                1.0
            );

            if bird.history.len() > 1 {
                for i in 0..bird.history.len() - 1 {
                    let p1 = bird.history[i];
                    let p2 = bird.history[i+1];
                    let alpha = 1.0 - (i as f32 / bird.history.len() as f32);
                    draw_line(p1.x, p1.y, p2.x, p2.y, 1.0, Color::new(color.r, color.g, color.b, alpha * 0.5));
                }
            }

            let dir = bird.vel.normalize();
            let r = config.bird_radius;
            let side = Vec2::new(-dir.y, dir.x) * r;
            let head = bird.pos + dir * r;
            let tail_l = bird.pos - dir * r + side;
            let tail_r = bird.pos - dir * r - side;

            draw_triangle(head, tail_l, tail_r, color);
        }

        draw_text(&format!("FPS: {}", get_fps()), 20.0, 20.0, 20.0, WHITE);
        draw_text(&format!("Birds: {}", config.num_birds), 20.0, 40.0, 20.0, WHITE);
        draw_text("Mouse acts as a predator", 20.0, 60.0, 20.0, GRAY);
        
        next_frame().await
    }
}
