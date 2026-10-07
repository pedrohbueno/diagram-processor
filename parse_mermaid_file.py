import xml.etree.ElementTree as ET
import re

INPUT_FILENAME = "temp/diagram.mmd"
OUTPUT_FILENAME = "output.xml"

NODE_WIDTH = 140
NODE_HEIGHT = 65

MAIN_X = 80
START_Y = 50
STEP_Y = 85

NO_COLUMN_OFFSET = 120
FINAL_Y_MARGIN = 20


def parse_mermaid_file(file_path):
    """Lê o arquivo .mmd e extrai os nós (vertices) e as conexões (edges)"""
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    vertices = {}
    edges = []

    # Expressões regulares para mapear a sintaxe do Mermaid
    node_pattern = re.compile(r'^\s*([a-zA-Z0-9_-]+)(?:\[\((.*?)\)\]|\[(.*?)\]|\((.*?)\)|\{(.*?)\})\s*$')
    edge_label_pattern = re.compile(r'^\s*([a-zA-Z0-9_-]+)\s*--\s*(.*?)\s*-->\s*([a-zA-Z0-9_-]+)\s*$')
    edge_inline_pattern = re.compile(r'^\s*([a-zA-Z0-9_-]+)\s*-->\|\s*(.*?)\s*\|\s*([a-zA-Z0-9_-]+)\s*$')
    edge_simple_pattern = re.compile(r'^\s*([a-zA-Z0-9_-]+)\s*-->\s*([a-zA-Z0-9_-]+)\s*$')

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or "flowchart" in cleaned_line or "graph" in cleaned_line:
            continue

        # 1. Identifica declaração de nós (ex: A[Texto])
        node_match = node_pattern.match(cleaned_line)
        if node_match:
            node_id = node_match.group(1)
            label = next(g for g in node_match.groups()[1:] if g is not None)
            vertices[node_id] = label
            continue

        # 2. Identifica conexões com rótulo externo (ex: A -- Rótulo --> B)
        edge_label_match = edge_label_pattern.match(cleaned_line)
        if edge_label_match:
            source, label, target = edge_label_match.groups()
            edges.append({"source": source, "target": target, "label": label.replace("-->", "").strip()})
            continue

        # 3. Identifica conexões com rótulo interno (ex: A -->|Rótulo| B)
        edge_inline_match = edge_inline_pattern.match(cleaned_line)
        if edge_inline_match:
            source, label, target = edge_inline_match.groups()
            edges.append({"source": source, "target": target, "label": label.strip()})
            continue

        # 4. Identifica conexões simples sem rótulo (ex: A --> B)
        edge_simple_match = edge_simple_pattern.match(cleaned_line)
        if edge_simple_match:
            source, target = edge_simple_match.groups()
            edges.append({"source": source, "target": target, "label": ""})
            continue

    return vertices, edges


def create_base_mxfile():
    """Gera o esqueleto base de árvore XML estruturado do Draw.io"""
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="Page-1", id="9vNrKDU1w07OYP0h8GQ4")
    graph_model = ET.SubElement(diagram, "mxGraphModel", dx="1627", dy="844", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="850", pageHeight="1100", math="0", shadow="0")
    root = ET.SubElement(graph_model, "root")
    
    # IDs internos obrigatórios e nativos do draw.io
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    
    return mxfile, root


def append_mx_point(parent, x, y):
    """Adiciona um waypoint manual mxPoint ao nó pai da linha"""
    ET.SubElement(parent, "mxPoint", {"x": str(int(x)), "y": str(int(y))})


def compile_graph_to_xml(vertices, edges, xml_root):
    """Aplica o algoritmo vetorial organizando os nós e roteando as arestas"""
    
    positioned_vertices = {}
    current_y = START_Y
    end_node_id = None
    
    # Localiza o nó final ("fim") no dicionário de dados
    for node_id, label in vertices.items():
        if label.strip().lower() == "fim":
            end_node_id = node_id
            break

    # 1. Posicionamento e estilização sequencial dos blocos verticais
    for node_id, label in vertices.items():
        if "?" in label or "encontrados" in label or "válidos" in label:
            style = "rhombus;whiteSpace=wrap;html=1;strokeWidth=2;fillColor=#ffffff;strokeColor=#28253D;fontColor=#28253D;fontSize=14;"
        elif label.lower() in ("início", "inicio", "fim"):
            style = "rounded=1;whiteSpace=wrap;html=1;arcSize=50;strokeWidth=2;fillColor=#ffffff;strokeColor=#28253D;fontColor=#28253D;fontSize=14;"
        else:
            style = "whiteSpace=wrap;html=1;strokeWidth=2;fillColor=#ffffff;strokeColor=#28253D;fontColor=#28253D;fontSize=14;"

        user_object = ET.SubElement(xml_root, "UserObject", label=label, id=node_id)
        mx_cell = ET.SubElement(user_object, "mxCell", style=style, vertex="1", parent="1")
        
        # CORREÇÃO: Passando 'as' e os atributos numéricos em um dicionário para contornar a sintaxe do Python
        geometry_attributes = {
            "x": str(MAIN_X),
            "y": str(current_y),
            "width": str(NODE_WIDTH),
            "height": str(NODE_HEIGHT),
            "as": "geometry"
        }
        ET.SubElement(mx_cell, "mxGeometry", **geometry_attributes)
        
        positioned_vertices[node_id] = {
            "id": node_id,
            "label": label,
            "x": float(MAIN_X),
            "y": float(current_y),
            "w": float(NODE_WIDTH),
            "h": float(NODE_HEIGHT)
        }
        current_y += STEP_Y

    # 2. Agrupa as origens das arestas de desvio "Não" para estruturar as pistas paralelas
    no_edges_sources = []
    for edge in edges:
        if edge["label"].strip().lower() in ("não", "nao") and edge["source"] in positioned_vertices:
            no_edges_sources.append(edge["source"])
            
    no_edges_sources.sort(key=lambda src: positioned_vertices[src]["y"])
    num_no_edges = len(no_edges_sources)

    # Alinha horizontalmente o nó Fim para coincidir com o prumo da seta da esquerda
    base_tx = MAIN_X + NODE_WIDTH / 2
    leftmost_arrow_tx = base_tx + (0 - (num_no_edges - 1) / 2) * 15 if num_no_edges > 0 else base_tx
    new_end_node_x = leftmost_arrow_tx - (NODE_WIDTH / 2)

    if end_node_id and end_node_id in positioned_vertices:
        positioned_vertices[end_node_id]["x"] = new_end_node_x
        for u_obj in xml_root.findall(f".//UserObject[@id='{end_node_id}']"):
            geom = u_obj.find(".//mxGeometry")
            if geom is not None:
                geom.set("x", str(new_end_node_x))

    max_right = MAIN_X + NODE_WIDTH
    no_column_x = max_right + NO_COLUMN_OFFSET

    # 3. Geração e roteamento das arestas (linhas) no XML
    for idx, edge in enumerate(edges):
        src_id = edge["source"]
        tgt_id = edge["target"]
        label = edge["label"].strip().lower()

        if src_id not in positioned_vertices or tgt_id not in positioned_vertices:
            continue

        s = positioned_vertices[src_id]
        t = positioned_vertices[tgt_id]

        sy = s["y"] + s["h"]
        tx = (new_end_node_x + NODE_WIDTH / 2) if tgt_id == end_node_id else (t["x"] + t["w"] / 2)
        ty = t["y"]

        edge_id = f"edge_{src_id}_{tgt_id}_{idx}"
        user_object_edge = ET.SubElement(xml_root, "UserObject", label=edge["label"], id=edge_id)
        mx_cell_edge = ET.SubElement(user_object_edge, "mxCell", edge="1", parent="1", source=src_id, target=tgt_id)
        
        edge_geometry_attributes = {"relative": "1", "as": "geometry"}
        geometry_edge = ET.SubElement(mx_cell_edge, "mxGeometry", **edge_geometry_attributes)
        points_array = ET.SubElement(geometry_edge, "Array", {"as": "points"})

        # Caminho NÃO: Desvios ortogonais em canais calculados em série
        if label in ("não", "nao"):
            mx_cell_edge.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;")
            
            lane_idx = no_edges_sources.index(src_id) if src_id in no_edges_sources else 0
            current_no_column_x = no_column_x + (lane_idx * 35)
            current_tx = tx + (lane_idx - (num_no_edges - 1) / 2) * 15

            exit_x = s["x"] + s["w"]
            exit_y = s["y"] + s["h"] / 2

            append_mx_point(points_array, exit_x, exit_y)
            append_mx_point(points_array, current_no_column_x, exit_y)
            append_mx_point(points_array, current_no_column_x, t["y"] - FINAL_Y_MARGIN)
            append_mx_point(points_array, current_tx, t["y"] - FINAL_Y_MARGIN)
            continue

        # Caminho SIM: Descida vertical centralizada em linha reta contínua
        if label == "sim":
            mx_cell_edge.set("style", "edgeStyle=straightEdgeStyle;rounded=0;html=1;")
            exit_x = s["x"] + s["w"] / 2

            append_mx_point(points_array, exit_x, sy)
            append_mx_point(points_array, exit_x, ty - 15)
            continue

        # Conexões genéricas padrão do fluxo principal
        mx_cell_edge.set("style", "edgeStyle=straightEdgeStyle;rounded=0;html=1;")


def main():
    print(f"Parsing '{INPUT_FILENAME}' structure...")
    try:
        vertices, edges = parse_mermaid_file(INPUT_FILENAME)
    except FileNotFoundError:
        print(f"File '{INPUT_FILENAME}' not found. Please ensure it exists.")
        return

    mxfile, xml_root = create_base_mxfile()
    compile_graph_to_xml(vertices, edges, xml_root)

    tree = ET.ElementTree(mxfile)
    tree.write(OUTPUT_FILENAME, encoding="utf-8", xml_declaration=True)
    print(f"Compilation finished. Saved to: {OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()
