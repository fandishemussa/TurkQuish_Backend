# Generate proposed system architecture diagram for TurkQuish.
# Outputs:
#   turkquish_proposed_system_architecture_final.png
#   turkquish_proposed_system_architecture_final.svg
#   turkquish_proposed_system_architecture_final.pdf
#   turkquish_proposed_system_architecture.drawio
#   turkquish_proposed_system_architecture.mmd
#   README_DIAGRAM_GENERATION.md

import base64

import matplotlib.pyplot as plt
from matplotlib.patches import (
    Arc,
    Circle,
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
    Wedge,
)
import numpy as np

W, H = 1672, 941

NAVY = "#0B2E8A"
BLUE = "#0B56C6"
LIGHT_BLUE = "#F6FBFF"
MID_BLUE = "#1E88E5"
GREEN = "#176B1A"
MID_GREEN = "#4A8B2C"
LIGHT_GREEN = "#F2FAE9"
PURPLE = "#6A1B9A"
DEEP_PURPLE = "#3B0A45"
LIGHT_PURPLE = "#FBF5FF"
RED = "#D71920"
LIGHT_RED = "#FFF8F8"
ORANGE = "#D95500"
LIGHT_ORANGE = "#FFF8EF"
YELLOW = "#FFF8E1"
TEAL = "#00897B"
LIGHT_TEAL = "#E7F7F5"
GRAY = "#333333"
MID_GRAY = "#666666"
LIGHT_GRAY = "#F7F7F7"
PANEL_EDGE = "#B8C1D1"
TEXT = "#111111"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)

fig, ax = plt.subplots(figsize=(16.72, 9.41), dpi=200)
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)


def rounded_box(
    x,
    y,
    w,
    h,
    fc="white",
    ec=GRAY,
    lw=1.5,
    radius=8,
    dashed=False,
    alpha=1.0,
    z=1,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
        linestyle=(0, (5, 4)) if dashed else "-",
        alpha=alpha,
        clip_on=False,
        zorder=z,
    )
    ax.add_patch(patch)
    return patch


def add_text(
    x,
    y,
    s,
    size=11,
    color=TEXT,
    weight="normal",
    ha="center",
    va="center",
    linespacing=1.15,
    z=5,
):
    return ax.text(
        x,
        y,
        s,
        fontsize=size,
        color=color,
        weight=weight,
        ha=ha,
        va=va,
        linespacing=linespacing,
        family="DejaVu Sans",
        clip_on=False,
        zorder=z,
    )


def draw_text_box(
    x,
    y,
    w,
    h,
    title=None,
    lines=(),
    fc="white",
    ec=GRAY,
    lw=1.4,
    radius=8,
    dashed=False,
    title_color=TEXT,
    title_size=12,
    body_size=10,
    body_color=TEXT,
):
    rounded_box(x, y, w, h, fc=fc, ec=ec, lw=lw, radius=radius, dashed=dashed, z=1)
    yy = y + 0.38 * h if title and lines else y + h / 2
    if title:
        add_text(
            x + w / 2, yy, title, size=title_size, color=title_color, weight="bold"
        )
    if lines:
        add_text(
            x + w / 2,
            y + 0.68 * h,
            "\n".join(lines),
            size=body_size,
            color=body_color,
            weight="normal",
        )


def draw_header(x, y, w, h, number, label, fc, font_size):
    rounded_box(x, y, w, h, fc=fc, ec=fc, lw=1.2, radius=8, z=3)
    r = h * 0.34
    cx = x + 27
    cy = y + h / 2
    ax.add_patch(Circle((cx, cy), r, fc="white", ec="white", lw=1.0, zorder=4))
    add_text(cx, cy, str(number), size=font_size - 2, color=fc, weight="bold", z=5)
    add_text(
        x + 55,
        cy,
        label,
        size=font_size,
        color="white",
        weight="bold",
        ha="left",
        z=5,
    )


def draw_poly_arrow(
    points, color=GRAY, lw=2.5, dashed=False, arrow_at_end=True, mutation=16, z=2
):
    linestyle = (0, (5, 4)) if dashed else "-"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if len(points) > 2 or not arrow_at_end:
        ax.plot(
            xs,
            ys,
            color=color,
            lw=lw,
            linestyle=linestyle,
            solid_capstyle="round",
            zorder=z,
        )
    if arrow_at_end and len(points) >= 2:
        arr = FancyArrowPatch(
            points[-2],
            points[-1],
            arrowstyle="-|>",
            mutation_scale=mutation,
            linewidth=lw,
            color=color,
            linestyle=linestyle,
            shrinkA=0,
            shrinkB=0,
            zorder=z,
        )
        ax.add_patch(arr)


def draw_bidirectional_arrow(x1, y1, x2, y2, color=BLUE, lw=3):
    arr = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="<|-|>",
        mutation_scale=18,
        linewidth=lw,
        color=color,
        shrinkA=4,
        shrinkB=4,
        zorder=2,
    )
    ax.add_patch(arr)


def draw_globe_search(cx, cy, s=44, color=NAVY):
    r = s / 2
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=color, lw=2.2, zorder=4))
    ax.add_patch(Ellipse((cx, cy), s * 0.50, s, fill=False, ec=color, lw=1.4, zorder=4))
    ax.add_patch(Ellipse((cx, cy), s, s * 0.48, fill=False, ec=color, lw=1.4, zorder=4))
    ax.plot([cx - r, cx + r], [cy, cy], color=color, lw=1.3, zorder=4)
    ax.plot([cx, cx], [cy - r, cy + r], color=color, lw=1.3, zorder=4)
    ax.add_patch(
        Circle(
            (cx + s * 0.34, cy + s * 0.31),
            s * 0.18,
            fill=False,
            ec=TEXT,
            lw=2.5,
            zorder=5,
        )
    )
    ax.plot(
        [cx + s * 0.47, cx + s * 0.65],
        [cy + s * 0.44, cy + s * 0.62],
        color=TEXT,
        lw=2.5,
        zorder=5,
    )
def draw_shield_filled(cx, cy, s=42, color=NAVY, fill="white", check=False):
    verts = [
        (cx, cy - s * 0.52),
        (cx + s * 0.42, cy - s * 0.34),
        (cx + s * 0.35, cy + s * 0.12),
        (cx, cy + s * 0.52),
        (cx - s * 0.35, cy + s * 0.12),
        (cx - s * 0.42, cy - s * 0.34),
    ]
    ax.add_patch(Polygon(verts, closed=True, fc=fill, ec=color, lw=2.0, zorder=4))
    if check:
        ax.plot(
            [cx - s * 0.18, cx - s * 0.04, cx + s * 0.20],
            [cy + s * 0.02, cy + s * 0.18, cy - s * 0.16],
            color=color,
            lw=2.6,
            solid_capstyle="round",
            zorder=5,
        )


def draw_shield(cx, cy, s=42, color=NAVY, fill="white", check=False):
    verts = [
        (cx, cy - s * 0.52),
        (cx + s * 0.42, cy - s * 0.34),
        (cx + s * 0.35, cy + s * 0.12),
        (cx, cy + s * 0.52),
        (cx - s * 0.35, cy + s * 0.12),
        (cx - s * 0.42, cy - s * 0.34),
    ]
    ax.add_patch(Polygon(verts, closed=True, fc=fill, ec=color, lw=2.0, zorder=4))
    if check:
        ax.plot(
            [cx - s * 0.18, cx - s * 0.04, cx + s * 0.20],
            [cy + s * 0.02, cy + s * 0.18, cy - s * 0.16],
            color=color,
            lw=1.4,
            solid_capstyle="round",
            zorder=5,
        )


def draw_solid_shield_mark(cx, cy, s=42, color=NAVY, mark="check"):
    draw_shield(cx, cy, s=s, color=color, fill=color)
    if mark == "plus":
        ax.plot(
            [cx, cx], [cy - s * 0.20, cy + s * 0.20], color="white", lw=2.8, zorder=5
        )
        ax.plot(
            [cx - s * 0.18, cx + s * 0.18], [cy, cy], color="white", lw=2.8, zorder=5
        )
    elif mark == "star":
        points = []
        for i in range(10):
            a = np.radians(-90 + i * 36)
            r = s * (0.18 if i % 2 == 0 else 0.08)
            points.append((cx + np.cos(a) * r, cy + np.sin(a) * r))
        ax.add_patch(
            Polygon(points, closed=True, fc="white", ec="white", lw=1.0, zorder=5)
        )
    else:
        ax.plot(
            [cx - s * 0.18, cx - s * 0.04, cx + s * 0.20],
            [cy + s * 0.02, cy + s * 0.18, cy - s * 0.16],
            color="white",
            lw=2.5,
            solid_capstyle="round",
            zorder=5,
        )


# def draw_database(cx, cy, s=42, color=GRAY, fill="white"):
#     w = s * 0.72
#     h = s * 0.92
#     top = cy - h / 2
#     bottom = cy + h / 2
#     ax.add_patch(Rectangle((cx - w / 2, top + 5), w, h - 10, fc=fill, ec=color, lw=1.9, zorder=4))
#     ax.add_patch(Ellipse((cx, top + 5), w, 12, fc=fill, ec=color, lw=1.9, zorder=5))
#     ax.add_patch(Ellipse((cx, bottom - 5), w, 12, fc=fill, ec=color, lw=1.9, zorder=5))
#     ax.plot([cx - w / 2, cx + w / 2], [cy - 2, cy - 2], color=color, lw=1.3, zorder=5)
#     ax.plot([cx - w / 2, cx + w / 2], [cy + s * 0.18, cy + s * 0.18], color=color, lw=1.3, zorder=5)


def draw_database(cx, cy, s=42, color=MID_GRAY, fill=None):
    """
    Draws a solid database cylinder like the reference:
    gray body with white separator curves.
    """
    if fill is None:
        fill = color

    w = s * 0.62
    h = s * 0.82

    top_y = cy - h / 2
    mid_y = cy
    bottom_y = cy + h / 2

    # Solid body
    ax.add_patch(
        Rectangle(
            (cx - w / 2, top_y),
            w,
            h,
            fc=fill,
            ec=fill,
            lw=0,
            zorder=4,
        )
    )

    # Top ellipse
    ax.add_patch(
        Ellipse(
            (cx, top_y),
            w,
            w * 0.38,
            fc=fill,
            ec="white",
            lw=1.8,
            zorder=5,
        )
    )

    # Middle separator
    ax.add_patch(
        Arc(
            (cx, mid_y),
            w,
            w * 0.38,
            theta1=0,
            theta2=180,
            ec="white",
            lw=1.8,
            zorder=5,
        )
    )

    # Lower separator
    ax.add_patch(
        Arc(
            (cx, cy + h * 0.25),
            w,
            w * 0.38,
            theta1=0,
            theta2=180,
            ec="white",
            lw=1.8,
            zorder=5,
        )
    )

    # Bottom ellipse outline/curve
    ax.add_patch(
        Ellipse(
            (cx, bottom_y),
            w,
            w * 0.38,
            fc=fill,
            ec=fill,
            lw=0,
            zorder=4,
        )
    )

    ax.add_patch(
        Arc(
            (cx, bottom_y),
            w,
            w * 0.38,
            theta1=0,
            theta2=180,
            ec="white",
            lw=1.8,
            zorder=5,
        )
    )


def draw_filled_database(cx, cy, s=42, color=NAVY):
    w = s * 0.72
    h = s * 0.92
    top = cy - h / 2
    bottom = cy + h / 2
    ax.add_patch(
        Rectangle(
            (cx - w / 2, top + 5), w, h - 10, fc=color, ec=color, lw=1.8, zorder=4
        )
    )
    ax.add_patch(Ellipse((cx, top + 5), w, 12, fc="white", ec=color, lw=2.0, zorder=5))
    ax.add_patch(Ellipse((cx, bottom - 5), w, 12, fc=color, ec=color, lw=2.0, zorder=5))
    ax.plot(
        [cx - w / 2 + 3, cx + w / 2 - 3],
        [cy + s * 0.05, cy + s * 0.05],
        color="white",
        lw=1.4,
        zorder=5,
    )


def draw_database_with_nodes(cx, cy, s=42, color=NAVY):
    draw_database(cx - s * 0.14, cy, s * 0.86, color=color)
    pts = [
        (cx + s * 0.22, cy - s * 0.22),
        (cx + s * 0.43, cy),
        (cx + s * 0.22, cy + s * 0.22),
    ]
    ax.plot(
        [pts[0][0], pts[1][0], pts[2][0]],
        [pts[0][1], pts[1][1], pts[2][1]],
        color=color,
        lw=1.8,
        zorder=5,
    )
    for p in pts:
        ax.add_patch(Circle(p, s * 0.06, fc=color, ec=color, zorder=6))


def draw_biohazard_or_hazard(cx, cy, s=42, color=TEXT):
    ax.add_patch(Circle((cx, cy), s * 0.10, fc=color, ec=color, zorder=5))
    for ang in [90, 210, 330]:
        rad = np.radians(ang)
        ox = cx + np.cos(rad) * s * 0.22
        oy = cy - np.sin(rad) * s * 0.22
        ax.add_patch(Circle((ox, oy), s * 0.18, fill=False, ec=color, lw=2.3, zorder=4))
        ax.plot([cx, ox], [cy, oy], color=color, lw=2.0, zorder=5)
    ax.add_patch(Circle((cx, cy), s * 0.40, fill=False, ec=color, lw=1.7, zorder=4))


# def draw_gear(cx, cy, s=40, color=MID_GRAY):
#     for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
#         tx = cx + np.cos(angle) * s * 0.35
#         ty = cy + np.sin(angle) * s * 0.35
#         ax.add_patch(
#             Rectangle(
#                 (tx - s * 0.06, ty - s * 0.06),
#                 s * 0.12,
#                 s * 0.12,
#                 angle=np.degrees(angle),
#                 fc=color,
#                 ec=color,
#                 zorder=4,
#             )
#         )
#     ax.add_patch(Circle((cx, cy), s * 0.30, fc=color, ec=color, lw=1.5, zorder=4))
#     ax.add_patch(Circle((cx, cy), s * 0.13, fc="white", ec="white", lw=1.0, zorder=5))


def draw_gear(cx, cy, s=40, color=MID_GRAY):
    """
    Draw a solid gear icon with connected teeth, closer to the reference icon.
    cx, cy: center
    s: overall icon size
    """

    outer_r = s * 0.50
    inner_r = s * 0.40
    teeth = 12

    points = []

    # Create connected gear outline using alternating outer/inner radii
    for i in range(teeth * 2):
        angle = -np.pi / 2 + i * np.pi / teeth
        r = outer_r if i % 2 == 0 else inner_r

        x = cx + np.cos(angle) * r
        y = cy + np.sin(angle) * r
        points.append((x, y))

    # Solid gear body
    ax.add_patch(
        Polygon(
            points,
            closed=True,
            fc=color,
            ec=color,
            lw=0,
            zorder=4,
        )
    )

    # Round body overlay to make gear less spiky
    ax.add_patch(
        Circle(
            (cx, cy),
            s * 0.34,
            fc=color,
            ec=color,
            lw=0,
            zorder=5,
        )
    )

    # White center hole
    ax.add_patch(
        Circle(
            (cx, cy),
            s * 0.18,
            fc="white",
            ec="white",
            lw=0,
            zorder=6,
        )
    )


# def draw_gear_database(cx, cy, s=54, color=MID_GRAY):
#     draw_gear(cx - s * 0.18, cy - s * 0.05, s * 0.72, color=color)
#     draw_database(cx + s * 0.30, cy + s * 0.16, s * 0.58, color=color)
def draw_gear_database(cx, cy, s=54, color=MID_GRAY):
    """
    Gear + database icon matching the original proposed-system style.
    Solid gear on upper-left, database cylinder on lower-right.
    """

    draw_gear(
        cx=cx - s * 0.18,
        cy=cy - s * 0.12,
        s=s * 0.72,
        color=color,
    )

    draw_database(
        cx=cx + s * 0.28,
        cy=cy + s * 0.20,
        s=s * 0.58,
        color=color,
    )


def draw_chain_link(cx, cy, s=48, color=TEXT):
    ax.add_patch(
        Ellipse(
            (cx - s * 0.16, cy + s * 0.03),
            s * 0.62,
            s * 0.28,
            angle=-45,
            fill=False,
            ec=color,
            lw=3.1,
            zorder=4,
        )
    )
    ax.add_patch(
        Ellipse(
            (cx + s * 0.16, cy - s * 0.03),
            s * 0.62,
            s * 0.28,
            angle=-45,
            fill=False,
            ec=color,
            lw=3.1,
            zorder=4,
        )
    )
    ax.plot(
        [cx - s * 0.08, cx + s * 0.08],
        [cy + s * 0.08, cy - s * 0.08],
        color="white",
        lw=3.8,
        zorder=5,
    )


def draw_Aa_icon(cx, cy, s=38):
    rounded_box(
        cx - s / 2, cy - s / 2, s, s, fc="#2E86DE", ec="#2E86DE", lw=1.0, radius=4, z=4
    )
    add_text(cx, cy + 1, "Aa", size=18, color="white", weight="bold", z=5)


def draw_spy_hat_glasses(cx, cy, s=44, color=TEXT):
    ax.add_patch(
        Rectangle(
            (cx - s * 0.36, cy - s * 0.15),
            s * 0.72,
            s * 0.10,
            fc=color,
            ec=color,
            zorder=4,
        )
    )
    ax.add_patch(
        Polygon(
            [
                (cx - s * 0.22, cy - s * 0.15),
                (cx + s * 0.22, cy - s * 0.15),
                (cx + s * 0.10, cy - s * 0.38),
                (cx - s * 0.10, cy - s * 0.38),
            ],
            fc=color,
            ec=color,
            zorder=4,
        )
    )
    ax.add_patch(
        Circle(
            (cx - s * 0.13, cy + s * 0.09),
            s * 0.11,
            fill=False,
            ec=color,
            lw=2.2,
            zorder=4,
        )
    )
    ax.add_patch(
        Circle(
            (cx + s * 0.13, cy + s * 0.09),
            s * 0.11,
            fill=False,
            ec=color,
            lw=2.2,
            zorder=4,
        )
    )
    ax.plot(
        [cx - s * 0.02, cx + s * 0.02],
        [cy + s * 0.09, cy + s * 0.09],
        color=color,
        lw=2.2,
        zorder=4,
    )


def draw_turkish_g_icon(cx, cy, s=42, color="#F39C12"):
    add_text(cx, cy, "ğ", size=s * 0.90, color=color, weight="bold", z=5)


def draw_network_nodes(cx, cy, s=46, color=NAVY):
    pts = [
        (cx, cy),
        (cx - s * 0.36, cy - s * 0.20),
        (cx + s * 0.35, cy - s * 0.22),
        (cx - s * 0.28, cy + s * 0.31),
        (cx + s * 0.31, cy + s * 0.28),
        (cx, cy - s * 0.43),
    ]
    for i, j in [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 3), (2, 4)]:
        ax.plot(
            [pts[i][0], pts[j][0]],
            [pts[i][1], pts[j][1]],
            color=color,
            lw=1.8,
            zorder=4,
        )
    for p in pts:
        ax.add_patch(Circle(p, s * 0.075, fc=color, ec=color, zorder=5))


def draw_bar_chart(cx, cy, s=44, color=GREEN):
    bw = s * 0.13
    heights = [s * 0.35, s * 0.58, s * 0.78]
    xs = [cx - s * 0.28, cx, cx + s * 0.28]
    for x, h in zip(xs, heights):
        ax.add_patch(
            Rectangle(
                (x - bw / 2, cy + s * 0.36 - h), bw, h, fc=color, ec=color, zorder=4
            )
        )


def draw_no_entry(cx, cy, s=44, color=RED):
    ax.add_patch(Circle((cx, cy), s / 2, fill=False, ec=color, lw=3.0, zorder=4))
    ax.plot(
        [cx - s * 0.34, cx + s * 0.34],
        [cy - s * 0.34, cy + s * 0.34],
        color=color,
        lw=3.0,
        zorder=4,
    )


def draw_funnel(cx, cy, s=42, color=GRAY):
    verts = [
        (cx - s * 0.43, cy - s * 0.35),
        (cx + s * 0.43, cy - s * 0.35),
        (cx + s * 0.12, cy + s * 0.06),
        (cx + s * 0.05, cy + s * 0.36),
        (cx - s * 0.05, cy + s * 0.36),
        (cx - s * 0.12, cy + s * 0.06),
    ]
    ax.add_patch(Polygon(verts, closed=True, fc=color, ec=color, zorder=4))


def draw_checklist(cx, cy, s=42, color=GREEN):
    rounded_box(
        cx - s / 2, cy - s / 2, s, s, fc="white", ec=color, lw=2.0, radius=5, z=4
    )
    for i in range(3):
        yy = cy - s * 0.25 + i * s * 0.22
        ax.plot(
            [cx - s * 0.31, cx - s * 0.22, cx - s * 0.10],
            [yy, yy + s * 0.10, yy - s * 0.10],
            color=color,
            lw=2.0,
            zorder=5,
        )
        ax.plot([cx - s * 0.02, cx + s * 0.31], [yy, yy], color=color, lw=2.0, zorder=5)


def draw_pie_chart(cx, cy, s=52, color=NAVY):
    ax.add_patch(Circle((cx, cy), s / 2, fc=color, ec=color, zorder=4))
    ax.add_patch(Wedge((cx, cy), s / 2, 270, 360, fc="white", ec="white", zorder=5))
    ax.plot([cx, cx + s / 2], [cy, cy], color="white", lw=2.2, zorder=6)
    ax.plot([cx, cx], [cy, cy - s / 2], color="white", lw=2.2, zorder=6)


def draw_prediction_pie(cx, cy, s=38):
    r = s / 2
    ax.add_patch(Wedge((cx, cy), r, 90, 275, fc=GREEN, ec="white", lw=0.9, zorder=4))
    ax.add_patch(
        Wedge((cx, cy), r, 275, 330, fc="#F4B400", ec="white", lw=0.9, zorder=4)
    )
    ax.add_patch(Wedge((cx, cy), r, 330, 360, fc=NAVY, ec="white", lw=0.9, zorder=4))
    ax.add_patch(Wedge((cx, cy), r, 0, 90, fc="#F6F8F8", ec="white", lw=0.9, zorder=4))
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=GREEN, lw=1.0, zorder=5))


def draw_neural_network(cx, cy, s=56, color=NAVY):
    left = [(cx - s * 0.35, cy - s * 0.22), (cx - s * 0.35, cy + s * 0.22)]
    mid = [(cx, cy - s * 0.34), (cx, cy), (cx, cy + s * 0.34)]
    right = [(cx + s * 0.35, cy - s * 0.20), (cx + s * 0.35, cy + s * 0.20)]
    for a in left:
        for b in mid:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=1.3, zorder=4)
    for a in mid:
        for b in right:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=1.3, zorder=4)
    for p in left + mid + right:
        ax.add_patch(Circle(p, s * 0.064, fc="white", ec=color, lw=2.1, zorder=5))


def draw_trophy(cx, cy, s=56, color="#F4B400"):
    ax.add_patch(
        Rectangle(
            (cx - s * 0.18, cy - s * 0.28),
            s * 0.36,
            s * 0.39,
            fc=color,
            ec=color,
            zorder=4,
        )
    )
    ax.add_patch(
        Arc(
            (cx - s * 0.25, cy - s * 0.12),
            s * 0.38,
            s * 0.38,
            theta1=80,
            theta2=250,
            ec=color,
            lw=3.0,
            zorder=4,
        )
    )
    ax.add_patch(
        Arc(
            (cx + s * 0.25, cy - s * 0.12),
            s * 0.38,
            s * 0.38,
            theta1=-70,
            theta2=100,
            ec=color,
            lw=3.0,
            zorder=4,
        )
    )
    ax.add_patch(
        Rectangle(
            (cx - s * 0.055, cy + s * 0.10),
            s * 0.11,
            s * 0.22,
            fc=color,
            ec=color,
            zorder=4,
        )
    )
    ax.add_patch(
        Rectangle(
            (cx - s * 0.23, cy + s * 0.32),
            s * 0.46,
            s * 0.08,
            fc=color,
            ec=color,
            zorder=4,
        )
    )
    ax.add_patch(
        Rectangle(
            (cx - s * 0.30, cy + s * 0.40),
            s * 0.60,
            s * 0.06,
            fc=GRAY,
            ec=GRAY,
            zorder=4,
        )
    )


def draw_magnifier_check(cx, cy, s=44, color=NAVY):
    ax.add_patch(
        Circle(
            (cx - s * 0.08, cy - s * 0.08),
            s * 0.28,
            fill=False,
            ec=color,
            lw=2.3,
            zorder=4,
        )
    )
    ax.plot(
        [cx + s * 0.12, cx + s * 0.36],
        [cy + s * 0.12, cy + s * 0.36],
        color=color,
        lw=2.3,
        zorder=4,
    )
    ax.plot(
        [cx - s * 0.22, cx - s * 0.08, cx + s * 0.12],
        [cy - s * 0.08, cy + s * 0.08, cy - s * 0.18],
        color=color,
        lw=2.3,
        zorder=5,
    )


def draw_target(cx, cy, s=46, color=GRAY):
    for r in [s * 0.44, s * 0.29, s * 0.14]:
        ax.add_patch(Circle((cx, cy), r, fill=False, ec=color, lw=2.1, zorder=4))
    ax.plot([cx, cx + s * 0.52], [cy, cy - s * 0.52], color=color, lw=2.2, zorder=4)
    ax.plot(
        [cx + s * 0.34, cx + s * 0.52, cx + s * 0.47],
        [cy - s * 0.52, cy - s * 0.52, cy - s * 0.34],
        color=color,
        lw=2.2,
        zorder=4,
    )


# def draw_qr_pattern(x, y, size=56):
#     cell = size / 9.0
#     ax.add_patch(Rectangle((x, y), size, size, fc="white", ec=GRAY, lw=1.2, zorder=5))

#     def finder(ix, iy):
#         ax.add_patch(Rectangle((x + ix * cell, y + iy * cell), cell * 3, cell * 3, fc="black", ec="black", zorder=6))
#         ax.add_patch(Rectangle((x + (ix + 0.55) * cell, y + (iy + 0.55) * cell), cell * 1.9, cell * 1.9, fc="white", ec="white", zorder=7))
#         ax.add_patch(Rectangle((x + (ix + 1.05) * cell, y + (iy + 1.05) * cell), cell * 0.9, cell * 0.9, fc="black", ec="black", zorder=8))

#     finder(0, 0)
#     finder(6, 0)
#     finder(0, 6)
#     dots = [(4, 1), (5, 3), (3, 4), (6, 5), (8, 5), (4, 6), (5, 7), (7, 8), (8, 8), (3, 8)]
#     for i, j in dots:
#         ax.add_patch(Rectangle((x + i * cell, y + j * cell), cell * 0.8, cell * 0.8, fc="black", ec="black", zorder=6))


# def draw_phone_with_qr(x, y, w=90, h=160):
#     rounded_box(x, y, w, h, fc="white", ec=GRAY, lw=3.0, radius=15, z=4)
#     ax.add_patch(Rectangle((x + w * 0.38, y + 9), w * 0.24, 4, fc=GRAY, ec=GRAY, zorder=5))
#     draw_qr_pattern(x + 17, y + 49, size=56)
MID_GRAY = "#2F2F2F"


def draw_qr_code_like(x, y, size=56, color="black", bg="white", z=8):
    """
    Draw a QR-code-like pattern.
    x, y = top-left of QR box.
    """
    n = 21
    cell = size / n

    ax.add_patch(Rectangle((x, y), size, size, fc=bg, ec="none", zorder=z))

    def finder(gx, gy):
        # Outer black square
        ax.add_patch(
            Rectangle(
                (x + gx * cell, y + gy * cell),
                7 * cell,
                7 * cell,
                fc=color,
                ec=color,
                lw=0,
                zorder=z + 1,
            )
        )

        # Inner white square
        ax.add_patch(
            Rectangle(
                (x + (gx + 1) * cell, y + (gy + 1) * cell),
                5 * cell,
                5 * cell,
                fc=bg,
                ec=bg,
                lw=0,
                zorder=z + 2,
            )
        )

        # Center black square
        ax.add_patch(
            Rectangle(
                (x + (gx + 2) * cell, y + (gy + 2) * cell),
                3 * cell,
                3 * cell,
                fc=color,
                ec=color,
                lw=0,
                zorder=z + 3,
            )
        )

    # Three finder patterns
    finder(0, 0)
    finder(14, 0)
    finder(0, 14)

    # Hand-tuned QR-like modules
    modules = [
        (8, 0),
        (9, 0),
        (10, 0),
        (12, 0),
        (8, 1),
        (10, 1),
        (12, 1),
        (8, 2),
        (9, 2),
        (11, 2),
        (12, 2),
        (7, 3),
        (8, 3),
        (10, 3),
        (12, 3),
        (13, 3),
        (8, 4),
        (9, 4),
        (11, 4),
        (8, 5),
        (10, 5),
        (12, 5),
        (7, 6),
        (9, 6),
        (10, 6),
        (12, 6),
        (7, 8),
        (8, 8),
        (10, 8),
        (11, 8),
        (13, 8),
        (6, 9),
        (8, 9),
        (9, 9),
        (12, 9),
        (14, 9),
        (7, 10),
        (10, 10),
        (11, 10),
        (13, 10),
        (8, 11),
        (9, 11),
        (12, 11),
        (13, 11),
        (6, 12),
        (7, 12),
        (10, 12),
        (11, 12),
        (14, 12),
        (8, 13),
        (9, 13),
        (12, 13),
        (14, 14),
        (16, 14),
        (17, 14),
        (19, 14),
        (15, 15),
        (17, 15),
        (18, 15),
        (14, 16),
        (15, 16),
        (17, 16),
        (19, 16),
        (16, 17),
        (18, 17),
        (19, 17),
        (14, 18),
        (16, 18),
        (17, 18),
        (15, 19),
        (17, 19),
        (19, 19),
        (5, 14),
        (7, 14),
        (9, 14),
        (11, 14),
        (6, 15),
        (8, 15),
        (10, 15),
        (12, 15),
        (5, 16),
        (7, 16),
        (9, 16),
        (11, 16),
        (6, 17),
        (8, 17),
        (10, 17),
        (12, 17),
        (5, 18),
        (7, 18),
        (9, 18),
        (11, 18),
        (14, 5),
        (15, 5),
        (17, 5),
        (19, 5),
        (15, 6),
        (16, 6),
        (18, 6),
        (14, 7),
        (17, 7),
        (19, 7),
        (15, 8),
        (16, 8),
        (18, 8),
        (14, 9),
        (17, 9),
        (19, 9),
        (15, 10),
        (18, 10),
        (14, 11),
        (16, 11),
        (17, 11),
        (19, 11),
    ]

    for gx, gy in modules:
        ax.add_patch(
            Rectangle(
                (x + gx * cell, y + gy * cell),
                cell,
                cell,
                fc=color,
                ec=color,
                lw=0,
                zorder=z + 1,
            )
        )


def draw_scan_brackets(x, y, w, h, color="#111111", lw=2.4, z=7):
    """
    Draw four QR scanner corner brackets.
    x, y = top-left of scan area.
    """
    L = min(w, h) * 0.18

    # Top-left
    ax.plot([x, x + L], [y, y], color=color, lw=lw, solid_capstyle="round", zorder=z)
    ax.plot([x, x], [y, y + L], color=color, lw=lw, solid_capstyle="round", zorder=z)

    # Top-right
    ax.plot(
        [x + w - L, x + w], [y, y], color=color, lw=lw, solid_capstyle="round", zorder=z
    )
    ax.plot(
        [x + w, x + w], [y, y + L], color=color, lw=lw, solid_capstyle="round", zorder=z
    )

    # Bottom-left
    ax.plot(
        [x, x + L], [y + h, y + h], color=color, lw=lw, solid_capstyle="round", zorder=z
    )
    ax.plot(
        [x, x], [y + h - L, y + h], color=color, lw=lw, solid_capstyle="round", zorder=z
    )

    # Bottom-right
    ax.plot(
        [x + w - L, x + w],
        [y + h, y + h],
        color=color,
        lw=lw,
        solid_capstyle="round",
        zorder=z,
    )
    ax.plot(
        [x + w, x + w],
        [y + h - L, y + h],
        color=color,
        lw=lw,
        solid_capstyle="round",
        zorder=z,
    )


def draw_phone_with_qr(x, y, w=90, h=170, color="#2F2F2F"):
    """
    Draw a close replica of the uploaded phone + QR scanner icon.

    This function matches your existing call:
        draw_phone_with_qr(905, 590, 90, 170)

    Parameters
    ----------
    x, y : float
        Top-left coordinate of phone.
    w, h : float
        Phone width and height.
    color : str
        Main phone body color.
    """

    # Outer dark phone body
    rounded_box(
        x,
        y,
        w,
        h,
        fc=color,
        ec=color,
        lw=1.4,
        radius=16,
        z=4,
    )

    # Inner white screen
    bezel = w * 0.075
    sx = x + bezel
    sy = y + bezel
    sw = w - 2 * bezel
    sh = h - 2 * bezel

    rounded_box(
        sx,
        sy,
        sw,
        sh,
        fc="white",
        ec="#111111",
        lw=1.0,
        radius=12,
        z=5,
    )

    # Top notch
    notch_w = w * 0.34
    notch_h = h * 0.055
    nx = x + (w - notch_w) / 2
    ny = sy - 1

    rounded_box(
        nx,
        ny,
        notch_w,
        notch_h,
        fc=color,
        ec=color,
        lw=0,
        radius=notch_h * 0.45,
        z=6,
    )

    # Speaker line
    ax.add_patch(
        Rectangle(
            (x + w * 0.43, ny + notch_h * 0.42),
            w * 0.14,
            notch_h * 0.13,
            fc="#555555",
            ec="#555555",
            lw=0,
            zorder=7,
        )
    )

    # Camera dot
    ax.add_patch(
        Circle(
            (x + w * 0.60, ny + notch_h * 0.49),
            radius=w * 0.011,
            fc="#555555",
            ec="#555555",
            lw=0,
            zorder=7,
        )
    )

    # Left side buttons
    ax.add_patch(
        Rectangle(
            (x - w * 0.025, y + h * 0.25),
            w * 0.035,
            h * 0.10,
            fc="#1E1E1E",
            ec="#1E1E1E",
            lw=0,
            zorder=4,
        )
    )

    ax.add_patch(
        Rectangle(
            (x - w * 0.020, y + h * 0.40),
            w * 0.030,
            h * 0.07,
            fc="#1E1E1E",
            ec="#1E1E1E",
            lw=0,
            zorder=4,
        )
    )

    # Scan bracket zone
    bracket_w = sw * 0.72
    bracket_h = sh * 0.46
    bx = x + w / 2 - bracket_w / 2
    by = y + h * 0.35

    draw_scan_brackets(
        bx,
        by,
        bracket_w,
        bracket_h,
        color="#111111",
        lw=2.2,
        z=8,
    )

    # QR code centered inside scan brackets
    qr_size = min(bracket_w, bracket_h) * 0.58
    qx = x + w / 2 - qr_size / 2
    qy = by + bracket_h / 2 - qr_size / 2

    draw_qr_code_like(
        qx,
        qy,
        size=qr_size,
        color="black",
        bg="white",
        z=9,
    )


def draw_server_stack(cx, cy, s=44, color=GRAY):
    for i in range(3):
        yy = cy - s * 0.31 + i * s * 0.22
        rounded_box(
            cx - s * 0.40,
            yy,
            s * 0.80,
            s * 0.15,
            fc="white",
            ec=color,
            lw=1.8,
            radius=3,
            z=4,
        )
        ax.add_patch(
            Circle(
                (cx - s * 0.29, yy + s * 0.075), s * 0.025, fc=color, ec=color, zorder=5
            )
        )


def draw_lightning(cx, cy, s=42, color=NAVY):
    verts = [
        (cx + s * 0.05, cy - s * 0.48),
        (cx - s * 0.20, cy + s * 0.02),
        (cx + s * 0.04, cy + s * 0.02),
        (cx - s * 0.06, cy + s * 0.48),
        (cx + s * 0.27, cy - s * 0.10),
        (cx + s * 0.04, cy - s * 0.10),
    ]
    ax.add_patch(Polygon(verts, closed=True, fc=color, ec=color, zorder=4))


def draw_speech_bubble(cx, cy, s=40, color=NAVY):
    rounded_box(
        cx - s / 2,
        cy - s * 0.35,
        s,
        s * 0.58,
        fc="white",
        ec=color,
        lw=2.0,
        radius=8,
        z=4,
    )
    ax.add_patch(
        Polygon(
            [
                (cx - s * 0.12, cy + s * 0.23),
                (cx + s * 0.04, cy + s * 0.23),
                (cx - s * 0.20, cy + s * 0.40),
            ],
            fc="white",
            ec=color,
            lw=2.0,
            zorder=4,
        )
    )
    for i in [-0.17, 0, 0.17]:
        ax.add_patch(
            Circle((cx + s * i, cy - s * 0.06), s * 0.035, fc=color, ec=color, zorder=5)
        )


def draw_lock(cx, cy, s=34, color=ORANGE):
    ax.add_patch(
        Rectangle(
            (cx - s * 0.28, cy - s * 0.02),
            s * 0.56,
            s * 0.42,
            fc="white",
            ec=color,
            lw=2.0,
            zorder=4,
        )
    )
    ax.add_patch(
        Arc(
            (cx, cy - s * 0.02),
            s * 0.46,
            s * 0.46,
            theta1=180,
            theta2=360,
            ec=color,
            lw=2.3,
            zorder=4,
        )
    )
    ax.add_patch(Circle((cx, cy + s * 0.17), s * 0.035, fc=color, ec=color, zorder=5))


def draw_status_shields(cx, cy, s=28):
    colors = [("#36A852", "#E9F7EC"), ("#F4B400", "#FFF8E1"), ("#D71920", "#FFEEEE")]
    for i, (ec, fill) in enumerate(colors):
        draw_shield(cx + i * s * 0.72, cy, s=s, color=ec, fill=fill, check=True)


def draw_section_frames():
    rounded_box(10, 10, 610, 910, fc="white", ec=PANEL_EDGE, lw=1.0, radius=7, z=0)
    rounded_box(625, 10, 400, 910, fc="white", ec=PANEL_EDGE, lw=1.0, radius=7, z=0)
    rounded_box(1035, 10, 630, 460, fc="white", ec=PANEL_EDGE, lw=1.0, radius=7, z=0)
    rounded_box(1035, 480, 630, 440, fc="white", ec=PANEL_EDGE, lw=1.0, radius=7, z=0)


def draw_section_1():
    rounded_box(20, 80, 235, 220, fc=LIGHT_BLUE, ec=BLUE, lw=1.4, radius=8)
    add_text(137.5, 105, "BENIGN URL SOURCES", size=10, color=BLUE, weight="bold")

    rounded_box(45, 130, 185, 75, fc="white", ec="#C7D3EA", lw=1.0, radius=5)
    draw_globe_search(75, 168, 40, NAVY)
    add_text(115, 162, "Common Crawl", size=8.5, weight="bold", ha="left")
    add_text(115, 184, "(.tr URLs, 2008-2026)", size=7, ha="left")

    rounded_box(45, 215, 185, 70, fc="white", ec="#C7D3EA", lw=1.0, radius=5)
    draw_solid_shield_mark(75, 250, 42, NAVY, mark="plus")
    add_text(110, 243, "Cisco Umbrella", size=9.4, weight="bold", ha="left")
    add_text(110, 264, "Top Domains", size=9.4, weight="bold", ha="left")

    rounded_box(18, 440, 230, 330, fc=LIGHT_RED, ec=RED, lw=1.4, radius=8)
    add_text(
        135.5,
        474,
        "MALICIOUS THREAT-\nINTELLIGENCE SOURCES",
        size=9.8,
        color=RED,
        weight="bold",
    )

    rounded_box(40, 515, 185, 70, fc="white", ec="#E7CACA", lw=1.0, radius=5)
    draw_solid_shield_mark(75, 550, 42, TEXT, mark="star")
    add_text(110, 542, "USOM", size=9.4, weight="bold", ha="left")
    add_text(110, 563, "(anchor source)", size=8.6, ha="left")

    rounded_box(40, 600, 185, 75, fc="white", ec="#E7CACA", lw=1.0, radius=5)
    draw_filled_database(66, 638, 38, NAVY)
    draw_network_nodes(92, 640, 22, NAVY)
    add_text(
        110, 631, "Open threat-\nintelligence feeds", size=7.1, weight="bold", ha="left"
    )

    rounded_box(40, 690, 185, 70, fc="white", ec="#E7CACA", lw=1.0, radius=5)
    draw_biohazard_or_hazard(75, 725, 38, TEXT)
    add_text(110, 709, "Examples:", size=8.8, weight="bold", ha="left")
    add_text(
        110, 733, "PhishTank / OpenPhish /\nURLhaus", size=6.1, weight="bold", ha="left"
    )

    rounded_box(260, 305, 150, 230, fc=LIGHT_GRAY, ec=GRAY, lw=1.4, radius=10)
    draw_gear_database(335, 358, 58, MID_GRAY)
    add_text(
        335,
        432,
        "Source-aware\nlabel harmonization\n+ deduplication +\nURL normalization",
        size=8.1,
        weight="bold",
    )

    rounded_box(
        260, 675, 200, 80, fc="#F9FCFF", ec=MID_BLUE, lw=1.5, radius=8, dashed=True
    )
    draw_shield(300, 715, 40, MID_BLUE, fill="white", check=True)
    add_text(
        325,
        715,
        "Path-preserving\nbenign URLs",
        size=10.2,
        color=BLUE,
        weight="bold",
        ha="left",
    )

    rounded_box(445, 230, 155, 390, fc=LIGHT_PURPLE, ec=PURPLE, lw=1.4, radius=11)
    draw_filled_database(518, 282, 58, DEEP_PURPLE)
    draw_gear(552, 304, 36, DEEP_PURPLE)
    add_text(
        522, 363, "TUMC:\nTurkish URL\nMulti-class Corpus", size=10.0, weight="bold"
    )
    add_text(522, 450, "1,239,308 URLs", size=11.4, color=PURPLE, weight="bold")
    add_text(
        522,
        532,
        "Classes:\nbenign, phishing,\nmalware, scam,\nother-malicious",
        size=9.2,
        weight="bold",
    )

    draw_poly_arrow(
        [(255, 173), (280, 173), (280, 305)], color=BLUE, lw=2.8, mutation=16
    )
    draw_poly_arrow(
        [(255, 630), (280, 630), (280, 535)], color=RED, lw=2.8, mutation=16
    )
    draw_poly_arrow([(410, 416), (445, 416)], color="#253858", lw=4.0, mutation=17)
    draw_poly_arrow(
        [(340, 675), (340, 535)], color=MID_BLUE, lw=2.0, dashed=True, mutation=14
    )


def draw_section_2():
    rounded_box(680, 70, 280, 75, fc="#F6FFF5", ec=GREEN, lw=1.5, radius=8)
    draw_chain_link(724, 110, 48, TEXT)
    add_text(825, 110, "URL parsing\nand tokenization", size=12.0, weight="bold")

    rounded_box(650, 165, 330, 320, fc="none", ec=GREEN, lw=1.6, radius=8, z=1)

    rounded_box(685, 180, 285, 52, fc="#EAF4FF", ec=MID_BLUE, lw=1.5, radius=6)
    draw_Aa_icon(720, 206, 38)
    add_text(
        750, 206, "1. Lexical & structural features", size=8.7, weight="bold", ha="left"
    )

    rounded_box(685, 245, 285, 52, fc="#FFF4E8", ec="#FB8C00", lw=1.5, radius=6)
    draw_spy_hat_glasses(720, 271, 40)
    add_text(
        750, 271, "2. Adversarial / brand features", size=9.1, weight="bold", ha="left"
    )

    rounded_box(685, 310, 285, 65, fc=YELLOW, ec="#F9A825", lw=1.5, radius=6)
    draw_turkish_g_icon(720, 343, 43, "#F39C12")
    add_text(
        750, 329, "3. Turkish linguistic features", size=8.9, weight="bold", ha="left"
    )
    add_text(750, 354, "vowel harmony, suffixes,\nsector keywords", size=7.7, ha="left")

    rounded_box(685, 395, 285, 75, fc=LIGHT_TEAL, ec=TEAL, lw=1.5, radius=6)
    draw_network_nodes(720, 432, 42, NAVY)
    add_text(
        755,
        416,
        "4. Graph-based infrastructure\nfeatures (18)",
        size=8.8,
        weight="bold",
        ha="left",
    )
    add_text(755, 449, "offline token co-occurrence graph", size=7.7, ha="left")

    rounded_box(650, 505, 330, 65, fc=LIGHT_GREEN, ec=MID_GREEN, lw=1.5, radius=8)
    draw_bar_chart(700, 537, 48, GREEN)
    add_text(
        730,
        537,
        "135 URL-only features",
        size=14.0,
        color=GREEN,
        weight="bold",
        ha="left",
    )

    rounded_box(640, 585, 260, 65, fc="white", ec=RED, lw=1.5, radius=8, dashed=True)
    draw_no_entry(680, 618, 42, RED)
    add_text(
        720,
        618,
        "No DNS / WHOIS / HTML /\nlive network queries",
        size=8.7,
        weight="bold",
        ha="left",
    )

    rounded_box(660, 675, 220, 85, fc=YELLOW, ec="#F9A825", lw=1.5, radius=8)
    draw_funnel(692, 724, 42, GRAY)
    add_text(
        720,
        724,
        "Artefact controls:\ndrop is_tr_domain\nand is_https",
        size=9.1,
        weight="bold",
        ha="left",
    )

    rounded_box(650, 805, 300, 70, fc="#F7FFF6", ec=GREEN, lw=1.5, radius=8)
    draw_checklist(689, 840, 44, GREEN)
    add_text(
        730,
        828,
        "Feature selection consensus",
        size=9.0,
        color=GREEN,
        weight="bold",
        ha="left",
    )
    add_text(
        730,
        854,
        "Mutual Information + Tree Gain +\nBoruta + correlation pruning",
        size=7.4,
        ha="left",
    )

    draw_poly_arrow([(600, 416), (648, 416)], color=PURPLE, lw=4.2, mutation=18)

    ax.plot([647, 647], [110, 455], color=GREEN, lw=2.1, zorder=2)
    draw_poly_arrow([(647, 110), (680, 110)], color=GREEN, lw=2.1, mutation=13)
    draw_poly_arrow([(647, 206), (685, 206)], color=GREEN, lw=2.1, mutation=13)
    draw_poly_arrow([(647, 271), (685, 271)], color=GREEN, lw=2.1, mutation=13)
    draw_poly_arrow([(647, 343), (685, 343)], color=GREEN, lw=2.1, mutation=13)
    draw_poly_arrow([(647, 432), (685, 432)], color=GREEN, lw=2.1, mutation=13)

    draw_poly_arrow([(820, 144), (820, 180)], color=GREEN, lw=2.6, mutation=14)
    draw_poly_arrow([(820, 470), (820, 505)], color=GREEN, lw=2.7, mutation=15)

    ax.plot([1000, 1000], [206, 537], color="#8A9700", lw=2.1, zorder=2)
    for yy in [206, 271, 343, 432]:
        draw_poly_arrow([(966, yy), (1000, yy)], color="#8A9700", lw=2.1, mutation=13)
    draw_poly_arrow([(1000, 537), (980, 537)], color="#8A9700", lw=2.1, mutation=13)

    draw_poly_arrow([(820, 570), (820, 585)], color=MID_GREEN, lw=2.3, mutation=13)
    draw_poly_arrow([(820, 650), (820, 675)], color=ORANGE, lw=2.3, mutation=13)
    #This arrow from artefact to feature selection box
    draw_poly_arrow([(775, 760), (775, 805)], color=GREEN, lw=2.3, mutation=13)
    #This arrow from artefact to flutter app
    draw_poly_arrow([(880, 724), (915, 724)], color=MID_GREEN, lw=2.7, mutation=13)


def draw_section_3():
    rounded_box(1050, 70, 215, 105, fc=LIGHT_BLUE, ec=BLUE, lw=1.5, radius=8)
    draw_pie_chart(1092, 123, 56, NAVY)
    add_text(
        1130,
        119,
        "Domain-insulated\n5-fold\ncross-validation",
        size=8.7,
        weight="bold",
        ha="left",
    )

    rounded_box(1320, 70, 310, 110, fc=LIGHT_BLUE, ec=BLUE, lw=1.5, radius=8)
    draw_neural_network(1365, 128, 58, NAVY)
    add_text(1425, 98, "Classifier suite", size=11.7, weight="bold", ha="left")
    add_text(
        1425,
        137,
        "HistGB, XGBoost, LightGBM,\nRF, LR, CNN+BiLSTM,\nTransformer",
        size=9.0,
        ha="left",
    )

    rounded_box(1150, 215, 375, 85, fc=LIGHT_BLUE, ec=BLUE, lw=1.7, radius=8)
    draw_trophy(1195, 257, 58)
    add_text(
        1245,
        242,
        "Selected deployment model:",
        size=11.4,
        color=BLUE,
        weight="bold",
        ha="left",
    )
    add_text(1315, 275, "HistGB", size=20, color=BLUE, weight="bold", ha="left")

    rounded_box(1045, 340, 170, 110, fc=LIGHT_BLUE, ec="#64A5F8", lw=1.2, radius=6)
    draw_magnifier_check(1082, 394, 43, NAVY)
    add_text(1117, 379, "Explainability:", size=8.2, weight="bold", ha="left")
    add_text(1117, 410, "SHAP, LIME,\npermutation\nimportance", size=7.8, ha="left")

    rounded_box(1230, 340, 180, 110, fc=LIGHT_BLUE, ec="#64A5F8", lw=1.2, radius=6)
    draw_shield(1268, 394, 44, GRAY, check=True)
    add_text(1304, 379, "Leakage check:", size=8.2, weight="bold", ha="left")
    add_text(
        1304, 410, "transductive vs\ninductive graph\nevaluation", size=7.8, ha="left"
    )

    rounded_box(1425, 340, 200, 110, fc=LIGHT_BLUE, ec="#64A5F8", lw=1.2, radius=6)
    draw_target(1463, 394, 45, GRAY)
    add_text(1499, 379, "Principal result:", size=8.2, weight="bold", ha="left")
    add_text(
        1499,
        411,
        "5-class macro-F1 =\n0.907 +/- 0.009",
        size=7.9,
        weight="bold",
        ha="left",
    )

    draw_bidirectional_arrow(1265, 123, 1320, 123, color=BLUE, lw=3.0)
    draw_poly_arrow([(1475, 180), (1475, 215)], color=BLUE, lw=3.0, mutation=16)
    draw_poly_arrow(
        [(1338, 300), (1338, 320), (1130, 320), (1130, 340)],
        color=BLUE,
        lw=2.0,
        dashed=True,
        mutation=12,
    )
    draw_poly_arrow(
        [(1338, 300), (1338, 340)], color=BLUE, lw=2.0, dashed=True, mutation=12
    )
    draw_poly_arrow(
        [(1338, 300), (1338, 320), (1515, 320), (1515, 340)],
        color=BLUE,
        lw=2.0,
        dashed=True,
        mutation=12,
    )


def draw_section_4():
    ax.add_patch(Rectangle((1012, 525), 48, 395, fc="white", ec="none", zorder=0.5))
    draw_phone_with_qr(914, 590, 75, 150)
    add_text(950, 770, "Flutter\nmobile app", size=8.5, weight="bold")

    ax.add_patch(Circle((1020, 595), 13, fc=ORANGE, ec=ORANGE, zorder=4))
    add_text(1020, 595, "1", size=12, color="white", weight="bold", z=5)
    add_text(1020, 630, "Scan\nQR code", size=7.8, weight="bold")

    ax.add_patch(Circle((1090, 595), 13, fc=ORANGE, ec=ORANGE, zorder=4))
    add_text(1090, 595, "2", size=12, color="white", weight="bold", z=5)
    add_text(1090, 630, "Decode and\npreview URL", size=7.1, weight="bold")

    ax.plot(
        [990, 1050],
        [680, 680],
        color="#8A8A8A",
        lw=2.0,
        solid_capstyle="round",
        zorder=2,
    )
    ax.plot(
        [1050, 1050],
        [680, 705],
        color="#8A8A8A",
        lw=2.0,
        solid_capstyle="round",
        zorder=2,
    )
    ax.plot(
        [1090, 1090],
        [680, 705],
        color="#9A9A9A",
        lw=2.0,
        solid_capstyle="round",
        zorder=2,
    )
    ax.plot(
        [1090, 1120],
        [680, 680],
        color="#9A9A9A",
        lw=2.0,
        solid_capstyle="round",
        zorder=2,
    )
    draw_lock(1030, 675, 23, "#8A8A8A")
    draw_shield(1110, 680, 13, "#8A8A8A", fill="#FFFCFC", check=True)
    rounded_box(1020, 705, 100, 40, fc="white", ec="#B8B8B8", lw=1.1, radius=6)
    draw_lock(1038, 725, 20, GREEN)
    add_text(1078, 725, "https://ornek-\nbanka.com/giris", size=5.1, ha="center")

    rounded_box(1145, 585, 265, 220, fc=LIGHT_GRAY, ec=GRAY, lw=1.5, radius=8)
    draw_server_stack(1176, 618, 44, GRAY)
    add_text(1210, 618, "REST inference backend", size=10.1, weight="bold", ha="left")

    rounded_box(1160, 650, 75, 110, fc=LIGHT_GREEN, ec=MID_GREEN, lw=1.2, radius=6)
    add_text(1198, 678, "URL-only\nfeature\nextractor", size=7.2, weight="bold")
    draw_gear(1198, 725, 35, GREEN)

    rounded_box(1245, 650, 75, 110, fc="#EEF5FF", ec=BLUE, lw=1.2, radius=6)
    add_text(1283, 678, "HistGB\ninference\n(~3 ms CPU)", size=6.8, color=NAVY, weight="bold" )
    draw_lightning(1283, 725, 38, NAVY)

    rounded_box(1330, 650, 75, 110, fc="#F4EDFF", ec="#7E57C2", lw=1.2, radius=6)
    add_text(
        1368,
        678,
        "Risk decision\n+ explanations",
        size=6.6,
        color="#4A148C",
        weight="bold",
    )
    draw_shield_filled(1368, 725, 38, "#FEFEFF", fill="#7E57C2", check=True)

    rounded_box(1435, 540, 215, 340, fc=LIGHT_ORANGE, ec="#FB8C00", lw=1.5, radius=8)

    rounded_box(1450, 555, 185, 65, fc="white", ec="#F5C16C", lw=1.0, radius=6)
    draw_prediction_pie(1480, 588, 36)
    add_text(
        1513,
        586,
        "Prediction: phishing /\nbenign / malware /\nscam / other-malicious",
        size=7.0,
        weight="bold",
        ha="left",
    )

    rounded_box(1450, 630, 185, 45, fc="white", ec="#F5C16C", lw=1.0, radius=6)
    draw_bar_chart(1480, 652, 34, GREEN)
    add_text(1518, 652, "Class probabilities", size=8.2, weight="bold", ha="left")

    rounded_box(1450, 685, 185, 55, fc="white", ec="#F5C16C", lw=1.0, radius=6)
    draw_magnifier_check(1480, 713, 34, NAVY)
    add_text(
        1518, 713, "Top feature-group\nexplanation", size=8.0, weight="bold", ha="left"
    )

    rounded_box(1450, 750, 185, 55, fc="white", ec="#F5C16C", lw=1.0, radius=6)
    draw_speech_bubble(1480, 778, 34, NAVY)
    add_text(
        1518, 778, "Bilingual warning\n(TR / EN)", size=8.0, weight="bold", ha="left"
    )

    rounded_box(1450, 815, 185, 55, fc="white", ec="#F5C16C", lw=1.0, radius=6)
    draw_status_shields(1473, 843, 25)
    add_text(
        1536, 843, "Safe to open /\nWarn / Block", size=7.6, weight="bold", ha="left"
    )

    rounded_box(985, 850, 425, 45, fc="white", ec=ORANGE, lw=1.5, radius=8, dashed=True)
    draw_lock(1014, 872, 31, ORANGE)
    add_text(
        1210,
        872,
        "Privacy-preserving: only decoded URL is analyzed",
        size=9.6,
        color=TEXT,
    )
    # this arrow from ornek to inference backend
    draw_poly_arrow([(1115, 680), (1145, 680)], color=ORANGE, lw=2.0, mutation=12)
    
    draw_poly_arrow([(1235, 705), (1245, 705)], color=GRAY, lw=2.0, mutation=12)
    draw_poly_arrow([(1320, 705), (1330, 705)], color=GRAY, lw=2.0, mutation=12)
    draw_poly_arrow([(1405, 705), (1435, 705)], color=ORANGE, lw=4.0, mutation=17)
    ax.plot(
        [1278, 1278], [805, 850], color=ORANGE, lw=1.7, linestyle=(0, (5, 4)), zorder=2  )


def write_supporting_files():
    drawio = """<mxfile host="app.diagrams.net">
  <diagram name="TurkQuish Proposed System Architecture">
    <mxGraphModel dx="1672" dy="941" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1672" pageHeight="941">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="s1" value="1 Dataset Construction" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#0B56C6;" vertex="1" parent="1"><mxGeometry x="10" y="10" width="610" height="910" as="geometry"/></mxCell>
        <mxCell id="s2" value="2 URL-only Feature Pipeline" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#176B1A;" vertex="1" parent="1"><mxGeometry x="625" y="10" width="400" height="910" as="geometry"/></mxCell>
        <mxCell id="s3" value="3 Model Training, Evaluation and Explainability" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#0B56C6;" vertex="1" parent="1"><mxGeometry x="1035" y="10" width="630" height="460" as="geometry"/></mxCell>
        <mxCell id="s4" value="4 Operational Deployment Prototype" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#D95500;" vertex="1" parent="1"><mxGeometry x="1035" y="480" width="630" height="440" as="geometry"/></mxCell>
        <mxCell id="sources" value="Benign and malicious URL sources" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="20" y="80" width="235" height="680" as="geometry"/></mxCell>
        <mxCell id="prep" value="Source-aware label harmonization + deduplication + URL normalization" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="260" y="305" width="150" height="230" as="geometry"/></mxCell>
        <mxCell id="tumc" value="TUMC: Turkish URL Multi-class Corpus" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8eefa;strokeColor=#6A1B9A;" vertex="1" parent="1"><mxGeometry x="445" y="230" width="155" height="390" as="geometry"/></mxCell>
        <mxCell id="features" value="URL parsing, tokenization and 135 URL-only features" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eef8ec;strokeColor=#176B1A;" vertex="1" parent="1"><mxGeometry x="650" y="70" width="340" height="805" as="geometry"/></mxCell>
        <mxCell id="model" value="Domain-insulated validation, classifier suite, selected HistGB model" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eef7ff;strokeColor=#0B56C6;" vertex="1" parent="1"><mxGeometry x="1045" y="70" width="585" height="380" as="geometry"/></mxCell>
        <mxCell id="deploy" value="Flutter app, REST inference backend, explanations and safe/warn/block output" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#D95500;" vertex="1" parent="1"><mxGeometry x="905" y="540" width="745" height="340" as="geometry"/></mxCell>
        <mxCell id="e1" edge="1" parent="1" source="sources" target="prep" style="endArrow=block;html=1;rounded=1;strokeColor=#0B56C6;"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e2" edge="1" parent="1" source="prep" target="tumc" style="endArrow=block;html=1;rounded=1;strokeColor=#253858;"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e3" edge="1" parent="1" source="tumc" target="features" style="endArrow=block;html=1;rounded=1;strokeColor=#6A1B9A;"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e4" edge="1" parent="1" source="features" target="deploy" style="endArrow=block;html=1;rounded=1;strokeColor=#4A8B2C;"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e5" edge="1" parent="1" source="model" target="deploy" style="endArrow=block;html=1;rounded=1;strokeColor=#0B56C6;"><mxGeometry relative="1" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
  T --> U
  A --> Phone
  H --> Backend
"""
    readme = """# Diagram Generation

Run this script from the diagrams directory:

```bash
python proposed_system_architecture.py
```

It generates:

- turkquish_proposed_system_architecture_final.png
- turkquish_proposed_system_architecture_final.svg
- turkquish_proposed_system_architecture_final.pdf
- turkquish_proposed_system_architecture.drawio

The Matplotlib figure uses a fixed 1672 x 941 coordinate canvas and normal savefig calls.
It avoids automatic layout tightening and tight bounding-box export, preserving the reference aspect ratio and coordinate design.
"""
    with open("turkquish_proposed_system_architecture_final.png", "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("ascii")
    drawio = f"""<mxfile host="app.diagrams.net">
  <diagram name="TurkQuish Proposed System Architecture">
    <mxGraphModel dx="{W}" dy="{H}" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" background="#ffffff">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="diagram-image" value="" style="shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;aspect=fixed;image=data:image/png,{image_b64};" vertex="1" parent="1">
          <mxGeometry x="0" y="0" width="{W}" height="{H}" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    with open(
        "turkquish_proposed_system_architecture.drawio", "w", encoding="utf-8"
    ) as f:
        f.write(drawio)
    with open("README_DIAGRAM_GENERATION.md", "w", encoding="utf-8") as f:
        f.write(readme)

def main():
    draw_section_frames()
    draw_header(10, 10, 610, 44, 1, "DATASET CONSTRUCTION", NAVY, 16)
    draw_header(625, 10, 400, 44, 2, "URL-ONLY FEATURE PIPELINE", GREEN, 13.4)
    draw_header(
        1035, 10, 630, 44, 3, "MODEL TRAINING, EVALUATION & EXPLAINABILITY", NAVY, 13.4
    )
    draw_header(1035, 480, 630, 44, 4, "OPERATIONAL DEPLOYMENT PROTOTYPE", ORANGE, 13.4)

    draw_section_1()
    draw_section_2()
    draw_section_3()
    draw_section_4()

    plt.savefig("turkquish_proposed_system_architecture_final.png", dpi=300)
    plt.savefig("turkquish_proposed_system_architecture_final.svg")
    plt.savefig("turkquish_proposed_system_architecture_final.pdf")
    plt.close(fig)
    write_supporting_files()

    print("Saved:")
    print(" - turkquish_proposed_system_architecture_final.png")
    print(" - turkquish_proposed_system_architecture_final.svg")
    print(" - turkquish_proposed_system_architecture_final.pdf")
    print(" - turkquish_proposed_system_architecture.drawio")
    print(" - README_DIAGRAM_GENERATION.md")


if __name__ == "__main__":
    main()
