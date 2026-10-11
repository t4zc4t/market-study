# Draws the two charts used in the README.
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, RULE, MILD, STRONG = "#1B2733", "#566574", "#D3DBE2", "#A8751C", "#2B4C86"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": RULE, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "font.family": "DejaVu Sans"})

scores = [float(r["indicator_score"]) for r in csv.DictReader(open("data/clean/scores.csv")) if r["indicator_score"]]
gensol = 50.0
fig, ax = plt.subplots(figsize=(8, 2.2))
ax.scatter(scores, [0] * len(scores), s=60, color=STRONG, alpha=.75, zorder=3)
ax.scatter([gensol], [0], s=90, facecolor="white", edgecolor=MILD, linewidth=2.5, zorder=4)
ax.annotate("Gensol, as of its FY2024 accounts", (gensol, 0), xytext=(gensol, .55), ha="center", color=MILD,
            arrowprops=dict(arrowstyle="-", color=MILD))
ax.annotate(f"{len(scores)} companies in the sample with a full score", (min(scores), 0), xytext=(0, -.65), color=STRONG)
ax.set_xlim(-2, 102); ax.set_ylim(-1, 1); ax.set_yticks([])
ax.set_xlabel("Indicator score out of 100")
for s in ("left", "right", "top"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("charts/score_spread.png", dpi=160)

names = {}
mild, strong, scored = [0] * 17, [0] * 17, [0] * 17
for r in csv.DictReader(open("data/clean/checks.csv")):
    i = int(r["check"]); names[i] = r["name"].split(" (")[0].split(",")[0]
    if r["result"] != "not scored": scored[i] += 1
    if r["result"] == "mild": mild[i] += 1
    if r["result"] == "strong": strong[i] += 1
order = list(range(16, 0, -1))
fig, ax = plt.subplots(figsize=(8, 5.2))
y = range(len(order))
ax.barh(y, [strong[i] for i in order], color=STRONG, label="well outside")
ax.barh(y, [mild[i] for i in order], left=[strong[i] for i in order], color=MILD, label="mildly outside")
ax.set_yticks(list(y)); ax.set_yticklabels([f"{i}. {names[i]}" for i in order])
ax.set_xlabel("Number of the 24 companies"); ax.set_xlim(0, 24)
for s in ("right", "top"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig("charts/checks_outside_range.png", dpi=160)
print([ (i, strong[i], mild[i], scored[i]) for i in range(1,17)])
