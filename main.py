# main.py
import pygame
import sys
import time
import random
import math
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
        
        self.grid_sizes = [10, 20, 30, 40, 50]
        self.current_grid_idx = 1
        self.grid = GridManager(self.grid_sizes[self.current_grid_idx], self.grid_sizes[self.current_grid_idx], DEFAULT_CELL_SIZE)
        
        self.stats = {"status": "Idle", "steps": 0, "recalcs": 0, "algorithm": ALGORITHMS[0]}

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
        self.is_simulating = False
        self.grid.cells.clear()
        self.known_cells.clear()
        self.grid.zombies.clear()
        self.grid.villager = None
        self.grid.ghost_trails.clear()
        self.grid.path_nodes.clear()
        self.grid.evaluated_nodes.clear()
        self.paths.clear()
        self.execution_steps.clear()
        self.current_cpp_line = "LINE_INIT"
        self.stats = {"status": "Idle", "steps": 0, "recalcs": 0, "algorithm": ALGORITHMS[self.current_algo]}

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
        self.reset_environment()
        w, h = self.grid.width, self.grid.height
        
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
        best_pos = self.grid.villager
        best_score = -9999
        vx, vy = self.grid.villager
        
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (0,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            nx, ny = vx+dx, vy+dy
            if 0 <= nx < self.grid.width and 0 <= ny < self.grid.height:
                t_type = self.grid.cells.get((nx, ny), "Empty")
                if TERRAIN[t_type]["weight"] != -1:
                    min_z_dist = min([math.hypot(nx-zx, ny-zy) for zx, zy in self.grid.zombies]) if self.grid.zombies else 100
                    mobility = 0
                    for ex, ey in [(0,1), (1,0), (0,-1), (-1,0)]:
                        if 0 <= nx+ex < self.grid.width and 0 <= ny+ey < self.grid.height:
                            if TERRAIN[self.grid.cells.get((nx+ex, ny+ey), "Empty")]["weight"] != -1:
                                mobility += 1
                    
                    score = (min_z_dist * 10) + mobility
                    if score > best_score:
                        best_score = score
                        best_pos = (nx, ny)
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
            
        if self.target_moving and self.current_scenario in [4, 5, 8] and self.grid.villager:
            if random.random() < 0.6: 
                self.grid.villager = self.get_villager_move()

        if self.current_scenario == 8:
            if random.random() < 0.15: 
                hx, hy = random.randint(0, self.grid.width-1), random.randint(0, self.grid.height-1)
                if (hx, hy) not in self.grid.zombies and (hx, hy) != self.grid.villager:
                    self.grid.cells[(hx, hy)] = "Fire"

    def simulation_tick(self):
        if not self.is_simulating: return
        
        if self.grid.villager in self.grid.zombies:
            self.is_simulating = False
            self.stats["status"] = "SUCCESS! VILLAGER CAUGHT."
            return
        
        now = time.time()
        speed_delay = SPEEDS[self.speed_idx][1]
        
        if now - self.last_tick > speed_delay:
            self.last_tick = now
            self.stats["status"] = "Running..."
            
            self.update_dynamic_elements()
            
            # Pop and flash the next line execution directly onto the UI terminal
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
                                
                    p, e, st = self.engine.calculate_path(self.grid.width, self.grid.height, z_pos, self.grid.villager, self.current_algo, temp_cells)
                    
                    if p: 
                        if p[0] == z_pos: p.pop(0) 
                        self.paths[i] = p
                        self.grid.evaluated_nodes = e
                        self.execution_steps = st # Load live trace steps
                    else:
                        if self.current_scenario != 6:
                            self.is_simulating = False
                            self.stats["status"] = "FAIL: NO PATH FOUND"
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
                            if self.is_simulating: self.is_simulating = False
                            elif reqs_met: self.is_simulating = True
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
        while self.running:
            self.process_events()
            self.simulation_tick()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    SimulationEngine().run()