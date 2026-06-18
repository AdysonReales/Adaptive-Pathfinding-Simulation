# config.py
SCREEN_W, SCREEN_H = 1400, 900
FPS = 60

DEFAULT_CELL_SIZE = 25
DEFAULT_GRID_W = 20
DEFAULT_GRID_H = 20

# CSS133 Colors
C_WHITE = (255, 255, 255)      # Empty Cell
C_BLACK = (0, 0, 0)            # Obstacle
C_GREEN = (46, 204, 113)       # Villager
C_RED = (231, 76, 60)          # Zombie
C_YELLOW = (241, 196, 15)      # Final Path
C_BLUE = (52, 152, 219)        # Open List / Highlight color
C_DARK_GRAY = (50, 50, 50)     # Explored Node
C_GRAY = (150, 150, 150)       # Ghost Trail
C_UI_BG = (30, 30, 35)         # UI Panels

ALGORITHMS = ["A*", "BFS", "Dijkstra"]

SCENARIOS = {
    1: {"title": "1. Sandbox Pathfinding", "type": "Baseline", "desc": "Free placement of agents and walls. Understand fundamental node exploration."},
    2: {"title": "2. Static Obstacles", "type": "Spatial Constraint", "desc": "Stationary barriers. Algorithm must find optimal detours."},
    3: {"title": "3. Moving Obstacles", "type": "Temporal Constraint", "desc": "Obstacles move during execution. Forces continuous adaptation."},
    4: {"title": "4. Moving Target", "type": "Dynamic Destination", "desc": "Villager changes position. Zombie must continuously pursue."},
    5: {"title": "5. Multiple Agents", "type": "Multi-Agent", "desc": "Multiple zombies navigate while avoiding collisions."},
    6: {"title": "6. Fog of War", "type": "Information Uncertainty", "desc": "Limited vision. Decisions made with incomplete information."},
    7: {"title": "7. Terrain Costs", "type": "Weighted Optimization", "desc": "Different terrain has different movement costs."},
    8: {"title": "8. Dynamic Survival", "type": "Chaotic Environment", "desc": "Unpredictable hazards appear. Prioritize survival."},
    9: {"title": "9. Algorithm Comparison", "type": "Comparative Analysis", "desc": "Compare A*, BFS, and Dijkstra simultaneously."}
}