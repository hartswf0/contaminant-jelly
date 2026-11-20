"""c13 · scene_trout · the trout think (board beats C0, C4, C5, C6; 0.0 to 4.5 s of this module) · ALL BLANK.

The next friend picked nothing, drew nothing and wrote nothing, so nothing is invented here.

C0  0.0-1.5  one clockwise sweep of the brass arm takes us round to the river side; the pick card ("The trout
             think": blue cross / pink square) is slid in, lies there with NEITHER button lit and the dashed ring
             empty, and is slid away again (it only ever travels clockwise).
C4  1.5-2.5  bolt 4 · die face 4 beside bolt 4 (six o'clock) of the tin's own porthole · the empty lit stage.
C5  2.5-3.5  bolt 5 · die face 5 at eight o'clock · the same empty lit stage.
C6  3.5-4.5  bolt 6 · die face 6 at ten o'clock · the same empty lit stage.

The stage is the river side: the riveted bread-roll tin low in frame, its brass porthole facing us and glowing
amber, the arch and the still bell above, weed. No trout, no Turkey, no caption, no action. Between the blanks the
only thing that changes is the die face, which steps clockwise round the tin's porthole from bolt to bolt. The
bolts never light.

Exposes SECONDS, CAPTIONS (empty: there are no sentences), draw(t, ink). Uses only world.py and the kit.
"""
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402
from kit import Ink, W, H, FPS, clamp, ramp, ease, smooth, lerp, lerp2     # noqa: E402,F401

SECONDS = 4.5
CAPTIONS = []                      # the sheet has no sentence for any of these beats

# ------------------------------------------------------------------ timing ---
T_SWEEP = (0.0, 0.42)              # the brass arm, once round, clockwise
T_LAY = (0.38, 0.68)               # the card slides in and is laid
T_TAKE = (1.20, 1.50)              # the card is lifted and slides on, the same way round
T_BOLT = {4: 1.5, 5: 2.5, 6: 3.5}  # each blank bolt gets one second
STEP = 0.24                        # the die's clockwise step from one bolt place to the next

CARD_C = (480, 190)                # where the card lies (upper half, clear of the tin and its porthole)
CARD_CLOCK = 0.0                   # ... which is twelve o'clock on the circle the card travels
CARD_PIVOT = (480, 640)            # the card travels on a big circle about this point, clockwise
CARD_RAD = CARD_PIVOT[1] - CARD_C[1]

DIE_SIZE = 36                      # small enough to sit ON its bolt of the tin's porthole
TIN_C, TIN_S = (452, 392), 1.12    # the tin a little nearer than the world's default, so its six bolts can be counted
BOLT_RAD = 1.2                     # bolt circle, in glass radii
DIE_LIT = 0.3                      # an unwritten bolt: its die face is dull, well short of lit; the bolt has no glow


# ------------------------------------------------------------------ the old scene (for the sweep only) ---
_OLD = {}


def _old_scene(ink, t):
    """What the brass arm sweeps away: the last frame of Turkey's part if that module is there, else the same
    seat set held dead still (bolt 3's ending: nothing outside moves, Turkey frozen and trembling)."""
    if "fn" not in _OLD:
        fn = None
        try:
            import scene_turkey as st                                # noqa: WPS433
            last = st.SECONDS - 1.0 / FPS
            probe = w.offscreen(ink)
            st.draw(last, probe)                                     # make sure it really draws before trusting it
            fn = lambda o, tt: st.draw(last, o)                      # noqa: E731
        except Exception:                                            # not written yet, or broken: stand-in
            fn = None
        _OLD["fn"] = fn
    if _OLD["fn"] is not None:
        _OLD["fn"](ink, t)
        return
    w.seat_stage(ink, 0.0, "back", calm=True)
    w.bell(ink, part="cord")
    w.seat_stage(ink, 0.0, "front", calm=True)
    w.bell(ink, part="body", disc="circle")
    w.turkey_reflection(ink, mood="frozen", t=t)
    w.seat_frame(ink)
    w.gauge(ink, 4)
    w.bolt_mark(ink, 3)


# ------------------------------------------------------------------ the empty lit stage ---
def _stage(ink):
    """River side, lit and empty. Drawn at a fixed time so that nothing in it moves at all. Returns the tin's points."""
    w.river_stage(ink, 0.0, "back", calm=True)
    tin = w.tin(ink, TIN_C, TIN_S, 0.0, mood=None, glow=1.0)
    w.weed(ink, 250, 520, 150, 0, 0.0, seed=7, n=5, sway=0)
    w.weed(ink, 742, 528, 190, 0, 0.0, seed=8, n=6, sway=0)
    px, py = tin["port"]
    for n in range(6):                                  # its six brass bolts, twelve o'clock and clockwise; none lit
        bx, by = w.clock_xy((px, py), tin["port_r"] * BOLT_RAD, n * 60)
        ink.d.ellipse([bx - 6, by - 4, bx + 9, by + 10], fill=(0, 0, 0, 130))
        ink.d.regular_polygon((bx, by, 7.5), 6, rotation=n * 60, fill=w.PAL["brass_dk"] + (255,), outline=w.PAL["brass_line"] + (255,))
        ink.d.regular_polygon((bx - 1, by - 1, 4.5), 6, rotation=n * 60, fill=w.PAL["brass_hi"] + (255,))
    return tin


def _die_clock(t):
    """(clock angle of the die round the tin's porthole, face shown, 0..1 how far the face has changed).
    Bolt 4 is at 180 (six o'clock), bolt 5 at 240, bolt 6 at 300. The die only ever goes clockwise."""
    a = 120.0 + 60.0 * smooth(ramp(t, T_BOLT[4] - STEP, T_BOLT[4]))          # in from the four o'clock place
    a += 60.0 * smooth(ramp(t, T_BOLT[5] - STEP / 2, T_BOLT[5] + STEP / 2))
    a += 60.0 * smooth(ramp(t, T_BOLT[6] - STEP / 2, T_BOLT[6] + STEP / 2))
    n = 4 if t < T_BOLT[5] else 5 if t < T_BOLT[6] else 6
    return a, n


def _die(ink, t, tin):
    if t < T_BOLT[4] - STEP:
        return
    a, n = _die_clock(t)
    px, py = tin["port"]
    pr = tin["port_r"]
    rad = pr * BOLT_RAD + DIE_SIZE * 0.42               # the face sits on its own (unlit) bolt, lapping the brass rim
    x, y = w.clock_xy((px, py), rad, a)
    alpha = ramp(t, T_BOLT[4] - STEP, T_BOLT[4] - STEP * 0.4)
    w.put(ink, _shadow(DIE_SIZE), x + 4, y + 6, alpha=0.55 * alpha)
    w.die_face(ink, n, x, y, DIE_SIZE, "ivory", lit=DIE_LIT, alpha=alpha)


_SH = {}


def _shadow(size):
    if size not in _SH:
        from PIL import ImageDraw, ImageFilter
        s = int(size * 1.7)
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        q = (s - size) / 2
        ImageDraw.Draw(im).rounded_rectangle([q, q, s - q, s - q], radius=size * 0.18, fill=(0, 0, 0, 190))
        _SH[size] = im.filter(ImageFilter.GaussianBlur(size * 0.12))
    return _SH[size]


# ------------------------------------------------------------------ the blank pick ---
def _card_clock(t):
    """Clock angle of the card on its big circle: in from the left, rests at twelve, on to the right. Monotonic."""
    a_in = lerp(-52.0, CARD_CLOCK, smooth(ramp(t, *T_LAY)))
    f = ramp(t, *T_TAKE)
    return a_in + 60.0 * f * f


def _card(ink, t):
    if t < T_LAY[0] or t >= T_TAKE[1]:
        return
    a = _card_clock(t)
    x, y = w.clock_xy(CARD_PIVOT, CARD_RAD, a)
    lift = max(1.0 - smooth(ramp(t, T_LAY[0] + 0.1, T_LAY[1])), smooth(ramp(t, T_TAKE[0], T_TAKE[0] + 0.12)))
    w.pick_card(ink, (x, y), side="trout", picked=None, press=0.0, loop=0.0, angle=-2.0 - a * 0.5,
                initial="M.", lift=lift)


# ------------------------------------------------------------------ draw ---
def _river_side(ink, t):
    tin = _stage(ink)
    _die(ink, t, tin)
    _card(ink, t)


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < T_SWEEP[1]:
        _old_scene(ink, t)
        o = w.offscreen(ink)
        _river_side(o, t)
        w.sweep(ink, o.img, ramp(t, *T_SWEEP))
    else:
        _river_side(ink, t)
    w.badge(ink)


def check():
    """Clockwise Etiquette, numerically, and the blanks kept blank."""
    assert CAPTIONS == [], "nothing was written for bolts 4 to 6: no captions"
    prev = None
    for k in range(int(SECONDS * FPS)):
        tt = k / FPS
        cur = (_card_clock(tt), _die_clock(tt)[0])
        if prev:
            assert cur[0] >= prev[0] - 1e-9, "the card went anticlockwise"
            assert cur[1] >= prev[1] - 1e-9, "the die went anticlockwise"
        prev = cur
    for n, a in ((4, 180.0), (5, 240.0), (6, 300.0)):
        for tt in (T_BOLT[n] + STEP / 2 + 0.01, T_BOLT[n] + 0.5, T_BOLT[n] + 1.0 - STEP / 2 - 0.01):
            aa, nn = _die_clock(tt)
            assert nn == n and abs(aa - a) < 1e-6, f"bolt {n}: its die must sit still at its own bolt place"
    assert DIE_LIT <= 0.3 and T_TAKE[1] <= T_BOLT[4] and abs(T_BOLT[6] + 1.0 - SECONDS) < 1e-9
    return True


if __name__ == "__main__":
    from kit import Film
    check()
    film = Film("c13_scene_trout", SECONDS)
    film.picture(draw)
    args = [float(a) for a in sys.argv[1:] if not a.startswith("-")]
    times = args or [0.0, 0.12, 0.3, 0.46, 0.62, 0.9, 1.18, 1.34, 1.46, 1.6, 2.0, 2.45, 2.54, 3.0, 3.54, 4.0, 4.3, 4.45]
    film.render(preview=times)
    sdir = Path(w.FILMS) / "stills" / "c13_scene_trout"
    cols = 3
    tw, th = 480, 270
    sheet = Image.new("RGB", (cols * tw, ((len(times) + cols - 1) // cols) * th), (20, 20, 20))
    for i, tt in enumerate(times):
        im = Image.open(sdir / f"{tt:06.2f}.png").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(sdir / "contact.png")
    print("contact ->", sdir / "contact.png")
