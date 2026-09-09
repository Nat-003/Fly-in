from classes import Graph, Zone

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
        data = body.split()
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
        self._parse_metadata(line_text, line_nb)
        zone = Zone(name, coords, zone_type="normal", max_cap=1, color=None)
        graph.add_zone(zone, is_start, is_end)

    def _parse_metadata(self, line_text: str, line_nb: int) -> dict[str, str]:
        metadata_dict = {}
        data = line_text.split("[")
        if data[1] == "]\n":
            raise ValueError(f"error while parsing line {line_nb}: Metadata field is empty")
        metadata_raw = data[1].strip().strip("]")
        metadata = metadata_raw.split(" ")
        for m in metadata:
            key, val = m.split("=")
            metadata_dict[key] = val
        return metadata_dict

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
                    # else:
                    #     raise ValueError(f"line {line_nb}: line invalid")
                graph.validate()
            return graph                   
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f'cannot open file: {self.file_path}: {e}')
