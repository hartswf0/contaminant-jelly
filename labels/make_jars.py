# Make jars in the same hand as the periodic-table jars (labels/cineosis/*.svg): the same body, lid, reel and film strip,
# the CONTAMINANT label and the small jelly; a new symbol, icon, name and line for each drift, archive level and bonus.
# Text is set as glyph outlines (DejaVu Serif Bold / DejaVu Sans Bold), so the jars need no fonts when used as images.
#   python3 labels/make_jars.py     -> labels/jars/<id>.svg
import copy, json, os, re, xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from cartoons import cartoon
HERE = os.path.dirname(os.path.abspath(__file__)); NS = 'http://www.w3.org/2000/svg'; ET.register_namespace('', NS)
SERIF = TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'); SANS = TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
TEMPLATE = os.path.join(HERE, 'cineosis', 'sign-29-wd.svg'); OUT = os.path.join(HERE, 'jars'); os.makedirs(OUT, exist_ok=True)

def glyphs(font, text, size, x0, y, maxw, fill, anchor='middle', squeeze=1.0):
    """Lay out text as <path> glyphs: returns (g element, width)."""
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font['hmtx']; upm = font['head'].unitsPerEm
    items, adv = [], 0
    for ch in text:
        gn = cmap.get(ord(ch));
        if gn is None: gn = cmap.get(ord(' '))
        pen = SVGPathPen(gs); gs[gn].draw(pen); items.append((pen.getCommands(), adv)); adv += hmtx[gn][0]
    sx = size / upm * squeeze; w = adv * sx
    if w > maxw: sx *= maxw / w; w = maxw
    sy = size / upm; left = x0 - w / 2 if anchor == 'middle' else x0
    g = ET.Element(f'{{{NS}}}g', {'fill': fill})
    for d, a in items:
        if d: ET.SubElement(g, f'{{{NS}}}path', {'d': d, 'transform': f'translate({left + a * sx:.2f} {y}) scale({sx:.6f} {-sy:.6f})'})
    return g, w

# palettes taken from the periodic-table jars (body, accent), so the new jars sit on the same shelf
def palettes():
    P = []
    for f in sorted(os.listdir(os.path.join(HERE, 'cineosis'))):
        if not f.endswith('.svg'): continue
        r = ET.parse(os.path.join(HERE, 'cineosis', f)).getroot(); ch = list(r)
        body = next((c.get('fill') for c in ch if c.tag.endswith('path') and c.get('fill', '').startswith('#') and c.get('fill') != '#F7E4BF'), None)
        acc = next((c.get('fill') for c in ch[4:8] if c.get('fill', '').startswith('#') and c.get('fill') not in (body, '#F7E4BF')), None)
        if body and acc and (body, acc) not in P: P.append((body, acc))
    return P

def icon(kind, D, A):   # drawn in the 0..100 box the template's icons use
    S = lambda d, w=6, c=D: f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    F = lambda d, c=D: f'<path d="{d}" fill="{c}"/>'
    C = lambda x, y, r, c=A: f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'
    I = {
      'ascent': F('M18 78H82V68H18Z') + F('M28 62H72V52H28Z') + F('M38 46H62V36H38Z') + C(50, 22, 8) + S('M50 6V10M30 14L34 18M70 14L66 18', 4, A),
      'pairs': f'<ellipse cx="32" cy="48" rx="20" ry="26" fill="{A}"/><ellipse cx="68" cy="48" rx="20" ry="26" fill="{D}"/>' + S('M50 22V74', 4, '#F7E4BF'),
      'lure': S('M14 84Q16 34 56 26Q78 24 80 40', 5) + C(80, 52, 10) + F('M20 70L30 60L40 70L50 60L60 70L70 60L80 70V78H20Z'),
      'surface': S('M6 22Q20 12 34 22T62 22T90 22', 5, A) + F('M34 70A16 16 0 0 1 66 70Z') + S('M42 74V88M50 74V90M58 74V88', 4) + C(72, 44, 4) + C(80, 32, 3),
      'halo': f'<ellipse cx="50" cy="52" rx="38" ry="16" fill="none" stroke="{A}" stroke-width="6"/>' + ''.join(F(f'M{x - 7} {y - 6}H{x + 7}V{y + 6}H{x - 7}Z') for x, y in [(50, 22), (14, 44), (86, 44), (26, 74), (74, 74)]),
      'rayrun': F('M8 48Q40 20 92 46Q40 34 8 48ZM8 48Q40 76 92 50Q40 62 8 48Z') + S('M92 48H100', 4) + S('M10 82H40M20 90H54', 4, A),
      'slices': ''.join(F(f'M{12 + k * 24} {12 + k * 24}H{46 + k * 24}V{36 + k * 24}H{12 + k * 24}Z') + F(f'M{18 + k * 24} {28 + k * 24}L{40 + k * 24} {18 + k * 24}V{32 + k * 24}Z', A) for k in range(3)),
      'caves': F('M4 90V40Q4 10 26 10Q48 10 48 40V90H38V44Q38 26 26 26Q14 26 14 44V90Z') + F('M52 90V40Q52 10 74 10Q96 10 96 40V90H86V44Q86 26 74 26Q62 26 62 44V90Z') + C(26, 72, 6) + C(74, 72, 6),
      'bloom': ''.join(C(50 + 26 * __import__('math').cos(a * 1.0472), 50 + 26 * __import__('math').sin(a * 1.0472), 13, A if a % 2 else D) for a in range(6)) + C(50, 50, 10, '#F7E4BF'),
      'descent': S('M14 14L50 34L86 14', 6) + S('M24 40L50 56L76 40', 6) + S('M34 64L50 74L66 64', 6) + C(50, 88, 5),
      'silt': S('M4 70Q16 62 28 70T52 70T76 70T100 70', 5) + S('M4 84Q16 76 28 84T52 84T76 84T100 84', 5, A) + S('M50 60Q46 36 62 24', 4) + C(64, 20, 7),
      'doodles': S('M10 70C20 20 36 86 48 42S74 18 86 60', 6) + S('M18 30Q28 18 38 30', 4, A) + C(84, 22, 6),
      'menagerie': F('M18 50Q40 24 70 50Q40 76 18 50Z') + F('M70 50L90 34V66Z') + C(32, 46, 4, '#F7E4BF') + S('M60 18L66 28L72 18', 4, A),
      'bolas': C(22, 66, 14, D) + C(78, 66, 14, A) + S('M22 54Q50 4 78 54', 4) + C(50, 26, 5, D),
      'strata': F('M6 18H94V26H6Z') + F('M6 34H94V40H6Z', A) + F('M6 48H94V60H6Z') + F('M6 68H94V72H6Z', A) + F('M6 80H94V90H6Z'),
      'spectrum': ''.join(F(f'M{8 + k * 18} {86 - 12 * k}H{22 + k * 18}V90H{8 + k * 18}Z', A if k % 2 else D) for k in range(5)),
      'reel': f'<circle cx="50" cy="50" r="40" fill="{D}"/>' + ''.join(C(50 + 22 * __import__('math').cos(a * 1.2566), 50 + 22 * __import__('math').sin(a * 1.2566), 9, '#F7E4BF') for a in range(5)) + C(50, 50, 7, A),
      'sewer': f'<circle cx="50" cy="50" r="40" fill="none" stroke="{D}" stroke-width="8"/><circle cx="50" cy="50" r="24" fill="none" stroke="{A}" stroke-width="5"/>' + S('M18 52Q30 40 42 52T66 52T84 50', 5),
      'medusae': F('M20 52A30 30 0 0 1 80 52Z') + S('M30 58Q24 72 32 86M44 58Q40 74 46 92M56 58Q60 74 54 92M70 58Q76 72 68 86', 4, A),
      'worms': S('M6 26Q20 14 34 26T62 26T94 26', 6) + S('M6 50Q20 38 34 50T62 50T94 50', 6, A) + S('M6 74Q20 62 34 74T62 74T94 74', 6),
    }
    return I[kind]

JARS = [  # id, symbol, name, line, icon, alt text
  ('ascent', 'At', 'Ascent', 'DRIFT  /  DESIGN V2', 'ascent', 'Rise through galleries of sleeping films; brushing wakes them.'),
  ('pairs', 'Pa', 'Pairs', 'DRIFT  /  DESIGN V4', 'pairs', 'Every pair is a cut: take a frame from both.'),
  ('lure', 'Lu', 'Lure', 'DRIFT  /  DESIGN V5', 'lure', 'The angler patrols, warns twice, lunges.'),
  ('surface', 'Ts', 'Toward the Surface', 'DRIFT  /  DESIGN V6', 'surface', 'The first film is enormous: stop and watch.'),
  ('halo', 'Ha', 'Halo', 'DRIFT  /  NEON BUTTERFLY 02', 'halo', 'The halo turns; take frames as it comes round.'),
  ('rayrun', 'Rr', 'Ray Run', 'DRIFT  /  NIGHT BUS 03', 'rayrun', 'Ride under the ray for a slipstream.'),
  ('slices', 'Sl', 'Slices', 'DRIFT  /  NIGHT BUS 06', 'slices', 'One film laid out in time; take its slices in order.'),
  ('caves', 'Tc', 'Twin Caves', 'DRIFT  /  NIGHT BUS 08', 'caves', 'A rock tongue splits the water into two caves.'),
  ('bloom', 'Bm', 'Bloom', 'DRIFT  /  NIGHT BUS 13', 'bloom', 'Watching is the game: hold, and it blooms.'),
  ('descent', 'Ld', 'The Long Descent', 'DRIFT  /  NIGHT BUS 14', 'descent', 'The light closes in; films show near you or when you pulse.'),
  ('silt', 'Si', 'Silt Bench', 'DRIFT  /  NIGHT BUS 17', 'silt', 'Films lie buried; swim low or pulse to stir them up.'),
  ('doodles', 'Dd', 'Secondhand Doodles', 'ARCHIVE  /  86 DRAWINGS', 'doodles', 'Traced drawings swim as eels and schools.'),
  ('menagerie', 'Mn', 'Menagerie', 'ARCHIVE  /  86 CREATURES', 'menagerie', 'All 86 drawings alive as creatures.'),
  ('bolas', 'Bo', 'Bolas', 'ARCHIVE  /  321 PLANES', 'bolas', 'Drawn planes replayed along their own tracks.'),
  ('strata', 'St', 'Strata', 'ARCHIVE  /  1900S TO 2020S', 'strata', 'The oldest footage at the floor, the newest at the surface.'),
  ('spectrum', 'Sc', 'Spectrum', 'ARCHIVE  /  BY COLOUR', 'spectrum', 'The archive sorted by its own colour.'),
  ('reel', 'Fr', 'Film-Reel Jelly', 'BONUS  /  AFTERLIGHT', 'reel', 'A 3D film-reel jellyfish of pixel flecks.'),
  ('sewer', 'Sw', 'Sentinel Timeworm', 'BONUS  /  SEWER CONDUIT', 'sewer', 'A timeworm in the sewer conduit of lost video.'),
  ('medusae', 'Me', 'Afterlight Medusae', 'BONUS  /  12-REEL VOYAGE', 'medusae', 'An abyssal cinema tunnel, an anglerfish, twelve reels.'),
  ('worms', 'Rw', 'Raw Doodle Worms', 'BONUS  /  PERIODIC TABLE', 'worms', 'Raw doodle worms swim the periodic table.'),
  ('subjects', 'Su', 'The Subjects', 'ARCHIVE  /  PEOPLE TO CROWDS', 'subjects', 'People, machines, landscapes, animals, screens, crowds.'),
]

def jelly(k, D, A):   # the mascot, drawn as a doodle: a bell with a row of perforations, film-strip tentacles; tilt and sway vary per jar
    import math
    tilt = (k * 37 % 21) - 10; sway = 1 + (k % 3) * .35; n = 3 + (k % 2)
    tent = ''.join(f'<path d="M{x} 6c{-6 * sway} 10 {6 * sway} 16 0 26s{6 * sway} 16 0 {16 + (k + i) % 3 * 5}" fill="none" stroke="{D}" stroke-width="5" stroke-linecap="round" stroke-dasharray="5 4"/>' for i, x in enumerate([-18 + 36 * j / (n - 1) for j in range(n)]))
    holes = ''.join(f'<circle cx="{-24 + 8 * j}" cy="-3" r="1.8" fill="#F7E4BF"/>' for j in range(7))
    return (f'<g transform="rotate({tilt})"><path d="M-34 4C-34 -26 -18 -38 0 -38S34 -26 34 4C24 9 -24 9 -34 4Z" fill="{A}" stroke="{D}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M-22 -14C-18 -26 -8 -31 2 -31" fill="none" stroke="#F7E4BF" stroke-width="3" stroke-linecap="round" opacity=".8"/>{holes}{tent}</g>')

def mono(svg, ink, paper, cols=None):   # a two-tone print: dark inks -> ink, light inks -> a mid tone, the label paper -> paper
    mid = '#8C8C8C' if ink == '#141414' else '#6E6E6E'
    def lum(h): r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)); return .299 * r + .587 * g + .114 * b
    for c in sorted(set(re.findall(r'#[0-9A-Fa-f]{6}', svg)) - {'#F7E4BF'}): svg = svg.replace(c, ink if lum(c) < .42 else mid)
    return svg.replace('#F7E4BF', paper)

def main():
    src = open(TEMPLATE).read(); P = palettes(); print(len(P), 'palettes')
    for k, (jid, sym, name, line, ic, alt) in enumerate(JARS):
        D, A = P[(k * 7) % len(P)]
        s = src.replace('#572D32', D).replace('#B46D3D', A)
        r = ET.fromstring(s); ch = list(r)
        ch[0].text = f'Contaminant jelly-films · {name}'; ch[1].text = alt
        # no periodic symbol on these: the label is a window. In it, a doodle of the mascot jelly (each one posed a little differently);
        # on the index, the jar's own video plays in this window.
        r.remove(ch[37]); g_icon = ch[38]; [g_icon.remove(c) for c in list(g_icon)]; g_icon.set('transform', 'translate(160 184) scale(.62)')
        for c in ET.fromstring(f'<g xmlns="{NS}">{cartoon(ic, D, A)}</g>'): g_icon.append(c)
        txt = ch[39]; old = list(txt)
        ng, _ = glyphs(SERIF, name, 24, 160, 247, 168, D, squeeze=.92); mg, _ = glyphs(SANS, line, 12, 160, 276, 160, D, squeeze=.9)
        for o in old[1:]: txt.remove(o)
        txt.extend([ng, mg])
        out = ET.tostring(r, encoding='unicode'); open(os.path.join(OUT, jid + '.svg'), 'w').write(out)
        for v, ink, paper in (('black', '#141414', '#FFFFFF'), ('white', '#F4F1EA', '#141414')): os.makedirs(os.path.join(OUT, v), exist_ok=True); open(os.path.join(OUT, v, jid + '.svg'), 'w').write(mono(out, ink, paper))
    json.dump([{'id': j[0], 'symbol': j[1], 'name': j[2], 'line': j[3], 'alt': j[5], 'file': j[0]} for j in JARS], open(os.path.join(OUT, 'index.json'), 'w'), indent=1)
    # black and white versions of the periodic-table jars too
    for f in sorted(os.listdir(os.path.join(HERE, 'cineosis'))):
        if not f.endswith('.svg'): continue
        t = open(os.path.join(HERE, 'cineosis', f)).read(); cols = sorted(set(re.findall(r'#[0-9A-Fa-f]{6}', t)) - {'#F7E4BF'})
        for v, ink, paper in (('black', '#141414', '#FFFFFF'), ('white', '#F4F1EA', '#141414')): os.makedirs(os.path.join(HERE, 'cineosis', v), exist_ok=True); open(os.path.join(HERE, 'cineosis', v, f), 'w').write(mono(t, ink, paper, cols))
    print('wrote', len(JARS), 'jars to', OUT, '+ black and white versions of every jar')
main()
