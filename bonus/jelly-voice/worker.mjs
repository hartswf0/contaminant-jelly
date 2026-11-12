import {initChimera} from './chimera/chimera.mjs';
import {renderTake} from './render.mjs';
import {sha256} from './score.mjs';
const PINNED = {
  'chimera.wasm': '606cfb8c02c4362c15548984a106640707208fd1518d6823c171fddd91d42f82',
  'cmudict.txt.gz': '336293a10a93c3ba183483308a22eab8e2b6a5e1ac91262dd0d3d4b85da285b5',
};
async function asset(name) {
  const response = await fetch(new URL(`./chimera/${name}`, import.meta.url));
  if (!response.ok) throw new Error(`${name} could not load (HTTP ${response.status}).`);
  const bytes = await response.arrayBuffer();
  if (await sha256(bytes) !== PINNED[name]) throw new Error(`${name} differs from the pinned runtime. Refresh or restore its matching asset.`);
  return bytes;
}
let runtime;
self.onmessage = async ({data}) => {
  const {id, score, sampleRate} = data;
  try {
    self.postMessage({id, status: 'loading'});
    if (!runtime) {
      const [wasm, dictionary] = await Promise.all([asset('chimera.wasm'), asset('cmudict.txt.gz')]);
      runtime = await initChimera(wasm);
      await runtime.loadDictionary(dictionary);
    }
    self.postMessage({id, status: 'rendering'});
    const take = await renderTake(runtime, score, sampleRate);
    self.postMessage({id, take}, [take.pcm.buffer, take.envelope.values.buffer]);
  } catch (error) { self.postMessage({id, error: error.message || String(error)}); }
};
