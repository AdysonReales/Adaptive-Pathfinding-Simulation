# main.py
import pygame
import sys
import time
import random
import math
import os
import csv
from config import *
from ui import UIManager
from grid import GridManager
from engine_connector import CppEngineConnector

class SimulationEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Adaptive Pathfinding Simulator")
        self.clock = pygame.time.Clock()
        
        self.ui = UIManager(self.screen)
        self.engine = CppEngineConnector()
        
        self.state = "MAIN_MENU"
        self.running = True
        self.is_simulating = False
        
        self.current_tool = "Zombie" 
        self.current_scenario = 1
        self.current_algo = 0
        self.show_terminal = False
        self.target_moving = True
        
        self.speed_idx = 1
        self.last_tick = 0
        self.paths = {} 
        self.known_cells = {} 
        
        # Code highlights caching
        self.execution_steps = []
        self.current_cpp_line = "LINE_INIT"
        
        # Enforce initial deterministic seeding
        random.seed(RANDOM_SEED)
        
        self.grid_sizes = [10, 20, 30, 40, 50]
        self.current_grid_idx = 1
        self.grid = GridManager(self.grid_sizes[self.current_grid_idx], self.grid_sizes[self.current_grid_idx], DEFAULT_CELL_SIZE)
        
        
        self.stats = {
            "status": "Idle", "steps": 0, "recalcs": 0, "algorithm": ALGORITHMS[0],
            "initial_time_us": 0, "total_replan_time_us": 0, "nodes_expanded": 0
        }

        self.initial_zombies = []
        self.initial_villager = None

    def check_requirements(self):
        reqs = []
        sc = self.current_scenario
        gz = len(self.grid.zombies)
        gv = self.grid.villager is not None
        gw = len([k for k, v in self.grid.cells.items() if TERRAIN[v]["weight"] == -1])
        
        if sc == 1 or sc == 6:
            reqs.append(("Place 1 Zombie", gz == 1))
            reqs.append(("Place 1 Villager", gv))
        elif sc in [2, 3, 4]:
            reqs.append(("Place 1 Zombie", gz == 1))
            reqs.append(("Place 1 Villager", gv))
            reqs.append(("Build Obstacles (>3 Walls)", gw >= 3))
        elif sc == 5:
            reqs.append(("Multiple Zombies (2-3)", gz >= 2))
            reqs.append(("Place 1 Villager", gv))
        elif sc == 7:
            reqs.append(("Place 3 Zombies", gz == 3))
            reqs.append(("Place 1 Villager", gv))
            reqs.append(("Generate Terrain", len(self.grid.cells) >= 10))
        elif sc == 8:
            reqs.append(("Place 1 Zombie", gz == 1))
            reqs.append(("Place 1 Villager", gv))
            
        ready = all(r[1] for r in reqs)
        return reqs, ready

    def reset_environment(self):
        """Resets active simulation performance metrics while preserving your custom map layout."""
        self.is_simulating = False
        
        # Clear paths, open/closed evaluation arrays, and traces
        self.grid.ghost_trails.clear()
        self.grid.path_nodes.clear()
        self.grid.evaluated_nodes.clear()
        self.paths.clear()
        self.known_cells.clear()
        self.execution_steps.clear()
        self.current_cpp_line = "LINE_INIT"
        
        # Restore the agents back to where they were before the simulation started
        if self.initial_zombies:
            self.grid.zombies = list(self.initial_zombies)
        if self.initial_villager:
            self.grid.villager = self.initial_villager
        
        # Force standard re-seed so dynamic behaviors stay perfectly deterministic
        random.seed(RANDOM_SEED)
        
        # Reset concrete counter statistics for the next comparative test run
        self.stats = {
            "status": "Idle", 
            "steps": 0, 
            "recalcs": 0, 
            "algorithm": ALGORITHMS[self.current_algo],
            "initial_time_us": 0, 
            "total_replan_time_us": 0, 
            "nodes_expanded": 0
        }

    def _get_environmental_metrics(self):
        """Calculates exact obstacle density and average terrain friction."""
        w, h = self.grid.width, self.grid.height
        total_cells = w * h
        impassable = 0
        total_friction = 0
        passable_count = 0
        
        for x in range(w):
            for y in range(h):
                t_type = self.grid.cells.get((x, y), "Empty")
                weight = TERRAIN[t_type]["weight"]
                if weight == -1:
                    impassable += 1
                else:
                    total_friction += weight
                    passable_count += 1
                    
        obs_density = round((impassable / total_cells) * 100, 2)
        avg_fric = round((total_friction / passable_count) if passable_count > 0 else 0, 2)
        return obs_density, avg_fric

    def generate_natural_terrain(self, w, h):
        for x in range(w):
            for y in range(h):
                self.grid.cells[(x,y)] = "Grass"
        total = w * h
        seeds = {"Water": max(1, total//30), "Mud": max(1, total//25), "Rock": max(1, total//40), "Tree": max(1, total//20)}
        for t_type, count in seeds.items():
            for _ in range(count):
                self.grid.cells[(random.randint(0, w-1), random.randint(0, h-1))] = t_type
        for _ in range(3):
            new_cells = self.grid.cells.copy()
            for x in range(w):
                for y in range(h):
                    nx, ny = x + random.choice([-1, 0, 1]), y + random.choice([-1, 0, 1])
                    if 0 <= nx < w and 0 <= ny < h:
                        neighbor = self.grid.cells.get((nx, ny), "Grass")
                        if neighbor != "Grass" and random.random() < 0.65: new_cells[(x,y)] = neighbor
            self.grid.cells = new_cells
            
        if self.grid.zombies: 
            for z in self.grid.zombies: self.grid.cells[z] = "Empty"
        if self.grid.villager: self.grid.cells[self.grid.villager] = "Empty"

    def load_scenario(self):
        """Prepares a fresh layout specific to the chosen scenario."""
        # 1. Clear out performance tracking data
        self.reset_environment()
        
        # 2. FORCE a hard clear of entities/cells ONLY when shifting scenarios
        self.grid.cells.clear()
        self.grid.zombies.clear()
        self.grid.villager = None
        self.paths.clear()
        self.known_cells.clear()
        
        w, h = self.grid.width, self.grid.height
        
        # 3. Load the specific scenario architecture
        if self.current_scenario == 2:
            self.grid.zombies = [(2, 2)]
            self.grid.villager = (w-3, h-3)
            for y in range(2, h-2):
                if y != h//2: self.grid.cells[(w//2, y)] = "Wall"
                
        elif self.current_scenario == 6:
            self.grid.zombies = [(1, 1)]
            self.grid.villager = (w-2, h-2)
            for _ in range(int(w * h * 0.25)): 
                rx, ry = random.randint(0, w-1), random.randint(0, h-1)
                if (rx, ry) not in self.grid.zombies and (rx, ry) != self.grid.villager:
                    self.grid.cells[(rx, ry)] = "Tree"
                    
        elif self.current_scenario == 7:
            self.grid.zombies = [(1, 1), (1, 1), (1, 1)]
            self.grid.villager = (w-2, h-2)
            self.generate_natural_terrain(w, h)

    def get_villager_move(self):
        if not self.grid.villager:
            return None
            
        if not hasattr(self, 'villager_dx'):
            self.villager_dx = 1
            self.villager_dy = 1
            self.panic_mode = False
            self.wall_hug_ticks = 0
            self.corner_escape_ticks = 0  

        vx, vy = self.grid.villager
        
        # --- SMART TURBO DIRECTIONAL LOCK OVERRIDE ---
        if self.corner_escape_ticks > 0:
            self.corner_escape_ticks -= 1
            
            # TURBO SPEED: If we are flat-sliding to escape (dx or dy is 0), 
            # we multiply the step by 2 to sprint faster along the wall!
            step_multiplier = 2 if (self.villager_dx == 0 or self.villager_dy == 0) else 1
            
            nx = vx + (self.villager_dx * step_multiplier)
            ny = vy + (self.villager_dy * step_multiplier)
            
            # Clamping bounds so the speed burst doesn't break out of the grid map
            nx = max(0, min(self.grid.width - 1, nx))
            ny = max(0, min(self.grid.height - 1, ny))
            
            if TERRAIN[self.grid.cells.get((nx, ny), "Empty")]["weight"] != -1:
                return (nx, ny)

        best_pos = None
        best_score = -99999999
        actual_dx = self.villager_dx
        actual_dy = self.villager_dy
        
        zombies_nearby = [z for z in self.grid.zombies if math.hypot(vx-z[0], vy-z[1]) <= 6.0]
        
        # Detect physical boundary contact
        touching_left = (vx <= 2)
        touching_right = (vx >= self.grid.width - 3)
        touching_top = (vy <= 2)
        touching_bottom = (vy >= self.grid.height - 3)
        
        touching_left_right = touching_left or touching_right
        touching_top_bottom = touching_top or touching_bottom
        in_absolute_corner = touching_left_right and touching_top_bottom

        # 1. EVASIVE VECTOR SELECTION & TURBO SLIDE INITIALIZATION
        if zombies_nearby:
            self.panic_mode = True
            
            avg_zx = sum(z[0] for z in zombies_nearby) / len(zombies_nearby)
            avg_zy = sum(z[1] for z in zombies_nearby) / len(zombies_nearby)
            
            if in_absolute_corner:
                out_dx = 1 if touching_left else -1
                out_dy = 1 if touching_top else -1
                
                z_dist_x = abs(vx - avg_zx)
                z_dist_y = abs(vy - avg_zy)
                
                if z_dist_x < z_dist_y:
                    # Zombie approaching vertically -> Turbo slide flat horizontally
                    self.villager_dx = out_dx
                    self.villager_dy = 0
                else:
                    # Zombie approaching horizontally -> Turbo slide flat vertically
                    self.villager_dx = 0
                    self.villager_dy = out_dy
                    
                self.corner_escape_ticks = 2  # Hug the wall at double speed for 2 frames
                self.wall_hug_ticks = 0  
                
                # Execute the fast first step immediately
                nx = max(0, min(self.grid.width - 1, vx + (self.villager_dx * 2)))
                ny = max(0, min(self.grid.height - 1, vy + (self.villager_dy * 2)))
                if TERRAIN[self.grid.cells.get((nx, ny), "Empty")]["weight"] != -1:
                    return (nx, ny)
            else:
                run_dx = 1 if vx >= avg_zx else -1
                run_dy = 1 if vy >= avg_zy else -1
                
                if touching_left_right or touching_top_bottom:
                    self.wall_hug_ticks += 1
                    if self.wall_hug_ticks > 2:
                        if touching_left_right: run_dx *= -1
                        if touching_top_bottom: run_dy *= -1
                        self.wall_hug_ticks = 0  
                else:
                    self.wall_hug_ticks = max(0, self.wall_hug_ticks - 1)
        else:
            self.panic_mode = False
            self.wall_hug_ticks = 0
            self.corner_escape_ticks = 0
            
            next_bounce_x = vx + self.villager_dx
            next_bounce_y = vy + self.villager_dy
            if next_bounce_x < 0 or next_bounce_x >= self.grid.width or TERRAIN[self.grid.cells.get((next_bounce_x, vy), "Empty")]["weight"] == -1:
                self.villager_dx *= -1
            if next_bounce_y < 0 or next_bounce_y >= self.grid.height or TERRAIN[self.grid.cells.get((vx, next_bounce_y), "Empty")]["weight"] == -1:
                self.villager_dy *= -1
            actual_dx = self.villager_dx
            actual_dy = self.villager_dy

        # 2. EVALUATE SURROUNDING TILES (Normal 1-tile movement weights)
        moving_directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        valid_fallback_moves = []
        
        for dx, dy in moving_directions:
            nx, ny = vx + dx, vy + dy
            
            if 0 <= nx < self.grid.width and 0 <= ny < self.grid.height:
                t_type = self.grid.cells.get((nx, ny), "Empty")
                if TERRAIN[t_type]["weight"] != -1:
                    
                    min_z_dist = min([math.hypot(nx-zx, ny-zy) for zx, zy in self.grid.zombies]) if self.grid.zombies else 100
                    valid_fallback_moves.append(((nx, ny), min_z_dist, (dx, dy)))
                    
                    mobility = 0
                    for ex, ey in [(0,1), (1,0), (0,-1), (-1,0)]:
                        if 0 <= nx+ex < self.grid.width and 0 <= ny+ey < self.grid.height:
                            if TERRAIN[self.grid.cells.get((nx+ex, ny+ey), "Empty")]["weight"] != -1:
                                mobility += 1

                    score = (min_z_dist * 1000) + (mobility * 10)
                    
                    if self.panic_mode:
                        if in_absolute_corner:
                            if dx == self.villager_dx and dy == self.villager_dy:
                                score += 5000  
                        else:
                            if 0 < self.wall_hug_ticks <= 2:
                                if touching_left_right and dx == 0 and dy != 0: score += 600
                                if touching_top_bottom and dy == 0 and dx != 0: score += 600
                        
                        if dx == run_dx: score += 200
                        if dy == run_dy: score += 200
                        
                        if nx <= 1 or nx >= self.grid.width-2 or ny <= 1 or ny >= self.grid.height-2:
                            score -= 1500
                    else:
                        if dx == self.villager_dx and dy == self.villager_dy:
                            score += 50

                    if score > best_score:
                        best_score = score
                        best_pos = (nx, ny)
                        actual_dx = dx
                        actual_dy = dy

        # 3. CRITICAL INTERCEPTOR
        if best_pos is None or best_pos == (vx, vy):
            if valid_fallback_moves:
                valid_fallback_moves.sort(key=lambda item: item[1], reverse=True)
                best_pos = valid_fallback_moves[0][0]
                actual_dx = valid_fallback_moves[0][2][0]
                actual_dy = valid_fallback_moves[0][2][1]
            else:
                return (vx, vy)

        self.villager_dx = actual_dx
        self.villager_dy = actual_dy

        return best_pos

    def update_dynamic_elements(self):
        if self.current_scenario in [3, 4] and self.grid.cells:
            new_cells = {}
            for (cx, cy), t in self.grid.cells.items():
                if TERRAIN[t]["weight"] == -1: 
                    ny = cy + self.grid.moving_wall_dir
                    if ny < 0 or ny >= self.grid.height: 
                        self.grid.moving_wall_dir *= -1 
                        ny = cy + self.grid.moving_wall_dir
                    new_cells[(cx, ny)] = t
                else: new_cells[(cx, cy)] = t
            self.grid.cells = new_cells
            
        # --- FIXED MOVEMENT TRIGGER ---
        if self.target_moving and self.grid.villager:
            # Check if zombies are near to see if the villager should be in full panic sprint
            vx, vy = self.grid.villager
            z_close = any(math.hypot(vx-zx, vy-zy) <= 6.0 for zx, zy in self.grid.zombies) if self.grid.zombies else False
            
            # If a zombie is hunting them, run 100% of the time (no random pacing freezes)
            if z_close:
                self.grid.villager = self.get_villager_move()
            elif random.random() < 0.4: # Gentle casual pacing if completely safe
                self.grid.villager = self.get_villager_move()

        if self.current_scenario == 8:
            if random.random() < 0.15: 
                hx, hy = random.randint(0, self.grid.width-1), random.randint(0, self.grid.height-1)
                if (hx, hy) not in self.grid.zombies and (hx, hy) != self.grid.villager:
                    self.grid.cells[(hx, hy)] = "Fire"

    def log_benchmark_results(self):
        """Appends formatted performance stats as a vertical report block."""
        try:
            with open(BENCHMARK_CSV, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                obs_density, avg_fric = self._get_environmental_metrics()
                grid_sz = self.grid_sizes[self.current_grid_idx]
                success_str = "SUCCESS" if "SUCCESS" in self.stats["status"] else "FAILED"
                moving_obs = self.current_scenario in [3, 4]

                # Write a vertical block for this specific run
                writer.writerow(["--- NEW BENCHMARK RUN ---"])
                writer.writerow(["Name", "Value"])
                writer.writerow(["Scenario_ID", self.current_scenario])
                writer.writerow(["Grid_Size", f"{grid_sz}x{grid_sz}"])
                writer.writerow(["Obstacle_Density", f"{obs_density}%"])
                writer.writerow(["Avg_Terrain_Friction", avg_fric])
                writer.writerow(["Zombie_Count", len(self.grid.zombies)])
                writer.writerow(["Algorithm", ALGORITHMS[self.current_algo]])
                writer.writerow(["Execution_Time_us", self.stats["initial_time_us"]])
                writer.writerow(["Nodes_Expanded", self.stats["nodes_expanded"]])
                writer.writerow(["Path_Length", self.stats["steps"]])
                writer.writerow(["Recalculation_Count", max(0, self.stats["recalcs"] - 1)])
                writer.writerow(["Moving_Obstacles", moving_obs])
                writer.writerow(["Status", success_str])
                writer.writerow([]) # Blank line for spacing
                
                print(f"[Autolog] Saved vertical report to {BENCHMARK_CSV}")
        except Exception as e:
            print(f"[Autolog Error] Could not write to benchmark file: {e}")

    def run_batch_benchmarks(self):
        """Runs an automated, headless benchmark sequence across multiple setups and exits."""
        print("==================================================")
        print("STARTING AUTOMATED SYSTEM PATHFINDING BENCHMARK")
        print("==================================================")
        
        scenarios_to_test = [2, 7]
        algorithms_to_test = [0, 1, 2] # A*, BFS, Dijkstra
        grid_sz = 20
        c_sz = DEFAULT_CELL_SIZE
        
        results = []
        
        for sc in scenarios_to_test:
            for algo in algorithms_to_test:
                print(f"Testing Scenario {sc} with Algorithm {ALGORITHMS[algo]}...")
                self.current_scenario = sc
                self.current_algo = algo
                self.grid = GridManager(grid_sz, grid_sz, c_sz)
                self.load_scenario()
                
                # Force standard re-seed
                random.seed(RANDOM_SEED)
                if sc == 7:
                    self.generate_natural_terrain(grid_sz, grid_sz)
                
                self.is_simulating = True
                self.stats = {
                    "status": "Running", "steps": 0, "recalcs": 0, "algorithm": ALGORITHMS[algo],
                    "initial_time_us": 0, "total_replan_time_us": 0, "nodes_expanded": 0
                }
                self.paths.clear()
                self.grid.ghost_trails.clear()
                self.known_cells.clear()
                
                steps_count = 0
                max_ticks = 2000
                success = False
                
                t0 = time.time()
                while self.is_simulating and steps_count < max_ticks:
                    self.update_dynamic_elements()
                    
                    if self.current_scenario == 6:
                        for zx, zy in self.grid.zombies:
                            for fx in range(self.grid.width):
                                for fy in range(self.grid.height):
                                    if math.hypot(fx - zx, fy - zy) <= 5:
                                        if (fx, fy) in self.grid.cells:
                                            self.known_cells[(fx, fy)] = self.grid.cells[(fx, fy)]
                        active_cells = self.known_cells
                    else:
                        active_cells = self.grid.cells
                    
                    for i in range(len(self.grid.zombies)):
                        z_pos = self.grid.zombies[i]
                        
                        if z_pos == self.grid.villager:
                            self.is_simulating = False
                            success = True
                            break
                            
                        needs_recalc = False
                        if i not in self.paths or not self.paths[i]: needs_recalc = True
                        elif self.grid.villager != self.paths[i][-1]: needs_recalc = True
                        else:
                            next_step = self.paths[i][0]
                            t_type = active_cells.get(next_step, "Empty")
                            if TERRAIN[t_type]["weight"] == -1: needs_recalc = True
                                
                        if needs_recalc:
                            self.stats["recalcs"] += 1
                            temp_cells = active_cells.copy()
                            if self.current_scenario == 7:
                                for oz_idx, oz_pos in enumerate(self.grid.zombies):
                                    if oz_idx != i and oz_pos != self.grid.villager:
                                        temp_cells[oz_pos] = "Mud"
                                        
                            t0_calc = time.perf_counter_ns()
                            p, e, st = self.engine.calculate_path(self.grid.width, self.grid.height, z_pos, self.grid.villager, self.current_algo, temp_cells)
                            t1_calc = time.perf_counter_ns()
                            exec_us = (t1_calc - t0_calc) // 1000
                            
                            self.stats["nodes_expanded"] += len(e)
                            if self.stats["recalcs"] == 1:
                                self.stats["initial_time_us"] = exec_us
                            else:
                                self.stats["total_replan_time_us"] += exec_us

                            if p:
                                if p[0] == z_pos: p.pop(0)
                                self.paths[i] = p
                            else:
                                if self.current_scenario != 6:
                                    self.is_simulating = False
                                    break
                                
                        if self.paths[i]:
                            next_pos = self.paths[i].pop(0)
                            self.grid.ghost_trails.append(z_pos)
                            self.grid.zombies[i] = next_pos
                            self.stats["steps"] += 1
                            
                    if self.grid.villager in self.grid.zombies:
                        self.is_simulating = False
                        success = True
                        break
                        
                    steps_count += 1
                
                obs_density, avg_fric = self._get_environmental_metrics()
                actual_recalcs = max(0, self.stats["recalcs"] - 1)
                avg_replan_us = round(self.stats["total_replan_time_us"] / actual_recalcs, 2) if actual_recalcs > 0 else 0
                moving_obs = sc in [3, 4]
                status_str = "SUCCESS" if success else "FAILED/TIMED_OUT"
                
                results.append([
                    sc, f"{grid_sz}x{grid_sz}", obs_density, avg_fric,
                    len(self.grid.zombies), ALGORITHMS[algo],
                    self.stats["initial_time_us"], self.stats["nodes_expanded"],
                    self.stats["steps"], actual_recalcs, avg_replan_us,
                    self.target_moving, moving_obs, status_str
                ])
                
        file_exists = os.path.exists(BENCHMARK_CSV)
        with open(BENCHMARK_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Scenario_ID", "Grid_Size", "Obstacle_Density_Pct", 
                    "Average_Terrain_Friction", "Zombie_Count", "Algorithm", 
                    "Execution_Time_us", "Nodes_Expanded", "Path_Length", 
                    "Recalculation_Count", "Average_Replan_Time_us", 
                    "Target_Is_Moving", "Moving_Obstacles_Present", "Success_Status"
                ])
            writer.writerows(results)
            
        print("==================================================")
        print(f"BENCHMARK COMPLETE. Results written to {BENCHMARK_CSV}")
        print("==================================================")

    def simulation_tick(self):
        if not self.is_simulating: return
        
        if self.grid.villager in self.grid.zombies:
            self.is_simulating = False
            self.stats["status"] = "SUCCESS! VILLAGER CAUGHT."
            self.log_benchmark_results() # Log interactive success runs
            return
        
        now = time.time()
        speed_delay = SPEEDS[self.speed_idx][1]
        
        if now - self.last_tick > speed_delay:
            self.last_tick = now
            self.stats["status"] = "Running..."
            
            self.update_dynamic_elements()
            
            if self.execution_steps:
                self.current_cpp_line = self.execution_steps.pop(0)
            
            if self.current_scenario == 6:
                for zx, zy in self.grid.zombies:
                    for fx in range(self.grid.width):
                        for fy in range(self.grid.height):
                            if math.hypot(fx - zx, fy - zy) <= 5: 
                                if (fx, fy) in self.grid.cells:
                                    self.known_cells[(fx, fy)] = self.grid.cells[(fx, fy)]
                active_cells = self.known_cells
            else:
                active_cells = self.grid.cells
            
            for i in range(len(self.grid.zombies)):
                z_pos = self.grid.zombies[i]
                
                if self.current_scenario == 6 and random.random() < 0.35:
                    continue 
                
                needs_recalc = False
                if i not in self.paths or not self.paths[i]: needs_recalc = True
                elif self.grid.villager != self.paths[i][-1]: needs_recalc = True
                else:
                    next_step = self.paths[i][0]
                    t_type = active_cells.get(next_step, "Empty")
                    if TERRAIN[t_type]["weight"] == -1: needs_recalc = True
                        
                if needs_recalc:
                    self.stats["recalcs"] += 1
                    
                    temp_cells = active_cells.copy()
                    if self.current_scenario == 7:
                        for oz_idx, oz_pos in enumerate(self.grid.zombies):
                            if oz_idx != i and oz_pos != self.grid.villager:
                                temp_cells[oz_pos] = "Mud" 
                                
                    t0_calc = time.perf_counter_ns()
                    p, e, st = self.engine.calculate_path(self.grid.width, self.grid.height, z_pos, self.grid.villager, self.current_algo, temp_cells)
                    t1_calc = time.perf_counter_ns()
                    exec_us = (t1_calc - t0_calc) // 1000
                    
                    self.stats["nodes_expanded"] += len(e)
                    if self.stats["recalcs"] == 1:
                        self.stats["initial_time_us"] = exec_us
                    else:
                        self.stats["total_replan_time_us"] += exec_us
                    
                    if p: 
                        if p[0] == z_pos: p.pop(0) 
                        self.paths[i] = p
                        self.grid.evaluated_nodes = e
                        self.execution_steps = st
                        self.stats["time"] = f"{len(e) // 2} ms"
                    else:
                        if self.current_scenario != 6:
                            self.is_simulating = False
                            self.stats["status"] = "FAIL: NO PATH FOUND"
                            self.log_benchmark_results() # Log interactive failures
                            return
                
                if self.paths[i]:
                    next_pos = self.paths[i].pop(0)
                    self.grid.ghost_trails.append(z_pos)
                    self.grid.zombies[i] = next_pos
                    self.grid.path_nodes = [step for p_list in self.paths.values() for step in p_list]
                    self.stats["steps"] += 1

            if self.grid.villager in self.grid.zombies:
                self.is_simulating = False
                self.stats["status"] = "SUCCESS! VILLAGER CAUGHT."
                self.log_benchmark_results() # Log interactive success runs
                return

    def process_events(self):
        reqs, reqs_met = self.check_requirements()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                left_click = event.button == 1
                
                if self.state == "MAIN_MENU" and left_click:
                    start_rect, exit_rect = self.ui.draw_main_menu()
                    if start_rect.collidepoint(mx, my): self.state = "SIMULATION"
                    elif exit_rect.collidepoint(mx, my): self.running = False
                
                elif self.state == "SIMULATION":
                    action = self.ui.handle_click(mx, my)
                    
                    if action and left_click:
                        if action == "SIMULATE": 
                            if self.is_simulating: 
                                self.is_simulating = False
                            elif reqs_met: 
                                # Save their exact current positions as the starting point
                                self.initial_zombies = list(self.grid.zombies)
                                self.initial_villager = self.grid.villager
                                self.is_simulating = True
                        elif action == "RESET": self.reset_environment()
                        elif action == "MENU": self.state = "MAIN_MENU"
                        elif action == "TOGGLE_TERMINAL": self.show_terminal = not self.show_terminal
                        elif action == "TOGGLE_SPEED":
                            self.speed_idx = (self.speed_idx + 1) % len(SPEEDS)
                        elif action == "TOGGLE_TGT": self.target_moving = not self.target_moving
                        elif action == "TOGGLE_SCENARIO" and not self.is_simulating: 
                            self.current_scenario = (self.current_scenario % 8) + 1
                            self.load_scenario()
                        elif action == "TOGGLE_ALGO":
                            self.current_algo = (self.current_algo + 1) % len(ALGORITHMS)
                            self.stats["algorithm"] = ALGORITHMS[self.current_algo]
                            print(f"Algorithm switched to: {ALGORITHMS[self.current_algo]}")
                        elif action == "TOGGLE_GRID" and not self.is_simulating:
                            self.current_grid_idx = (self.current_grid_idx + 1) % len(self.grid_sizes)
                            new_sz = self.grid_sizes[self.current_grid_idx]
                            c_sz = 15 if new_sz >= 40 else (20 if new_sz >= 30 else DEFAULT_CELL_SIZE)
                            self.grid = GridManager(new_sz, new_sz, c_sz)
                            self.load_scenario()
                        elif action == "CYCLE_TOOL" and not self.is_simulating:
                            try:
                                idx = TERRAIN_TOOLS.index(self.current_tool)
                                self.current_tool = TERRAIN_TOOLS[(idx + 1) % len(TERRAIN_TOOLS)]
                            except ValueError:
                                self.current_tool = TERRAIN_TOOLS[0]
                        elif "TOOL_" in action and not self.is_simulating: 
                            self.current_tool = action.split("_")[1]
                            
                    else:
                        self.grid.update_offsets(self.show_terminal)
                        if self.grid.offset_x < mx < SCREEN_W - 300 and my < SCREEN_H - 80 and not self.is_simulating:
                            self.grid.handle_click(mx, my, self.current_tool, event.button, self.current_scenario)

    def render(self):
        if self.state == "MAIN_MENU": self.ui.draw_main_menu()
        elif self.state == "SIMULATION":
            self.screen.fill((10, 10, 10))
            self.grid.update_offsets(self.show_terminal)
            self.grid.render(self.screen, self.current_scenario, self.known_cells)
            
            reqs, reqs_met = self.check_requirements()
            self.ui.draw_dashboard(
                self.current_scenario, self.current_algo, self.stats, self.current_tool, 
                self.show_terminal, self.grid_sizes[self.current_grid_idx], reqs, reqs_met, 
                self.is_simulating, SPEEDS[self.speed_idx][0], self.target_moving, self.current_cpp_line
            )
        pygame.display.flip()

    def run(self):
        if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
            self.run_batch_benchmarks()
            pygame.quit()
            sys.exit()
            
        while self.running:
            self.process_events()
            self.simulation_tick()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    SimulationEngine().run()