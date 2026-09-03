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