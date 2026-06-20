# **Adaptive Pathfinding Under Increasing Environmental Complexity**

An interactive, educational simulator and pathfinding benchmarking platform built with **Python (Pygame)** and a high-performance **C++ Algorithmic Engine**.

This application visualizes and evaluates pathfinding algorithms (A\*, Breadth-First Search, Dijkstra) across 8 progressively complex dynamic scenarios—ranging from static baseline pathfinding to chaotic environments featuring shifting obstacles, fleeing targets, multi-agent congestion, Fog of War, and dynamic fire hazards.

## **📁 File Structure**

For the simulation to run properly, ensure all files are placed in the same project directory:

AdaptivePathfinding/  
├── assets/                     \# (Optional) Folder for image assets  
│   ├── zombie.png              \# Scaled image for zombies (falls back to Red block)  
│   └── villager.png            \# Scaled image for villagers (falls back to Green block)  
├── config.py                   \# Configuration, colors, speed settings, scenario descriptions  
├── engine.cpp                  \# C++ Pathfinding backend (A\*, BFS, Dijkstra)  
├── engine\_connector.py         \# Subprocess communication bridge (Python \<-\> C++)  
├── grid.py                     \# Grid mapping, canvas rendering, fog-of-war, asset loading  
├── main.py                     \# Core game loop, simulation tick engine, state controller  
├── ui.py                       \# Bottom taskbar dashboard, terminal panel, layout sidebars  
└── README.md                   \# This instruction guide

## **🛠️ Prerequisites & Setup**

Ensure both you and your friend have the following installed before launching:

### **1\. Python 3.10+ & Pygame**

The graphical interface is built using Pygame. If you do not have Pygame installed, open your terminal/command prompt and run:

pip install pygame

### **2\. C++ Compiler (GCC/g++)**

The performance backend requires a C++ compiler supporting standard compilation flags (MinGW/MSYS2 for Windows, Xcode command-line tools for macOS, or build-essential for Linux).

## **🚀 How to Build & Run**

### **Step 1: Compile the C++ Backend**

Before running the Python application, you must compile engine.cpp into a machine binary inside the project folder.

* **Windows (MinGW / MINGW64):**  
  g++ \-O3 engine.cpp \-o engine.exe

* **macOS / Linux:**  
  g++ \-O3 engine.cpp \-o engine

*Note: The Python subprocess connector is smart—it automatically checks your operating system and loads engine.exe on Windows or ./engine on Unix systems.*

### **Step 2: Launch the Simulator**

Run the main controller file using Python:

* **Standard Run:**  
  python main.py

* **If using explicit environment paths (e.g. on Windows Local Python installs):**  
  C:/Users/User/AppData/Local/Programs/Python/Python310/python.exe main.py

## **🎮 How to Use the Simulator**

### **1\. The Main Menu**

* Click **START SIMULATION** to enter the workspace canvas.  
* Click **EXIT** to close the window.

### **2\. Placing Agents & Editing Terrain (Scenario 1: Sandbox)**

In **Scenario 1**, you have full control over the canvas:

* **Equip Tools**: Click Zombie or Villager to equip those placement tools.  
* **Paint Entities**: **Left-click** on the grid canvas to spawn your zombie or villager.  
* **Cycle Terrain**: Equip the Draw Wall tool. Click the Terrain button next to it to cycle your brush through **Wall, Mud, Water, Tree, Rock, and Fire**.  
* **Draw/Erase Terrain**: **Left-click** on grid cells to paint your chosen terrain. **Right-click** to erase.

### **3\. Progressive Scenarios (Scenarios 2 to 8\)**

Click the **Scenario: X** button on the bottom taskbar to cycle through the guided lesson plans.

* Scenarios 2–8 feature **premade baseline maps** and lock down the building tools accordingly.  
* Every scenario has a dynamic **Requirements Checklist** displayed in the right sidebar. You **must meet all requirements** (e.g., placing 3 zombies in Scenario 7\) to unlock the **SIMULATE** button.

### **4\. Simulation Execution & Real-Time Adjustments**

* **Simulate/Stop**: Press **SIMULATE** to start the pathfinding run. Press **STOP** to freeze execution.  
* **Reset**: Click **RESET** to clear paths, traces, and entities back to the scenario's baseline state.  
* **Target Mode (TGT: MOVE/STAY)**: Toggle whether the target (Villager) actively flees from zombies.  
* **Speed Selector**: Cycle speed delays between **Very Slow, Normal, Fast, and Lightning** to slow down or speed up the zombie's movement speed.  
* **Algorithm Selector**: Cycle between **A\*, BFS, and Dijkstra** to benchmark performance metrics.  
* **Live Terminal**: Click **Terminal** to slide out a debugger window showing actual C++ code lines highlighting step-by-step as evaluations occur\!

## **⚡ Troubleshooting**

* **Error: "Could not find compiled engine"**: Ensure you successfully compiled engine.cpp into engine.exe (or engine on Mac/Linux) and that the file is sitting in the *exact same folder* as your Python files.  
* **Zombie is not moving**: Make sure you have compiled the latest version of engine.cpp so it outputs the proper path coordinates downstream to Pygame.  
* **Executable Permisson Issues (Mac/Linux)**: If the backend fails to open, you may need to grant execution permissions to the compiled file. Open your terminal in the directory and run:  
  chmod \+x engine

* **"ModuleNotFoundError: No module named 'pygame'"**: Your active Python environment does not have pygame installed. Ensure you install it via pip install pygame and run the script with the exact same python executable.