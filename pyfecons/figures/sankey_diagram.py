from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.enums import FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.power_input import PowerInput

matplotlib.use("Agg")

# Colors
C_THERMAL = "#D4792A"  # orange — thermal flows
C_ELECTRIC = "#3A7CC6"  # blue — electric flows
C_NET = "#28964A"  # green — net output
C_LOSS = "#AA3333"  # red — losses / rejection
C_RECIRC = "#7B5BA5"  # purple — recirculating
C_FEEDBACK = "#888888"  # gray — feedback loops
C_DEC = "#C49A2A"  # gold — DEC flows
C_SIDE = "#6AA08A"  # teal — side inputs (blanket gain, p_input, pump recovery)


@dataclass
class _Node:
    name: str
    col: int
    value: float  # MW
    color: str
    label: str
    sort_order: int = 0  # 0 = main flow (top), 1 = losses/sinks (bottom)
    y: float = 0.0  # center y (set by layout)
    height: float = 0.0  # (set by layout)
    _in_cursor: float = 0.0
    _out_cursor: float = 0.0

    def alloc_in(self, h):
        """Allocate input attachment space. Returns y-center of allocated slot."""
        yc = (self.y + self.height / 2) - self._in_cursor - h / 2
        self._in_cursor += h
        return yc

    def alloc_out(self, h):
        """Allocate output attachment space. Returns y-center of allocated slot."""
        yc = (self.y + self.height / 2) - self._out_cursor - h / 2
        self._out_cursor += h
        return yc


@dataclass
class _Link:
    source: str
    target: str
    value: float  # MW
    color: str


# Layout constants
NODE_W = 0.055
GAP = 0.018  # gap between nodes in same column
DIAGRAM_H = 0.75  # available vertical space
CENTER_Y = 0.5


def _draw_flow(ax, x0, y0, x1, y1, width, color, alpha=0.4):
    """Draw a curved flow band (bezier) between two points."""
    if width < 0.002:
        return
    hw = width / 2
    xm = (x0 + x1) / 2
    verts = [
        (x0, y0 + hw),
        (xm, y0 + hw),
        (xm, y1 + hw),
        (x1, y1 + hw),
        (x1, y1 - hw),
        (xm, y1 - hw),
        (xm, y0 - hw),
        (x0, y0 - hw),
        (x0, y0 + hw),
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec="none", alpha=alpha))


def _draw_backward_flow(ax, x0, y0, x1, y1, width, color, y_bottom, alpha=0.3):
    """Draw a backward (right-to-left) flow that curves below the diagram.

    Goes: (x0, y0) down to y_bottom, across to x1, up to (x1, y1).
    """
    if width < 0.002:
        return
    hw = width / 2
    # Control points for a U-shaped path curving below
    verts = [
        # Top edge (outer)
        (x0, y0 + hw),
        (x0 + 0.02, y_bottom + hw),  # curve down on right side
        (x1 - 0.02, y_bottom + hw),  # across bottom
        (x1, y1 + hw),  # curve up on left side
        # Bottom edge (inner) — reverse direction
        (x1, y1 - hw),
        (x1 - 0.02, y_bottom - hw),
        (x0 + 0.02, y_bottom - hw),
        (x0, y0 - hw),
        (x0, y0 + hw),
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec="none", alpha=alpha))


def _draw_side_input(
    ax, node_x, node_y, node_h, width, color, label_text, side="bottom"
):
    """Draw a small side-input arrow entering a node from below."""
    if width < 0.002:
        return
    hw = width / 2
    x_center = node_x
    if side == "bottom":
        y_start = node_y - node_h / 2 - 0.06
        y_end = node_y - node_h / 2
    else:
        y_start = node_y + node_h / 2 + 0.06
        y_end = node_y + node_h / 2
    # Simple vertical flow band
    verts = [
        (x_center - hw, y_start),
        (x_center - hw, y_end),
        (x_center + hw, y_end),
        (x_center + hw, y_start),
        (x_center - hw, y_start),
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec="none", alpha=0.35))
    # Label
    ax.text(
        x_center + hw + 0.005,
        (y_start + y_end) / 2,
        label_text,
        fontsize=6,
        va="center",
        ha="left",
        color="#555",
        style="italic",
    )


def _draw_node_rect(ax, x, y, w, h, color, label, value_mw):
    """Draw a labeled node rectangle."""
    h = max(h, 0.01)
    rect = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.004",
        fc=color,
        ec="white",
        lw=1.2,
        alpha=0.85,
    )
    ax.add_patch(rect)
    # Label: inside if tall enough, else beside
    if h > 0.04:
        ax.text(
            x,
            y,
            f"{label}\n{value_mw:.0f} MW",
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color="white",
        )
    else:
        ax.text(
            x + w / 2 + 0.008,
            y,
            f"{label} ({value_mw:.0f} MW)",
            ha="left",
            va="center",
            fontsize=6.5,
            color="#333",
        )


def _layout_column(nodes_in_col, scale, col_x):
    """Stack nodes vertically, centered at CENTER_Y. Sets y and height on each node."""
    total_h = sum(n.value * scale for n in nodes_in_col) + GAP * max(
        len(nodes_in_col) - 1, 0
    )
    y_top = CENTER_Y + total_h / 2
    for node in nodes_in_col:
        node.height = node.value * scale
        node.y = y_top - node.height / 2
        y_top -= node.height + GAP


class PowerFlowSankey:
    """Generates a Sankey diagram of the power balance."""

    @staticmethod
    def create(power_table: PowerTable, basic: Basic, power_input: PowerInput) -> bytes:
        pt = power_table
        pi = power_input
        is_mfe = basic.fusion_machine_type == FusionMachineType.MFE
        p_nrl = float(basic.p_nrl)

        # --- Extract values ---
        f_dec = float(pi.f_dec) if pi.f_dec else 0.0
        p_ash = float(pt.p_ash)
        p_neutron = float(pt.p_neutron)
        mn = float(pi.mn) if pi.mn else 1.0
        p_neutron_th = mn * p_neutron
        blanket_gain = (mn - 1) * p_neutron
        p_wall = float(pt.p_wall) if pt.p_wall else p_ash
        p_dee = float(pt.p_dee) if pt.p_dee else 0.0
        p_dec_waste = float(pt.p_dec_waste) if pt.p_dec_waste else 0.0
        p_input = float(pi.p_input) if pi.p_input else 0.0
        p_pump = float(pt.p_pump) if pt.p_pump else 0.0
        eta_p = float(pi.eta_p) if pi.eta_p else 0.0
        pump_recovery = eta_p * p_pump
        p_th = float(pt.p_th)
        p_the = float(pt.p_the)
        p_et = float(pt.p_et)
        p_net = float(pt.p_net)
        thermal_reject = p_th - p_the

        # Recirculating breakdown
        recirc_items: List[Tuple[str, float]] = []
        if is_mfe:
            p_coils_v = float(pt.p_coils) if pt.p_coils else 0.0
            p_cool_v = float(pt.p_cool) if pt.p_cool else 0.0
            eta_pin = float(pi.eta_pin) if pi.eta_pin else 1.0
            p_input_driver = p_input / eta_pin if eta_pin > 0 else 0.0
            p_cryo = float(pi.p_cryo) if pi.p_cryo else 0.0
            p_sub = float(pt.p_sub) if pt.p_sub else 0.0
            p_aux = float(pt.p_aux) if pt.p_aux else 0.0
            for lbl, val in [
                ("Coils", p_coils_v),
                ("Pump", p_pump),
                ("Subsys", p_sub),
                ("Aux", p_aux),
                ("Cooling", p_cool_v),
                ("Cryo", p_cryo),
                ("Input Drv", p_input_driver),
            ]:
                if val > 0:
                    recirc_items.append((lbl, val))
        else:
            p_target = float(pi.p_target) if pi.p_target else 0.0
            eta_pin1 = float(pi.eta_pin1) if pi.eta_pin1 else 1.0
            eta_pin2 = float(pi.eta_pin2) if pi.eta_pin2 else 1.0
            p_imp = float(pi.p_implosion) if pi.p_implosion else 0.0
            p_ign = float(pi.p_ignition) if pi.p_ignition else 0.0
            p_cryo = float(pi.p_cryo) if pi.p_cryo else 0.0
            p_sub = float(pt.p_sub) if pt.p_sub else 0.0
            p_aux = float(pt.p_aux) if pt.p_aux else 0.0
            for lbl, val in [
                ("Target", p_target),
                ("Pump", p_pump),
                ("Subsys", p_sub),
                ("Aux", p_aux),
                ("Cryo", p_cryo),
                ("Implosion", p_imp / eta_pin1 if eta_pin1 > 0 else 0),
                ("Ignition", p_ign / eta_pin2 if eta_pin2 > 0 else 0),
            ]:
                if val > 0:
                    recirc_items.append((lbl, val))

        total_recirc = sum(v for _, v in recirc_items)

        # --- Build nodes ---
        has_dec = f_dec > 0 and p_dee > 0.5
        nodes: Dict[str, _Node] = {}

        # Col 0: Fusion
        nodes["fusion"] = _Node("fusion", 0, p_nrl, C_THERMAL, "Fusion\nPower")

        # Col 1: Split
        nodes["neutrons"] = _Node("neutrons", 1, p_neutron, C_THERMAL, "Neutrons")
        if has_dec:
            nodes["wall"] = _Node("wall", 1, p_wall, C_THERMAL, "Wall\nThermal")
            nodes["dec_e"] = _Node("dec_e", 1, p_dee, C_DEC, "DEC\nElec")
            if p_dec_waste > 0.5:
                nodes["dec_w"] = _Node(
                    "dec_w", 1, p_dec_waste, C_LOSS, "DEC\nWaste", sort_order=1
                )
        else:
            nodes["ash"] = _Node("ash", 1, p_ash, C_THERMAL, "Charged\nPtcls")

        # Col 2: Thermal (single node)
        nodes["thermal"] = _Node("thermal", 2, p_th, C_THERMAL, "Thermal\nPower")

        # Col 3: Gross Electric + Thermal Rejection (both outputs of thermal conversion)
        nodes["gross"] = _Node(
            "gross", 3, p_et, C_ELECTRIC, "Gross\nElectric", sort_order=0
        )
        nodes["reject"] = _Node(
            "reject", 3, thermal_reject, C_LOSS, "Thermal\nRejection", sort_order=1
        )

        # Col 4: Net + Recirculating (as one aggregate node)
        nodes["net"] = _Node("net", 4, p_net, C_NET, "Net\nElectric", sort_order=0)
        nodes["recirc"] = _Node(
            "recirc", 4, total_recirc, C_RECIRC, "Recirc", sort_order=1
        )

        # --- Build links (ordered top-to-bottom per source) ---
        links: List[_Link] = []

        # From fusion
        links.append(_Link("fusion", "neutrons", p_neutron, C_THERMAL))
        if has_dec:
            links.append(_Link("fusion", "wall", p_wall, C_THERMAL))
            links.append(_Link("fusion", "dec_e", p_dee, C_DEC))
            if "dec_w" in nodes:
                links.append(_Link("fusion", "dec_w", p_dec_waste, C_LOSS))
        else:
            links.append(_Link("fusion", "ash", p_ash, C_THERMAL))

        # Into thermal
        links.append(_Link("neutrons", "thermal", p_neutron, C_THERMAL))
        if has_dec:
            links.append(_Link("wall", "thermal", p_wall, C_THERMAL))
        else:
            links.append(_Link("ash", "thermal", p_wall, C_THERMAL))

        # DEC electric → gross (skip column 2)
        if has_dec:
            links.append(_Link("dec_e", "gross", p_dee, C_DEC))

        # Thermal → outputs
        links.append(_Link("thermal", "gross", p_the, C_ELECTRIC))
        links.append(_Link("thermal", "reject", thermal_reject, C_LOSS))

        # Gross → outputs
        links.append(_Link("gross", "net", p_net, C_NET))
        links.append(_Link("gross", "recirc", total_recirc, C_RECIRC))

        # --- Compute scale ---
        # Scale factor: MW → diagram height units
        # Use the tallest column to determine scale
        columns: Dict[int, List[_Node]] = {}
        for n in nodes.values():
            columns.setdefault(n.col, []).append(n)
        # Sort: main-flow nodes (sort_order=0) on top, losses (sort_order=1) below
        for col_nodes in columns.values():
            col_nodes.sort(key=lambda n: (n.sort_order, -n.value))

        max_col_mw = max(
            sum(n.value for n in col_nodes) for col_nodes in columns.values()
        )
        scale = DIAGRAM_H / max_col_mw

        # --- Layout columns ---
        num_cols = max(columns.keys()) + 1
        col_x = {i: 0.06 + i * 0.21 for i in range(num_cols)}

        for col_idx, col_nodes in columns.items():
            _layout_column(col_nodes, scale, col_x[col_idx])

        # --- Draw ---
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.set_xlim(-0.02, 1.02)
        y_vals = [n.y - n.height / 2 for n in nodes.values()] + [
            n.y + n.height / 2 for n in nodes.values()
        ]
        ax.set_ylim(min(y_vals) - 0.25, max(y_vals) + 0.12)
        ax.set_aspect("auto")
        ax.axis("off")

        fuel_name = basic.fuel_type.name if basic.fuel_type else "Unknown"
        machine = "MFE" if is_mfe else "IFE"
        ax.set_title(
            f"Power Flow \u2014 {machine} {fuel_name} ({p_net:.0f} MW net)",
            fontsize=13,
            fontweight="bold",
            pad=10,
        )

        # Draw nodes
        for n in nodes.values():
            _draw_node_rect(
                ax, col_x[n.col], n.y, NODE_W, n.height, n.color, n.label, n.value
            )

        # Draw links
        for lk in links:
            src = nodes[lk.source]
            tgt = nodes[lk.target]
            flow_h = lk.value * scale
            y_src = src.alloc_out(flow_h)
            y_tgt = tgt.alloc_in(flow_h)
            x0 = col_x[src.col] + NODE_W / 2
            x1 = col_x[tgt.col] - NODE_W / 2
            _draw_flow(ax, x0, y_src, x1, y_tgt, flow_h, lk.color)

        # --- Side inputs to thermal (blanket gain, pump recovery) ---
        th_node = nodes["thermal"]
        side_x = col_x[th_node.col]

        if blanket_gain > 0.5:
            bh = blanket_gain * scale
            _draw_side_input(
                ax,
                side_x,
                th_node.y,
                th_node.height,
                bh,
                C_SIDE,
                f"Blanket gain ({blanket_gain:.0f} MW, M_N={mn:.2f})",
            )

        if pump_recovery > 0.5:
            ph = pump_recovery * scale
            _draw_side_input(
                ax,
                side_x + 0.02,
                th_node.y,
                th_node.height,
                ph,
                C_FEEDBACK,
                f"Pump recovery ({pump_recovery:.0f} MW)",
            )

        # --- Feedback: p_input flows backward from recirc (col 4) to thermal (col 2) ---
        if p_input > 0.5:
            rc_node = nodes["recirc"]
            fb_h = p_input * scale
            # Source: bottom of recirc node, Target: bottom of thermal node
            y_fb_src = rc_node.y - rc_node.height / 2
            y_fb_tgt = th_node.y - th_node.height / 2
            x_fb_src = col_x[rc_node.col] - NODE_W / 2
            x_fb_tgt = col_x[th_node.col] - NODE_W / 2
            y_bottom = min(y_vals) - 0.08
            _draw_backward_flow(
                ax, x_fb_src, y_fb_src, x_fb_tgt, y_fb_tgt, fb_h, C_FEEDBACK, y_bottom
            )
            # Label on the backward flow
            ax.text(
                (x_fb_src + x_fb_tgt) / 2,
                y_bottom - fb_h / 2 - 0.015,
                f"p_input = {p_input:.0f} MW (heating \u2192 thermal)",
                fontsize=7,
                ha="center",
                va="top",
                color="#666",
                style="italic",
            )

        # --- Annotations ---
        # Mn near neutrons→thermal flow
        if mn > 1.0:
            n_node = nodes["neutrons"]
            mid_x = (col_x[n_node.col] + col_x[th_node.col]) / 2
            ax.text(
                mid_x,
                n_node.y + n_node.height / 2 + 0.015,
                f"\u00d7{mn:.2f} (blanket M_N)",
                fontsize=7,
                ha="center",
                color="#555",
                style="italic",
            )

        # η_th near thermal→gross flow
        eta_th = float(pi.eta_th) if pi.eta_th else 0.0
        g_node = nodes["gross"]
        mid_x2 = (col_x[th_node.col] + col_x[g_node.col]) / 2
        ax.text(
            mid_x2,
            th_node.y + th_node.height / 2 + 0.015,
            f"\u03b7_th = {eta_th:.0%}",
            fontsize=7,
            ha="center",
            color="#555",
            style="italic",
        )

        # Recirculating breakdown annotation
        if recirc_items:
            rc_node = nodes["recirc"]
            breakdown_lines = [f"  {lbl}: {val:.0f} MW" for lbl, val in recirc_items]
            ax.text(
                col_x[rc_node.col] + NODE_W / 2 + 0.008,
                rc_node.y,
                "\n".join(breakdown_lines),
                fontsize=6,
                va="center",
                ha="left",
                color="#555",
                family="monospace",
            )

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1, dpi=150)
        buf.seek(0)
        plt.close(fig)
        return buf.read()
