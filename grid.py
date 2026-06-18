# grid.py
import pygame
from config import *

class GridManager:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        self.offset_x = 260
        self.offset_y = 20

        self.walls = set()
        self.zombie_pos = None
        self.villager_pos = None
        self.path_nodes = []
        self.evaluated_nodes = []

    def update_offsets(self, show_terminal):
        self.offset_x = 560 if show_terminal else 260

    def handle_click(self, mx, my, current_tool, button_type):
        adj_x, adj_y = mx - self.offset_x, my - self.offset_y
        if adj_x < 0 or adj_y < 0: return

        gx, gy = adj_x // self.cell_size, adj_y // self.cell_size
        if gx >= self.width or gy >= self.height: return

        if current_tool == "Zombie" and button_type == 1: self.zombie_pos = (gx, gy)
        elif current_tool == "Villager" and button_type == 1: self.villager_pos = (gx, gy)
        elif current_tool == "Wall":
            if button_type == 1: self.walls.add((gx, gy))
            elif button_type == 3 and (gx, gy) in self.walls: self.walls.remove((gx, gy))

    def render(self, screen):
        canvas_w, canvas_h = self.width * self.cell_size, self.height * self.cell_size
        pygame.draw.rect(screen, (10, 10, 10), (self.offset_x, self.offset_y, canvas_w, canvas_h))

        for x in range(self.width):
            for y in range(self.height):
                rect = pygame.Rect(self.offset_x + (x * self.cell_size), self.offset_y + (y * self.cell_size), self.cell_size, self.cell_size)
                color = C_WHITE
                if (x, y) in self.walls: color = C_BLACK
                elif (x, y) in self.path_nodes: color = C_YELLOW
                elif (x, y) in self.evaluated_nodes: color = C_DARK_GRAY
                
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)

        if self.zombie_pos:
            zx, zy = self.zombie_pos
            pygame.draw.rect(screen, C_RED, (self.offset_x + (zx * self.cell_size), self.offset_y + (zy * self.cell_size), self.cell_size, self.cell_size))
        if self.villager_pos:
            vx, vy = self.villager_pos
            pygame.draw.rect(screen, C_GREEN, (self.offset_x + (vx * self.cell_size), self.offset_y + (vy * self.cell_size), self.cell_size, self.cell_size))