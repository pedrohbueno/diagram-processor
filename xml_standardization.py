import xml.etree.ElementTree as ET

INPUT_FILE = "input.xml"
OUTPUT_FILE = "output.xml"

NODE_WIDTH = 140
NODE_HEIGHT = 65

MAIN_X = 80
START_Y = 10
STEP_Y = 100

NO_COLUMN_OFFSET = 120
FINAL_Y_MARGIN = 20


def get_vertexes(root):
    result = []

    for elem in root.iter():
        mxcell = elem.find("./mxCell")

        if mxcell is not None and mxcell.get("vertex") == "1":
            result.append(elem)

    return result


def get_geometry(vertex):
    mxcell = vertex.find("./mxCell")

    if mxcell is None:
        return None

    return mxcell.find("./mxGeometry")


def get_label(vertex):
    return vertex.attrib.get("label", "")


def apply_resize(vertices):
    for vertex in vertices:

        geom = get_geometry(vertex)

        if geom is None:
            continue

        geom.set("width", str(NODE_WIDTH))
        geom.set("height", str(NODE_HEIGHT))


def apply_vertical_flow(vertices):

    sortable = []

    for vertex in vertices:

        geom = get_geometry(vertex)

        if geom is None:
            continue

        y = float(geom.get("y", "0"))

        sortable.append((y, vertex, geom))

    sortable.sort(key=lambda x: x[0])

    current_y = START_Y

    for _, _, geom in sortable:

        geom.set("x", str(MAIN_X))
        geom.set("y", str(current_y))

        current_y += STEP_Y


def build_vertex_map(root):

    vertices = {}

    for elem in root.iter():

        mxcell = elem.find("./mxCell")

        if mxcell is None:
            continue

        if mxcell.get("vertex") != "1":
            continue

        geom = mxcell.find("./mxGeometry")

        if geom is None:
            continue

        vid = elem.get("id")

        vertices[vid] = {
            "id": vid,
            "label": elem.attrib.get("label", ""),
            "x": float(geom.get("x", 0)),
            "y": float(geom.get("y", 0)),
            "w": float(geom.get("width", NODE_WIDTH)),
            "h": float(geom.get("height", NODE_HEIGHT))
        }

    return vertices


def find_end_node(vertices):

    for vertex in vertices.values():

        label = vertex["label"].strip().lower()

        if label == "fim":
            return vertex

    return None


def clear_waypoints(edge):

    geom = edge.find("./mxGeometry")

    if geom is None:
        return None

    points = geom.find("./Array")

    if points is not None:
        geom.remove(points)

    return geom


def create_points(geom):

    return ET.SubElement(
        geom,
        "Array",
        {"as": "points"}
    )


def add_point(parent, x, y):

    ET.SubElement(
        parent,
        "mxPoint",
        {
            "x": str(int(x)),
            "y": str(int(y))
        }
    )


def is_no_edge(edge):

    parent_obj = edge.getparent() if hasattr(edge, "getparent") else None

    return False


def extract_label(edge, root):

    edge_parent_id = edge.get("id")

    for obj in root.iter():

        mxcell = obj.find("./mxCell")

        if mxcell is None:
            continue

        if mxcell is edge:

            return obj.attrib.get("label", "")

    return ""


def rebuild_edges(root):

    vertices = build_vertex_map(root)

    end_node = find_end_node(vertices)

    if end_node is None:
        return

    max_right = max(
        v["x"] + v["w"]
        for v in vertices.values()
    )

    no_column_x = max_right + NO_COLUMN_OFFSET

    # -----------------------------------------------------------------
    # AJUSTE: Identifica e ordena as origens do "Não" para separar as pistas
    # -----------------------------------------------------------------
    no_edges_sources = []
    for obj in root.iter():
        mxcell = obj.find("./mxCell")
        if mxcell is None or mxcell.get("edge") != "1":
            continue
        source = mxcell.get("source")
        label = obj.attrib.get("label", "").strip().lower()
        if label in ("não", "nao") and source in vertices:
            if source not in no_edges_sources:
                no_edges_sources.append(source)
    
    # Organiza do topo para baixo para criar o efeito de camadas paralelas
    no_edges_sources.sort(key=lambda src: vertices[src]["y"])
    # -----------------------------------------------------------------

    for obj in root.iter():

        mxcell = obj.find("./mxCell")

        if mxcell is None:
            continue

        if mxcell.get("edge") != "1":
            continue

        source = mxcell.get("source")
        target = mxcell.get("target")

        if source not in vertices:
            continue

        if target not in vertices:
            continue

        label = obj.attrib.get("label", "").strip().lower()

        geom = clear_waypoints(mxcell)

        if geom is None:
            continue

        points = create_points(geom)

        s = vertices[source]
        t = vertices[target]

        sx = s["x"] + s["w"] / 2
        sy = s["y"] + s["h"]

        tx = t["x"] + t["w"] / 2
        ty = t["y"]

        # Caminho NÃO

        if label in ("não", "nao"):

            exit_x = s["x"] + s["w"] * 0.65

            # Calcula um X exclusivo para cada linha vertical externa com base no índice
            lane_idx = no_edges_sources.index(source) if source in no_edges_sources else 0
            current_no_column_x = no_column_x + (lane_idx * 35)
            
            # Distribui sutilmente os pontos de chegada no topo de Fim para não sobrepor
            current_tx = tx + (lane_idx * 15)

            add_point(
                points,
                exit_x,
                sy
            )

            add_point(
                points,
                current_no_column_x,
                sy
            )

            add_point(
                points,
                current_no_column_x,
                end_node["y"] - FINAL_Y_MARGIN
            )

            add_point(
                points,
                current_tx,
                end_node["y"] - FINAL_Y_MARGIN
            )

            continue

        # Caminho SIM

        if label == "sim":

            exit_x = s["x"] + s["w"] * 0.35

            add_point(
                points,
                exit_x,
                sy
            )

            add_point(
                points,
                exit_x,
                ty - 15
            )

            continue

        # Fluxo principal

        continue


def main():

    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()

    vertices = get_vertexes(root)

    apply_resize(vertices)
    apply_vertical_flow(vertices)
    rebuild_edges(root)

    tree.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True
    )


if __name__ == "__main__":
    main()
