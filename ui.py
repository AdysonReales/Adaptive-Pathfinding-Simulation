# ui.py
import pygame
from config import *

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Consolas", 14)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.stats_font = pygame.font.SysFont("Consolas", 16)
        self.buttons = {}

    def draw_main_menu(self):
        self.screen.fill((20, 20, 20))
        title_surf = pygame.font.SysFont("Arial", 36, bold=True).render("Adaptive Pathfinding Complexity", True, C_WHITE)
        self.screen.blit(title_surf, (SCREEN_W//2 - title_surf.get_width()//2, 200))

        start_rect = pygame.Rect(SCREEN_W//2 - 100, 350, 200, 50)
        exit_rect = pygame.Rect(SCREEN_W//2 - 100, 420, 200, 50)

        pygame.draw.rect(self.screen, C_BLUE, start_rect, border_radius=5)
        pygame.draw.rect(self.screen, C_RED, exit_rect, border_radius=5)

        self.screen.blit(self.font.render("START SIMULATION", True, C_WHITE), (start_rect.x + 35, start_rect.y + 15))
        self.screen.blit(self.font.render("EXIT", True, C_WHITE), (exit_rect.x + 80, exit_rect.y + 15))
        return start_rect, exit_rect

    def create_btn(self, text, x, y, w, h, action_code, active=False, color=None, disabled=False):
        if disabled:
            bg = (70, 70, 70)
            text_color = (150, 150, 150)
        else:
            bg = color if color else (C_GREEN if active else (100, 100, 100))
            text_color = C_WHITE
            
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        txt = self.font.render(text, True, text_color)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
        if not disabled: self.buttons[action_code] = rect

    def draw_dashboard(self, current_scenario, current_algo, stats, current_tool, show_terminal, grid_size):
        self.buttons.clear()
        tools_locked = current_scenario != 1
        taskbar_y = SCREEN_H - 80

        # BOTTOM TASKBAR
        pygame.draw.rect(self.screen, C_UI_BG, (0, taskbar_y, SCREEN_W, 80))
        pygame.draw.line(self.screen, C_WHITE, (0, taskbar_y), (SCREEN_W, taskbar_y))
        
        self.create_btn(f"Grid: {grid_size}x{grid_size}", 20, taskbar_y + 25, 110, 30, "TOGGLE_GRID", color=(142, 68, 173), disabled=tools_locked)
        self.create_btn("SIMULATE", 140, taskbar_y + 20, 100, 40, "SIMULATE", color=C_BLUE)
        self.create_btn("NPC (Villager)", 260, taskbar_y + 25, 120, 30, "TOOL_Villager", current_tool == "Villager", disabled=tools_locked)
        self.create_btn("Enemy (Zombie)", 390, taskbar_y + 25, 120, 30, "TOOL_Zombie", current_tool == "Zombie", disabled=tools_locked)
        self.create_btn("Build Wall", 520, taskbar_y + 25, 100, 30, "TOOL_Wall", current_tool == "Wall", disabled=tools_locked)
        
        term_color = C_GREEN if show_terminal else (100, 100, 100)
        self.create_btn("Terminal", 640, taskbar_y + 25, 90, 30, "TOGGLE_TERMINAL", color=term_color)
        self.create_btn(f"Scenario: {current_scenario}", 750, taskbar_y + 25, 120, 30, "TOGGLE_SCENARIO", color=(230, 126, 34))
        self.create_btn(ALGORITHMS[current_algo], 880, taskbar_y + 25, 90, 30, "TOGGLE_ALGO", color=(52, 73, 94))
        self.create_btn("Reset", 980, taskbar_y + 25, 70, 30, "RESET", color=C_RED, disabled=tools_locked)
        self.create_btn("Menu", SCREEN_W - 80, taskbar_y + 25, 60, 30, "MENU", color=(50, 50, 50))

        # LEFT SIDEBAR (Scenario Panel)
        start_x = 300 if show_terminal else 0
        pygame.draw.rect(self.screen, C_UI_BG, (start_x, 0, 250, taskbar_y))
        pygame.draw.line(self.screen, C_WHITE, (start_x + 250, 0), (start_x + 250, taskbar_y))
        
        sc_data = SCENARIOS[current_scenario]
        self.screen.blit(self.title_font.render("SCENARIO INFO", True, C_YELLOW), (start_x + 20, 20))
        self.screen.blit(self.stats_font.render(sc_data["title"], True, C_WHITE), (start_x + 20, 60))
        self.screen.blit(self.font.render(f"Complexity: {sc_data['type']}", True, (150, 150, 250)), (start_x + 20, 85))
        
        words, y_off, line = sc_data["desc"].split(' '), 120, ""
        for w in words:
            if self.font.size(line + w)[0] > 210:
                self.screen.blit(self.font.render(line, True, (200, 200, 200)), (start_x + 20, y_off))
                line, y_off = w + " ", y_off + 20
            else: line += w + " "
        self.screen.blit(self.font.render(line, True, (200, 200, 200)), (start_x + 20, y_off))

        # RIGHT SIDEBAR (Statistics Panel)
        rs_x = SCREEN_W - 300
        pygame.draw.rect(self.screen, C_UI_BG, (rs_x, 0, 300, taskbar_y))
        pygame.draw.line(self.screen, C_WHITE, (rs_x, 0), (rs_x, taskbar_y))
        self.screen.blit(self.title_font.render("STATISTICS", True, C_YELLOW), (rs_x + 20, 20))
        
        y = 70
        for k, v in stats.items():
            color = C_YELLOW if "status" in k.lower() else C_WHITE
            self.screen.blit(self.stats_font.render(f"{k.upper()}:", True, color), (rs_x + 20, y))
            self.screen.blit(self.stats_font.render(str(v), True, C_WHITE), (rs_x + 150, y))
            y += 35

        # f) TERMINAL PANEL (Overlay)
        if show_terminal:
            pygame.draw.rect(self.screen, (10, 10, 15), (0, 0, 300, taskbar_y))
            pygame.draw.line(self.screen, C_GREEN, (300, 0), (300, taskbar_y), 2)
            self.screen.blit(self.title_font.render("ALGORITHM TERMINAL", True, C_GREEN), (20, 20))
            
            code_lines = [
                "1. Add Start Node to Open List",
                "2. Loop while Open List not empty:",
                "3.   Select Node with lowest F-Cost",
                "4.   If Node == Goal:",
                "5.     Return Path Found",
                "6.   Move Node to Closed List",
                "7.   Evaluate Neighbors...",
            ]
            cy = 70
            for i, line in enumerate(code_lines):
                text_color = C_YELLOW if (i == 2 and stats.get("status") == "Calculating...") else (150, 150, 150)
                self.screen.blit(self.stats_font.render(line, True, text_color), (20, cy))
                cy += 25

    def handle_click(self, mx, my):
        for action, rect in self.buttons.items():
            if rect.collidepoint(mx, my): return action
        return None