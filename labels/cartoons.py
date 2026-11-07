# The mascot jelly as a cartoon, one character per jar: a bell, a face and film-strip tentacles, with a pose and props for what that level does.
# Coordinates: centred on (0, 0); the bell spans about x -34..34, y -40..6; tentacles hang to about y 46; props may reach the edges (±80, -46..50).
P = '#F7E4BF'   # label paper

def bell(D, A, w=34, h=40, squash=1.0):
    return f'<path d="M{-w} 4C{-w} {-h * .7 * squash} {-w * .5} {-h * squash} 0 {-h * squash}S{w} {-h * .7 * squash} {w} 4C{w * .6} 10 {-w * .6} 10 {-w} 4Z" fill="{A}" stroke="{D}" stroke-width="4" stroke-linejoin="round"/>' \
           f'<path d="M{-w * .62} {-h * .38 * squash}C{-w * .5} {-h * .72 * squash} {-w * .2} {-h * .85 * squash} {w * .08} {-h * .84 * squash}" fill="none" stroke="{P}" stroke-width="3" stroke-linecap="round" opacity=".75"/>' \
           + ''.join(f'<circle cx="{-w * .74 + j * w * .245}" cy="1" r="1.7" fill="{D}" opacity=".7"/>' for j in range(7))

def tents(D, n=4, sway=6, length=40, spread=26, dash=True, curl=0):
    out = ''
    for i in range(n):
        x = -spread + 2 * spread * i / max(1, n - 1); s = sway * (1 if i % 2 else -1)
        tail = f'q{s * .6} {8 + curl} {-s * .4 + curl * .6} {12}' if curl else ''
        out += f'<path d="M{x:.1f} 8c{s} {length * .25} {-s} {length * .45} 0 {length * .65}s{s} {length * .2} 0 {length * .35}{tail}" fill="none" stroke="{D}" stroke-width="4.4" stroke-linecap="round"{" stroke-dasharray=&quot;5 3.5&quot;" if dash else ""}/>'
    return out.replace('&quot;', '"')

def eyes(D, kind='dot', y=-14, gap=11):
    L, R = -gap, gap
    E = {
      'dot': f'<circle cx="{L}" cy="{y}" r="3.6" fill="{D}"/><circle cx="{R}" cy="{y}" r="3.6" fill="{D}"/><circle cx="{L + 1.2}" cy="{y - 1.3}" r="1.1" fill="{P}"/><circle cx="{R + 1.2}" cy="{y - 1.3}" r="1.1" fill="{P}"/>',
      'up': f'<circle cx="{L}" cy="{y}" r="4.2" fill="{P}" stroke="{D}" stroke-width="2"/><circle cx="{R}" cy="{y}" r="4.2" fill="{P}" stroke="{D}" stroke-width="2"/><circle cx="{L + .6}" cy="{y - 2}" r="2" fill="{D}"/><circle cx="{R + .6}" cy="{y - 2}" r="2" fill="{D}"/>',
      'wide': f'<circle cx="{L}" cy="{y}" r="6" fill="{P}" stroke="{D}" stroke-width="2.4"/><circle cx="{R}" cy="{y}" r="6" fill="{P}" stroke="{D}" stroke-width="2.4"/><circle cx="{L + 1}" cy="{y + 1}" r="2.2" fill="{D}"/><circle cx="{R + 1}" cy="{y + 1}" r="2.2" fill="{D}"/>',
      'closed': f'<path d="M{L - 5} {y}q5 4 10 0M{R - 5} {y}q5 4 10 0" fill="none" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/>',
      'sleepy': f'<path d="M{L - 5} {y + 1}h10M{R - 5} {y + 1}h10" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/><path d="M{L - 5} {y - 2}q5 -3 10 0M{R - 5} {y - 2}q5 -3 10 0" fill="none" stroke="{D}" stroke-width="1.6" stroke-linecap="round"/>',
      'heart': ''.join(f'<path d="M{x} {y + 4}l-5 -5a3 3 0 0 1 5 -3a3 3 0 0 1 5 3z" fill="{D}"/>' for x in (L, R)),
      'fierce': f'<path d="M{L - 6} {y - 6}l11 4M{R + 6} {y - 6}l-11 4" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/><circle cx="{L}" cy="{y + 1}" r="3.2" fill="{D}"/><circle cx="{R}" cy="{y + 1}" r="3.2" fill="{D}"/>',
      'star': ''.join(f'<path d="M{x} {y - 6}l1.8 4.2 4.4.4-3.4 2.9 1 4.4-3.8-2.3-3.8 2.3 1-4.4-3.4-2.9 4.4-.4z" fill="{D}"/>' for x in (L, R)),
      'wink': f'<circle cx="{L}" cy="{y}" r="3.6" fill="{D}"/><path d="M{R - 5} {y}q5 -4 10 0" fill="none" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/>',
      'side': f'<circle cx="{L + 3}" cy="{y}" r="3.4" fill="{D}"/><circle cx="{R + 3}" cy="{y}" r="3.4" fill="{D}"/>',
      'goggle': f'<circle cx="{L}" cy="{y}" r="7" fill="{P}" stroke="{D}" stroke-width="3"/><circle cx="{R}" cy="{y}" r="7" fill="{P}" stroke="{D}" stroke-width="3"/><path d="M{L + 7} {y}h{R - L - 14}" stroke="{D}" stroke-width="3"/><circle cx="{L}" cy="{y}" r="2.6" fill="{D}"/><circle cx="{R}" cy="{y}" r="2.6" fill="{D}"/>',
    }
    return E[kind]

def mouth(D, kind='smile', y=-3):
    M = {'smile': f'<path d="M-7 {y}q7 7 14 0" fill="none" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/>',
         'grin': f'<path d="M-9 {y - 1}q9 11 18 0z" fill="{D}"/><path d="M-6 {y + 1}h12" stroke="{P}" stroke-width="1.6"/>',
         'o': f'<ellipse cx="0" cy="{y + 1}" rx="3.6" ry="4.6" fill="{D}"/>',
         'wavy': f'<path d="M-8 {y}q2 -3 4 0t4 0t4 0t4 0" fill="none" stroke="{D}" stroke-width="2.2" stroke-linecap="round"/>',
         'flat': f'<path d="M-5 {y}h10" stroke="{D}" stroke-width="2.6" stroke-linecap="round"/>',
         'tongue': f'<path d="M-8 {y - 1}q8 9 16 0z" fill="{D}"/><path d="M-3 {y + 3}q3 5 6 0" fill="#d8574a"/>',
         'kiss': f'<path d="M-2 {y - 2}q4 2 0 4q4 2 0 4" fill="none" stroke="{D}" stroke-width="2.2" stroke-linecap="round"/>'}
    return M[kind]

def blush(y=-6):
    return f'<ellipse cx="-19" cy="{y}" rx="4" ry="2.2" fill="#e2766a" opacity=".55"/><ellipse cx="19" cy="{y}" rx="4" ry="2.2" fill="#e2766a" opacity=".55"/>'

def J(D, A, e='dot', m='smile', rot=0, tx=0, ty=0, s=1, n=4, sway=6, length=40, extra_back='', extra_front='', b=True, curl=0, squash=1):
    return (f'<g transform="translate({tx} {ty}) rotate({rot}) scale({s})">{extra_back}{tents(D, n, sway, length, curl=curl)}{bell(D, A, squash=squash)}'
            f'{eyes(D, e)}{mouth(D, m)}{blush() if b else ""}{extra_front}</g>')

def cartoon(kind, D, A):
    S = lambda d, w=4, c=None: f'<path d="{d}" fill="none" stroke="{c or D}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    C = {
      # rising, arms up, eyes on the light above; little tiers of frames below
      'ascent': J(D, A, 'up', 'o', ty=-2, sway=3, length=34, curl=4) + S('M-64 44h26M-58 36h14M58 44h-26M52 36h-14', 4) + S('M0 -60v-10M-16 -56l-6-8M16 -56l6-8', 3, A),
      # two jellies holding tentacles, one shy, one beaming
      'pairs': J(D, A, 'closed', 'smile', rot=-10, tx=-30, s=.74) + J(D, P, 'dot', 'grin', rot=10, tx=30, s=.74) + S('M-14 36q14 10 28 0', 4) + f'<path d="M0 -34l-5-5a3 3 0 0 1 5-3a3 3 0 0 1 5 3z" fill="#d8574a"/>',
      # terrified: wide eyes, sweat drop, the lure's light hanging close, teeth below
      'lure': J(D, A, 'wide', 'o', rot=-8, tx=-14, b=False, sway=10) + f'<path d="M22 -30q4 6 0 9q-4-3 0-9z" fill="#7fb7d6" stroke="{D}" stroke-width="1.5"/>'
              + S('M70 50Q76 -10 44 -40', 3) + f'<circle cx="44" cy="-36" r="7" fill="#f6d36b" stroke="{D}" stroke-width="2.4"/>' + f'<path d="M40 50l6-10 6 10 6-10 6 10 6-10 6 10z" fill="{D}"/>',
      # dreamy, eyes closed, drifting up toward a wavy surface, a big face's eye above
      'surface': S('M-70 -50q12-8 24 0t24 0t24 0t24 0t24 0', 3, A) + J(D, A, 'closed', 'kiss', rot=6, ty=4) + S('M38 -24q6-4 12 0', 2.6) + f'<circle cx="54" cy="-8" r="3" fill="{P}" stroke="{D}" stroke-width="1.6"/><circle cx="62" cy="-22" r="2" fill="{P}" stroke="{D}" stroke-width="1.4"/>',
      # angelic: halo ring over the bell, tiny film frames orbiting
      'halo': J(D, A, 'closed', 'smile', extra_front=f'<ellipse cx="0" cy="-50" rx="22" ry="6" fill="none" stroke="#f6d36b" stroke-width="4"/>')
              + ''.join(f'<rect x="{x - 6}" y="{y - 5}" width="12" height="10" rx="1.5" fill="{P}" stroke="{D}" stroke-width="2.4"/>' for x, y in ((-62, -10), (62, -10), (-50, 30), (50, 30))),
      # surfing the ray's wake: determined, speed lines, the ray above
      'rayrun': f'<path d="M-40 -58q40-22 96 0q-40-6-96 0zM56 -58l18 4" fill="{D}"/>' + J(D, A, 'fierce', 'grin', rot=-18, n=4, sway=12, curl=6) + S('M-76 -6h20M-80 8h28M-74 22h18', 3, A),
      # holding a strip of film slices like a banner, delighted
      'slices': J(D, A, 'dot', 'grin', tx=-8) + ''.join(f'<rect x="{30 + i * 14}" y="{-30 + i * 14}" width="18" height="14" fill="{P}" stroke="{D}" stroke-width="2.4"/><path d="M{33 + i * 14} {-18 + i * 14}l10-8v8z" fill="{A}"/>' for i in range(4)) + S('M26 -6l6-18', 3),
      # peeking from a cave mouth, curious side-eye
      'caves': f'<path d="M-80 50V-10Q-80 -50 -44 -50Q-8 -50 -8 -10V50Z" fill="{D}"/><path d="M8 50V-10Q8 -50 44 -50Q80 -50 80 -10V50Z" fill="{D}"/>'
               + J(D, A, 'side', 'wavy', tx=-44, ty=8, s=.62, b=False) + f'<circle cx="44" cy="10" r="3" fill="#f6d36b"/><circle cx="52" cy="2" r="2" fill="#f6d36b"/><circle cx="36" cy="22" r="2.2" fill="#f6d36b"/>',
      # in love with the film blooming open around it
      'bloom': ''.join(f'<ellipse cx="{x}" cy="{y}" rx="11" ry="16" transform="rotate({r} {x} {y})" fill="{P}" stroke="{D}" stroke-width="2.4"/>' for x, y, r in ((-58, -18, -30), (58, -18, 30), (-60, 22, 30), (60, 22, -30))) + J(D, A, 'heart', 'smile'),
      # sinking, asleep, Zz rising, a little anchor of light below
      'descent': J(D, A, 'sleepy', 'flat', rot=12, ty=-4, sway=3, length=36) + S('M30 -44h12l-12 12h12M46 -58h8l-8 8h8', 2.8)
                 + S('M-60 28l8 10 8-10M-60 42l8 10 8-10', 3, A),
      # half buried, digging with a tentacle, dust flying
      'silt': f'<path d="M-82 30q20-10 40 0t40 0t40 0t42 0V52H-82Z" fill="{D}"/>' + J(D, A, 'wink', 'tongue', rot=-6, ty=-6, length=28) + ''.join(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{A}"/>' for x, y in ((44, 12), (54, 2), (60, 16), (-50, 14))),
      # an artist: holding a pencil, a doodle squiggle drawn beside
      'doodles': J(D, A, 'dot', 'grin', tx=-14) + f'<path d="M30 -10l26-26 6 6-26 26-9 3z" fill="#f6d36b" stroke="{D}" stroke-width="2.6"/>' + S('M30 26c8-14 18 8 26-6s14 4 22-6', 3, A),
      # with a fish friend, both winking
      'menagerie': J(D, A, 'wink', 'smile', tx=-22, s=.86) + f'<path d="M30 6q22-22 44 0q-22 22-44 0zM74 6l12-10v20z" fill="{P}" stroke="{D}" stroke-width="2.6"/><circle cx="42" cy="2" r="2.4" fill="{D}"/>',
      # juggling two bolas balls
      'bolas': J(D, A, 'up', 'grin') + S('M-40 -40Q0 -76 40 -40', 3) + f'<circle cx="-42" cy="-38" r="9" fill="{P}" stroke="{D}" stroke-width="3"/><circle cx="42" cy="-38" r="9" fill="{D}"/>',
      # an old-timer in film goggles with a stack of eras
      'strata': J(D, A, 'goggle', 'smile') + ''.join(f'<rect x="-78" y="{-30 + i * 14}" width="26" height="10" rx="2" fill="{c}" stroke="{D}" stroke-width="2"/>' for i, c in enumerate((P, A, P, A, P))),
      # rainbow: a prism splitting light through the bell
      'spectrum': ''.join(f'<path d="M30 {-6 + i * 5}L82 {-30 + i * 14}" stroke="{c}" stroke-width="4" stroke-linecap="round"/>' for i, c in enumerate(('#d8574a', '#f0a43a', '#f6d36b', '#6fb36d', '#5a8fd0'))) + J(D, A, 'star', 'grin', tx=-10),
      # inside a film reel, peeking out of the hub
      'reel': f'<circle cx="0" cy="-6" r="56" fill="none" stroke="{D}" stroke-width="6"/>' + ''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{D}"/>' for x, y in ((0, -50), (-42, -20), (42, -20), (-26, 30), (26, 30))) + J(D, A, 'dot', 'o', s=.72, ty=2),
      # a sentinel with a flashlight in the pipe
      'sewer': f'<circle cx="0" cy="0" r="60" fill="none" stroke="{D}" stroke-width="7"/>' + f'<path d="M30 -12l48-18v36z" fill="#f6d36b" opacity=".75"/>' + J(D, A, 'fierce', 'flat', s=.8, b=False) + f'<rect x="20" y="-18" width="14" height="10" rx="2" fill="{D}"/>',
      # the queen of the medusae, crowned
      'medusae': J(D, A, 'closed', 'smile', n=5, length=46, extra_front=f'<path d="M-18 -40l6-14 6 10 6-12 6 12 6-10 6 14z" fill="#f6d36b" stroke="{D}" stroke-width="2.4" stroke-linejoin="round"/>'),
      # tangled up with worm friends, laughing
      'worms': J(D, A, 'closed', 'grin', tx=-6) + S('M-80 30q10-14 20 0t20 0', 5, A) + S('M40 34q10-14 20 0t20 0', 5, A) + f'<circle cx="-40" cy="26" r="2.4" fill="{D}"/><circle cx="80" cy="30" r="2.4" fill="{D}"/>',
      # many subjects: wearing a little hat, holding a frame like a sign
      'subjects': J(D, A, 'dot', 'smile', tx=-16, extra_front=f'<path d="M-14 -40h28l-4-10h-20z" fill="{D}"/>') + f'<rect x="28" y="-24" width="44" height="34" rx="3" fill="{P}" stroke="{D}" stroke-width="3"/><circle cx="50" cy="-12" r="6" fill="{A}"/><path d="M36 6l10-10 8 6 10-12 8 16z" fill="{D}"/>',
    }
    return C[kind]
