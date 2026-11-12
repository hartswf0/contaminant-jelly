# Writes the Bolas edition of the orchestra: bolas/cities/index.html. One source (bonus/jellyorchestra.html), relocated.
# The page lives in Bolas with the city data beside it; songs, the species rigs, fonts and three.js are read from the contaminant-jelly site, which shares its address.
import shutil, os, sys, glob
SRC = '/home/user/contaminant-jelly/'; DST = (sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas') + '/cities/'; os.makedirs(DST + 'data', exist_ok=True)
s = open(SRC + 'bonus/jellyorchestra.html').read(); CJ = '/contaminant-jelly/'
def R(a, b, n=1):
    global s; assert s.count(a) == n, (a[:70], s.count(a)); s = s.replace(a, b)
R('href="../fonts/fonts.css"', 'href="%sfonts/fonts.css"' % CJ)
R('"three":"../paeleo/scion/videotext/vendor/three.module.min.js","three/addons/":"../paeleo/scion/videotext/vendor/addons/"', '"three":"%spaeleo/scion/videotext/vendor/three.module.min.js","three/addons/":"%spaeleo/scion/videotext/vendor/addons/"' % (CJ, CJ))
R("from './tractjelly.js'", "from '%sbonus/tractjelly.js'" % CJ)
R("from '../current/drift/rigs.js'", "from '%scurrent/drift/rigs.js'" % CJ)
R("new URL('./jellystudio/', import.meta.url)", "new URL('%sbonus/jellystudio/', location.origin)" % CJ)
R("new URL('../current/drift/data/crashlab/', import.meta.url)", "new URL('%scurrent/drift/data/crashlab/', location.origin)" % CJ)
R("const CROOT = new URL('cities/', ROOT),", "const CROOT = new URL('./data/', import.meta.url),")
for a in ('jellystudio.html', 'realjelly.html', 'lab.html'): s = s.replace('href="%s' % a, 'href="%sbonus/%s' % (CJ, a)).replace("href = '%s" % a, "href = '%sbonus/%s" % (CJ, a))
R('href="worlds.html"', 'href="../worlds/"')
R("const WIMG = 'worlds/',", "const WIMG = '../worlds/img/',")
R('<title>The Jelly Orchestra · jelly-films</title>', '<title>Celluloid Cities · CRASH LAB</title>')
R('<b>THE JELLY ORCHESTRA</b>', '<b><a href="../" style="color:inherit">CRASH LAB</a> · CELLULOID CITIES</b>')
R('<div class="k">BONUS · THE JELLY ORCHESTRA</div><h1>Every jellyfish is one sound</h1>', '<div class="k">CRASH LAB · CELLULOID CITIES</div><h1>The archive is a city. The jellies are its archivists.</h1>')
i = s.index('<p>Each soloist is one sampled sound'); j = s.index('</p>', i) + 4
s = s[:i] + '<p>Fourteen cities built of film hold the whole Cineosis archive: a city for each poem, a street for each scene, a tower for each film, a floor for each shot. While a song plays, the jellies go into the towers looking for their material. On every street one of them comes back carrying a frame, the shot the poem’s cut chose, and splices it into a reel in the avenue. Touch any floor to read its address.</p>' + s[j:]
open(DST + 'index.html', 'w').write(s)
for f in glob.glob(SRC + 'bonus/jellystudio/cities/*.json') + glob.glob(SRC + 'bonus/jellystudio/cities/*.jpg'): shutil.copy(f, DST + 'data/')
print('wrote', DST + 'index.html', len(s) // 1024, 'KB;', len(os.listdir(DST + 'data')), 'data files')
