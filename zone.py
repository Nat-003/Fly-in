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
