"""Figures of lab report 6. Data are copied from the bench result file (paper6-data.md,
one JSON per run) and h2h-data.md. Run: python3 make_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

INK, INK2, GRID, BG = "#1a1a19", "#6b6a63", "#e6e5e0", "#ffffff"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "figure.facecolor": BG,
                     "font.family": "sans-serif"})


def clean(ax, grid="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


# ---- 1 head-to-head pass rates: six runs of the night (tab:h2h), from h2h-data.md ----
H2H = ["short\n(20)", "easy\n(40)", "hard\n(40)", "real\n(5)"]
HN = [20, 40, 40, 5]
# None = series not usable (phase D real: watchdog fault, recovered outcomes only)
H2H_RUNS = [("A: Signal 2, single", BLUE, [16, 39, 37, 4]),
            ("B: Gyro-S v2, single", ORANGE, [2, 39, 11, 3]),
            ("C: Signal 2, inst. 1", "#5b9bd8", [16, 37, 31, 3]),
            ("C: Signal 2, inst. 2", "#9ecbf5", [18, 39, 32, 4]),
            ("D: Gyro-S v2, inst. 1", "#f2a65c", [15, 38, 35, None]),
            ("D: Gyro-S v2, inst. 2", "#f8c98f", [17, 36, 27, None])]
fig, ax = plt.subplots(figsize=(7.4, 4.0))
w = 0.13
for j, (name, c, passed) in enumerate(H2H_RUNS):
    xs = [i + (j - 2.5) * w for i in range(4)]
    vals = [None if p is None else 100 * p / n for p, n in zip(passed, HN)]
    for x, v, p in zip(xs, vals, passed):
        if v is None:
            # phase D real: watchdog-stopped; hatched empty bar marks it (annotation once, below)
            ax.bar(x, 0, width=w, color=BG, edgecolor=c, linewidth=1.4, hatch="//")
            continue
        ax.bar(x, v, width=w, color=c, label=name if j == 0 else None)
        ax.text(x, v + 2.5, str(p), ha="center", va="bottom", fontsize=6.5, color=INK, rotation=90)
ax.set_xticks(range(4))
ax.set_xticklabels(H2H)
ax.set_ylim(0, 125)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel("share of tasks passed (%)")
legend = ax.legend(handles=[Patch(color=c, label=name) for name, c, _ in H2H_RUNS],
                   frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3)
for handle in legend.get_patches():
    handle.set_height(0.6)
clean(ax, "y")
ax.set_title("Head-to-head: pass rate per set for the six runs of 25/26 November",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.text(0.5, 0.045, "D: incomplete (watchdog)", ha="center", va="bottom",
         color=INK2, fontsize=7.5, fontweight="bold")
fig.tight_layout(rect=(0, 0.16, 1, 1))
fig.savefig("fig-h2h-pass.pdf")
plt.close(fig)

# ---- 2 memory per instance: footprint vs resident size, idle and under load (tab:h2h-mem) ----
MEM = [("S2 single", BLUE, 28, 27, 9.0, 7.5),
       ("G2 single", ORANGE, 16, 23, 36.6, 43.4),
       ("S2 double 1", "#5b9bd8", 18, 17, 34.0, 34.0),
       ("G2 double 1", "#f2a65c", 16, 22, 33.2, 39.2),
       ("S2 double 2", "#9ecbf5", 17, 25, 35.8, 43.4),
       ("G2 double 2", "#f8c98f", 16, 22, 36.0, 42.9)]
fig, ax = plt.subplots(figsize=(7.4, 3.6))
w = 0.115
for j, (name, c, fp_i, fp_l, rs_i, rs_l) in enumerate(MEM):
    base = [i + (j - 2.5) * w for i in range(4)]
    vals = [fp_i, rs_i, fp_l, rs_l]
    labels = ["FP idle", "RS idle", "FP load", "RS load"]
    for x, v, lab in zip(base, vals, labels):
        hollow = lab.startswith("RS")
        ax.bar(x, v, width=w, color=(BG if hollow else c), edgecolor=c, linewidth=1.4)
        ax.text(x, v + 0.8, str(v), ha="center", va="bottom", fontsize=6.5, color=INK)
ax.set_xticks([i for i in range(4)])
ax.set_xticklabels(["footprint\nidle", "resident\nidle", "footprint\nload", "resident\nload"])
ax.set_ylim(0, 52)
ax.set_ylabel("GiB")
legend = ax.legend(handles=[Patch(color=c, label=name) for name, c, *_ in MEM] +
                   [Patch(facecolor=BG, edgecolor=INK, linewidth=1.4, label="resident (hollow): incl. mapped file pages"),
                    Patch(facecolor=INK, label="footprint (solid): held memory")],
                   frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3)
for handle in legend.get_patches():
    handle.set_height(0.6)
clean(ax, "y")
ax.set_title("Memory per instance: footprint vs resident size, at idle and under load",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout(rect=(0, 0.14, 1, 1))
fig.savefig("fig-h2h-memory.pdf")
plt.close(fig)

# ---- 3 run-to-run spread: hard set (left) and short set (right), per model, one dot per run ----
HARD_ROWS = [
    ("h2h double B", "Gyro-S v2", 27),
    ("h2h double A", "Gyro-S v2", 35),
    ("h2h single", "Gyro-S v2", 11),
    ("author's table, rerun", "Gyro-S v2", 33),
    ("author's table, cap 2 (rerun)", "Gyro-S v2", 30),
    ("wrong table, dual (cap 6)", "Gyro-S v2", 32),
    ("wrong table, solo", "Gyro-S v2", 8),
    ("h2h double B", "Signal 2", 32),
    ("h2h double A", "Signal 2", 31),
    ("h2h single", "Signal 2", 37),
    ("dual 0.2.21", "Signal 2", 30),
    ("reference run", "Signal 2", 33),
]
SHORT_ROWS = [
    ("h2h double B", "Gyro-S v2", 17),
    ("h2h double A", "Gyro-S v2", 15),
    ("h2h single", "Gyro-S v2", 2),
    ("author's table, rerun", "Gyro-S v2", 15),
    ("wrong table, dual (cap 6)", "Gyro-S v2", 15),
    ("wrong table, solo", "Gyro-S v2", 8),
    ("h2h double B", "Signal 2", 18),
    ("h2h double A", "Signal 2", 16),
    ("h2h single", "Signal 2", 16),
    ("dual 0.2.21", "Signal 2", 17),
    ("reference run", "Signal 2", 16),
]
MODEL_COLOR = {"Gyro-S v2": ORANGE, "Signal 2": BLUE}


def spread_panel(ax, rows, n, xlabel):
    for y, (label, model, v) in enumerate(rows):
        ax.scatter(v, y, s=52, color=MODEL_COLOR[model], zorder=3)
        ax.text(v + 1.2, y, str(v), va="center", fontsize=7.5, color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{label}  ({m})" for label, m, _ in rows], fontsize=7.5)
    ax.set_xlim(0, n + 4)
    ax.set_xticks(range(0, n + 1, 10))
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    clean(ax)


fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})
spread_panel(axes[0], HARD_ROWS, 40, "hard tasks passed out of 40")
axes[0].set_title("Hard set: Gyro-S v2 swings (8-35/40),\nSignal 2 stays in a band (30-37)",
                  loc="left", color=INK, fontsize=9.5, fontweight="bold")
spread_panel(axes[1], SHORT_ROWS, 20, "short questions passed out of 20")
axes[1].set_title("Short set: Gyro-S v2 swings (2-17/20),\nSignal 2 stays in a band (16-18)",
                  loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.legend(handles=[Patch(color=c, label=m) for m, c in MODEL_COLOR.items()],
           frameon=False, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, -0.01), ncol=2)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig("fig-h2h-spread.pdf")
plt.close(fig)

print("ok")
