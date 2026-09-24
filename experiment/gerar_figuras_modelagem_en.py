from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon


BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR
OUT_DIR.mkdir(exist_ok=True)


def save_text_figure(filename, lines, height=2.2, fontsize=18):
    fig = plt.figure(figsize=(12, height), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(
        0.5,
        0.5,
        "\n".join(lines),
        ha="center",
        va="center",
        fontsize=fontsize,
        family="DejaVu Serif",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F6F6F6", edgecolor="#666666"),
    )
    fig.savefig(OUT_DIR / filename, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def style_axes(ax, xlim=(0, 100), ylim=(0, 100), xlabel="", ylabel=""):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.tick_params(labelsize=11)
    ax.grid(True, alpha=0.25, linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save_geometry_feasible_region():
    fig, ax = plt.subplots(figsize=(8.5, 6), dpi=200)
    style_axes(
        ax,
        xlabel="x = wagons allocated to PM1",
        ylabel="y = wagons allocated to PM2",
    )

    feasible_segment = [(20, 80), (60, 40)]
    polygon = Polygon([(0, 0), (20, 80), (60, 40), (0, 40)], closed=True, facecolor="#d9ead3", alpha=0.6)
    ax.add_patch(polygon)

    ax.axvline(60, color="#c00000", linestyle="--", linewidth=1.8, label="Capacidade de PM1: x <= 60")
    ax.axhline(80, color="#1f4e79", linestyle="--", linewidth=1.8, label="Capacidade de PM2: y <= 80")
    ax.plot([0, 100], [100, 0], color="#3d3d3d", linewidth=2.2, label="Demanda: x + y = 100")
    ax.plot([20, 60], [80, 40], color="#2f6b2f", linewidth=4, label="Trecho viável da solução")
    ax.scatter([20, 60], [80, 40], color="#2f6b2f", s=45, zorder=5)
    ax.annotate("A", (20, 80), textcoords="offset points", xytext=(5, 8), fontsize=11, weight="bold")
    ax.annotate("B", (60, 40), textcoords="offset points", xytext=(5, 8), fontsize=11, weight="bold")
    ax.text(8, 87, "Região factível\nsimplificada", fontsize=10, color="#2f6b2f")
    ax.legend(loc="lower left", fontsize=9, frameon=False)
    ax.text(6, 4, "x >= 0; y >= 0", fontsize=10, color="#444444")
    ax.set_title("Ilustração geométrica da região viável em duas variáveis", fontsize=13)
    fig.savefig(OUT_DIR / "figura_02_regiao_viavel_2d.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def save_geometry_objective():
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    style_axes(
        ax,
        xlabel="x = wagons allocated to PM1",
        ylabel="y = wagons allocated to PM2",
    )

    ax.axvline(60, color="#c00000", linestyle="--", linewidth=1.6, label="PM1 capacity: x <= 60")
    ax.axhline(80, color="#1f4e79", linestyle="--", linewidth=1.6, label="PM2 capacity: y <= 80")
    ax.plot([0, 100], [100, 0], color="#3d3d3d", linewidth=2.2, label="Demand: x + y = 100")
    ax.plot([20, 60], [80, 40], color="#2f6b2f", linewidth=4, label="Feasible allocation segment")
    ax.text(5, 3, "x >= 0; y >= 0", fontsize=11, color="#444444")

    # Isocost lines for Z = 80x + 100y
    for cost, color in [(9600, "#8e7cc3"), (9200, "#6fa8dc"), (8800, "#f6b26b")]:
        x_vals = [0, cost / 80]
        y_vals = [cost / 100, 0]
        ax.plot(x_vals, y_vals, color=color, linewidth=1.8, linestyle="-.")

    optimum = (60, 40)
    ax.scatter([optimum[0]], [optimum[1]], color="#cc0000", s=70, zorder=6)
    ax.annotate(
        "Optimal point",
        optimum,
        textcoords="offset points",
        xytext=(-78, -2),
        fontsize=12,
        color="#cc0000",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
    )
    ax.text(67, 49, "Isocost lines move downward\nuntil touching the feasible set", fontsize=11)
    ax.text(5, 8, "One-period illustration; backlog fixed at zero", fontsize=10.5, color="#555555")
    ax.legend(loc="upper right", fontsize=9.5, frameon=False)
    ax.set_title("Isocost movement toward the optimal allocation", fontsize=15)
    fig.savefig(OUT_DIR / "figure_03_isocost_optimum_2d.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def save_geometry_integer_points():
    fig, ax = plt.subplots(figsize=(8.5, 6), dpi=200)
    style_axes(
        ax,
        xlabel="x = vagões alocados ao posto PM1",
        ylabel="y = vagões alocados ao posto PM2",
    )

    ax.plot([0, 100], [100, 0], color="#3d3d3d", linewidth=2.0, label="x + y = 100")
    ax.axvline(60, color="#c00000", linestyle="--", linewidth=1.6, label="x <= 60")
    ax.axhline(80, color="#1f4e79", linestyle="--", linewidth=1.6, label="y <= 80")

    feasible_x = list(range(20, 61, 5))
    feasible_y = [100 - x for x in feasible_x]
    ax.scatter(feasible_x, feasible_y, color="#2f6b2f", s=35, label="Soluções inteiras factíveis")

    best = (60, 40)
    ax.scatter([best[0]], [best[1]], color="#cc0000", s=85, zorder=6, label="Melhor vértice inteiro")
    ax.annotate(
        "Melhor alocação\nentre os pontos factíveis",
        best,
        textcoords="offset points",
        xytext=(-85, -30),
        fontsize=10,
        color="#cc0000",
    )
    ax.text(12, 58, "No problema real, a lógica é a mesma,\nmas com muitas variáveis e restrições.", fontsize=10)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    ax.set_title("Leitura didática da otimização inteira por vértices factíveis", fontsize=13)
    fig.savefig(OUT_DIR / "figura_04_solucao_inteira_2d.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    save_geometry_objective()

    print(f"Figure generated in: {OUT_DIR}")


if __name__ == "__main__":
    main()
