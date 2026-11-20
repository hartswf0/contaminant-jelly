"""c33 · scene_trout · The trout think (board beats R0, R4, R5, R6; film 38.0 to 48.9 s; times here from 0).

R0   0.0- 2.5  E.'s pick: the trout card on the table ("Rivet-toothed monster jaw" blue cross, "Movie projector"
               pink square). The pencil colours the pink square in, corner to corner; the button presses down and
               lights pink. The "Draw the one you pick" ring stays empty paper: nothing was drawn there that we can
               see. Velvet iris. Then the river side: the canted tin, its porthole a bright disc, a cone of lamp
               light already reaching through the bars to the wall. The trout swim in from the left in two rows.
R4   2.5- 8.5  bolt 4 · die 4 · Probable · "A movie."  The rows of trout face the wall; on it, many times life
               size and striped by the bars' shadows, is the shadow of Turkey at his window, beak gaping, wings
               beating the rim. It jerks and dims with each heavy breath. The trout settle lower together and watch.
               Bubbles leave the porthole's cracks into the beam; the dial falls 5 to 4; the picture ends dimmer.
R5   8.5- 9.7  bolt 5 · die 5 · Plausible · BLANK. The same stage, the wall lit and nothing on it. No letter, no
               caption (the sheet has one unfinished, unsure letter: nothing certain to show).
R6   9.7-10.9  bolt 6 · die 6 · Preposterous · BLANK. The same empty lit stage.

All from the river side, the tin and its six-bolt porthole in frame, except the pick card. Scene changes are the
velvet iris; the module opens with the iris opening over the whole frame and ends with it closing.
Exposes SECONDS, CAPTIONS, draw(t, ink). Uses only world.py and the kit. Captions are drawn by the editor.
The breath clock is the film's (film time = 38.0 + t, and 38.0 is a whole number of breaths and shoves).

Test:  python3 films/swarm/c33/scene_trout.py [t ...]   writes stills to films/stills/c33_scene_trout/ and a
contact sheet (sheet.png) beside them, captions hidden.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd                                                        # noqa: E402
from PIL import Image, ImageDraw, ImageFilter                            # noqa: E402
from kit import clamp, ramp, ease, smooth, lerp, lerp2                    # noqa: E402,F401

# Repair: the pick is held PICK_HOLD seconds longer (the pink square lit for over a second) before the iris shuts.
# Everything after keeps its own clock (INNER time = module time - PICK_HOLD), a whole second: breaths stay in step.
PICK_HOLD = 1.0
INNER_SECONDS = 10.9
SECONDS = INNER_SECONDS + PICK_HOLD
_CAPS = [
    (2.7, 8.3, "A movie."),
]
CAPTIONS = [(a + PICK_HOLD, b + PICK_HOLD, s) for a, b, s in _CAPS]

T_RIVER = 2.05          # the iris is shut here: table -> river side
S4, S5, S6 = 2.5, 8.5, 9.7
IRIS = 0.2              # half an iris move
IRIS_Q = 0.14           # half of the quick iris between the two blanks
TICK = 5.5              # the breath at which the dial drops its notch (5 -> 4)
ROWS = ((4, 413, 112), (5, 450, 132))      # lifted a little: the caption sits whole under the front row
AUD_X = (330, 800)
SWIM_IN = 620.0         # how far left of their places the trout start (off the frame's edge)


def _notches(t):
    """The dial: 5 at the start of the ending, one whole notch down at the chosen breath. Never near 0."""
    return 5.0 - ease(t, TICK, TICK + 0.25)


def _iris_f(t):
    f = 1 - ease(t, 0.0, IRIS)
    for a, h in ((T_RIVER, IRIS), (S5, IRIS), (S6, IRIS_Q)):
        if a - h <= t < a + h:
            f = max(f, ease(t, a - h, a) if t < a else 1 - ease(t, a, a + h))
    return max(f, ease(t, INNER_SECONDS - IRIS, INNER_SECONDS))


# ------------------------------------------------------------------ R0: the pick ---
ZOOM = 1.32             # the card is looked at a little closer than the first friend's: only two things happen on it


def _halo(ink, xy, r, k):
    """The pressed button's pink light on the paper round its well (handmade here: a soft ring of the button's own
    pink, strongest at the well's rim)."""
    if k <= 0:
        return
    S = int(r * 8)
    col = tuple(Wd.BUTTONS["square"])
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([S / 2 - r * 2.2, S / 2 - r * 2.2, S / 2 + r * 2.2, S / 2 + r * 2.2], fill=col + (int(235 * k),))
    lay = lay.filter(ImageFilter.GaussianBlur(r * 0.55))
    d = ImageDraw.Draw(lay)
    d.ellipse([S / 2 - r * 1.32, S / 2 - r * 1.32, S / 2 + r * 1.32, S / 2 + r * 1.32], fill=(0, 0, 0, 0))   # the well is the card's own
    q = r * 0.74                                                    # the cap shines up through the pencil
    hot = tuple(min(255, int(c * 1.15 + 30)) for c in col)
    d.rounded_rectangle([S / 2 - q, S / 2 - q, S / 2 + q, S / 2 + q], radius=r * 0.16, fill=hot + (int(150 * k),))
    ink.paste(lay, (int(xy[0] - S / 2), int(xy[1] - S / 2)))


def _pick(t, ink0):
    ink = Wd.offscreen(ink0)
    _pick_table(t, ink)
    w, h = ink0.w / ZOOM, ink0.h / ZOOM
    cx, cy = 470, 272
    box = (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))
    ink0.img.paste(ink.img.convert("RGB").crop(box).resize((ink0.w, ink0.h), Image.LANCZOS), (0, 0))
    ink0.d = ImageDraw.Draw(ink0.img, "RGBA")


def _pick_table(t, ink):
    Wd.table(ink, sheet=False)
    scrib = ramp(t, 0.35, 1.3)
    press = ease(t, 1.35, 1.6)
    r = Wd.pick_card(ink, (480, 268), "trout", picked="square", press=press, mark=0.0, scribble=scrib, angle=2,
                     initial="E.", lift=1 - ease(t, 0.0, 0.3))
    b = r["buttons"]["square"]
    _halo(ink, b, 17, press * (0.82 + 0.18 * math.sin(t * 9)))
    tip = r["tip"] or (b[0] - 14, b[1] - 15)
    if t < 0.35:                                                   # the pencil comes in to the pink square
        tip = lerp2((b[0] + 130, b[1] + 150), (b[0] - 14, b[1] - 15), ease(t, 0.0, 0.35))
        lift = 1 - ease(t, 0.18, 0.35)
    elif t < 1.3:
        lift = 0.0
    else:                                                          # and goes away: nothing is drawn in the ring
        k = ease(t, 1.3, 1.75)
        k = ease(t, 1.3, 2.1)                                       # right off the table: the held card is left alone
        tip = (tip[0] + 420 * k, tip[1] + 330 * k)
        lift = min(1.0, 2 * k)
    Wd.pencil(ink, tip, lift=lift)


# ------------------------------------------------------------ the river-side stage ---
def _stage(ink, t, movie=True, audience=True, turkey=True, settle=0.0, dial=5.0, dim=0.0, swim=0.0, bolt=None, lit=1.0,
           leak_since=None):
    """The river side in the world's one draw order (river_backdrop -> wall_picture -> wreck -> river_bars ->
    light_cone -> trout_audience -> bolt_label), with the crack bubbles in the beam and a clump of weed on the
    nearest plane added. turkey=False, movie=False, audience=False is the empty lit stage of a BLANK: the light
    holds still (nobody's breath dims it) and nothing is on the wall."""
    tl = t if turkey else 0.0                                      # light clock: still when nobody breathes
    Wd.river_backdrop(ink, t, dim=0.35)
    Wd.wall_picture(ink, tl, show=movie, mood="shove", dim=dim, bar_shadows=movie)
    tp = Wd.wreck(ink, t, mood="shove" if turkey else None, dial=dial)
    Wd.river_bars(ink)
    Wd.light_cone(ink, tp["port"], strength=1.0 - 0.35 * dim, t=tl)
    if turkey and leak_since is not None:                          # air leaving the cracks, out into the beam
        _leak(ink, t, tp, leak_since)
    if audience:
        Wd.trout_audience(ink, t, settle, rows=ROWS, x0=AUD_X[0] - swim, x1=AUD_X[1] - swim)
    Wd.weed(ink, 46, 560, 250, lean=10 * math.sin(t * 0.8), t=t, seed=11, n=5, spread=46, dark=0.75)
    Wd.weed(ink, 610, 566, 120, lean=8 * math.sin(t * 0.9 + 1), t=t, seed=5, n=3, spread=22, dark=0.75)
    if bolt:
        Wd.bolt_label(ink, bolt, lit=lit)
    return tp


def _leak(ink, t, tp, since):
    """With every heavy breath a bead of fine bubbles leaves each crack of the small porthole and rises through the
    beam (the world's crack_bubbles is sized for the big glass; this is the same clock at the tin's scale)."""
    pts = Wd.crack_points(tp["port"], tp["port_r"], mirror=True)
    k1 = Wd.breath_index(t)
    for k in range(max(0, k1 - 5), k1 + 1):
        t0 = k / Wd.BREATH_HZ + 0.12
        if t0 < since:
            continue
        for q, p in enumerate(pts[::2]):
            Wd.bubbles(ink, p, t, t0=t0 + q * 0.05, n=2, rise=120, spread=7, size=3.0)


def _movie(t, ink):
    """R0's payoff and bolt 4. The trout slide in from the frame's left edge on their own plane, take their rows,
    then settle lower together and watch. Turkey never stops shoving and breathing; the picture ends dimmer."""
    swim = SWIM_IN * (1 - ease(t, T_RIVER + 0.05, 3.5))
    settle = ease(t, 4.3, 5.3)
    dim = 0.32 * ramp(t, 3.6, S5)
    _stage(ink, t, swim=swim, settle=settle, dial=_notches(t), dim=dim, bolt=4 if t >= S4 else None,
           leak_since=T_RIVER)


def _blank(t, ink, n):
    # the die is shown at full contrast (the emptiness is the stage's, not the die's); the dial stays riveted on
    # the tin where bolt 4 left it
    _stage(ink, t, movie=False, audience=False, turkey=False, dial=4.0, bolt=n, lit=1.0)


# ------------------------------------------------------------------------- draw ---
def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    hold0 = T_RIVER - IRIS                            # the pick is held here, lit, before the iris moves
    tp = t                                            # the pick's own clock runs on (the halo keeps glimmering)
    t = t if t < hold0 else (hold0 if t < hold0 + PICK_HOLD else t - PICK_HOLD)
    if t < T_RIVER:
        _pick(tp, ink)
    elif t < S5:
        _movie(t, ink)
    elif t < S6:
        _blank(t, ink, 5)
    else:
        _blank(t, ink, 6)
    f = _iris_f(t)
    if f > 0:
        Wd.iris(ink, f, r=600)
    Wd.badge(ink)


def check():
    assert all(0 <= a < b <= SECONDS and b - a >= 2.5 for a, b, _ in CAPTIONS)
    assert [c[2] for c in CAPTIONS] == ["A movie."]                # bolts 5 and 6 are blank: no caption, no letter
    assert all(S4 <= a and b <= S5 for a, b, _ in _CAPS)
    assert abs(_notches(S4) - 5) < 1e-6 and abs(_notches(S5 - 0.05) - 4) < 1e-6
    assert abs(TICK * Wd.BREATH_HZ - round(TICK * Wd.BREATH_HZ)) < 1e-9          # the notch drops on a breath


if __name__ == "__main__":
    from kit import Film, HERE
    check()
    film = Film("c33_scene_trout", SECONDS)
    film.picture(draw)
    args = [float(a) for a in sys.argv[1:] if not a.startswith("-")]
    times = args or [0.1, 0.5, 1.0, 1.5, 1.9, 2.2, 2.4, 2.8, 3.3, 3.9, 4.6, 5.3, 5.6, 6.5, 7.5, 8.2,
                     8.4, 8.6, 9.0, 9.4, 9.7, 9.9, 10.3, 10.75]
    film.render(preview=times)
    pdir = HERE / "stills" / film.slug
    cols = 4
    tw, th = 480, 270
    sheet = Image.new("RGB", (cols * tw, -(-len(times) // cols) * th), (20, 20, 20))
    for k, tt in enumerate(times):
        im = Image.open(pdir / f"{tt:06.2f}.png").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
    sheet.save(pdir / "sheet.png")
    print("sheet ->", pdir / "sheet.png")
