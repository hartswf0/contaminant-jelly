"""m33 · the MAKING film for porthole 33 · Salon · "Velvet iris frame around culvert bar shadows".

The writing of the sheet that c33 staged: one Porthole Log passing through three children (swarm/m33/board.md
lists the traces of working that are really on the sheet).

   0.0 .. 32.0   the pilot, L.: page 1                                    swarm/m33/scene_pilot.py
  32.0 .. 33.0   THE PASS, left: whip along the row
  33.0 .. 56.0   the first friend, E.: Turkey's seat                      swarm/m33/scene_turkey.py
  56.0 .. 57.0   THE PASS, left again: whip
  57.0 .. 80.0   the next friend, E.: the trout's side                    swarm/m33/scene_trout.py
  80.0 .. 90.0   the ending: hold on the last desk, then cam.rise to the whole room; the die is not thrown.

Written by hand after the swarm's editor unit stopped (usage limit); modelled on m10.py and m25.py.
Sound is synthesized with the kit's Mix. Foraged pieces come only through c33's world: credits/m33.json.

  python3 films/m33.py      -> assets/films/m33.mp4
"""
from __future__ import annotations

import importlib.util, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "swarm" / "c33"))
from kit import Film, ramp  # noqa: E402
import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c33 world; not edited)

M = HERE / "swarm" / "m33"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


SP = _load("m33_scene_pilot", M / "scene_pilot.py")
ST = _load("m33_scene_turkey", M / "scene_turkey.py")
SR = _load("m33_scene_trout", M / "scene_trout.py")
W, H = 960, 540
PASS = 1.0
T_TURKEY = SP.SECONDS + PASS
T_TROUT = T_TURKEY + ST.SECONDS + PASS
T_END = T_TROUT + SR.SECONDS
END_SECONDS = 10.0
SECONDS = round(T_END + END_SECONDS, 3)

CAPTIONS = [(a, b, s) for a, b, s in SP.CAPTIONS] + [(T_TURKEY + a, T_TURKEY + b, s) for a, b, s in ST.CAPTIONS] + \
           [(T_TROUT + a, T_TROUT + b, s) for a, b, s in SR.CAPTIONS]
CAPTIONS = sorted((round(a, 3), round(b, 3), s) for a, b, s in CAPTIONS)
_last = {}


def _f(mod, t):
    k = (mod.__name__, round(t, 3))
    if k not in _last:
        if len(_last) > 6: _last.clear()
        _last[k] = mod.frame(t).convert("RGB")
    return _last[k]


def _pass(a_mod, b_mod, u):
    return cam.whip(_f(a_mod, a_mod.SECONDS - 1e-3), _f(b_mod, 0.0), ramp(u, 0.1, 0.9), direction=-1)


HERO_BOX = (385, 268, 577, 376)
_room_cache = {}


def _room(t):
    k = int(t * 12)
    if k not in _room_cache:
        if len(_room_cache) > 3: _room_cache.clear()
        im = Image.new("RGB", (W, H)); P.classroom(im, k / 12.0, cup_at="hero"); _room_cache[k] = im
    return _room_cache[k]


def _ending(e):
    last = _f(SR, SR.SECONDS - 1e-3)
    if e < 2.5:
        return last
    u = cam.smooth(ramp(e, 2.5, 8.0)); room = _room(e)
    if u >= 1:
        return room
    a = last
    melt = cam.smooth((u - 0.5) / 0.42)
    if melt > 0.004:
        a = Image.blend(a, room.crop(HERO_BOX).resize((W, H), Image.BICUBIC), melt)
    return cam.rise(a, room, u, box=HERO_BOX, tip=26, sway=5)


def picture(t):
    if t < SP.SECONDS: return SP.frame(t)
    if t < T_TURKEY: return _pass(SP, ST, t - SP.SECONDS)
    if t < T_TURKEY + ST.SECONDS: return ST.frame(t - T_TURKEY)
    if t < T_TROUT: return _pass(ST, SR, t - T_TURKEY - ST.SECONDS)
    if t < T_END: return SR.frame(t - T_TROUT)
    return _ending(t - T_END)


film = Film("m33", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + 8.0


@film.picture
def frame(t, ink):
    ink._grain = False
    fr = picture(t)
    ink.img.paste(fr if fr.mode == "RGB" else fr.convert("RGB")); ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)
    for a, b, text in CAPTIONS:
        if a <= t < b:
            ink.caption(text, size=27); break


@film.sound
def sound(mix):
    mix.room(0, SECONDS, 0.018)
    mix.murmur(0, SECONDS, 0.03, 150, 0.0, seed=33)                  # a room of children, far off
    rs = np.random.RandomState(33)
    for a, b, _ in CAPTIONS:                                         # pencil working up to each finished line
        for k in range(int((min(2.4, a) ) * 9)):
            mix.click(max(0, a - 2.4) + k / 9.0 + rs.uniform(0, 0.05), 0.035, rs.uniform(-0.2, 0.2), 3200, 0.025)
    for at in (SP.SECONDS, T_TURKEY + ST.SECONDS):                   # the passes: paper and a chair
        mix.whoosh(at, 0.8, 0.12, -0.3); mix.thud(at + 0.6, 160, 0.06, 0.0, 0.2)
    mix.drone(T_TURKEY + 3, ST.SECONDS - 6, (55, 82.5), 0.04)        # inside the tin
    mix.water(T_TROUT + 3, SR.SECONDS - 6, 0.06)                     # in the river
    mix.reverb(0.18)


if __name__ == "__main__":
    film.render()
