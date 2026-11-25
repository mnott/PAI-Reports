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
fig, ax = plt.subplots(figsize=(7.4, 3.4))
w = 0.15
for j, (name, c, passed) in enumerate(RUNS):
    xs = [i + (j - 2) * w for i in range(4)]
    vals = [100 * p / n for p, n in zip(passed, NS)]
    ax.bar(xs, vals, width=w, color=c, label=name)
    for x, v, p, n in zip(xs, vals, passed, NS):
        ax.text(x, v + 2.5, f"{p}/{n}", ha="center", fontsize=7, color=INK)
ax.set_xticks(range(4))
ax.set_xticklabels(SETS)
ax.set_ylim(0, 112)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel("share of tasks passed (%)")
ax.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(-0.02, 1.02), ncol=3)
clean(ax, "y")
ax.set_title("Pass rate per set: Gyro-S v2 and Signal 2, alone and in parallel",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.text(0.01, 0.01, "One run per bar. Orange shades are Gyro-S v2 (light orange = rerun with the model author's IQ4_NL PLE table); blue shades are Signal 2. Lighter blue = dual run (two servers on one machine).",
         color=INK2, fontsize=7)
fig.tight_layout(rect=(0, 0.05, 1, 1))
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
fig, ax = plt.subplots(figsize=(7.4, 3.8))
w = 0.15
for j, (name, c, rows) in enumerate(REAL):
    xs = [i + (j - 2) * w for i in range(5)]
    for x, (ok, s) in zip(xs, rows):
        ax.bar(x, s / 60, width=w, color=c if ok else BG, edgecolor=c, linewidth=1.4)
        ax.text(x, s / 60 + 2.5, "P" if ok else "F", ha="center", fontsize=7,
                color=INK if ok else c, fontweight="bold")
ax.set_xticks(range(5))
ax.set_xticklabels(TASKS)
ax.set_ylim(0, 42)
ax.set_ylabel("minutes for the task (less is better)")
ax.legend(handles=[Patch(color=BLUE, label="pass: filled bar"),
                   Patch(facecolor=BG, edgecolor=BLUE, linewidth=1.4, label="fail: hollow bar")],
          frameon=False, fontsize=7.5, loc="upper right", bbox_to_anchor=(1.02, 1.02), ncol=2)
clean(ax, "y")
ax.set_title("Real tasks per run: pass (P, filled) or fail (F, hollow), bar height is wall time",
             loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.text(0.01, 0.01, "Letters above each bar: P passed, F failed hidden tests. Orange shades are Gyro-S v2 (light orange = rerun with the author's IQ4_NL PLE table), blue shades Signal 2.",
         color=INK2, fontsize=7)
fig.tight_layout(rect=(0, 0.05, 1, 1))
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
print("ok")
