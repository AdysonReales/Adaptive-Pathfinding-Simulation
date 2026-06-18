# main.py
import pygame
import sys
import time
from config import *
from ui import UIManager
from grid import GridManager
from engine_connector import CppEngineConnector

class SimulationEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Adaptive Pathfinding Suite")
        self.clock = pygame.time.Clock()
        
        self.ui = UIManager(self.screen)
        self.engine = CppEngineConnector()
        
        self.state = "MAIN_MENU"
        self.running = True
        
        self.current_tool = "Wall" 
        self.current_scenario = 1
        self.current_algo = 0
        self.show_terminal = False
        
        self.grid_sizes = [10, 20, 30, 40, 50]
        self.current_grid_idx = 1 
        
        self.grid = GridManager(self.grid_sizes[self.current_grid_idx], self.grid_sizes[self.current_grid_idx], DEFAULT_CELL_SIZE)
        self.stats = {"status": "Idle", "time": "0ms", "length": 0, "explored": 0, "recalcs": 0, "algorithm": ALGORITHMS[0]}

    def load_scenario_environment(self):
        self.grid.walls.clear()
        self.grid.path_nodes.clear()
        self.grid.evaluated_nodes.clear()
        self.stats = {"status": "Idle", "time": "0ms", "length": 0, "explored": 0, "recalcs": 0, "algorithm": ALGORITHMS[self.current_algo]}
        
        if self.current_scenario == 1:
            self.grid.zombie_pos = None
            self.grid.villager_pos = None
        elif self.current_scenario == 2:
            self.grid.zombie_pos = (2, 2)
            self.grid.villager_pos = (17, 17)
            for y in range(2, 18):
                if y != 10: self.grid.walls.add((10, y))
        elif self.current_scenario >= 3:
            self.grid.zombie_pos = (1, 1)
            self.grid.villager_pos = (18, 18)
            import random
            for _ in range(35):
                self.grid.walls.add((random.randint(3, 16), random.randint(3, 16)))

    def run_simulation(self):
        if not self.grid.zombie_pos or not self.grid.villager_pos:
            self.stats["status"] = "Error: Missing Agents"
            return
            
        self.stats["status"] = "Calculating..."
        self.render()
        
        t0 = time.time()
        path, evaluated = self.engine.calculate_path(self.grid.width, self.grid.height, self.grid.zombie_pos, self.grid.villager_pos, self.current_algo, self.grid.walls)
        t1 = time.time()
        
        self.grid.path_nodes = path
        self.grid.evaluated_nodes = evaluated
        
        self.stats["time"] = f"{int((t1-t0)*1000)} ms"
        self.stats["length"] = len(path)
        self.stats["explored"] = len(evaluated)
        self.stats["status"] = "TARGET REACHED" if path else "PATH NOT FOUND"

    def process_events(self):
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
                        if action == "SIMULATE": self.run_simulation()
                        elif action == "RESET": self.load_scenario_environment()
                        elif action == "MENU": self.state = "MAIN_MENU"
                        elif action == "TOGGLE_TERMINAL": self.show_terminal = not self.show_terminal
                        elif action == "TOGGLE_SCENARIO": 
                            self.current_scenario = (self.current_scenario % 9) + 1
                            self.load_scenario_environment()
                        elif action == "TOGGLE_ALGO":
                            self.current_algo = (self.current_algo + 1) % len(ALGORITHMS)
                            self.stats["algorithm"] = ALGORITHMS[self.current_algo]
                        elif action == "TOGGLE_GRID":
                            self.current_grid_idx = (self.current_grid_idx + 1) % len(self.grid_sizes)
                            new_size = self.grid_sizes[self.current_grid_idx]
                            c_size = 15 if new_size >= 40 else (20 if new_size >= 30 else DEFAULT_CELL_SIZE)
                            self.grid = GridManager(new_size, new_size, c_size)
                        elif "TOOL_" in action: self.current_tool = action.split("_")[1]
                        time.sleep(0.15)
                    else:
                        self.grid.update_offsets(self.show_terminal)
                        if self.grid.offset_x < mx < SCREEN_W - 300 and my < SCREEN_H - 80:
                            if self.current_scenario == 1:
                                self.grid.handle_click(mx, my, self.current_tool, event.button)

    def render(self):
        if self.state == "MAIN_MENU": self.ui.draw_main_menu()
        elif self.state == "SIMULATION":
            self.screen.fill((10, 10, 10))
            self.grid.update_offsets(self.show_terminal)
            self.grid.render(self.screen)
            self.ui.draw_dashboard(self.current_scenario, self.current_algo, self.stats, self.current_tool, self.show_terminal, self.grid_sizes[self.current_grid_idx])
        pygame.display.flip()

    def run(self):
        while self.running:
            self.process_events()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    SimulationEngine().run()