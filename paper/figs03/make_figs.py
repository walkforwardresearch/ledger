"""Figures for Walkforward Paper 2026/03, house palette.

Adapted from the author's make_figs.py. Every plotted value is unchanged. Differences from the
supplied SVGs: colours mapped to the site tokens (slate -> block, petrol -> accent, ink -> ink),
axis rules in the house line grey, and the in-figure title and subtitle removed because the
paper's caption carries them. Text is left live (svg.fonttype none) so that, inlined in the
paper HTML, it takes the page's Source Serif 4 and IBM Plex Mono.

    python3 make_figs_house.py svg figs
"""
import sys, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

ext, out = sys.argv[1], sys.argv[2]
INK = '#17211F'; BLOCK = '#A6B2B6'; ACCENT = '#21645A'; LINE = '#C3CBCC'; MUTED = '#5C6A6C'
SERIF = ['Source Serif 4', 'DejaVu Serif']; MONO = ['IBM Plex Mono', 'DejaVu Sans Mono']
plt.rcParams.update({
    'svg.fonttype': 'none', 'font.family': 'serif', 'font.serif': SERIF, 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': LINE,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.labelcolor': INK, 'ytick.labelcolor': INK,
    'axes.labelcolor': INK, 'text.color': INK, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
})

def mono_ticks(ax):
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontfamily(MONO); lab.set_fontsize(9.5)

# ---- Figure 1: the debt interest channel ------------------------------------------------
v = pd.read_csv('data/vintages_year3_revisions.csv').dropna(subset=['d_gilt_proxy_stated_windows'])
x = v.d_gilt_proxy_stated_windows.values; y = v.und_debt_interest_y3.values
b = np.polyfit(x, y, 1)
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(x, y, s=42, color=BLOCK, edgecolor=INK, linewidth=0.6, zorder=3)
xx = np.linspace(-1.6, 3.0, 50); ax.plot(xx, b[0]*xx + b[1], color=INK, linewidth=1.2, zorder=2)
p = b[0]*0.68 + b[1]
ax.scatter([0.68], [p], s=110, color=ACCENT, edgecolor='white', linewidth=1, zorder=4)
ax.annotate(f'September 2026: +0.68 points, {p:.1f}', xy=(0.68, p), xytext=(0.9, -8), color=ACCENT,
            fontsize=10, fontfamily=MONO, arrowprops=dict(arrowstyle='-', color=ACCENT, lw=0.8))
i = list(v.event).index('November 2022')
ax.annotate('November 2022', xy=(x[i], y[i]), xytext=(2.0, 20), color=INK, fontsize=9, fontfamily=MONO)
ax.axhline(0, color=LINE, lw=0.6); ax.axvline(0, color=LINE, lw=0.6)
ax.set_xlabel('Change in DMO-weighted gilt yield between OBR windows, percentage points')
ax.set_ylabel('Year-three debt interest revision, £bn')
mono_ticks(ax)
fig.tight_layout(); fig.savefig(f'{out}/fig1_debt_interest_channel.{ext}', dpi=110); plt.close()

# ---- Figure 2: the waterfall ------------------------------------------------------------
steps = [('March 2026 EFO', 23.6, True), ('Debt interest', -8.5, False), ('Receipts carry-forward', 3.0, False),
         ('Spending drift', -3.5, False), ('Before Budget measures', 14.6, True)]
fig, ax = plt.subplots(figsize=(8, 4.6)); level = 0
for i, (lab, val, tot) in enumerate(steps):
    if tot:
        bottom, h, col = 0, val, (BLOCK if i == 0 else ACCENT); level = val
    else:
        bottom, h, col = (level if val > 0 else level + val), abs(val), ACCENT; level += val
    ax.bar(i, h, bottom=bottom, color=col, width=0.62, edgecolor='white')
    ax.text(i - (0.42 if i == 4 else 0), bottom + h + 0.6, (f'{val:.1f}' if tot else f'{val:+.1f}'),
            ha=('right' if i == 4 else 'center'), color=INK, fontsize=11, fontfamily=MONO)
ax.errorbar(4, 14.6, yerr=[[18.6], [19.4]], fmt='none', ecolor=ACCENT, elinewidth=1.4, capsize=6)
ax.text(4.42, 33, '80% interval\n-4 to +34', color=ACCENT, fontsize=9, fontfamily=MONO, va='center')
ax.set_xticks(range(5))
ax.set_xticklabels(['March 2026 EFO', 'Debt interest', 'Receipts\ncarry-forward', 'Spending drift',
                    'Before Budget\nmeasures'], fontsize=9)
ax.set_ylabel('£bn, 2029-30 current budget surplus'); ax.set_ylim(-6, 40); ax.axhline(0, color=LINE, lw=0.6)
for lab in ax.get_yticklabels(): lab.set_fontfamily(MONO); lab.set_fontsize(9.5)
fig.tight_layout(); fig.savefig(f'{out}/fig2_composition.{ext}', dpi=110); plt.close()

# ---- Figure 3: the distribution ---------------------------------------------------------
u = pd.read_csv('data/vintages_year3_revisions.csv').underlying_y3.dropna().values
fig, ax = plt.subplots(figsize=(8, 4.4)); bins = np.arange(-40, 80, 10)
ax.hist(u, bins=bins, color=BLOCK, edgecolor='white')
for xv, lab in [(0, 'no change'), (17.5, 'the £17.5bn range'), (23.6, 'the whole £23.6bn cushion')]:
    ax.axvline(xv, color=INK, lw=0.8, ls='--' if xv else '-')
    ax.text(xv + 0.5, 10.6, lab, rotation=90, va='top', fontsize=8, color=INK, fontfamily=MONO)
ax.set_xlabel('Year-three underlying revision to borrowing, £bn (positive means headroom lost)')
ax.set_ylabel('Forecasts'); ax.set_ylim(0, 12)
mono_ticks(ax)
fig.tight_layout(); fig.savefig(f'{out}/fig3_distribution.{ext}', dpi=110); plt.close()
print('figures written')
