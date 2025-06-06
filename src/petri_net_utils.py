# src/petri_net_utils.py
import json
from graphviz import Digraph, CalledProcessError
from pathlib import Path
import shutil


def petri_json_to_dot(
    petri_json_data: dict, filename: str, output_dir: Path
) -> tuple[Path | None, None]:
    """
    Converts Petri Net JSON, renders a PDF to the specified output_dir, and does not save the .gv file.
    The final PDF filename will be filename.pdf.

    Args:
        petri_json_data (dict): The Petri Net data.
        filename (str): Base name for output PDF file (e.g., "candidate_xxxx"). No extensions.
        output_dir (Path): Directory to save .pdf file.

    Returns:
        tuple: (Path_to_pdf, None) if PDF is successful,
               (None, None) if PDF rendering fails.
    """
    if not isinstance(petri_json_data, dict):
        print("Error: Input petri_json_data must be a dictionary.")
        return None, None
    if not filename:
        print("Error: Filename cannot be empty for visualization.")
        return None, None
    if not isinstance(output_dir, Path):
        print("Error: output_dir must be a Path object.")
        return None, None

    output_dir.mkdir(parents=True, exist_ok=True)

    dot_graph = Digraph(name=filename, comment=f"Petri Net: {filename}")
    dot_graph.attr(rankdir="LR", fontsize="10")
    dot_graph.graph_attr["splines"] = "true"
    dot_graph.graph_attr["nodesep"] = "0.5"
    dot_graph.graph_attr["ranksep"] = "0.75"

    places = petri_json_data.get("places", {})
    transitions = petri_json_data.get("transitions", {})
    arcs = petri_json_data.get("arcs", [])
    initial_marking = petri_json_data.get("initial", {})

    for p_id, p_label in places.items():
        display_label = (p_label[:25] + "...") if len(p_label) > 25 else p_label
        full_node_label = f"{display_label}\nID: {p_id}"
        node_attrs = {
            "shape": "ellipse",
            "style": "filled",
            "fillcolor": "lightblue",
            "fontsize": "9",
        }
        if p_id in initial_marking:
            tokens = initial_marking[p_id]
            node_attrs["penwidth"] = "2"
            full_node_label += f"\n({tokens} token{'s' if tokens > 1 else ''})"
        dot_graph.node(p_id, label=full_node_label, **node_attrs)

    for t_id, t_label in transitions.items():
        display_label = (t_label[:25] + "...") if len(t_label) > 25 else t_label
        full_node_label = f"{display_label}\nID: {t_id}"
        dot_graph.node(
            t_id,
            label=full_node_label,
            shape="box",
            style="filled",
            fillcolor="lightgray",
            fontsize="9",
        )

    for arc_idx, arc in enumerate(arcs):
        arc_from, arc_to = arc.get("from"), arc.get("to")
        if arc_from and arc_to:
            dot_graph.edge(arc_from, arc_to)
        else:
            print(f"Warning: Skipping invalid arc (index {arc_idx}): {arc}")

    pdf_file_path = output_dir / f"{filename}.pdf"

    # Clean up any pre-existing PDF file with this name to avoid confusion from previous runs
    if pdf_file_path.exists():
        pdf_file_path.unlink(missing_ok=True)

    try:
        rendered_pdf_actual_path_str = dot_graph.render(
            filename=filename,
            directory=str(output_dir),
            format="pdf",
            cleanup=True,
            quiet=True,
        )

        if pdf_file_path.exists():
            return pdf_file_path, None
        else:
            print(
                f"Error: PDF file creation failed for '{filename}' in '{output_dir}'."
            )
            return None, None

    except CalledProcessError as cpe:
        print(
            f"Error: Graphviz 'dot' command failed during PDF rendering for '{filename}'."
        )
        print(f"Command: {' '.join(cpe.cmd) if cpe.cmd else 'Unknown'}")
        if shutil.which("dot") is None:
            print(
                "CRITICAL: The 'dot' command (Graphviz executable) was not found in your system's PATH."
            )
        return None, None

    except Exception as e:
        print(f"Error: Unexpected error generating PDF for '{filename}': {e}")
        return None, None
