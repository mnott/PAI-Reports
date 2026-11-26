"""Figures of lab report 6. Data are copied from the bench result file (paper6-data.md,
one JSON per run) and the loop-guard counts quoted in the text. Run: python3 make_figures.py"""
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



# ---- 1 pass rate per set (grouped bars), from tab:sets and tab:rerun ----
SETS = ["short\n(20)", "easy\n(40)", "hard\n(40)", "real\n(5)"]
NS = [20, 40, 40, 5]
RUNS = [("Gyro-S v2, alone", ORANGE, [8, 37, 8, 3]),
        ("Gyro-S v2, author's PLE", "#f2a65c", [15, 37, 33, 4]),
        ("Gyro-S v2, dual", "#9ecbf5", [15, 35, 32, 2]),
        ("Signal 2, alone", BLUE, [16, 38, 33, 5]),
        ("Signal 2, dual", "#1b4f8f", [17, 39, 30, 4])]
fig, ax = plt.subplots(figsize=(7.4, 3.9))
w = 0.15
for j, (name, c, passed) in enumerate(RUNS):
    xs = [i + (j - 2) * w for i in range(4)]
    vals = [100 * p / n for p, n in zip(passed, NS)]
    ax.bar(xs, vals, width=w, color=c, label=name)
    for x, v, p in zip(xs, vals, passed):
        ax.text(x, v + 2.5, str(p), ha="center", va="bottom", fontsize=7, color=INK, rotation=90)
ax.set_xticks(range(4))
ax.set_xticklabels(SETS)
ax.set_ylim(0, 125)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel("share of tasks passed (%)")
legend = ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=5)
for handle in legend.get_patches():
    handle.set_height(0.6)
clean(ax, "y")
ax.set_title("Pass rate per set: Gyro-S v2 and Signal 2, alone and in parallel",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout(rect=(0, 0.18, 1, 1))
fig.savefig("fig-pass-rate.pdf")
plt.close(fig)

# ---- 2 real tasks: pass/fail and seconds per task, four runs ----
TASKS = ["prune-dist-\nrerun\n(confounded)", "mirror-sync-\ntoken", "worker-\npriority",
         "session-move-\nselectors", "escalate-\nloopstop"]
REAL = [("Gyro-S v2, alone", ORANGE, [(0, 499), (1, 235), (0, 93), (1, 176), (1, 400)]),
        ("Gyro-S v2, author's PLE", "#f2a65c", [(0, 140), (1, 571), (1, 1651), (1, 386), (1, 596)]),
        ("Gyro-S v2, dual", "#9ecbf5", [(0, 186), (1, 345), (0, 280), (0, 110), (1, 951)]),
        ("Signal 2, alone", BLUE, [(1, 1235), (1, 247), (1, 1434), (1, 781), (1, 298)]),
        ("Signal 2, dual", "#1b4f8f", [(0, 2177), (1, 710), (1, 1073), (1, 649), (1, 279)])]
fig, ax = plt.subplots(figsize=(7.4, 4.3))
w = 0.15
for j, (name, c, rows) in enumerate(REAL):
    xs = [i + (j - 2) * w for i in range(5)]
    for x, (ok, s) in zip(xs, rows):
        ax.bar(x, s / 60, width=w, color=c if ok else BG, edgecolor=c, linewidth=1.4)
        ax.text(x, s / 60 + 2.5, "P" if ok else "F", ha="center", va="bottom", fontsize=7,
                color=INK if ok else c, fontweight="bold")
ax.set_xticks(range(5))
ax.set_xticklabels(TASKS)
ax.set_ylim(0, 42)
ax.set_ylabel("minutes for the task (less is better)")
legend = ax.legend(handles=[Patch(color=c, label=name) for name, c, _ in REAL] +
                   [Patch(facecolor=BG, edgecolor=INK, linewidth=1.4, label="fail: hollow bar"),
                    Patch(color=INK, label="pass: filled bar")],
                   frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3)
for handle in legend.get_patches():
    handle.set_height(0.6)
clean(ax, "y")
ax.set_title("Real tasks per run: pass (P, filled) or fail (F, hollow), bar height is wall time",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout(rect=(0, 0.14, 1, 1))
fig.savefig("fig-real-tasks.pdf")
plt.close(fig)

# ---- 3 effort at stop: turns and tokens of a hard run (own axes), plus guard firings ----
fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.9), gridspec_kw={"width_ratios": [0.85, 0.85, 1.1]})
effort = [("turns", 13, 46, "turns"), ("output tokens", 3.8, 14.0, "k tok")]
for ax, (label, g, s, unit) in zip(axes[:2], effort):
    ax.barh(1, g, height=0.5, color=ORANGE)
    ax.barh(0, s, height=0.5, color=BLUE)
    ax.text(g + 0.6, 1, f"{g}", va="center", fontsize=8, color=INK)
    ax.text(s + 0.6, 0, f"{s}", va="center", fontsize=8, color=INK)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Signal 2", "Gyro-S v2"])
    ax.set_xlim(0, max(g, s) * 1.35)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    clean(ax)
    ax.set_title(f"{label} ({unit})", loc="left", color=INK, fontsize=9, fontweight="bold")

ax = axes[2]
guards = [("announced-no-action, solo", 7, ORANGE), ("announced-no-action, dual", 6, "#9ecbf5"),
          ("identical-write, dual", 14, ORANGE)]
for i, (label, v, c) in enumerate(guards[::-1]):
    ax.barh(i, v, height=0.55, color=c)
    ax.text(v + 0.3, i, str(v), va="center", fontsize=8, color=INK)
ax.set_yticks(range(3))
ax.set_yticklabels([g[0] for g in guards[::-1]])
ax.set_xlim(0, 17)
ax.set_xlabel("guard firings")
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
clean(ax)
ax.set_title("Loop-guard firings of Gyro-S v2", loc="left", color=INK, fontsize=9, fontweight="bold")
fig.text(0.01, 0.01, "Announced-no-action: the model announces a step and ends the turn without doing it;\nidentical-write: the same file content rewritten unchanged.",
         color=INK2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.09, 1, 1))
fig.savefig("fig-effort-guards.pdf")
plt.close(fig)

# ---- 4 instrument faults: real tasks passed out of 5, faulty run vs corrected ----
fig, ax = plt.subplots(figsize=(7.0, 2.9))
faults = [("Gyro-S v2 alone\n(disabled provider logged as done)", 0, "0/5", 3, "3/5"),
          ("code-graph OFF arm\n(task rewrote the bench config)", 3, "3/5", 5, "5/5")]
for i, (label, reported, rep_txt, corrected, corr_txt) in enumerate(faults[::-1]):
    ax.barh(i + 0.2, reported, height=0.34, color=ORANGE)
    ax.text(reported + 0.15, i + 0.2, rep_txt, va="center", fontsize=7.5, color=INK)
    ax.barh(i - 0.2, corrected, height=0.34, color=BLUE)
    ax.text(corrected + 0.15, i - 0.2, corr_txt, va="center", fontsize=7.5, color=INK)
ax.set_yticks([0, 1])
ax.set_yticklabels(["code-graph OFF\n(after rerun)", "Gyro-S v2 alone\n(after fix)"])
ax.set_xlim(0, 6)
ax.set_xticks(range(6))
ax.set_xlabel("real tasks passed out of 5")
ax.legend(handles=[Patch(color=ORANGE, label="what the faulty run reported"),
                   Patch(color=BLUE, label="the corrected result")],
          frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(-0.02, 1.02), ncol=2)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
clean(ax)
ax.set_title("Two instrument faults: the verdict they would have produced", loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.text(0.01, 0.01, "Faulty runs refused every start in 1 s and logged them as done with 0 passes; both were found and fixed.",
         color=INK2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.045, 1, 1))
fig.savefig("fig-instrument-faults.pdf")
plt.close(fig)

# ---- 5 head-to-head pass rates: six runs of the night (tab:h2h), from h2h-data.md ----
H2H = ["short\n(20)", "easy\n(40)", "hard\n(40)", "real\n(5)"]
HN = [20, 40, 40, 5]
# None = series not usable (phase D real: watchdog fault, recovered outcomes only)
H2H_RUNS = [("A: Signal 2, single", BLUE, [16, 39, 37, 4]),
            ("B: Gyro-S v2, single", ORANGE, [2, 39, 11, 3]),
            ("C: Signal 2, inst. 1", "#5b9bd8", [16, 37, 31, 3]),
            ("C: Signal 2, inst. 2", "#9ecbf5", [18, 39, 32, None]),
            ("D: Gyro-S v2, inst. 1", "#f2a65c", [15, 38, 35, None]),
            ("D: Gyro-S v2, inst. 2", "#f8c98f", [17, 36, 27, None])]
fig, ax = plt.subplots(figsize=(7.4, 4.0))
w = 0.13
for j, (name, c, passed) in enumerate(H2H_RUNS):
    xs = [i + (j - 2.5) * w for i in range(4)]
    vals = [None if p is None else 100 * p / n for p, n in zip(passed, HN)]
    for x, v, p in zip(xs, vals, passed):
        if v is None:
            ax.text(x, 3, "fault", ha="center", va="bottom", fontsize=6.5, color=INK2)
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
fig.text(0.01, 0.01, "'fault' = phase D real series stopped by the watchdog; outcomes recovered per task (Sec. of the paper).",
         color=INK2, fontsize=7)
fig.tight_layout(rect=(0, 0.16, 1, 1))
fig.savefig("fig-h2h-pass.pdf")
plt.close(fig)

# ---- 6 memory per instance: footprint vs resident size, idle and under load (tab:h2h-mem) ----
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

# ---- 7 hard-set spread per model across all runs of the report ----
SPREAD = [("Gyro-S v2", ORANGE,
           [("wrong PLE table, solo", 8), ("wrong table, dual (cap 6)", 32),
            ("author's table, rerun", 33), ("h2h single", 11), ("h2h double A", 35), ("h2h double B", 27)]),
          ("Signal 2", BLUE,
           [("ref loop-stopped", 33), ("dual 0.2.21", 30), ("h2h single", 37),
            ("h2h double A", 31), ("h2h double B", 32)])]
fig, ax = plt.subplots(figsize=(7.4, 3.4))
for i, (name, c, pts) in enumerate(SPREAD[::-1]):
    ys = [len(pts) - 1 - k for k in range(len(pts))]
    ax.scatter([v for _, v in pts], ys, s=52, color=c, zorder=3)
    for v, y in zip([p[1] for p in pts], ys):
        ax.text(v + 1.2, y, str(v), va="center", fontsize=7.5, color=INK)
ax.set_yticks(range(len(SPREAD[0][2]) + len(SPREAD[1][2])))
ax.set_yticklabels([p[0] for p in SPREAD[1][2]] + [p[0] for p in SPREAD[0][2]])
ax.set_xlim(0, 44)
ax.set_xticks(range(0, 45, 10))
ax.set_xlabel("hard tasks passed out of 40")
ax.legend(handles=[Patch(color=c, label=name) for name, c, _ in SPREAD],
          frameon=False, fontsize=7.5, loc="upper right", bbox_to_anchor=(1.02, 1.03))
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
clean(ax)
ax.set_title("Hard-set score per run: Gyro-S v2 swings (8-35/40),\nSignal 2 stays in a band (30-37)",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout()
fig.savefig("fig-h2h-spread.pdf")
plt.close(fig)
print("ok")
