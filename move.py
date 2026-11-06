import heapq
import math
import random
import time
from collections import deque

import pygame


ALGORITHM_DISPLAY_NAMES = {
    "direct": "Direct",
    "astar": "A*",
    "bfs": "BFS",
    "dijkstra": "Dijkstra",
    "greedy": "Greedy",
    "hill_climbing": "Hill Climbing",
}

ALGORITHM_COLORS = {
    "direct": (255, 220, 0),
    "astar": (255, 80, 80),
    "bfs": (80, 170, 255),
    "dijkstra": (180, 90, 255),
    "greedy": (90, 220, 120),
    "hill_climbing": (255, 120, 180),
}

ALGORITHM_KEYS = [
    "direct",
    "astar",
    "bfs",
    "dijkstra",
    "greedy",
    "hill_climbing",
]


def normalize_algorithm_key(name):
    if not name:
        return "direct"
    key = str(name).strip().lower().replace("-", "_").replace(" ", "_")
    return key if key in ALGORITHM_DISPLAY_NAMES else "direct"


def get_algorithm_display_name(name):
    return ALGORITHM_DISPLAY_NAMES.get(normalize_algorithm_key(name), "Direct")


def get_algorithm_color(name):
    return ALGORITHM_COLORS.get(normalize_algorithm_key(name), ALGORITHM_COLORS["direct"])


class Pathfinder:
    algorithm_key = "direct"

    def __init__(self, width, height, cell_size=32):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.last_visited_cells = []
        self.last_metrics = self._build_metrics(0, [], 0.0, False)

    def _build_metrics(self, nodes_visited, path, elapsed_ms, success):
        return {
            "algorithm": get_algorithm_display_name(self.algorithm_key),
            "nodes_visited": int(nodes_visited),
            "path_length": int(len(path)),
            "calculation_time_ms": float(elapsed_ms),
            "success": bool(success),
            "failed_attempts": 0 if success else 1,
        }

    def _store_metrics(self, nodes_visited, path, elapsed_ms, success):
        self.last_metrics = self._build_metrics(nodes_visited, path, elapsed_ms, success)

    def find_path(self, start_x, start_y, target_x, target_y):
        raise NotImplementedError


class NodeGrid:
    def __init__(self, width, height, cell_size=32):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid_width = max(1, width // cell_size)
        self.grid_height = max(1, height // cell_size)
        self.walkable = [[True for _ in range(self.grid_height)] for _ in range(self.grid_width)]

    def to_cell(self, x, y):
        gx = max(0, min(int(x / self.cell_size), self.grid_width - 1))
        gy = max(0, min(int(y / self.cell_size), self.grid_height - 1))
        return gx, gy

    def to_world(self, gx, gy):
        cx = gx * self.cell_size + self.cell_size // 2
        cy = gy * self.cell_size + self.cell_size // 2
        return cx, cy

    def is_walkable(self, gx, gy):
        return 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.walkable[gx][gy]

    def update_obstacles(self, obstacles):
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                self.walkable[x][y] = True

        for obstacle in obstacles:
            ox, oy, ow, oh = obstacle
            start_x = max(0, int(ox / self.cell_size))
            start_y = max(0, int(oy / self.cell_size))
            end_x = min(self.grid_width, int((ox + ow) / self.cell_size) + 1)
            end_y = min(self.grid_height, int((oy + oh) / self.cell_size) + 1)
            for gx in range(start_x, end_x):
                for gy in range(start_y, end_y):
                    self.walkable[gx][gy] = False


class GridPathfinder(Pathfinder):
    NEIGHBORS = [
        (0, 1, 10),
        (1, 0, 10),
        (0, -1, 10),
        (-1, 0, 10),
        (1, 1, 14),
        (1, -1, 14),
        (-1, -1, 14),
        (-1, 1, 14),
    ]

    def __init__(self, width, height, cell_size=32):
        super().__init__(width, height, cell_size)
        self.grid = NodeGrid(width, height, cell_size)

    def update_obstacles(self, obstacles):
        self.grid.update_obstacles(obstacles)

    def _heuristic(self, cell_a, cell_b):
        dx = abs(cell_a[0] - cell_b[0])
        dy = abs(cell_a[1] - cell_b[1])
        return 14 * min(dx, dy) + 10 * abs(dx - dy)

    def _reconstruct_path(self, came_from, start, goal):
        if goal not in came_from and goal != start:
            return []
        current = goal
        path_cells = []
        while current != start:
            path_cells.append(current)
            current = came_from[current]
        path_cells.reverse()
        return [self.grid.to_world(gx, gy) for gx, gy in path_cells]


class AStarPathfinder(GridPathfinder):
    algorithm_key = "astar"

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        start = self.grid.to_cell(start_x, start_y)
        goal = self.grid.to_cell(target_x, target_y)
        self.last_visited_cells = []

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            self._store_metrics(0, [], elapsed_ms, False)
            return []

        open_heap = []
        heapq.heappush(open_heap, (self._heuristic(start, goal), 0, start))
        came_from = {}
        g_score = {start: 0}
        visited = set()
        tie = 0

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current in visited:
                continue
            visited.add(current)
            self.last_visited_cells.append(current)

            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                self._store_metrics(len(visited), path, elapsed_ms, True)
                return path

            for dx, dy, cost in self.NEIGHBORS:
                nxt = (current[0] + dx, current[1] + dy)
                if not self.grid.is_walkable(*nxt):
                    continue
                tentative = g_score[current] + cost
                if tentative < g_score.get(nxt, float("inf")):
                    came_from[nxt] = current
                    g_score[nxt] = tentative
                    tie += 1
                    f_score = tentative + self._heuristic(nxt, goal)
                    heapq.heappush(open_heap, (f_score, tie, nxt))

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self._store_metrics(len(visited), [], elapsed_ms, False)
        return []


class BFSPathfinder(GridPathfinder):
    algorithm_key = "bfs"

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        start = self.grid.to_cell(start_x, start_y)
        goal = self.grid.to_cell(target_x, target_y)
        self.last_visited_cells = []

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            self._store_metrics(0, [], elapsed_ms, False)
            return []

        queue = deque([start])
        visited = {start}
        came_from = {}

        while queue:
            current = queue.popleft()
            self.last_visited_cells.append(current)
            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                self._store_metrics(len(visited), path, elapsed_ms, True)
                return path

            for dx, dy, _ in self.NEIGHBORS:
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in visited or not self.grid.is_walkable(*nxt):
                    continue
                visited.add(nxt)
                came_from[nxt] = current
                queue.append(nxt)

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self._store_metrics(len(visited), [], elapsed_ms, False)
        return []


class DijkstraPathfinder(GridPathfinder):
    algorithm_key = "dijkstra"

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        start = self.grid.to_cell(start_x, start_y)
        goal = self.grid.to_cell(target_x, target_y)
        self.last_visited_cells = []

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            self._store_metrics(0, [], elapsed_ms, False)
            return []

        open_heap = [(0, 0, start)]
        came_from = {}
        g_score = {start: 0}
        visited = set()
        tie = 0

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current in visited:
                continue
            visited.add(current)
            self.last_visited_cells.append(current)

            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                self._store_metrics(len(visited), path, elapsed_ms, True)
                return path

            for dx, dy, cost in self.NEIGHBORS:
                nxt = (current[0] + dx, current[1] + dy)
                if not self.grid.is_walkable(*nxt):
                    continue
                tentative = g_score[current] + cost
                if tentative < g_score.get(nxt, float("inf")):
                    g_score[nxt] = tentative
                    came_from[nxt] = current
                    tie += 1
                    heapq.heappush(open_heap, (tentative, tie, nxt))

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self._store_metrics(len(visited), [], elapsed_ms, False)
        return []


class GreedyBestFirstPathfinder(GridPathfinder):
    algorithm_key = "greedy"

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        start = self.grid.to_cell(start_x, start_y)
        goal = self.grid.to_cell(target_x, target_y)
        self.last_visited_cells = []

        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            self._store_metrics(0, [], elapsed_ms, False)
            return []

        open_heap = [(self._heuristic(start, goal), 0, start)]
        came_from = {}
        visited = set()
        tie = 0

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current in visited:
                continue
            visited.add(current)
            self.last_visited_cells.append(current)

            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                self._store_metrics(len(visited), path, elapsed_ms, True)
                return path

            for dx, dy, _ in self.NEIGHBORS:
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in visited or not self.grid.is_walkable(*nxt):
                    continue
                if nxt not in came_from:
                    came_from[nxt] = current
                tie += 1
                heapq.heappush(open_heap, (self._heuristic(nxt, goal), tie, nxt))

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self._store_metrics(len(visited), [], elapsed_ms, False)
        return []


class HillClimbingPathfinder(Pathfinder):
    algorithm_key = "hill_climbing"
    directions = [
        (0, 1),
        (1, 0),
        (0, -1),
        (-1, 0),
        (1, 1),
        (1, -1),
        (-1, -1),
        (-1, 1),
    ]

    def __init__(self, width, height, cell_size=32):
        super().__init__(width, height, cell_size)
        self.obstacles = []
        self.local_minima_threshold = 6
        self.random_restart_chance = 0.12
        self.max_steps = 35
        self.step_size = max(10, cell_size // 2)

    def update_obstacles(self, obstacles):
        self.obstacles = obstacles

    def _is_blocked(self, x, y):
        if x < 0 or x > self.width or y < 0 or y > self.height:
            return True
        for ox, oy, ow, oh in self.obstacles:
            if ox <= x <= ox + ow and oy <= y <= oy + oh:
                return True
        return False

    def _score(self, x, y, target_x, target_y):
        if self._is_blocked(x, y):
            return float("inf")
        dx = target_x - x
        dy = target_y - y
        return math.sqrt(dx * dx + dy * dy)

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        current_x, current_y = float(start_x), float(start_y)
        current_score = self._score(current_x, current_y, target_x, target_y)
        if current_score == float("inf"):
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            self.last_visited_cells = []
            self._store_metrics(0, [], elapsed_ms, False)
            return []

        path = [(current_x, current_y)]
        self.last_visited_cells = []
        visited_nodes = 1
        stuck_count = 0

        for _ in range(self.max_steps):
            best_x = current_x
            best_y = current_y
            best_score = current_score

            for dx, dy in self.directions:
                next_x = current_x + dx * self.step_size
                next_y = current_y + dy * self.step_size
                score = self._score(next_x, next_y, target_x, target_y)
                visited_nodes += 1
                if score < best_score:
                    best_score = score
                    best_x = next_x
                    best_y = next_y

            if best_score >= current_score:
                stuck_count += 1
                if stuck_count >= self.local_minima_threshold or random.random() < self.random_restart_chance:
                    angle = random.uniform(0.0, 2.0 * math.pi)
                    jump = random.uniform(self.step_size, self.step_size * 4)
                    candidate_x = max(0, min(self.width, current_x + math.cos(angle) * jump))
                    candidate_y = max(0, min(self.height, current_y + math.sin(angle) * jump))
                    candidate_score = self._score(candidate_x, candidate_y, target_x, target_y)
                    if candidate_score != float("inf"):
                        best_x, best_y, best_score = candidate_x, candidate_y, candidate_score
                        stuck_count = 0
            else:
                stuck_count = 0

            current_x, current_y = best_x, best_y
            current_score = best_score
            path.append((current_x, current_y))
            self.last_visited_cells.append((int(current_x / self.cell_size), int(current_y / self.cell_size)))

            if current_score < self.cell_size:
                break

        success = len(path) > 1 and current_score < self.cell_size * 1.25
        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self._store_metrics(visited_nodes, path, elapsed_ms, success)
        return path


class DirectChasePathfinder(Pathfinder):
    algorithm_key = "direct"

    def find_path(self, start_x, start_y, target_x, target_y):
        start_perf = time.perf_counter()
        path = [(float(target_x), float(target_y))]
        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        self.last_visited_cells = []
        self._store_metrics(1, path, elapsed_ms, True)
        return path


PATHFINDERS = {
    "direct": DirectChasePathfinder,
    "astar": AStarPathfinder,
    "bfs": BFSPathfinder,
    "dijkstra": DijkstraPathfinder,
    "greedy": GreedyBestFirstPathfinder,
    "hill_climbing": HillClimbingPathfinder,
}


def _ensure_path_metrics(monster, algorithm_key):
    if not hasattr(monster, "path_metrics"):
        monster.path_metrics = {}
    monster.path_metrics.setdefault("algorithm", get_algorithm_display_name(algorithm_key))
    monster.path_metrics.setdefault("nodes_visited", 0)
    monster.path_metrics.setdefault("path_length", 0)
    monster.path_metrics.setdefault("calculation_time_ms", 0.0)
    monster.path_metrics.setdefault("failed_attempts", 0)
    monster.path_metrics.setdefault("success_rate", 1.0)
    monster.path_metrics.setdefault("attempts", 0)
    monster.path_metrics.setdefault("successes", 0)


def _collides_environment(monster, new_x, new_y):
    obstacles = getattr(monster, "environment_obstacles", [])
    if not obstacles:
        return False
    monster_rect = pygame.Rect(
        int(new_x),
        int(new_y),
        int(monster.sprite_width * monster.scale_factor),
        int(monster.sprite_height * monster.scale_factor),
    )
    for obstacle in obstacles:
        if monster_rect.colliderect(obstacle):
            return True
    return False


def _can_move(monster, monsters, new_x, new_y):
    if not getattr(monster, "ignore_monster_collisions", False):
        for other in monsters:
            if other == monster:
                continue
            dx = other.x - new_x
            dy = other.y - new_y
            distance = math.sqrt(dx * dx + dy * dy)
            min_distance = (monster.radius + other.radius) * (1 - monster.max_overlap)
            if distance < min_distance:
                return False
    if _collides_environment(monster, new_x, new_y):
        return False
    return True


def _set_direction_from_vector(monster, dx, dy):
    if abs(dx) > abs(dy):
        monster.direction = 2 if dx < 0 else 3
    else:
        monster.direction = 1 if dy < 0 else 0


def _update_common_monster_state(monster, players, current_time):
    if monster.is_slowed and time.time() >= monster.slow_effect_end_time:
        monster.speed = monster.original_speed
        monster.animation_speed = monster.animation_speed / 1.5
        monster.is_slowed = False

    for text in monster.damage_texts[:]:
        if not text.update(1 / 60):
            monster.damage_texts.remove(text)

    if monster.is_dying:
        monster.death_timer += 1 / 60
        monster.animation_timer += 1 / 60
        if not monster.hurt_animation_played and monster.animation_timer >= monster.hurt_animation_speed:
            monster.animation_timer = 0
            monster.hurt_frame = (monster.hurt_frame + 1) % 5
            if monster.hurt_frame == 0:
                monster.hurt_animation_played = True
        if monster.death_timer >= monster.death_duration:
            return True, None
        return False, None

    if monster.monster_type == "slime3" and monster.health < monster.max_health:
        monster.last_heal_time += 1 / 60
        if monster.last_heal_time >= 1.0:
            heal_amount = max(0, int(current_time / 60))
            monster.health = min(monster.health + heal_amount, monster.max_health)
            monster.last_heal_time = 0

    if monster.is_attacking:
        monster.attack_timer += 1 / 60
        if monster.attack_timer >= monster.attack_duration:
            monster.is_attacking = False
            monster.attack_timer = 0
            monster.current_frame = 0
        return False, None

    alive_players = [player for player in players if not player.is_dead]
    if not alive_players:
        return False, None

    closest_player = min(
        alive_players,
        key=lambda player: (player.x - monster.x) ** 2 + (player.y - monster.y) ** 2,
    )
    monster.target = closest_player
    return False, closest_player


def _try_attack(monster, current_time):
    dx = monster.target.x - monster.x
    dy = monster.target.y - monster.y
    distance = math.sqrt(dx * dx + dy * dy)
    if distance >= monster.radius + monster.attack_range:
        return False

    if current_time - monster.last_attack_time < monster.attack_cooldown:
        return True

    monster.is_attacking = True
    monster.attack_timer = 0
    monster.last_attack_time = current_time
    monster.current_frame = 0

    if current_time - monster.last_damage_time >= monster.damage_cooldown:
        monster_center_x = monster.x + (monster.sprite_width * monster.scale_factor / 2)
        monster_center_y = monster.y + (monster.sprite_height * monster.scale_factor / 2)
        player_center_x = monster.target.x + (monster.target.sprite_width * monster.target.scale_factor / 2)
        player_center_y = monster.target.y + (monster.target.sprite_height * monster.target.scale_factor / 2)
        ddx = player_center_x - monster_center_x
        ddy = player_center_y - monster_center_y
        actual_distance = math.sqrt(ddx * ddx + ddy * ddy)
        if actual_distance <= monster.radius + monster.attack_range:
            monster.target.health -= monster.damage
            monster.last_damage_time = current_time
            if monster.hit_sound:
                monster.hit_sound.play()
    return True


def _ensure_pathfinder(monster, algorithm_key, field_width, field_height):
    if not hasattr(monster, "pathfinder_instances"):
        monster.pathfinder_instances = {}
    if not hasattr(monster, "path"):
        monster.path = []
    if not hasattr(monster, "path_index"):
        monster.path_index = 0
    if not hasattr(monster, "path_update_time"):
        monster.path_update_time = 0.0
    if not hasattr(monster, "path_update_interval"):
        base = 0.3 + (hash(monster.monster_type) % 5) * 0.1
        monster.path_update_interval = max(0.3, min(base, 0.7))
    if not hasattr(monster, "movement_algorithm"):
        monster.movement_algorithm = algorithm_key

    algorithm_key = normalize_algorithm_key(algorithm_key)
    if algorithm_key not in monster.pathfinder_instances:
        cls = PATHFINDERS.get(algorithm_key, DirectChasePathfinder)
        monster.pathfinder_instances[algorithm_key] = cls(field_width, field_height, 32)

    if getattr(monster, "_last_algorithm_key", algorithm_key) != algorithm_key:
        monster.path = []
        monster.path_index = 0
        monster.path_update_time = 0.0
    monster._last_algorithm_key = algorithm_key

    pathfinder = monster.pathfinder_instances[algorithm_key]
    monster.pathfinding_grid = getattr(pathfinder, "grid", None)
    return pathfinder


def _build_dynamic_obstacles(monster, monsters):
    obstacles = []
    if not getattr(monster, "ignore_monster_obstacles", False):
        for other in monsters:
            if other == monster:
                continue
            obstacle_x = other.x - other.radius
            obstacle_y = other.y - other.radius
            obstacle_width = other.radius * 2
            obstacle_height = other.radius * 2
            obstacles.append((obstacle_x, obstacle_y, obstacle_width, obstacle_height))
    environment = getattr(monster, "environment_obstacle_tuples", [])
    clearance = int(getattr(monster, "path_obstacle_clearance", 0))
    if clearance > 0:
        for ox, oy, ow, oh in environment:
            obstacles.append((ox - clearance, oy - clearance, ow + clearance * 2, oh + clearance * 2))
    else:
        obstacles.extend(environment)
    return obstacles


def _update_animation(monster):
    monster.animation_timer += 1 / 60
    if monster.animation_timer >= monster.animation_speed:
        monster.animation_timer = 0
        monster.current_frame = (monster.current_frame + 1) % monster.columns


def _update_metrics(monster, algorithm_key, metrics):
    _ensure_path_metrics(monster, algorithm_key)
    monster.path_metrics["algorithm"] = get_algorithm_display_name(algorithm_key)
    monster.path_metrics["nodes_visited"] = metrics.get("nodes_visited", 0)
    monster.path_metrics["path_length"] = metrics.get("path_length", 0)
    monster.path_metrics["calculation_time_ms"] = metrics.get("calculation_time_ms", 0.0)
    monster.path_metrics["failed_attempts"] += 0 if metrics.get("success", False) else 1
    monster.path_metrics["attempts"] += 1
    monster.path_metrics["successes"] += 1 if metrics.get("success", False) else 0
    attempts = max(1, monster.path_metrics["attempts"])
    monster.path_metrics["success_rate"] = monster.path_metrics["successes"] / attempts


def _direct_fallback_step(monster, monsters):
    dx = monster.target.x - monster.x
    dy = monster.target.y - monster.y
    distance = math.sqrt(dx * dx + dy * dy)
    if distance <= 0:
        return
    dx /= distance
    dy /= distance
    _set_direction_from_vector(monster, dx, dy)
    new_x = monster.x + dx * monster.speed
    new_y = monster.y + dy * monster.speed
    if _can_move(monster, monsters, new_x, new_y):
        monster.x = new_x
        monster.y = new_y
        return

    # Thoát kẹt cục bộ khi đâm vào vật cản: thử đi lệch 2 bên rồi lùi nhẹ.
    step = max(2.0, monster.speed * 1.35)
    candidates = [
        (monster.x + dy * step, monster.y - dx * step),
        (monster.x - dy * step, monster.y + dx * step),
        (monster.x - dx * step, monster.y - dy * step),
    ]
    for cand_x, cand_y in candidates:
        if _can_move(monster, monsters, cand_x, cand_y):
            monster.x = cand_x
            monster.y = cand_y
            return


def update_monster_movement(monster, players, monsters, current_time, field_width, field_height, algorithm_key=None):
    if algorithm_key is None:
        algorithm_key = getattr(monster, "movement_algorithm", "direct")
    algorithm_key = normalize_algorithm_key(algorithm_key)
    monster.movement_algorithm = algorithm_key

    should_remove, target = _update_common_monster_state(monster, players, current_time)
    if should_remove:
        return True
    if monster.is_attacking:
        return False
    if target is None or not getattr(monster, "target", None) or monster.target.is_dead:
        _update_animation(monster)
        return False

    if _try_attack(monster, current_time):
        _update_animation(monster)
        return False

    pathfinder = _ensure_pathfinder(monster, algorithm_key, field_width, field_height)
    _ensure_path_metrics(monster, algorithm_key)
    should_refresh_path = (
        not monster.path
        or current_time - monster.path_update_time >= monster.path_update_interval
        or monster.path_index >= len(monster.path)
    )

    if should_refresh_path:
        if hasattr(pathfinder, "update_obstacles"):
            pathfinder.update_obstacles(_build_dynamic_obstacles(monster, monsters))
        monster.path = pathfinder.find_path(monster.x, monster.y, monster.target.x, monster.target.y)
        monster.path_index = 0
        monster.path_update_time = current_time
        monster.path_visited_cells = list(getattr(pathfinder, "last_visited_cells", []))
        _update_metrics(monster, algorithm_key, pathfinder.last_metrics)

    if monster.path and monster.path_index < len(monster.path):
        waypoint_x, waypoint_y = monster.path[monster.path_index]
        dx = waypoint_x - monster.x
        dy = waypoint_y - monster.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance < max(monster.speed, 2):
            monster.path_index += 1
        else:
            dx /= distance
            dy /= distance
            _set_direction_from_vector(monster, dx, dy)
            new_x = monster.x + dx * monster.speed
            new_y = monster.y + dy * monster.speed
            if _can_move(monster, monsters, new_x, new_y):
                monster.x = new_x
                monster.y = new_y
            else:
                # Đường hợp lệ trên grid nhưng va chạm thực tế: ép tính lại path.
                monster.path = []
                monster.path_index = 0
                monster.path_update_time = current_time - monster.path_update_interval
                _direct_fallback_step(monster, monsters)
    else:
        _direct_fallback_step(monster, monsters)

    _update_animation(monster)
    return False


def slime2_astar_movement(monster, players, monsters, current_time, field_width, field_height):
    return update_monster_movement(
        monster,
        players,
        monsters,
        current_time,
        field_width,
        field_height,
        algorithm_key="astar",
    )


def slime4_hill_climbing_movement(monster, players, monsters, current_time, field_width, field_height):
    return update_monster_movement(
        monster,
        players,
        monsters,
        current_time,
        field_width,
        field_height,
        algorithm_key="hill_climbing",
    )


def draw_path(surface, monster):
    if not hasattr(monster, "movement_algorithm"):
        return

    algorithm_key = normalize_algorithm_key(monster.movement_algorithm)
    color = get_algorithm_color(algorithm_key)
    camera_x = int(getattr(monster, "camera_offset_x", 0))
    camera_y = int(getattr(monster, "camera_offset_y", 0))

    path = getattr(monster, "path", [])
    path_index = int(getattr(monster, "path_index", 0))
    if path and path_index < len(path):
        for index in range(path_index, len(path) - 1):
            sx, sy = path[index]
            ex, ey = path[index + 1]
            pygame.draw.line(
                surface,
                color,
                (int(sx - camera_x), int(sy - camera_y)),
                (int(ex - camera_x), int(ey - camera_y)),
                2,
            )
        wx, wy = path[path_index]
        pygame.draw.circle(surface, (255, 255, 255), (int(wx - camera_x), int(wy - camera_y)), 5)
    elif algorithm_key == "direct" and getattr(monster, "target", None):
        start_x = monster.x + (monster.sprite_width * monster.scale_factor) * 0.5
        start_y = monster.y + (monster.sprite_height * monster.scale_factor) * 0.5
        end_x = monster.target.x + (monster.target.sprite_width * monster.target.scale_factor) * 0.5
        end_y = monster.target.y + (monster.target.sprite_height * monster.target.scale_factor) * 0.5
        pygame.draw.line(
            surface,
            color,
            (int(start_x - camera_x), int(start_y - camera_y)),
            (int(end_x - camera_x), int(end_y - camera_y)),
            2,
        )

    # F3 label: hiển thị tên thuật toán trên đầu slime
    label = get_algorithm_display_name(algorithm_key)
    if not hasattr(monster, "_algo_label_font"):
        monster._algo_label_font = pygame.font.Font(None, 18)
    text = monster._algo_label_font.render(label, True, color)
    text_x = int(monster.x + (monster.sprite_width * monster.scale_factor) * 0.5 - text.get_width() * 0.5 - camera_x)
    text_y = int(monster.y - 20 - camera_y)
    surface.blit(text, (text_x, text_y))
