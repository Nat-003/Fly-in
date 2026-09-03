from zone import Graph

class Parser():
    def __init__(self, path):
        self.file_path = path

    def parse(self) -> Graph:
        graph = Graph()
        try:
            with open(self.file_path, "r") as f:
                line_counter = 1
                line_map = {}
                for line in f:
                    line_map.update([(str(line_counter), line.strip())])
                    if line.startswith('#'):
                        continue
                    line_counter += 1
                    if line.startswith("nb_drones"):
                        clean_line = line.strip()
                        value = clean_line.split(':')
                        try:
                            numerical_value = int(value[1])
                            graph.nb_drones = numerical_value
                        except ValueError:
                            raise ValueError('error while parsing')
            return graph                   
        except (FileNotFoundError, PermissionError) as e:
            print(f"{e}")
