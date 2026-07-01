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
        title = pygame.font.SysFont("Arial", 36, bold=True).render("Adaptive Pathfinding Complexity", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 200))
        start_rect = pygame.Rect(SCREEN_W//2 - 100, 350, 200, 50)
        exit_rect = pygame.Rect(SCREEN_W//2 - 100, 420, 200, 50)
        pygame.draw.rect(self.screen, C_BLUE, start_rect, border_radius=5)
        pygame.draw.rect(self.screen, C_RED, exit_rect, border_radius=5)
        self.screen.blit(self.font.render("START SIMULATION", True, C_WHITE), (start_rect.x + 35, start_rect.y + 15))
        self.screen.blit(self.font.render("EXIT", True, C_WHITE), (exit_rect.x + 80, exit_rect.y + 15))
        return start_rect, exit_rect

    def create_btn(self, text, x, y, w, h, action_code, active=False, color=None, disabled=False):
        bg = (70, 70, 70) if disabled else (color if color else (C_GREEN if active else (100, 100, 100)))
        text_color = (150, 150, 150) if disabled else C_WHITE
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        txt = self.font.render(text, True, text_color)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
        if not disabled: self.buttons[action_code] = rect

    def draw_dashboard(self, cur_scen, cur_algo, stats, cur_tool, show_term, grid_size, reqs, reqs_met, is_simulating, speed_name, tgt_moving, current_code_line):
        self.buttons.clear()
        taskbar_y = SCREEN_H - 80

        # BOTTOM TASKBAR
        pygame.draw.rect(self.screen, C_UI_BG, (0, taskbar_y, SCREEN_W, 80))
        pygame.draw.line(self.screen, C_WHITE, (0, taskbar_y), (SCREEN_W, taskbar_y))
        
        self.create_btn(f"Grid: {grid_size}x{grid_size}", 20, taskbar_y + 25, 110, 30, "TOGGLE_GRID", color=(142, 68, 173), disabled=is_simulating)
        sim_color = C_BLUE if not is_simulating else C_RED
        sim_text = "STOP" if is_simulating else "SIMULATE"
        self.create_btn(sim_text, 140, taskbar_y + 20, 100, 40, "SIMULATE", color=sim_color, disabled=(not reqs_met and not is_simulating))
        self.create_btn(f"Speed: {speed_name}", 250, taskbar_y + 25, 140, 30, "TOGGLE_SPEED", color=(22, 160, 133))
        
        build_off = cur_scen == 1 or is_simulating
        self.create_btn("Villager", 400, taskbar_y + 25, 80, 30, "TOOL_Villager", cur_tool == "Villager", disabled=is_simulating)
        self.create_btn("Zombie", 490, taskbar_y + 25, 70, 30, "TOOL_Zombie", cur_tool == "Zombie", disabled=is_simulating)
        
        self.create_btn("Build Wall", 570, taskbar_y + 25, 100, 30, "TOOL_Wall", cur_tool == "Wall", disabled=build_off)
        is_terrain_tool = cur_tool in TERRAIN_TOOLS and cur_tool != "Wall"
        tool_color = TERRAIN[cur_tool]["color"] if is_terrain_tool else None
        self.create_btn(f"Terrain: {cur_tool}", 680, taskbar_y + 25, 130, 30, "CYCLE_TOOL", active=is_terrain_tool, color=tool_color, disabled=build_off)
        
        self.create_btn("Terminal", 820, taskbar_y + 25, 80, 30, "TOGGLE_TERMINAL", active=show_term)
        self.create_btn(f"Scenario: {cur_scen}", 910, taskbar_y + 25, 110, 30, "TOGGLE_SCENARIO", color=(230, 126, 34), disabled=is_simulating)
        
        tgt_color = C_GREEN if tgt_moving else C_RED
        self.create_btn("TGT: " + ("MOVE" if tgt_moving else "STAY"), 1030, taskbar_y + 25, 90, 30, "TOGGLE_TGT", color=tgt_color)
        self.create_btn("Reset", 1130, taskbar_y + 25, 60, 30, "RESET", color=C_RED)
        
        # ALGO TOGGLE BUTTON (Placed cleanly at X=1200)
        self.create_btn(f"Algo: {ALGORITHMS[cur_algo]}", 1200, taskbar_y + 25, 110, 30, "TOGGLE_ALGO", color=(52, 73, 94), disabled=is_simulating)
        
        self.create_btn("Menu", SCREEN_W - 80, taskbar_y + 25, 60, 30, "MENU", color=(50, 50, 50))

        # LEFT SIDEBAR
        start_x = 350 if show_term else 0
        pygame.draw.rect(self.screen, C_UI_BG, (start_x, 0, 250, taskbar_y))
        pygame.draw.line(self.screen, C_WHITE, (start_x + 250, 0), (start_x + 250, taskbar_y))
        sc_data = SCENARIOS[cur_scen]
        self.screen.blit(self.title_font.render("SCENARIO INFO", True, C_YELLOW), (start_x + 20, 20))
        self.screen.blit(self.stats_font.render(sc_data["title"], True, C_WHITE), (start_x + 20, 60))
        words, y_off, line = sc_data["desc"].split(' '), 100, ""
        for w in words:
            if self.font.size(line + w)[0] > 210:
                self.screen.blit(self.font.render(line, True, (200, 200, 200)), (start_x + 20, y_off))
                line, y_off = w + " ", y_off + 20
            else: line += w + " "
        self.screen.blit(self.font.render(line, True, (200, 200, 200)), (start_x + 20, y_off))

        # RIGHT SIDEBAR
        rs_x = SCREEN_W - 300
        pygame.draw.rect(self.screen, C_UI_BG, (rs_x, 0, 300, taskbar_y))
        pygame.draw.line(self.screen, C_WHITE, (rs_x, 0), (rs_x, taskbar_y))
        self.screen.blit(self.title_font.render("REQUIREMENTS", True, C_BLUE), (rs_x + 20, 20))
        ry = 60
        for text, is_met in reqs:
            pygame.draw.rect(self.screen, C_GREEN if is_met else C_RED, (rs_x + 20, ry + 2, 12, 12))
            self.screen.blit(self.stats_font.render(text, True, C_WHITE), (rs_x + 40, ry))
            ry += 25
        pygame.draw.line(self.screen, C_WHITE, (rs_x + 20, ry + 10), (rs_x + 280, ry + 10))
        self.screen.blit(self.title_font.render("STATISTICS", True, C_YELLOW), (rs_x + 20, ry + 30))
        sy = ry + 70
        for k, v in stats.items():
            col = C_YELLOW if "status" in k.lower() else C_WHITE
            self.screen.blit(self.stats_font.render(f"{k.upper()}:", True, col), (rs_x + 20, sy))
            self.screen.blit(self.stats_font.render(str(v), True, C_WHITE), (rs_x + 150, sy))
            sy += 35

        # REAL C++ CODE HIGH-LIGHTED TERMINAL PANEL
        if show_term:
            term_w = 350
            pygame.draw.rect(self.screen, (15, 15, 22), (0, 0, term_w, taskbar_y))
            pygame.draw.line(self.screen, C_GREEN, (term_w, 0), (term_w, taskbar_y), 2)
            self.screen.blit(self.title_font.render("LIVE C++ CODE TERMINAL", True, C_GREEN), (20, 20))
            
            cpp_code = [
                ("LINE_INIT",     "pq.push(startNode); closedSet[sx][sy]=true;"),
                ("LINE_WHILE",    "while (!pq.empty()) {"),
                ("LINE_POP",      "  Node* curr = pq.top(); pq.pop();"),
                ("LINE_GOAL",      "  if (curr->x == gx && curr->y == gy) break;"),
                ("LINE_CLOSE",     "  closedSet[curr->x][curr->y] = true;"),
                ("LINE_NEIGHBOR",  "  for(auto n : getNeighbors(curr)) {"),
                ("LINE_NEIGHBOR",  "    if(valid) pq.push(n); } }")
            ]
            
            cy = 70
            for code_tag, code_str in cpp_code:
                is_active = (code_tag == current_code_line and is_simulating)
                if is_active:
                    line_rect = pygame.Rect(15, cy - 2, term_w - 30, 20)
                    pygame.draw.rect(self.screen, (39, 174, 96, 100), line_rect)
                    text_col = (255, 255, 255)
                else:
                    text_col = (130, 140, 150)
                
                self.screen.blit(self.font.render(code_str, True, text_col), (20, cy))
                cy += 24

    def handle_click(self, mx, my):
        for action, rect in self.buttons.items():
            if rect.collidepoint(mx, my): return action
        return None