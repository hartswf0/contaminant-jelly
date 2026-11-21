#!/usr/bin/env python3
"""cowpaths: Don't Pave the Cow Paths. What a SCION is, where the idea came from, and how it animates.

    python3 cowpaths.py     # assets/dont-pave-the-cow-paths.mp4

The story: Anthropic's engineers replaced Git with a source-control system named Scion, built for agents
that are always online ("Redesigning source control", October 2026). The lesson people drew from it was
"don't pave the cow paths". That changed how these films are made: from one drawing desk doing eight jobs
(MULTIPLANE ANIMATION STUDIO) to a swarm with an independent critic (SCION: AUTONOMOUS ANIMATION STUDIO),
by way of AGENT_FIRST_ARCHITECT_PROMPT. This project borrows the name; it is not Anthropic's.

Each new scene is animated in the method of one animation SCION from ../drawn/scions.json, named on screen:
  the cows          SCION 02  Lotte Reiniger, articulated shadow theater (backlit shapes, pinned joints)
  the flood         SCION 06  John Whitney, harmonic motion (one phase rule moves every dot)
  the word          SCION 07  Peter Foldes, drawn metamorphosis (one line, point for point)
  the river planes  SCION 44  multiplane parallax
  cows and fish     SCION 48  state machines, characters that can refuse
The remaining scenes come from scion_film.py.
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
import scion_film as S
from scion_film import Wd, ink, center, N
from class_cut import W, H, TMP, F, PAPER, INK, MUTE, RUST, TEAL, GOLD, PENCIL, ease, back, lerp, segment, tone, whoosh
from scion_explainer import MONO, SERIF, table, sheet, typed, heading, img, first_render, final_frame, clip

BLACK = (18, 14, 12)


def tag(im, text):
    d = ImageDraw.Draw(im, "RGBA"); w = d.textlength(text, font=F(13, "SemiBold")) + 18
    d.rounded_rectangle((W - w - 12, H - 34, W - 12, H - 10), 6, fill=(14, 18, 20, 170)); d.text((W - w - 3, H - 30), text, font=F(13, "SemiBold"), fill=(236, 226, 204)); return im


# ---------- the shadow theater: cows (SCION 02) ----------
def backlight():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        u = y / H; d.line((0, y, W, y), fill=(int(lerp(246, 222, u)), int(lerp(214, 150, u)), int(lerp(150, 74, u))))
    g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).ellipse((300, 60, 660, 420), fill=120)
    im.paste(Image.new("RGB", (W, H), (255, 240, 200)), (0, 0), g.filter(ImageFilter.GaussianBlur(90))); return im
BACK = backlight()


def ground(x):
    """The hill's contour, which is also the path the cows wear."""
    return 392 + 34 * math.sin(x / 150.0) + 16 * math.sin(x / 57.0 + 1.3)


def cow(d, x, phase, s=1.0, look=0.0):
    """A cut silhouette on pins: body, neck and head, tail, and four two-part legs with limited swing."""
    gy = ground(x); slope = 0.45 * math.atan2(ground(x + 30) - ground(x - 30), 60)
    def P(px, py):                                   # body coordinates to screen, tilted with the hill
        c, sn = math.cos(slope), math.sin(slope); return (x + s * (px * c - py * sn), gy - 58 * s + s * (px * sn + py * c))
    body = [(-52, -4), (-46, -24), (-10, -30), (34, -28), (50, -14), (52, 12), (30, 24), (-34, 24), (-52, 14)]
    d.polygon([P(*p) for p in body], fill=BLACK)
    nod = 8 * math.sin(phase * 2) + look
    head = [(44, -22), (70, -30 + nod), (86, -22 + nod), (88, -8 + nod), (72, -4 + nod), (52, -6)]
    d.polygon([P(*p) for p in head], fill=BLACK); d.polygon([P(66, -32 + nod), P(70, -46 + nod), P(74, -31 + nod)], fill=BLACK)   # horn
    d.polygon([P(74, -30 + nod), P(84, -40 + nod), P(80, -27 + nod)], fill=BLACK)                                                   # ear
    sw = 14 * math.sin(phase * 2 + 1); d.line([P(-50, -18), P(-64, -6 + sw * 0.3), P(-66, 14 + sw)], fill=BLACK, width=max(2, int(4 * s)))
    d.ellipse((P(10, 18)[0] - 9 * s, P(10, 18)[1], P(10, 18)[0] + 9 * s, P(10, 18)[1] + 12 * s), fill=BLACK)                        # udder
    for hx, off in ((-38, 0.0), (-26, math.pi), (30, math.pi / 2), (42, 3 * math.pi / 2)):
        a = max(-0.5, min(0.5, 0.45 * math.sin(phase + off))); k = max(0.0, 0.5 * math.sin(phase + off + 1.2))
        hip = P(hx, 18); knee = (hip[0] + s * 24 * math.sin(a), hip[1] + s * 24 * math.cos(a)); foot = (knee[0] + s * 24 * math.sin(a - k), knee[1] + s * 24 * math.cos(a - k))
        d.line([hip, knee, foot], fill=BLACK, width=max(3, int(9 * s))); d.ellipse((hip[0] - 4, hip[1] - 4, hip[0] + 4, hip[1] + 4), fill=(120, 84, 40))


def house(d, x, u):
    gy = ground(x); h = 46 * u; d.polygon([(x - 22, gy), (x - 22, gy - h), (x, gy - h - 20 * u), (x + 22, gy - h), (x + 22, gy)], fill=BLACK)
    if u > 0.9: d.rectangle((x - 6, gy - 26, x + 6, gy - 12), fill=(250, 220, 140))


def s_cows(t):
    im = BACK.copy(); d = ImageDraw.Draw(im)
    d.polygon([(0, H)] + [(x, ground(x) + 70 + 20 * math.sin(x / 90.0)) for x in range(0, W + 1, 12)] + [(W, H)], fill=(120, 78, 40))        # far hill
    d.polygon([(0, H)] + [(x, ground(x)) for x in range(0, W + 1, 6)] + [(W, H)], fill=(44, 30, 20))
    lead = -80 + 62 * t                                    # the first cow's place
    worn = min(W, max(0, lead - 20))
    if worn > 0:                                           # the path the hooves wear, following every dip
        pave = ease((t - 21.0) / 5.0); col = (150, 150, 150) if t > 21.0 else (176, 132, 74)
        d.line([(x, ground(x) + 2) for x in range(0, int(worn), 6)], fill=(176, 132, 74), width=5)
        if pave > 0: d.line([(x, ground(x) + 2) for x in range(0, int(W * pave), 6)], fill=col, width=11)
    for k, hx in enumerate((150, 330, 520, 700, 860)):
        u = ease((t - 11.0 - k * 1.2) / 1.2)
        if u > 0: house(d, hx, u)
    for k in range(5):
        x = lead - k * 150
        if -120 < x < W + 120: cow(d, x, t * 4.2 + k * 0.9)
    if t > 21.0:                                           # the roller paves the same crooked line
        rx = W * ease((t - 21.0) / 5.0); gy = ground(rx); d.ellipse((rx - 26, gy - 50, rx + 26, gy + 2), fill=BLACK); d.rectangle((rx - 60, gy - 66, rx - 6, gy - 30), fill=BLACK); d.ellipse((rx - 62, gy - 26, rx - 34, gy + 2), fill=BLACK)
    if t > 27.0:                                           # where the road should have gone
        u = ease((t - 27.0) / 2.0); d.line((40, 330, 40 + (W - 80) * u, 330), fill=(255, 250, 230), width=4)
        for x in range(60, int(40 + (W - 80) * u), 40): d.line((x, 330, x, ground(x)), fill=(255, 250, 230), width=1)
    d = ImageDraw.Draw(im)
    if 2.0 < t < 11.0: d.text((40, 30), "Cows walk where the walking is easy.", font=F(30), fill=BLACK)
    if 11.0 <= t < 21.0: d.text((40, 30), "A town grows along the path they wore.", font=F(30), fill=BLACK)
    if 21.0 <= t < 27.0: d.text((40, 30), "The easy thing is to pave it.", font=F(30), fill=BLACK)
    if t >= 27.0: d.text((40, 30), "DON'T PAVE THE COW PATHS.", font=F(44), fill=BLACK); d.text((42, 86), "Ask where the road should go.", font=F(26), fill=(90, 50, 20))
    return tag(im, "animated with SCION 02 · Reiniger shadow theater")


# ---------- the flood (SCION 06) ----------
def s_flood(t):
    im = Image.new("RGB", (W, H), (12, 18, 22)); d = ImageDraw.Draw(im)
    f = ease((t - 3.0) / 12.0); merges = int(lerp(2500, 30000, f)); n = int(merges / 12)
    th = 0.11 * t                                          # one phase rule: dot i turns i times as fast as dot 1
    for i in range(1, n + 1):
        a = i * th * 0.02 + i * 2.39996; r = 14 + 250 * math.sqrt(i / 2500.0) * (0.86 + 0.14 * math.sin(i * th * 0.05))
        x = 600 + r * math.cos(a); y = 290 + r * 0.82 * math.sin(a); c = PENCIL if i % 12 else (255, 250, 230)
        d.point((x, y), fill=c); d.point((x + 1, y), fill=c)
    d.rounded_rectangle((574, 268, 626, 312), 6, fill=PAPER); d.ellipse((590, 276, 610, 296), outline=INK, width=3); d.ellipse((597, 283, 603, 289), fill=INK)   # one reader
    d.text((40, 26), "WHERE THE NAME COMES FROM", font=F(30), fill=PAPER)
    d.text((40, 110), "%s" % format(merges, ","), font=F(84), fill=PENCIL); d.text((44, 204), "code changes merged each day", font=F(20, "SemiBold"), fill=PAPER)
    d.text((44, 232), "at Anthropic, May to September 2026" if f < 1 else "at Anthropic, by September 2026", font=F(16, "SemiBold"), fill=(170, 180, 180))
    lines = [(16.5, "Git was built for a person at a desk"), (16.5, "who might go offline."), (20.5, "The clients were agents, always online."), (24.5, "So they built source control"), (24.5, "for machines first. They named it Scion.")]
    y = 290
    for at, ln in lines:
        if t > at: d.text((44, y), ln, font=SERIF(23), fill=PAPER)
        y += 30
    if t > 29.5: d.text((44, 462), "Writing was no longer the bottleneck. Reading was.", font=F(22), fill=PENCIL)
    d.text((44, 492), "source: Anthropic, \"Redesigning source control\", 2026.", font=F(13, "SemiBold"), fill=(150, 160, 160)); d.text((44, 510), "This project borrows the name. It is not Anthropic's.", font=F(13, "SemiBold"), fill=(150, 160, 160))
    return tag(im, "animated with SCION 06 · Whitney harmonic motion")


# ---------- the word (SCION 07) ----------
def poly(points, n=120):
    """Resample a polyline to n points by arc length, so every drawing has the same points to match."""
    seg = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]; total = sum(seg); out = []; i = 0; acc = 0.0
    for k in range(n):
        target = total * k / (n - 1)
        while i < len(seg) - 1 and acc + seg[i] < target: acc += seg[i]; i += 1
        u = (target - acc) / seg[i] if seg[i] else 0; a, b = points[i], points[i + 1]; out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


SEED = poly([(480, 400), (462, 386), (456, 362), (468, 340), (480, 332), (492, 340), (504, 362), (498, 386), (480, 400)])
SPROUT = poly([(480, 420), (480, 360), (478, 320), (450, 296), (430, 300), (452, 316), (478, 320), (482, 290), (508, 262), (530, 266), (506, 288), (482, 300), (480, 250), (480, 230)])
SHOOT = poly([(470, 420), (476, 330), (440, 300), (476, 322), (480, 250), (462, 214), (482, 240), (486, 200), (490, 240), (512, 212), (492, 250), (488, 322), (520, 296), (490, 334), (492, 420)])
GRAFT = poly([(440, 470), (444, 380), (430, 372), (500, 372), (488, 380), (492, 344), (486, 300), (452, 268), (486, 290), (490, 230), (470, 190), (492, 220), (498, 176), (502, 222), (528, 190), (506, 236), (500, 292), (536, 264), (504, 304), (512, 344), (520, 380), (524, 470)])
TREE = poly([(450, 470), (458, 360), (400, 300), (372, 240), (402, 280), (396, 200), (424, 262), (450, 300), (452, 200), (430, 130), (462, 180), (480, 110), (498, 180), (530, 130), (508, 200), (510, 300), (540, 256), (566, 196), (560, 276), (590, 236), (566, 304), (506, 360), (512, 470)])
STAGES = [(0.0, SEED), (4.0, SEED), (7.0, SPROUT), (10.5, SPROUT), (13.5, SHOOT), (17.0, SHOOT), (20.0, GRAFT), (24.5, GRAFT), (27.5, TREE), (40.0, TREE)]


def s_word(t):
    k = ink(); k.paper(); d = k.d
    for i in range(len(STAGES) - 1):
        (a, A), (b, B) = STAGES[i], STAGES[i + 1]
        if a <= t <= b:
            u = ease((t - a) / (b - a)); pts = [(p[0] + (q[0] - p[0]) * u + 200, p[1] + (q[1] - p[1]) * u) for p, q in zip(A, B)]; break
    d.line(pts, fill=(40, 40, 44), width=5, joint="curve")
    if 17.0 < t < 27.5: d.line((630, 372, 700, 372), fill=RUST, width=3); d.text((716, 360), "the graft", font=F(17, "SemiBold"), fill=RUST)
    d.text((40, 28), "scion", font=F(84), fill=INK); d.text((270, 74), "/ˈsīən/", font=SERIF(34), fill=MUTE)
    rows = [(1.0, "from a root meaning", "to burst out, to sprout"), (7.0, "Old French cion", "a shoot, a twig"), (13.5, "in the orchard", "a shoot cut from one tree"),
            (20.0, "", "and grafted onto the roots of another"), (27.5, "later", "a descendant, an heir")]
    y = 150
    for at, a, b in rows:
        if t > at:
            if a: d.text((40, y), a, font=F(16, "SemiBold"), fill=MUTE)
            typed(d, (40, y + 22), b, SERIF(28), INK, (t - at) / 1.2)
        y += 66
    if t > 32.0: d.text((40, 488), "\"a mere scion of the evil principle\"   Mary Shelley, Frankenstein, 1818", font=SERIF(19), fill=MUTE)
    return tag(k.img.convert("RGB"), "animated with SCION 07 · Foldès drawn metamorphosis")


# ---------- the turn: my own cow path ----------
def s_turn(t):
    im = table(); d = sheet(im, (110, 110, 850, 440))
    d.text((150, 136), "Seeing that changed my work.", font=F(40), fill=INK)
    if t > 3.4: d.text((150, 206), "I was animating with one prompt.", font=SERIF(32), fill=INK)
    if t > 6.6: d.text((150, 252), "One model. Eight jobs. One after another.", font=SERIF(32), fill=INK)
    if t > 10.6: d.text((150, 330), "That was my cow path.", font=F(46), fill=RUST)
    return im


# ---------- cows and fish (SCION 48) ----------
def s_cowfish(t):
    k = ink(); Wd.river(k, t, planes=("back", "far", "bed"))
    im = k.img.convert("RGB"); top = BACK.crop((0, 0, W, 230)); im.paste(top, (0, 0)); d = ImageDraw.Draw(im)
    gy = lambda x: 178 + 10 * math.sin(x / 90.0)
    d.polygon([(0, 230)] + [(x, gy(x)) for x in range(0, W + 1, 8)] + [(W, 230)], fill=(44, 30, 20)); d.line([(x, gy(x) + 2) for x in range(0, W + 1, 8)], fill=(150, 150, 150), width=7)
    d.rectangle((700, 110, 712, 190), fill=BLACK); d.line((706, 150, 640 if int(t * 0.5) % 2 else 706, 150 if int(t * 0.5) % 2 else 110), fill=BLACK, width=6)       # one gate
    global ground; g0 = ground; ground = gy
    for j in range(6):                                    # single file: each waits for the one in front
        x = 640 - j * 96 + (18 * ((t * 0.5) % 1.0) if int(t * 0.5) % 2 else 0); cow(d, x, (t * 4 if int(t * 0.5) % 2 else 0) + j, s=0.62)
    ground = g0
    d.text((24, 14), "ONE AT A TIME", font=F(26), fill=BLACK); d.text((24, 246), "ALL AT ONCE", font=F(26), fill=PAPER)
    k2 = kit_ink(im)
    for j in range(9):                                    # the school: every builder swims its own line
        x = (j * 137 + t * (60 + 9 * (j % 4))) % 1100 - 70; y = 300 + (j * 53) % 170 + 8 * math.sin(t * 2 + j)
        Wd.trout(k2, x, y, length=120 + 10 * (j % 3), angle=4 * math.sin(t * 2 + j), flip=True, phase=t * 4 + j)
    # the critic at the right: watches, refuses once, then passes
    st = "WATCH" if t < 13.0 else ("REFUSE" if t < 19.0 else ("WATCH" if t < 24.0 else "PASS"))
    turn = 150 if st == "REFUSE" else 0
    Wd.trout(k2, 820, 420, length=230, angle=turn, phase=t * 1.5, amp=3.0)
    bx = lerp(520, 660, ease((t - 9.0) / 4.0)) if t < 19.0 else lerp(430, 660, ease((t - 20.0) / 4.0))
    Wd.trout(k2, bx, 430, length=130, angle=0, flip=True, phase=t * 5)
    im = k2.img.convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle((bx + 60, 404, bx + 108, 432), fill=PAPER, outline=INK)                         # the builder's film
    cols = {"WATCH": PENCIL, "REFUSE": RUST, "PASS": (120, 214, 200)}
    for j, s in enumerate(("WATCH", "REFUSE", "PASS")):
        on = s == st; d.rounded_rectangle((690 + j * 88, 252, 690 + j * 88 + 82, 284), 8, fill=cols[s] if on else None, outline=cols[s], width=2); center(d, 731 + j * 88, 259, s, F(14), INK if on else cols[s])
    if t > 13.0: d.text((24, 484), "The critic built nothing. It can refuse.", font=F(24), fill=PAPER)
    return tag(im, "animated with SCION 48 · characters that can refuse")


def kit_ink(im):
    k = ink(); k.img.paste(im.convert(k.img.mode)); k.d = ImageDraw.Draw(k.img, "RGBA"); return k


def s_close(t):
    im = BACK.copy(); d = ImageDraw.Draw(im)
    d.polygon([(0, H)] + [(x, ground(x)) for x in range(0, W + 1, 6)] + [(W, H)], fill=(44, 30, 20))
    for k in range(3): cow(d, 250 + k * 170, 0.4 * math.sin(t + k), look=-6)
    d.text((40, 40), "DON'T PAVE", font=F(64), fill=BLACK); d.text((40, 112), "THE COW PATHS.", font=F(64), fill=BLACK)
    if t > 3.0: d.text((44, 200), "Graft a new shoot.", font=F(34), fill=(90, 50, 20))
    return tag(im, "animated with SCION 02 · Reiniger shadow theater")


def planes(t): return tag(S.s_planes(t), "animated with SCION 44 · multiplane parallax")


if __name__ == "__main__":
    parts = [
        segment("c_cows", 31.5, s_cows, [(1.6, "Cows walk where the walking is easy. Over years, their hooves wear a path.", N), (11.0, "A town grows along that path.", N),
                                        (15.4, "Then somebody has to build a road.", N), (21.0, "The easy thing is to pave the path the cows made.", N), (27.0, "Don't pave the cow paths. Ask where the road should go.", N)],
                sfx=[(tone, (27.0, 196))]),
        segment("c_flood", 34.0, s_flood, [(0.6, "In twenty twenty six, Anthropic was merging about twenty five hundred code changes a day.", N), (7.6, "Four months later, it was more than thirty thousand.", N),
                                          (12.4, "Its own agents were writing the code.", N), (16.5, "Git was built for a person at a desk, who might go offline.", N),
                                          (20.5, "But the clients were agents now, always online.", N), (24.5, "So they did not patch Git. They built source control for machines first, and named it Scion.", N),
                                          (30.2, "Writing was no longer the bottleneck. Reading was.", N)]),
        segment("c_word", 37.5, s_word, [(0.8, "Scion is an old word. It comes from a root that means to burst out, to sprout.", N), (7.0, "In Old French, a shoot. A twig.", N),
                                        (13.5, "In the orchard, a scion is a shoot cut from one tree,", N), (20.0, "and grafted onto the roots of another.", N), (27.5, "Later it came to mean a descendant. An heir.", N),
                                        (32.2, "Mary Shelley used it for her creature's idea of mankind.", N)]),
        segment("c_turn", 15.0, s_turn, [(0.5, "Seeing that changed my work.", N), (3.4, "I was animating with one prompt. One model. Eight jobs, one after another.", N), (10.6, "That was my cow path.", N)], sfx=[(tone, (10.5, 150, 0.4, 0.5))]),
        segment("s_desk", 23.5, S.s_desk, [(0.6, "Here is that prompt. It tells one model to be the whole studio.", N), (5.6, "Eight jobs, one model.", N),
                                          (12.0, "Its rule is simple. Draw. Look. Compare. Adjust. Draw again.", N), (19.0, "Do not try to finish the shot in one drawing.", N)]),
        segment("s_keys", 24.5, S.s_keys, [(0.6, "It draws the key poses first. Four drawings tell the whole leap.", N), (8.0, "Then the breakdowns. They say how the move happens.", N),
                                          (12.0, "Then the in-betweens, close together where the fish is slow.", N), (17.0, "Play them, and the fish jumps.", N),
                                          (19.6, "A drawing means something because of the drawing before it and the drawing after it.", N)]),
        segment("s_planes", 17.5, planes, [(0.6, "It builds depth in planes. Watch the camera move.", N), (4.4, "Near layers move more. Far layers move less.", N), (9.4, "The craft was never the problem.", N)]),
        segment("s_problem", 20.5, S.s_problem, [(0.6, "The problem was the desk. It does one job at a time.", N), (3.4, "Ask it for a hundred times more, and the hard part is no longer drawing.", N), (9.8, "It is watching.", N),
                                                (15.5, "And the desk checks its own work. It cannot see what it cannot see.", N)]),
        segment("s_four", 24.5, S.s_four, [(0.4, "So I wrote a second prompt. It asks four questions of any way of working.", N), (5.0, "Where does the work live?", N),
                                          (7.2, "Who works when?", N), (11.8, "Who checks?", N), (16.4, "And when do we look?", N), (20.4, "Move verification from syntax to invariants.", N)]),
        segment("s_chain", 23.0, S.s_chain, [(0.4, "Put the animation desk through those questions, and you get a SCION.", N), (5.0, "It owns the whole viewing experience. It coordinates a swarm. It keeps the project state.", N),
                                            (12.0, "It tests against references you can inspect. It improves through independent critique.", N), (18.4, "And it delivers a finished film.", N)]),
        segment("s_laws", 29.0, S.s_laws, [(0.6, "It has fifteen laws.", N), (12.0, "Law three. Prove the production method early. Build the hardest passage first.", N),
                                          (17.5, "Law nine. Never let the builder award the pass.", N), (22.5, "Law fourteen. Every finding is measured, structural, judged, or unknown.", N)]),
        segment("c_cowfish", 29.0, s_cowfish, [(0.6, "Cows go one at a time. Every one waits at the same gate.", N), (6.4, "Fish go all at once. Each builder swims its own line.", N),
                                              (11.6, "One fish built nothing. It only watches.", N), (15.0, "And it can refuse.", N), (20.0, "The builder goes back, repairs the cause, and comes again.", N), (25.0, "Now it passes.", N)],
                sfx=[(tone, (13.2, 130, 0.4, 0.5)), (tone, (24.2, 392))]),
        segment("s_how", 37.0, S.s_how(img(S.ST + "08_props.png"), img(S.ST + "12_wheel.png"), first_render(30.5, "hb"), final_frame(30.5, "ha")),
                [(0.4, "So how does a SCION animate? The craft does not go away. It is grafted onto a swarm.", N), (6.6, "One agent builds the world. The planes. The pieces.", N),
                 (12.0, "Other agents build the performances, from keys and timing.", N), (17.0, "An editor keeps a cut you can always play.", N),
                 (21.4, "And a critic who built nothing watches it at normal speed.", N), (25.6, "Every performance starts with a situation and an intention, and ends with a consequence.", N), (32.5, "Do not smooth away intention.", N)]),
        clip(9.0, 28.0),
        segment("s_end", 10.5, S.s_end, [(0.6, "Make every important claim about quality answerable by opening the work and watching it.", N)]),
        segment("c_close", 8.0, s_close, [(0.6, "Don't pave the cow paths.", N), (3.0, "Graft a new shoot.", N)], sfx=[(tone, (3.0, 262))]),
    ]
    lst = TMP + "/c.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts)); out = "assets/dont-pave-the-cow-paths.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
