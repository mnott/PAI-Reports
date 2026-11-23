"""Figures of lab report 5. Data are copied from the bench result files (one JSON per run,
<data dir>/results/<set>/<key>/rep*.json) and the prefill A/B logs (<notes dir>/ab/*.jsonl);
extract.py in this directory prints the bench values. Run: python3 make_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

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


# (passed, n, seconds) per set; first rep only unless stated
SETUPS = ["Gyro-L", "Signal 2 (solo)", "Signal 2 (dual A)", "Signal 2 (dual B)", "Inkling, Locals",
          "Inkling, MTPLX default", "Inkling, MTPLX low", "Inkling, MTPLX medium",
          "Inkling, MTPLX off", "Inkling, Strata"]
DATA = {
    "short (20 questions)": [(19, 20, 54), (16, 20, 52), (17, 20, 70), (17, 20, 74), (18, 20, 69),
                             (20, 20, 288), (20, 20, 147), (18, 20, 96), (19, 20, 122), (17, 20, 68)],
    "easy (40 tasks)": [(38, 40, 399), (38, 40, 327), (38, 40, 392), (37, 40, 782), (39, 40, 352),
                        (39, 40, 637), (40, 40, 170), (40, 40, 456), (40, 40, 567), (3, 40, 75)],
    "hard (40 tasks)": [(35, 40, 525), (33, 40, 542), (31, 40, 851), (34, 40, 1152), (36, 40, 753),
                        (37, 40, 2301), (36, 40, 604), (33, 40, 2214), (36, 40, 3381), (7, 40, 841)],
    "real (5 repository tasks)": [(5, 5, 3920), (5, 5, 4003), (4, 5, 4008), (4, 5, 4422), (3, 5, 1471),
                                  (2, 5, 5600), (3, 5, 1773), (3, 5, 4887), (2, 5, 4534), (2, 5, 4332)],
}


def fmt(sec):
    return f"{sec:.0f} s" if sec < 120 else f"{sec / 60:.1f} min"


def col(name):
    return ORANGE if name == "Gyro-L" else BLUE


# 1 pass rate small multiples
fig, axes = plt.subplots(2, 2, figsize=(7.4, 6.6), sharey=True)
for ax, (title, rows) in zip(axes.flat, DATA.items()):
    ys = list(range(len(SETUPS)))[::-1]
    for y, name, (p, n, s) in zip(ys, SETUPS, rows):
        v = 100 * p / n
        ax.barh(y, v, color=col(name), height=0.5)
        ax.text(v + 2, y, f"{p}/{n}, {fmt(s)}", va="center", fontsize=7.5, color=INK)
    ax.set_title(title, loc="left", color=INK, fontsize=9.5, fontweight="bold")
    ax.set_xlim(0, 160)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0", "50", "100 %"])
    ax.set_yticks(ys)
    ax.set_yticklabels(SETUPS)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    clean(ax)
fig.legend(handles=[Patch(color=ORANGE, label="Gyro-L (baseline)"), Patch(color=BLUE, label="other setups")],
           loc="lower center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 0.025))
fig.text(0.01, 0.005, "Bar: share of tasks passed. Label: passed of n, wall time of the run. Single run per bar "
         "(real: first run of the series).", color=INK2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig("fig-pass-rate.pdf")
plt.close(fig)

# 2 real tasks: quality vs minutes (all five-task runs)
PTS = [("Gyro-L", 5, 3920, True), ("Gyro-L", 5, 3975, False),
       ("Signal 2", 5, 4003, True), ("Signal 2", 3, 3294, False),
       ("Signal 2 dual A", 4, 4008, True), ("Signal 2 dual B", 4, 4422, True),
       ("Locals", 3, 1471, True), ("MTPLX default", 2, 5600, True),
       ("MTPLX low", 3, 1773, True), ("MTPLX low", 3, 2413, False),
       ("MTPLX medium", 3, 4887, True), ("MTPLX off", 2, 4534, True), ("Strata", 2, 4332, True)]
fig, ax = plt.subplots(figsize=(6.6, 3.8))
OFF = {"Gyro-L": (-34, 6), "Signal 2": (6, 6), "Signal 2 dual A": (-75, 5), "Signal 2 dual B": (6, 5),
       "Locals": (-10, -14), "MTPLX default": (6, 5), "MTPLX low": (6, 5), "MTPLX medium": (-30, -13),
       "MTPLX off": (6, -11), "Strata": (6, 5)}
for name, p, s, first in PTS:
    c = ORANGE if name == "Gyro-L" else BLUE
    ax.scatter(s / 60, p, s=26, facecolor=c if first else BG, edgecolor=c, linewidth=1.2, zorder=3)
    if first:
        ax.annotate(name, (s / 60, p), xytext=OFF[name], textcoords="offset points", fontsize=7.5, color=INK)
ax.set_xlabel("minutes for the five tasks (less is better)")
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=ORANGE, label="Gyro-L (baseline)"),
                   Line2D([], [], marker="o", ls="", color=BLUE, label="other setups"),
                   Line2D([], [], marker="o", ls="", color=INK2, label="filled: first run of a series"),
                   Line2D([], [], marker="o", ls="", mfc=BG, color=INK2, label="hollow: further run")],
          frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
ax.set_ylabel("tasks passed of 5")
ax.set_ylim(1.4, 5.6)
ax.set_xlim(0, 105)
ax.set_yticks(range(2, 6))
clean(ax, "both")
ax.set_title("Real tasks: quality against time", loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.text(0.01, 0.01, "Filled: first run of a series; hollow: further run (Gyro-L rep. 3, Signal 2 rep. 2, MTPLX low rep. 2).",
         color=INK2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("fig-real-quality-time.pdf")
plt.close(fig)

# 3 throughput: real-task passes per hour (seconds of the five-task runs)
g = (10, 3920 + 3975)
s = (8, 4003 + 3294)
da = 4 / 4008 * 3600
db = 4 / 4422 * 3600
bars = [("Gyro-L, one server (2 runs)", g[0] / g[1] * 3600, ORANGE),
        ("Signal 2, one server (2 runs)", s[0] / s[1] * 3600, BLUE),
        ("Signal 2, dual A", da, BLUE),
        ("Signal 2, dual B", db, BLUE),
        ("Signal 2, A + B together", da + db, BLUE)]
fig, ax = plt.subplots(figsize=(6.6, 2.7))
for i, (n, v, c) in enumerate(bars[::-1]):
    ax.barh(i, v, color=c, height=0.5)
    ax.text(v + 0.1, i, f"{v:.2f}", va="center", fontsize=8, color=INK)
ax.set_yticks(range(len(bars)))
ax.set_yticklabels([b[0] for b in bars[::-1]])
ax.set_xlim(0, 8)
ax.legend(handles=[Patch(color=ORANGE, label="Gyro-L (baseline)"), Patch(color=BLUE, label="Signal 2")],
          frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2)
ax.set_xlabel("passed real tasks per hour of run time")
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
clean(ax)
ax.set_title("Throughput on the real tasks", loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout()
fig.savefig("fig-throughput.pdf")
plt.close(fig)

# 4 failure classes of the 22 real-task non-passes (taxonomy table; A loop, B stall, C wrong fix, E harness)
FAIL = [("Locals", 2, 0, 0, 0), ("MTPLX low rep. 1", 0, 1, 0, 1), ("MTPLX low rep. 2", 0, 1, 1, 0),
        ("MTPLX default", 0, 2, 0, 3), ("MTPLX think redo", 0, 3, 0, 0), ("MTPLX medium", 0, 2, 0, 0),
        ("MTPLX off", 0, 3, 0, 0), ("Strata", 0, 0, 0, 3)]
CLS = [("A loop", "#9ecbf5"), ("B stall, no edit", BLUE), ("C wrong fix", "#1b4f8f"), ("E harness fault", ORANGE)]
MEAN = {"A loop": "A: loop, same calls repeated", "B stall, no edit": "B: stall, only reading, no edit made",
        "C wrong fix": "C: wrong fix, edit made but tests fail", "E harness fault": "E: fault of our harness, not the model"}
fig, ax = plt.subplots(figsize=(6.6, 3.9))
for i, row in enumerate(FAIL[::-1]):
    left = 0
    for k, (cname, cc) in enumerate(CLS):
        v = row[1 + k]
        if v:
            ax.barh(i, v, left=left, color=cc, height=0.55, edgecolor=BG, linewidth=1.5,
                    label=cname if i == 0 else None)
            ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=7.5,
                    color=BG if cname != "A loop" else INK)
            left += v
ax.set_yticks(range(len(FAIL)))
ax.set_yticklabels([f[0] for f in FAIL[::-1]])
ax.set_xlim(0, 5.2)
ax.set_xticks(range(0, 6))
ax.set_xlabel("number of failed real tasks, by cause")
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
clean(ax)
ax.legend([Patch(color=c[1]) for c in CLS], [MEAN[c[0]] for c in CLS],
          frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.3, -0.2), ncol=2,
          title="Failure class (D, gave up: none occurred)", title_fontsize=7.5)
ax.set_title("Why 22 real tasks failed in the Inkling runs (Gyro-L: none)", loc="left", color=INK, fontsize=9.5, fontweight="bold")
fig.tight_layout()
fig.savefig("fig-failure-classes.pdf")
plt.close(fig)

# 5 Gyro-L prefill, cold prompts, ranges (min-max tok/s)
sizes = ["2k", "8k", "30k"]
P18 = [(1005, 1248), (1142, 1192), (1097, 1210)]
P19 = [(1184, 1237), (1163, 1236), (1188, 1229)]
Q18 = [(1085, 1154), (1260, 1269), (1257, 1263)]
Q20 = [(1161, 1197), (1224, 1249), (1259, 1272)]
fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0), sharey=True)
for ax, (a, b, la, lb, title) in zip(axes, [(P18, P19, "0.2.18", "0.2.19", "0.2.18 and 0.2.19"),
                                            (Q18, Q20, "0.2.18", "0.2.20", "0.2.18 and 0.2.20 (paired run)")]):
    for i in range(3):
        ax.plot([i - 0.12] * 2, a[i], color=ORANGE, linewidth=4, solid_capstyle="round")
        ax.plot([i + 0.12] * 2, b[i], color=BLUE, linewidth=4, solid_capstyle="round")
    ax.text(2.3, a[2][0] - 40, la, color=ORANGE, fontsize=8, ha="left")
    ax.text(2.3, b[2][1] + 10, lb, color=BLUE, fontsize=8, ha="left")
    ax.legend(handles=[Line2D([], [], color=ORANGE, lw=4, label=f"Strata {la}"), Line2D([], [], color=BLUE, lw=4, label=f"Strata {lb}")],
              frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{x} tokens" for x in sizes])
    ax.set_xlim(-0.5, 2.9)
    ax.set_ylim(950, 1320)
    ax.set_title(title, loc="left", color=INK, fontsize=9, fontweight="bold")
    clean(ax, "y")
axes[0].set_ylabel("cold prefill, tokens/s (range)")
fig.text(0.01, 0.01, "Each bar spans the lowest to the highest measured speed per prompt size.", color=INK2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("fig-prefill-versions.pdf")
plt.close(fig)
print("ok")
