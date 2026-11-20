"""c25 · TURKEY THINKS · the first friend's pick, then bolts 1, 2 and 3, from Turkey's seat looking out.

Board beats (module time):
  T0  0.0 ..  2.5   the pick card "Scuba helmet", green triangle pressed, the bowl ringed green
  B1  2.5 ..  6.5   bolt 1 · Probable      "The air runs out."
  B2  6.5 .. 10.5   bolt 2 · Plausible     "A little uncomfy."
  B3 10.5 .. 15.5   bolt 3 · Preposterous  "It is not wet."

Every cut is the card turned over (world.card_flip, 8 frames). Turkey panics in every beat; only a counted
wing-beat sends bubbles out and drops the gauge a tick. Each ending starts again from half.
Exposes SECONDS, CAPTIONS, draw(t, ink). The editor draws the captions and may draw the badge again.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402
from kit import W, H, FPS, clamp, ramp, ease, smooth, lerp          # noqa: E402
from PIL import Image, ImageDraw                                      # noqa: E402

SECONDS = 15.5
T_B1, T_B2, T_B3 = 2.5, 6.5, 10.5
FLIP = 1.0 / 3.0                                                      # 8 frames

CAPTIONS = [
    (T_B1 + 0.3, T_B2, "The air runs out."),
    (T_B2 + 0.3, T_B3, "A little uncomfy."),
    (T_B3 + 0.3, SECONDS, "It is not wet."),
]

PUFF = (296, 250)                    # where Turkey's panic bubbles leave, by the left rim of the glass
DIE = 38
REFL = dict(cx=352, cy=372, height=212, alpha=0.68, wing_scale=0.66)      # Turkey's reflection, low left in the glass, big enough to see the wings go


def _puff(ink, u, t0, n, size=9.0):
    """One wing-beat's bubbles: they leave by the left rim, rise outside the tin and are gone before the next beat."""
    if n and u > t0:
        w.bubbles(ink, PUFF, u, t0=t0, n=n, size=size, rise=190, spread=22, alpha=1 - ramp(u - t0, 0.75, 1.25))


# ------------------------------------------------------------------ shared bits ---

def _beat(u, beats, top=100.0, rest=0.0, dur=0.5):
    """Wing angle for counted beats: up and down once per beat, a small tremble between."""
    v = rest + 4 * abs(math.sin(u * 17))
    for b in beats:
        v = max(v, top * math.sin(math.pi * clamp((u - b) / dur)))
    return v


def _ticks(u, beats, start=3.0):
    """The level the wings have spent the air down to: one whole tick per beat, falling as the wing comes down."""
    return start - sum(ramp(u, b + 0.2, b + 0.3) for b in beats)


def _needle(beats, seconds, start=3.0):
    """Secondary dynamics: the needle goes a little too far and comes back."""
    return w.Follower(lambda u: _ticks(u, beats, start), seconds, f=3.0, zeta=0.35)


def _flip_kick(u, amp=10.0):
    """The card has just been turned over: the water in the bowl is thrown once."""
    return amp if u < 0.12 else 0.0


def _wattle(beats, seconds):
    return w.Follower(lambda u: 30.0 * math.sin(math.pi * clamp((u - 0.05 - min(beats, key=lambda b: abs(u - b))) / 0.5))
                      if beats else 0.0, seconds, f=2.2, zeta=0.22)


# ------------------------------------------------------------------ T0 · the pick ---

T0_LEN = T_B1
T0_SLOSH = w.Follower(lambda u: _flip_kick(u, 8.0), T0_LEN + 1, f=1.5, zeta=0.3)
CARD_C = (712, 176)


def _card_up(ink, u):
    """The pick card flips up over the porthole about its own lower edge, then lies flat."""
    f = ease(u, 0.1, 0.55)
    press = ease(u, 0.75, 0.95)
    mark = ramp(u, 1.05, 1.75)
    kw = dict(side="turkey", picked="triangle", press=press, mark=mark, initial="K.")
    if f <= 0:
        return None
    if f >= 1:
        return w.pick_card(ink, CARD_C, **kw)
    lay = ink.layer()
    w.pick_card(lay, CARD_C, lift=1 - f, **kw)
    box = (CARD_C[0] - 240, CARD_C[1] - 150, min(W, CARD_C[0] + 250), CARD_C[1] + 170)
    piece = lay.img.crop(box)
    c = math.sin(f * math.pi / 2)
    hh = max(2, int(piece.height * c))
    piece = piece.resize((piece.width, hh), Image.BILINEAR)
    shade = 0.55 + 0.45 * c
    r, g, b, a = piece.split()
    piece = Image.merge("RGBA", (r.point(lambda v: int(v * shade)), g.point(lambda v: int(v * shade)),
                                 b.point(lambda v: int(v * shade)), a))
    ink.paste(piece, (box[0], box[3] - hh))
    return None


def scene_pick(ink, u):
    sl = T0_SLOSH.at(u)
    wp, _ = w.seat_scene(ink, u, dict(x=438, step=0.0, bowl_bubbles=u, slosh=sl, wave=clamp(abs(sl) / 8), phase=u * 3, amp=3),
                         dict(REFL, mood="panic", t=u), notches=3.0, frame=False)
    w.seat_frame(ink)
    # the bowl is ringed once in green, through the glass: that is the helmet
    done = ramp(u, 1.15, 2.0)
    if done > 0:
        w.crayon_ring(ink, wp["bowl"], wp["bowl_r"][0] * 1.13, wp["bowl_r"][1] * 1.18, w.PAL["green"], done, seed=4, width=7)
    w.gauge(ink, 3.0, t=u)                       # as the pilot's page left it: half
    r = _card_up(ink, u)
    if r and r["tip"] is not None and 1.05 <= u < 1.8:
        w.pencil(ink, r["tip"], 50)
    elif r and 0.95 <= u < 1.05:
        w.pencil(ink, (r["ring"][0] - 4, r["ring"][1] + 6), 50, lift=1 - ramp(u, 0.95, 1.05))
    elif r and 1.8 <= u < 2.15:
        q = ease(u, 1.8, 2.15)
        w.pencil(ink, (r["ring"][0] + 6 + 130 * q, r["ring"][1] + 4 + 60 * q), 50, lift=min(1.0, q * 3), alpha=1 - q * 0.2)


# --------------------------------------------------------- B1 · The air runs out. ---

B1_LEN = T_B2 - T_B1
B1_BEATS = [0.45, 1.05, 1.65, 2.35, 2.95, 3.5]  # three spend the last three ticks; then the wings go and nothing comes
B1_PUFFS = [8, 4, 1, 0, 0, 0]
B1_NEEDLE = _needle(B1_BEATS[:3], B1_LEN + 1)
B1_PACE = 0.36                                       # strides a second: walking slowly
B1_SLOSH = w.Follower(lambda u: _flip_kick(u) + 6.0 * math.sin(2 * math.pi * B1_PACE * 2 * u), B1_LEN + 1, f=1.5, zeta=0.3)
B1_WATTLE = _wattle(B1_BEATS, B1_LEN + 1)


def scene_runs_out(ink, u):
    step = u * B1_PACE
    x = 640 - step * 0.36 * 306
    sl = B1_SLOSH.at(u)
    w.seat_backdrop(ink, u)
    w.walker(ink, x=x, step=step, bowl_bubbles=u, slosh=sl, wave=clamp(abs(sl) / 8), phase=u * 4, amp=5)
    for b, n in zip(B1_BEATS, B1_PUFFS):
        if n == 1:                                   # the last of the air: one big bubble, alone, going up slowly. Then none.
            v = u - b - 0.2
            if 0 < v < 1.5:
                bx, by = PUFF[0] + 16 + 9 * math.sin(v * 5), PUFF[1] + 60 - 150 * v / 1.5
                r = 17 + 2 * math.sin(v * 9)
                al = int(255 * min(1.0, v * 8) * (1 - ramp(v, 1.2, 1.5)))
                ink.d.ellipse([bx - r, by - r, bx + r, by + r], fill=(236, 250, 250, al // 4), outline=(244, 252, 252, al), width=3)
                ink.d.arc([bx - r * 0.6, by - r * 0.6, bx + r * 0.6, by + r * 0.6], 200, 260, fill=(255, 255, 255, al), width=2)
        else:
            _puff(ink, u, b + 0.2, n, 9.0)
    w.turkey_reflection(ink, mood="panic", t=u, **REFL, wing=_beat(u, B1_BEATS), wattle=B1_WATTLE.at(u),
                        beak=14 + 14 * ease(u, 1.9, 2.5) + 3 * math.sin(u * 13), neck=-5 - 5 * ease(u, 1.9, 2.6) + 4 * math.sin(u * 9))
    w.seat_frame(ink)
    n = max(0.0, B1_NEEDLE.at(u))
    w.gauge(ink, n, 124, 424, r=88, tremble=ease(u, 2.0, 2.3), t=u)      # this ending is the dial's: it is the biggest thing on the wall
    w.bolt_mark(ink, 1, size=DIE)


def _gauge(ink, notches, u, tremble=0.0):
    """The air dial, lower left of Turkey's seat, a size its needle can be read at."""
    w.gauge(ink, notches, 112, 440, r=66, tremble=tremble, t=u)


# --------------------------------------------------------- B2 · A little uncomfy. ---

B2_LEN = T_B3 - T_B2
B2_BEATS = [2.75]                                   # one beat, one tick, inside the twist


def _wrig(u):
    """The helmet shifted on its collar: three short tugs, each a finger's width."""
    return (math.sin(2 * math.pi * 1.6 * (u - 1.0)) if 1.0 <= u < 2.25 else 0.0) * (1 - 0.35 * ramp(u, 1.0, 2.25))


B2_SLOSH = w.Follower(lambda u: _flip_kick(u) + 20.0 * _wrig(u), B2_LEN + 1, f=1.5, zeta=0.3)
B2_NEEDLE = _needle(B2_BEATS, B2_LEN + 1)
B2_WATTLE = w.Follower(lambda u: 26.0 * _wrig(u - 1.0), B2_LEN + 1, f=2.2, zeta=0.22)


def scene_uncomfy(ink, u):
    hk = ease(u, 0.45, 0.95) - ease(u, 2.6, 3.1) * 0.55          # the hand goes up under the collar and mostly stays
    sq = ease(u, 0.2, 0.7)
    wr = _wrig(u)
    sl = B2_SLOSH.at(u)
    w.seat_backdrop(ink, u)
    wp = w.walker(ink, x=530 + 9 * wr, y=486, height=404, step=0.0, hook=hk, squash=sq,
                  bowl_shift=(40 * wr, -9 * abs(wr)), bowl_tilt=-4 * sq - 13 * wr,
                  slosh=sl, wave=clamp(abs(sl) / 7), bowl_bubbles=u, lid=0.5 * ease(u, 0.3, 0.8),
                  phase=u * 2 + 5 * wr, amp=2 + 7 * abs(wr), lean=5 * wr, swing=-14 * wr)
    # Turkey does the same wriggle a beat later, neck twisting under the tin's low roof, inside the panic
    tw = _wrig(u - 1.0)
    on = ease(u, 1.9, 2.2) - ease(u, 3.3, 3.7)
    for b in B2_BEATS:
        _puff(ink, u, b + 0.2, 5)
    w.turkey_reflection(ink, mood="panic", **REFL, t=u, wing=_beat(u, B2_BEATS),
                        neck=lerp(-5 + 5 * math.sin(9 * u), -6 + 24 * tw, on), wattle=B2_WATTLE.at(u) + 8 * math.sin(11 * u),
                        beak=lerp(13 + 6 * math.sin(13 * u), 29, on), ruff=lerp(0.55, 1.0, on))
    w.seat_frame(ink)
    _gauge(ink, B2_NEEDLE.at(u), u)
    w.bolt_mark(ink, 2, size=DIE)
    return wp


# ----------------------------------------------------------- B3 · It is not wet. ---

B3_LEN = SECONDS - T_B3
B3_BEATS = [0.3, 3.5]                              # one in the river, one in dry air: he has not noticed
B3_NEEDLE = _needle(B3_BEATS, B3_LEN + 1)
B3_PACE = 0.45
B3_SLOSH = w.Follower(lambda u: _flip_kick(u) + 7.0 * math.sin(2 * math.pi * B3_PACE * 2 * u), B3_LEN + 1, f=1.5, zeta=0.3)
B3_WATTLE = _wattle(B3_BEATS, B3_LEN + 1)
B3_LIFT = (0.5, 2.0)
B3_X0 = 660
B3_STRIDE = 0.36 * 306


def _b3_lift(u):
    return ease(u, *B3_LIFT)


def _hem(u):
    lf = _b3_lift(u)
    return H if lf <= 0 else int(round((H + 26) * (1 - lf))) - 13


def _hem_passes(y):
    """The moment the lifting river's lower edge goes above height y."""
    u = B3_LIFT[0]
    while u < B3_LIFT[1] and _hem(u) > y:
        u += 1.0 / 96
    return u


def scene_not_wet(ink, u):
    step = u * B3_PACE
    x = B3_X0 - step * B3_STRIDE
    sl = B3_SLOSH.at(u)
    hem = w.seat_backdrop(ink, u, lift=_b3_lift(u))
    # dust under each foot that lands on ground the river has already left
    k = 0
    while True:
        s_land = 0.25 + 0.5 * k
        u_land = s_land / B3_PACE
        if u_land > u:
            break
        if u - u_land < 0.7 and _hem(u_land) < w.GROUND - 30:
            # the foot that lands is a little ahead of the body: near foot on even k, far foot on odd
            fx = B3_X0 - s_land * B3_STRIDE + (-58 if k % 2 == 0 else -22)
            w.dust(ink, fx, w.GROUND + (4 if k % 2 == 0 else -2), u - u_land, size=1.7, toward=1.0)
        k += 1
    wp = w.walker(ink, x=x, step=step, bowl_bubbles=u, slosh=sl, wave=clamp(abs(sl) / 8), phase=u * 4, amp=5)
    # the bubbles of the first beat are rising when the river leaves them: each stops and drops like a pebble
    b0 = B3_BEATS[0]
    w.bubbles(ink, PUFF, u, t0=b0 + 0.2, n=6, size=9.0, rise=190, spread=22, drop_at=_hem_passes(215) + 0.02)
    # the second beat is in dry air: the wings go, the needle drops, and there is nothing for a bubble to be made in
    w.turkey_reflection(ink, mood="panic", t=u, **REFL, wing=_beat(u, B3_BEATS), wattle=B3_WATTLE.at(u))
    w.seat_frame(ink)
    _gauge(ink, B3_NEEDLE.at(u), u)
    w.bolt_mark(ink, 3, size=DIE)
    return wp


# ------------------------------------------------------------------------ the cut ---

SCENES = [(0.0, scene_pick), (T_B1, scene_runs_out), (T_B2, scene_uncomfy), (T_B3, scene_not_wet)]


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    k = max(i for i, (t0, _) in enumerate(SCENES) if t >= t0)
    t0, fn = SCENES[k]
    f = (t - t0) / FLIP
    if k > 0 and f < 1.0:
        # the old card (held on its last frame) is turned over top to bottom; the new scene is on its back
        p0, pfn = SCENES[k - 1]
        pfn(ink, t0 - p0 - 1.0 / FPS)
        o = w.offscreen(ink)
        fn(o, t - t0)
        w.card_flip(ink, o.img, f)
    else:
        fn(ink, t - t0)
    w.badge(ink)


# ------------------------------------------------------------------- test harness ---

if __name__ == "__main__":
    from kit import Film

    out = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("/tmp/c25_scene_turkey")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in sys.argv[2:] if not a.startswith("--")] or [
        0.2, 0.45, 0.9, 1.5, 2.2, 2.62, 3.0, 3.6, 4.4, 5.2, 5.8, 6.3,
        6.7, 7.3, 7.8, 8.2, 8.9, 9.4, 10.2, 10.65, 11.2, 12.0, 12.6, 13.2, 13.8, 14.3, 14.9, 15.4]
    captions = "--captions" in sys.argv
    film = Film("c25_scene_turkey", SECONDS)

    def frame(t, ink):
        draw(t, ink)
        if captions:
            for a, b, text in CAPTIONS:
                if a <= t < b:
                    ink.caption(text, size=27)
    film.picture(frame)
    frames = []
    for tt in times:
        im = film.frame(int(round(tt * film.fps)))
        im.save(out / f"{tt:06.2f}.png")
        frames.append(im)
    cols = 4
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 20))
    for i, im in enumerate(frames):
        sheet.paste(im.resize((480, 270), Image.LANCZOS), ((i % cols) * 480, (i // cols) * 270))
        ImageDraw.Draw(sheet).text(((i % cols) * 480 + 6, (i // cols) * 270 + 4), f"{times[i]:.2f}", fill=(255, 255, 0))
    sheet.save(out / "sheet.png")
    print("wrote", out / "sheet.png")
