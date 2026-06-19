# grid.py
import pygame
import math
import os
from config import *

class GridManager:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        self.offset_x = 260
        self.offset_y = 20

        self.cells = {} 
        self.zombies = [] 
        self.villager = None
        self.ghost_trails = [] 
        
        self.path_nodes = []
        self.evaluated_nodes = []
        
        self.moving_wall_dir = 1
        self.fog_surf = pygame.Surface((self.width * self.cell_size, self.height * self.cell_size), pygame.SRCALPHA)
        
        # Grid weight numeric overlay engine
        self.cost_font = pygame.font.SysFont("Consolas", max(10, int(self.cell_size * 0.45)), bold=True)
        
        self.v_img = None
        self.z_img = None
        self.load_assets()

    def load_assets(self):
        v_path = os.path.join("assets", "villager.png")
        z_path = os.path.join("assets", "zombie.png")
        if os.path.exists(v_path):
            img = pygame.image.load(v_path).convert_alpha()
            self.v_img = pygame.transform.scale(img, (self.cell_size, self.cell_size))
        if os.path.exists(z_path):
            img = pygame.image.load(z_path).convert_alpha()
            self.z_img = pygame.transform.scale(img, (self.cell_size, self.cell_size))

    def update_offsets(self, show_terminal):
        self.offset_x = 560 if show_terminal else 260

    def handle_click(self, mx, my, current_tool, button_type, current_scenario):
        adj_x, adj_y = mx - self.offset_x, my - self.offset_y
        if adj_x < 0 or adj_y < 0: return

        gx, gy = adj_x // self.cell_size, adj_y // self.cell_size
        if gx >= self.width or gy >= self.height: return

        max_zombies = 3 if current_scenario in [5, 7] else 1

        if current_tool == "Zombie" and button_type == 1: 
            if len(self.zombies) >= max_zombies: self.zombies.pop(0) 
            self.zombies.append((gx, gy))
        elif current_tool == "Villager" and button_type == 1: 
            self.villager = (gx, gy)
        elif current_tool in TERRAIN_TOOLS:
            if button_type == 1: self.cells[(gx, gy)] = current_tool
            elif button_type == 3 and (gx, gy) in self.cells: del self.cells[(gx, gy)]

    def render(self, screen, current_scenario, known_cells):
        canvas_w, canvas_h = self.width * self.cell_size, self.height * self.cell_size
        pygame.draw.rect(screen, (10, 10, 10), (self.offset_x, self.offset_y, canvas_w, canvas_h))

        for x in range(self.width):
            for y in range(self.height):
                rect = pygame.Rect(self.offset_x + (x * self.cell_size), self.offset_y + (y * self.cell_size), self.cell_size, self.cell_size)
                
                t_type = "Empty"
                if current_scenario == 6:
                    if (x, y) in known_cells: t_type = known_cells[(x,y)]
                else:
                    if (x, y) in self.cells: t_type = self.cells[(x,y)]
                
                color = TERRAIN[t_type]["color"]
                if (x, y) in self.ghost_trails: color = C_DARK_GRAY
                elif (x, y) in self.path_nodes: color = C_YELLOW
                elif (x, y) in self.evaluated_nodes: color = (100, 100, 150)
                
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)

                # RENDER TEXT WEIGHT NUMERICAL OVERLAYS ON TILES
                weight_val = TERRAIN[t_type]["weight"]
                if weight_val != 1 and weight_val != -1: # Skip standard blank space/unpathable walls
                    txt_surf = self.cost_font.render(str(weight_val), True, (255, 255, 255))
                    screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

        if self.villager:
            vx, vy = self.villager
            rect_pos = (self.offset_x + (vx * self.cell_size), self.offset_y + (vy * self.cell_size))
            if self.v_img: screen.blit(self.v_img, rect_pos)
            else: pygame.draw.rect(screen, C_GREEN, (*rect_pos, self.cell_size, self.cell_size))
            
        for zx, zy in self.zombies:
            rect_pos = (self.offset_x + (zx * self.cell_size), self.offset_y + (zy * self.cell_size))
            if self.z_img: screen.blit(self.z_img, rect_pos)
            else: pygame.draw.rect(screen, C_RED, (*rect_pos, self.cell_size, self.cell_size))

        if current_scenario == 6 and self.zombies:
            self.fog_surf.fill((20, 20, 20, 240))
            zx, zy = self.zombies[0]
            vision_radius = 5
            for fx in range(self.width):
                for fy in range(self.height):
                    if math.hypot(fx - zx, fy - zy) <= vision_radius:
                        rect = pygame.Rect(fx * self.cell_size, fy * self.cell_size, self.cell_size, self.cell_size)
                        pygame.draw.rect(self.fog_surf, (0,0,0,0), rect) 
            screen.blit(self.fog_surf, (self.offset_x, self.offset_y))