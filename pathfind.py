from classes import Graph, Zone
import heapq

class Pathfinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def _reconstruct_path(self, came_from: dict[Zone, Zone]) -> list[Zone]:
        solution: list[Zone] = []
        current = self.graph.end
        while current != self.graph.start:
            solution.append(current)
            current = came_from[current]
        solution.append(self.graph.start)
        return list(reversed(solution))

    def find_path(self, penalty: dict[Zone, int]) -> list[Zone] | None:
        if penalty is None:
            penalty = {}
        start = self.graph.start
        counter = 0
        queue: list[tuple[int, int, Zone]] = [(0, counter, start)]
        cost_so_far: dict[Zone, int] = {start: 0}
        came_from: dict[Zone, Zone] = {}
        while queue:
            cost, _, current_node = heapq.heappop(queue)
            if self.graph.end == current_node:
                return self._reconstruct_path(came_from)
            for neighbor in self.graph.get_neighbors(current_node):
                if neighbor.is_blocked():
                    continue
                new_cost = cost + neighbor.movement_cost() + penalty.get(neighbor, 0)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current_node
                    heapq.heappush(queue, (new_cost, counter, neighbor))
                    counter += 1
        return None

    def find_paths(self) -> list[list[Zone]]:
        paths = []
        penality = {}
        PEN = len(self.graph.zones)
        n = 0
        while n < 4:
            path = self.find_path(penality)
            if path is None:
                break
            if path in paths:
                break
            paths.append(path)
            for zone in path[1:-1]:
                penality[zone] = penality.get(zone, 0) + PEN
            n += 1
        return paths
