from typing import Any 

class Zone:
    VALID_ZONE = ('normal', 'restricted', 'priority', 'blocked')

    def __init__(
        self,
        name: str,
        coords: tuple[int, int],
        zone_type: str,
        max_cap: int,
        color: str | None = None,
    ) -> None:
        self.name = name
        self.coords = coords
        if zone_type not in self.VALID_ZONE:
            raise ValueError('Unknown zone type')
        self.zone_type = zone_type
        if max_cap <= 0:
            raise ValueError('max cap must be above 0')
        self.max_cap = max_cap
        self.color = color
        self.occupants: list[int] = []

    def occupancy(self) -> int:
        return len(self.occupants)

    def has_room(self) -> bool:
        if self.occupancy() >= self.max_cap:
            return False
        return True

    def add_drone(self, drone: int) -> None:
        if self.has_room():
            self.occupants.append(drone)
        else:
            raise ValueError('no more room')

    def remove_drone(self, drone: int) -> None:
        self.occupants.remove(drone)

    def movement_cost(self) -> int:
        if self.zone_type == 'normal':
            return 1
        elif self.zone_type == 'restricted':
            return 2
        elif self.zone_type == 'priority':
            return 1
        else:
            return 1

    def is_blocked(self) -> bool:
        if self.zone_type == 'blocked':
            return True
        else:
            return False


class Connection:
    def __init__(self, zone_a: Zone, zone_b: Zone, max_link_capacity: int = 1):
        self.zone_a = zone_a
        self.zone_b = zone_b
        if max_link_capacity <= 0:
            raise ValueError('max cap must be above 0')
        self.max_link_capacity = max_link_capacity
        self.drones: list[int] = []

    def crossing(self) -> int:
        return len(self.drones)

    def can_cross(self) -> bool:
        if len(self.drones) >= self.max_link_capacity:
            return False
        else:
            return True

    def add_drone(self, drone: int) -> None:
        if self.can_cross():
            self.drones.append(drone)
        else:
            raise ValueError('no more room')

    def remove_drone(self, drone: int) -> None:
        self.drones.remove(drone)

    def normalized_key(self) -> tuple[str, str]:
        first, second = sorted((self.zone_a.name, self.zone_b.name))
        return (first, second)

    def end_point(self, zone: Zone) -> Zone:
        if zone.name == self.zone_a.name:
            return self.zone_b
        elif zone.name == self.zone_b.name:
            return self.zone_a
        else:
            raise ValueError('zone is not an endpoint of this connection')


class Graph:
    def __init__(self) -> None:
        self.nb_drones = 0
        self.zones: dict[str, Zone] = {}
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: Zone | None = None
        self.end: Zone | None = None
        self.seen_connections: set[tuple[str, str]] = set()

    def add_zone(
        self,
        zone: Zone,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        if zone.name in self.zones:
            raise ValueError(f'duplicate zone name: {zone.name}')
        if is_start:
            if self.start is not None:
                raise ValueError('more than one start zone')
            self.start = zone
        if is_end:
            if self.end is not None:
                raise ValueError('more than one end zone')
            self.end = zone
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        key = connection.normalized_key()
        if key in self.seen_connections:
            raise ValueError('duplicate connection')
        if connection.zone_a.name not in self.zones:
            raise ValueError(f'unknown zone: {connection.zone_a.name}')
        if connection.zone_b.name not in self.zones:
            raise ValueError(f'unknown zone: {connection.zone_b.name}')
        self.seen_connections.add(key)
        self.adjacency[connection.zone_a.name].append(connection)
        self.adjacency[connection.zone_b.name].append(connection)

    def get_zone(self, name: str) -> Zone:
        zone = self.zones.get(name)
        if zone is None:
            raise ValueError(f'{name} not found in zones')
        return zone

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        neighbors = []
        for connection in self.adjacency[zone.name]:
            neighbors.append(connection.end_point(zone))
        return neighbors

    def validate(self) -> None:
        if self.start is None:
            raise ValueError('no start zone')
        if self.end is None:
            raise ValueError('no end zone')
        if self.nb_drones <= 1:
            raise ValueError("Number of drones cannot be less than 1")


class Drone:
    def __init__(self, id: int, path: list[Zone]) -> None:
        self.id = id
        self.path = path
        self.path_index = 0

    def get_current_zone(self) -> Zone:
        return self.path[self.path_index]

    def get_next_zone(self) -> Zone | None:
        if not self.has_arrived():
            return self.path[self.path_index + 1]
        else:
            return None

    def move(self) -> None:
        self.path_index += 1

    def has_arrived(self) -> bool:
        if self.path_index == len(self.path) - 1:
            return True
        else:
            return False


class Simulation:
    def __init__(self, graph: Graph, pathfinder: Any):
        self.graph = graph
        self.pathfinder = pathfinder
        self.path = pathfinder.find_path()
        self.drones: list[Drone] = []
        self.create_drones()
        self.turn_count = 0

    def create_drones(self) -> None:
        for n in range(1, self.graph.nb_drones + 1):
            self.drones.append(Drone(n, self.path))


    def all_arrived(self) -> bool:
        return all(d.has_arrived() for d in self.drones)

    def take_turn(self):
        to_move = []
        output_lines = []
        projected = {zone: zone.occupancy() for zone in self.graph.zones.values()}
        for d in sorted(self.drones, key=lambda dr: dr.path_index, reverse=True):
            if d.has_arrived():
                continue
            current = d.get_current_zone()
            next_zone = d.get_next_zone()
            if next_zone == self.graph.end:
                to_move.append((d, current, next_zone))
                projected[current] -= 1
                projected[next_zone] += 1
            elif projected[next_zone] < next_zone.max_cap:
                to_move.append((d, current, next_zone))
                projected[current] -= 1
                projected[next_zone] += 1
        for d, current, next_zone in to_move:
            if next_zone != self.graph.end:
                next_zone.add_drone(d.id)
            if current != self.graph.start:
                current.remove_drone(d.id)
            d.move()
            line = f"D{d.id}-{next_zone.name}"
            output_lines.append(line)
        return output_lines

    def run(self):
        max_turns = 100
        while not self.all_arrived() and self.turn_count < max_turns:
           moves = self.take_turn()
           line = " ".join(moves)
           print(line)
           self.turn_count += 1
    
