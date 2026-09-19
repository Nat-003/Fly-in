from classes import Graph, Zone, Connection

class Parser():
    def __init__(self, path: str) -> None:
        self.file_path = path

    def _parse_zone(self, line_text: str, line_nb: int, graph: Graph) -> None:
        is_start = False
        is_end = False
        if line_text.startswith("start_hub:"):
            is_start = True
        elif line_text.startswith("end_hub:"):
            is_end = True
        elif line_text.startswith("hub:"):
            pass
        else:
            raise ValueError(f"line {line_nb}: unrecognized zone prefix")
        # everything after the prefix, split into fields
        body = line_text.split(":", 1)[1].strip()
        # print(body)
        data = body.split()
        # print(data)
        if len(data) < 3:
            raise ValueError(f"error while parsing line {line_nb}: Missing field")

        name = data[0]
        if "-" in name:
            raise ValueError(f"error while parsing line {line_nb}: Invalid name (name must not containe '-')")
        try:
            coords_x = int(data[1])
            coords_y = int(data[2])
        except ValueError:
            raise ValueError(f"error while parsing line {line_nb}: coordinates must be integers")
        coords = (coords_x, coords_y)
        metadata =  self._parse_metadata(line_text, line_nb)
        if metadata.get("zone") is not None:
            zone_type = metadata.get("zone")
        else:
            zone_type = "normal"
        if metadata.get("color") is not None:
            color = metadata.get("color")
        else:
            color = None
        if metadata.get("max_drones") is not None:
            max_drones = metadata.get("max_drones")
        else:
            max_drones = 1
        zone = Zone(name, coords, zone_type, max_drones, color)
        graph.add_zone(zone, is_start, is_end)

    def _validate_key_values(self, key: str, value: str | int, line_nb: int) -> None:
        VALID_ZONE_KEYS = ("zone", "color", "max_drones", "max_link_capacity")
        if key not in VALID_ZONE_KEYS:
            raise ValueError(f"error while parsing line {line_nb}: {key} is not a valid key")
        if key == "max_drones" or key == "max_link_capacity":
            try:
                val = int(value)
            except ValueError:
                raise ValueError(f"error while parsing line {line_nb}: {value} is not an int")
            if val < 1:
                raise ValueError(f"error while parsing line {line_nb}: {value} is less than 1")

    def _parse_metadata(self, line_text: str, line_nb: int) -> dict[str, str | int]:
        metadata_dict = {}
        if "[" in line_text and "]" in line_text:
            data = line_text.split("[")
            if data[1].strip("]\n") == "":
                return metadata_dict
            metadata_raw = data[1].strip().strip("]")
            metadata = metadata_raw.split()
            for m in metadata:
                if len(m.split("=")) != 2:
                    raise ValueError("Eroor")
                key, val = m.split("=")
                if key == "max_drones" or key == "max_link_capacity":
                    try:
                        val = int(val)
                    except ValueError:
                        raise ValueError(f"error while parsing line {line_nb}: {val} is not an int")
                self._validate_key_values(key, val, line_nb)
                metadata_dict[key] = val
        elif "[" not in line_text and "]" not in line_text:
            return metadata_dict
        else:
            raise ValueError(f"error while parsing line {line_nb}: missing brackets")   
        return metadata_dict

    def _parse_connection(self, line_text: str, line_nb: int, graph: Graph) -> None:
        if len(line_text.split(":")) != 2:
            raise ValueError("test")
        line = line_text.split(":")
        body = line[1].strip()
        data = body.split()
        if len(data) < 1:
            raise ValueError(f"error while parsing line {line_nb}: missing fields")
        link = data[0]
        if "-" not in link:
            raise ValueError(f"error while parsing line {line_nb}: link must contain dashes: ex <name1>-<name2>")
        zones = link.split("-")
        if len(zones) != 2:
            raise ValueError(f"error while parsing line {line_nb}: need 2 zones for a connection")
        zone_a_str = zones[0]
        zone_b_str = zones[1]
        metadata = self._parse_metadata(line_text, line_nb)
        if metadata.get("max_link_capacity") is not None:
            max_link_capacity = metadata.get("max_link_capacity")
        else:
            max_link_capacity = 1
        zone_a = graph.get_zone(zone_a_str)
        zone_b = graph.get_zone(zone_b_str)
        connection = Connection(zone_a, zone_b, max_link_capacity)
        graph.add_connection(connection)

    def parse(self) -> Graph:
        graph = Graph()
        try:
            with open(self.file_path, "r") as f:
                for line_nb, line_text in enumerate(f, start=1):
                    if line_text.startswith('#') or line_text.startswith("\n"):
                        continue
                     #must split this part in helper function frome here to 
                    if line_text.startswith("nb_drones"):
                        clean_line = line_text.strip()
                        value = clean_line.split(':')
                        try:
                            numerical_value = int(value[1])
                        except ValueError:
                            raise ValueError(f'error while parsing line {line_nb}: Expected valide positive number')
                        if numerical_value < 1:
                            raise ValueError(f'error while parsing line {line_nb}: Expected a positive number')
                        graph.nb_drones = numerical_value
                    #here
                    elif line_text.startswith("start_hub:"):
                        self._parse_zone(line_text, line_nb, graph)
                    elif line_text.startswith("end_hub:"):
                        self._parse_zone(line_text, line_nb, graph)
                    elif line_text.startswith("hub:"):
                        self._parse_zone(line_text, line_nb, graph)
                    elif line_text.startswith("connection"):
                        self._parse_connection(line_text, line_nb, graph)
                    # else:
                    #     raise ValueError(f"line {line_nb}: line invalid")
                graph.validate()
            return graph                   
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f'cannot open file: {self.file_path}: {e}')
