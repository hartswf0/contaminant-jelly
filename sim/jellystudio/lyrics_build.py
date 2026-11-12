# The words the cast sings in each language. Spanish, Portuguese and Amharic are the titles only; Mandarin also has the mechanisms.
# All are hand translations made for this work and not yet checked by native speakers. Writes bonus/jellystudio/voice/lyrics.json.
import json, re
from pypinyin import lazy_pinyin, Style
ROWS = """boxes-found,boxes-made|tú también, bruto, cajas en mi espalda|até tu, bruto, caixas nas minhas costas|አንተም ብሩተስ፣ ሳጥኖች በጀርባዬ
a2-pickup|anacrusa|anacruse|መነሻ
a3-late|tarde|tarde|ዘግይቶ
a4-clock|reloj del campo|relógio do campo|የሜዳ ሰዓት
a5-remains|lo que queda|o que resta|የቀረው
a6-sixty|sesenta pulsos|sessenta batidas|ስልሳ ምት
a7-room|una sala|uma sala|አንድ ክፍል
a8-rebuilt|el coro, reconstruido|o coro, reconstruído|መዘምራኑ እንደገና ተሠራ
remix-boom|remezcla bum bap|remix bum bap|ሪሚክስ ቡም ባፕ
remix-dub|remezcla dub|remix dub|ሪሚክስ ዳብ
remix-half|remezcla a medio tiempo|remix em meio tempo|ሪሚክስ ግማሽ ፍጥነት
s01-cut-answers|el corte responde|o corte responde|ቁርጡ ይመልሳል
s02-three-clocks|tres relojes en una sala|três relógios numa sala|ሦስት ሰዓቶች በአንድ ክፍል
s03-wrong-turn|el desvío que da fruto|o desvio que dá fruto|ፍሬ ያለው የተሳሳተ መንገድ
s04-floor-plan|el miedo tiene un plano|o medo tem uma planta|ፍርሃት ንድፍ አለው
s05-threshold|el umbral del reconocimiento|o limiar do reconhecimento|የመለየት ደፍ
s06-room-document|la sala alrededor del documento|a sala em volta do documento|በሰነዱ ዙሪያ ያለው ክፍል
s07-sentence-chorus|la frase humana se vuelve coro|a frase humana vira coro|የሰው ዓረፍተ ነገር መዝሙር ይሆናል
s08-rule|la regla hace la música|a regra faz a música|ደንቡ ሙዚቃውን ይሠራል
s09-narrator|la interrupción cambia al narrador|a interrupção muda o narrador|ማቋረጡ ተራኪውን ይቀይራል
s10-audible-past|un futuro con un pasado que se oye|um futuro com um passado que se ouve|የሚሰማ ትናንት ያለው ነገ
s11-one-breath|un coro hecho de un solo aliento|um coro feito de um só sopro|ከአንድ ትንፋሽ የተሠራ መዘምራን
s12-landscape|el paisaje entra en la banda|a paisagem entra na banda|መልክዓ ምድሩ ባንዱን ይቀላቀላል
s13-missing-downbeat|el tiempo fuerte que falta es el gancho|o tempo forte que falta é o gancho|የጎደለው ምት መንጠቆው ነው
s14-clothes|un ritmo que se cambia de ropa|um ritmo que troca de roupa|ልብሱን የሚቀይር ምት
s15-understatement|lo dicho a media voz llega|o dito em voz baixa chega|ዝቅ ብሎ የተነገረው ይደርሳል
s16-scene-cut|el empalme es un corte de escena|a emenda é um corte de cena|መገጣጠሚያው የትዕይንት ቁርጥ ነው
s17-room-for-voice|el bajo deja sitio a la voz|o baixo deixa lugar para a voz|ባሱ ለድምፁ ቦታ ይተዋል
s18-horn-remembers|la trompa recuerda la estrofa|a trompa lembra a estrofe|መለከቱ ስንኙን ያስታውሳል
s19-seam-sings|la costura canta|a costura canta|ስፌቱ ይዘምራል
s20-one-hit-kit|un golpe se vuelve batería|uma batida vira bateria|አንድ ምት ከበሮ ይሆናል
s21-collision|el choque aún se entiende|o choque ainda se entende|ግጭቱ አሁንም ይነበባል
s22-one-shadow|una sombra sostiene la escena|uma sombra segura a cena|አንድ ጥላ ትዕይንቱን ይይዛል
s23-the-one|el uno es un acuerdo entre todos|o um é um acordo entre todos|አንደኛው ምት የሁሉም ስምምነት ነው
s24-break-grammar|una pausa tiene gramática|uma pausa tem gramática|ዕረፍት ሰዋስው አለው
s25-exclamation|la exclamación es un tambor|a exclamação é um tambor|ጩኸቱ ከበሮ ነው
s26-pressure|el ruido da presión al argumento|o ruído dá pressão ao argumento|ጫጫታ ለክርክሩ ግፊት ይሰጣል
s27-two-rooms|dos salas, una ciudad|duas salas, uma cidade|ሁለት ክፍሎች፣ አንድ ከተማ
s28-negative-space|el ritmo tiene espacio vacío|o ritmo tem espaço vazio|ምቱ ባዶ ቦታ አለው
s29-counterline|la contralínea se esconde a la vista|a contralinha se esconde à vista|ተቃራኒው መስመር በግልጽ ይደበቃል
s30-persona|un personaje se mueve entre mundos|uma persona se move entre mundos|አንድ ገጸ ባሕርይ በዓለማት መካከል ይንቀሳቀሳል
s31-space-to-speak|el conjunto hace sitio para hablar|o conjunto abre espaço para falar|ቡድኑ ለመናገር ቦታ ይሠራል
s32-bass-conversation|la línea de bajo lleva la conversación|a linha do baixo leva a conversa|የባስ መስመሩ ውይይቱን ይሸከማል
s33-hand-to-room|un gancho que puedes darle a la sala|um gancho que você pode dar à sala|ለክፍሉ ልትሰጠው የምትችል መንጠቆ
s34-harmony-arrives|la armonía llega antes que la palabra|a harmonia chega antes da palavra|ስምምነቱ ከቃሉ በፊት ይደርሳል
s35-uneasy-room|la sala inquieta la línea|a sala inquieta a linha|ክፍሉ መስመሩን ያስጨንቃል
s36-slow-anchor|la frase lenta puede ser un ancla|a frase lenta pode ser uma âncora|ዝግ ያለው ሐረግ መልሕቅ ሊሆን ይችላል
s37-meter|el compás enseña al oído|o compasso ensina o ouvido|ምቱ ጆሮን ያስተምራል
s38-spoken-cut|el corte hablado cambia la frase|o corte falado muda a frase|የተነገረው ቁርጥ ዓረፍተ ነገሩን ይቀይራል"""
out = {'es': {}, 'pt': {}, 'am': {}, 'zh': {}, 'zh_py': {}}
for r in ROWS.split('\n'):
    ids, es, pt, am = r.split('|')
    for i in ids.split(','): out['es'][i] = [es]; out['pt'][i] = [pt]; out['am'][i] = [am]
src = open('/home/user/contaminant-jelly/bonus/jellyorchestra.html').read(); m = re.search(r"const SONGZH = \{(.*?)\};\n", src, re.S)
for k, v in re.findall(r"'?([a-z0-9-]+)'?: \[((?:'[^']*'(?:, )?)+)\]", m.group(1)):
    lines = re.findall(r"'([^']*)'", v); out['zh'][k] = lines
    for l in lines:   # readings chosen in context, so 乐 in 音乐 is yue and not le
        chars = [c for c in l if '一' <= c <= '鿿']; py = lazy_pinyin(''.join(chars), style=Style.TONE3, neutral_tone_with_five=True)
        for c, p in zip(chars, py): out['zh_py'].setdefault(l, {})[c] = p
json.dump(out, open('/home/user/contaminant-jelly/bonus/jellystudio/voice/lyrics.json', 'w'), ensure_ascii=False, separators=(',', ':')); print({k: len(v) for k, v in out.items()})
