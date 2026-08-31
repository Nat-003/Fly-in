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
