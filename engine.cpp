#include <iostream>
#include <vector>
#include <queue>
#include <cmath>
#include <algorithm>

using namespace std;

struct Node {
    int x, y, g, h;
    Node* parent;
    Node(int _x, int _y, int _g, int _h, Node* _p = nullptr) 
        : x(_x), y(_y), g(_g), h(_h), parent(_p) {}
    int f() const { return g + h; }
};

// Priority Queue sorting logic (Lowest f() first for A* / Dijkstra)
struct CompareNode {
    bool operator()(const Node* a, const Node* b) { return a->f() > b->f(); }
};

// Octile Distance handles diagonal weights accurately for 8-directional movement
int octileDistance(int x1, int y1, int x2, int y2) {
    int dx = abs(x1 - x2);
    int dy = abs(y1 - y2);
    return 10 * (dx + dy) + (14 - 20) * min(dx, dy);
}

void findPath(int width, int height, const vector<vector<int>>& grid, int startX, int startY, int goalX, int goalY, int algo) {
    cout << "STEP LINE_INIT\n";
    
    priority_queue<Node*, vector<Node*>, CompareNode> pq;
    queue<Node*> q; 
    vector<vector<bool>> closedSet(width, vector<bool>(height, false));
    
    // Master tracking list to ensure 100% clean memory deallocation (no heap leaks)
    vector<Node*> allAllocatedNodes;

    // Calculate initial heuristic: Only A* (algo 0) utilizes a heuristic
    int initialH = (algo == 0) ? octileDistance(startX, startY, goalX, goalY) : 0;
    Node* startNode = new Node(startX, startY, 0, initialH);
    allAllocatedNodes.push_back(startNode);
    
    if (algo == 1) q.push(startNode);
    else pq.push(startNode);

    // 8-Directional Delta Arrays
    int dx[] = {0, 0, -1, 1, -1, 1, -1, 1}; 
    int dy[] = {-1, 1, 0, 0, -1, -1, 1, 1};
    Node* targetNode = nullptr;

    while ((algo == 1 && !q.empty()) || (algo != 1 && !pq.empty())) {
        cout << "STEP LINE_WHILE\n";
        Node* current;
        
        if (algo == 1) { 
            current = q.front(); 
            q.pop(); 
        } else { 
            current = pq.top(); 
            pq.pop(); 
        }

        cout << "STEP LINE_POP\n";
        if (current->x == goalX && current->y == goalY) {
            cout << "STEP LINE_GOAL\n";
            targetNode = current; 
            break;
        }

        if (closedSet[current->x][current->y]) continue;
        closedSet[current->x][current->y] = true;
        
        cout << "EVAL " << current->x << " " << current->y << "\n";
        cout << "STEP LINE_CLOSE\n";

        for (int i = 0; i < 8; ++i) {
            int nx = current->x + dx[i];
            int ny = current->y + dy[i];

            if (nx >= 0 && nx < width && ny >= 0 && ny < height && !closedSet[nx][ny] && grid[nx][ny] != -1) {
                cout << "STEP LINE_NEIGHBOR\n";
                
                int tile_weight = grid[nx][ny];
                int move_cost = (i < 4) ? 10 : 14; // Straight = 10, Diagonal = 14
                
                // Algorithmic Differences in Path Generation:
                int gCost, hCost;
                if (algo == 1) {
                    // BFS treats all steps equally (ignores terrain friction weights entirely)
                    gCost = current->g + move_cost;
                    hCost = 0;
                } else if (algo == 2) {
                    // Dijkstra calculates true cumulative friction weight, no heuristic steering
                    gCost = current->g + (move_cost * tile_weight);
                    hCost = 0;
                } else {
                    // A* evaluates true terrain friction cost AND applies heuristic positioning
                    gCost = current->g + (move_cost * tile_weight);
                    hCost = octileDistance(nx, ny, goalX, goalY);
                }
                
                Node* neighbor = new Node(nx, ny, gCost, hCost, current);
                allAllocatedNodes.push_back(neighbor);
                
                if (algo == 1) q.push(neighbor);
                else pq.push(neighbor);
            }
        }
    }

    // Output Path Coordinates to standard out if path exists
    if (targetNode != nullptr) {
        vector<pair<int, int>> path;
        Node* curr = targetNode;
        while (curr != nullptr) {
            path.push_back({curr->x, curr->y});
            curr = curr->parent;
        }
        reverse(path.begin(), path.end());
        for (const auto& pt : path) cout << "PATH " << pt.first << " " << pt.second << "\n";
    }
    cout << "DONE\n" << flush;

    // Automated cleanup loop to eliminate Errno 13 / Memory Overhangs
    for (Node* node : allAllocatedNodes) {
        delete node;
    }
}

int main() {
    int width, height, startX, startY, goalX, goalY, algo;
    if (!(cin >> width >> height >> startX >> startY >> goalX >> goalY >> algo)) return 1;

    vector<vector<int>> grid(width, vector<int>(height, 1));
    int x, y, w;
    while (cin >> x >> y >> w) {
        if (x == -1 && y == -1 && w == -1) break;
        if (x >= 0 && x < width && y >= 0 && y < height) grid[x][y] = w;
    }

    findPath(width, height, grid, startX, startY, goalX, goalY, algo);
    return 0;
}