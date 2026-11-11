// Reproduce the listening fixtures with the vendored, pinned runtime.
import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {initChimera} from '../../bonus/jelly-voice/chimera/chimera.mjs';
import {createScore} from '../../bonus/jelly-voice/score.mjs';
import {renderTake} from '../../bonus/jelly-voice/render.mjs';
import {encodeWav} from '../../bonus/jelly-voice/performance.mjs';

const base = new URL('../../bonus/jelly-voice/', import.meta.url);
const engine = await initChimera(await fs.readFile(new URL('chimera/chimera.wasm', base)));
await engine.loadDictionary(await fs.readFile(new URL('chimera/cmudict.txt.gz', base)));
const samples = [
  {id:'take-17', actorId:'G', mode:'speech', text:'The little jelly has a voice.'},
  {id:'take-62', actorId:'F1', mode:'speech', text:'The little jelly has a voice.'},
  {id:'take-31', actorId:'G', mode:'joke', text:'I bottled my thoughts. | They escaped.', pause:.6},
  {id:'take-84', actorId:'G', mode:'sing', text:'Carry me home.', melody:'0:1 4:1 7:1 0:2', bpm:110},
  {id:'take-45', actorId:'G', mode:'rap', text:'Wet bell, slow glow. Let the river flow.', bpm:96},
];
await fs.mkdir(new URL('samples/', base), {recursive:true});
const records = [];
for (const {id, ...input} of samples) {
  const take = await renderTake(engine, createScore({...input, material:0}), 48000);
  const {pcm, envelope, telemetry, ...record} = take;
  await fs.writeFile(new URL(`samples/${id}.wav`, base), new Uint8Array(encodeWav(take)));
  records.push({id, file:`${id}.wav`, ...record});
  console.log(JSON.stringify({id, duration:take.duration, peak:take.signal.peak, hash:take.pcmHash}));
}
await fs.writeFile(new URL('samples/records.json', base), JSON.stringify({status:'rendered-not-human-reviewed', sampleRate:48000, records},null,2)+'\n');
console.log(`Saved ${records.length} listening fixtures in ${fileURLToPath(new URL('samples/',base))}`);
