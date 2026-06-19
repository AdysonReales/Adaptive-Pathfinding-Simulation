#include <iostream>
#include <vector>
#include <queue>
#include <cmath>
#include <algorithm>

using namespace std;

struct Node {
    int x, y, g, h;
    Node* parent;
    Node(int _x, int _y, int _g, int _h, Node* _p = nullptr) : x(_x), y(_y), g(_g), h(_h), parent(_p) {}
    int f() const { return g + h; }
};

struct CompareNode {
    bool operator()(const Node* a, const Node* b) { return a->f() > b->f(); }
};

int manhattanDistance(int x1, int y1, int x2, int y2) { return abs(x1 - x2) + abs(y1 - y2); }

void findPath(int width, int height, const vector<vector<int>>& grid, int startX, int startY, int goalX, int goalY, int algo) {
    priority_queue<Node*, vector<Node*>, CompareNode> pq;
    queue<Node*> q; 
    vector<vector<bool>> closedSet(width, vector<bool>(height, false));

    int initialH = (algo == 0) ? manhattanDistance(startX, startY, goalX, goalY) * 10 : 0;
    Node* startNode = new Node(startX, startY, 0, initialH);
    
    if (algo == 1) q.push(startNode);
    else pq.push(startNode);

    int dx[] = {0, 0, -1, 1, -1, 1, -1, 1}; 
    int dy[] = {-1, 1, 0, 0, -1, -1, 1, 1};
    Node* targetNode = nullptr;

    while ((algo == 1 && !q.empty()) || (algo != 1 && !pq.empty())) {
        Node* current;
        if (algo == 1) { current = q.front(); q.pop(); }
        else { current = pq.top(); pq.pop(); }

        if (current->x == goalX && current->y == goalY) {
            targetNode = current; break;
        }

        if (closedSet[current->x][current->y]) { delete current; continue; }
        closedSet[current->x][current->y] = true;

        for (int i = 0; i < 8; ++i) {
            int nx = current->x + dx[i];
            int ny = current->y + dy[i];

            if (nx >= 0 && nx < width && ny >= 0 && ny < height && !closedSet[nx][ny] && grid[nx][ny] != -1) {
                int tile_weight = grid[nx][ny];
                int move_cost = (i < 4) ? 10 : 14; 
                int gCost = current->g + (move_cost * tile_weight); 
                int hCost = (algo == 0) ? manhattanDistance(nx, ny, goalX, goalY) * 10 : 0;
                
                Node* neighbor = new Node(nx, ny, gCost, hCost, current);
                if (algo == 1) q.push(neighbor);
                else pq.push(neighbor);
            }
        }
    }

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