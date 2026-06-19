# config.py
SCREEN_W, SCREEN_H = 1400, 900
FPS = 60

DEFAULT_CELL_SIZE = 25
DEFAULT_GRID_W = 20
DEFAULT_GRID_H = 20

C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_GREEN = (46, 204, 113)       
C_RED = (231, 76, 60)          
C_YELLOW = (241, 196, 15)      
C_BLUE = (52, 152, 219)
C_DARK_GRAY = (50, 50, 50)
C_GRAY = (150, 150, 150)
C_UI_BG = (30, 30, 35)

TERRAIN = {
    "Empty": {"weight": 1, "color": C_WHITE},
    "Grass": {"weight": 1, "color": (124, 252, 0)},      
    "Wall":  {"weight": -1, "color": C_BLACK},
    "Tree":  {"weight": -1, "color": (34, 139, 34)},     
    "Rock":  {"weight": 4,  "color": (105, 105, 105)},   
    "Mud":   {"weight": 8,  "color": (139, 69, 19)},     
    "Water": {"weight": 12, "color": (65, 105, 225)},    
    "Fire":  {"weight": -1, "color": (255, 69, 0)}       
}
TERRAIN_TOOLS = ["Wall", "Mud", "Water", "Tree", "Rock", "Fire"]

ALGORITHMS = ["A*", "BFS", "Dijkstra"]
SPEEDS = [("Very Slow", 0.8), ("Normal", 0.2), ("Fast", 0.05), ("Lightning", 0.005)]

SCENARIOS = {
    1: {"title": "1. Basic A*", "type": "Baseline", "desc": "User must place 1 Zombie and 1 Villager in the grid. Build tools are restricted."},
    2: {"title": "2. Static Obstacles", "type": "Spatial Constraint", "desc": "Place 1 Zombie, 1 Villager, and build a straight wall with a gap."},
    3: {"title": "3. Moving Obstacles", "type": "Temporal Constraint", "desc": "Obstacles shift dynamically, forcing immediate recalculations."},
    4: {"title": "4. Moving Target", "type": "Dynamic Destination", "desc": "Target attempts to escape. Zombie continuously pursues."},
    5: {"title": "5. Multiple Agents", "type": "Multi-Agent", "desc": "Multiple zombies swarm the target simultaneously."},
    6: {"title": "6. Limited Vision", "type": "Information Uncertainty", "desc": "Zombie can only see nearby tiles. Confused by limited sight."},
    7: {"title": "7. Terrain Costs", "type": "Weighted Optimization", "desc": "Mud is slower than Rock! 3 zombies spawn on one tile and race taking unique routes."},
    8: {"title": "8. Dynamic Survival", "type": "Chaotic Environment", "desc": "Fire spawns randomly! Evade hazards while chasing the target."}
}