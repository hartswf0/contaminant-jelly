// Independent critic. Run: node tests/jelly-voice/critic-core.mjs
// Uses actual pinned WASM/dictionary. No production imports are mocked except
// the clock/source and Worker doubles explicitly named in their test labels.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {initChimera} from '../../bonus/jelly-voice/chimera/chimera.mjs';
import {CAST, resolveActor} from '../../bonus/jelly-voice/cast.mjs';
import {createScore, compileScore} from '../../bonus/jelly-voice/score.mjs';
import {renderTake} from '../../bonus/jelly-voice/render.mjs';
import {encodeWav, frameAt, TakePlayer} from '../../bonus/jelly-voice/performance.mjs';
import {VoiceRenderer} from '../../bonus/jelly-voice/client.mjs';

const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const results = [], evidence = [];
async function test(name, fn) {
  const started = performance.now();
  try { const detail = await fn(); results.push({name, status: 'PASS', elapsedMs: Math.round(performance.now()-started), detail}); }
  catch (error) { results.push({name, status: 'FAIL', elapsedMs: Math.round(performance.now()-started), error: error.stack}); }
  console.log(`${results.at(-1).status} ${name}${results.at(-1).error ? ': ' + results.at(-1).error.split('\n')[0] : ''}`);
}
const inspected = {};
for (const file of ['cast.mjs', 'score.mjs', 'render.mjs', 'performance.mjs', 'client.mjs', 'worker.mjs', 'panel.js', 'adapters.js', 'chimera/chimera.mjs', 'chimera/chimera.wasm', 'chimera/cmudict.txt.gz']) inspected[file] = hash(await fs.readFile(path.join(base, 'bonus/jelly-voice', file)));
const runtime = await initChimera(await fs.readFile(path.join(base,'bonus/jelly-voice/chimera/chimera.wasm')));
await runtime.loadDictionary(await fs.readFile(path.join(base,'bonus/jelly-voice/chimera/cmudict.txt.gz')));
const defaults = {actorId:'G', text:'We are jelly.', material:0};

await test('pinned engine and dictionary match independently hashed bytes', () => {
  assert.equal(inspected['chimera/chimera.wasm'], '606cfb8c02c4362c15548984a106640707208fd1518d6823c171fddd91d42f82');
  assert.equal(inspected['chimera/cmudict.txt.gz'], '336293a10a93c3ba183483308a22eab8e2b6a5e1ac91262dd0d3d4b85da285b5');
});
await test('invalid score fields reject with field-specific errors', () => {
  const cases = [
    [{text:''}, /English phrase/], [{text:'12345'}, /English phrase/], [{text:'a'.repeat(241)}, /240/],
    [{actorId:'no-such-actor'}, /Unknown actor/], [{mode:'opera'}, /speech.*joke.*sing.*rap/],
    [{feel:'banana'}, /straight.*swing.*triplet/], [{bpm:NaN}, /Tempo/], [{bpm:49}, /Tempo/], [{bpm:181}, /Tempo/],
    [{rate:0}, /rate/], [{pause:3}, /pause/], [{vibrato:61}, /Vibrato/], [{material:Infinity}, /Material/],
    [{melody:''}, /1–32/], [{melody:'0:1 7:0'}, /Note beats/], [{melody:'20:1'}, /interval/],
    [{melody:'0:1.2.3'}, /Melody/], [{melody:Array(33).fill('0:1').join(' ')}, /1–32/],
    [{mode:'joke',text:'No punchline'}, /one \|/], [{mode:'joke',text:'Setup | | Punch'}, /one \|/],
    [{mode:'joke',text:'Setup | 12'}, /one \|/]
  ];
  for (const [patch,error] of cases) assert.throws(() => createScore({...defaults,...patch}),error,JSON.stringify(patch));
  return {rejected:cases.length};
});
await test('inherited Object keys are rejected as actors', () => {
  for (const actorId of ['toString','constructor','__proto__','valueOf']) {
    assert.throws(() => resolveActor(actorId),/Unknown actor/,actorId);
    assert.throws(() => createScore({...defaults,actorId}),/Unknown actor/,actorId);
  }
});
await test('actor profile identity is independent of body snapshot and page hint', () => {
  for (const actorId of Object.keys(CAST)) {
    const a=createScore({...defaults,actorId,pageId:'realjelly'}, {energy:0,pressure:0,color:0});
    const b=createScore({...defaults,actorId,pageId:'jellyjar'}, {energy:1,pressure:1,color:1});
    assert.equal(a.voice_profile_id,b.voice_profile_id); assert.equal(a.voice_profile_revision,b.voice_profile_revision);
    assert.deepEqual(compileScore(runtime,a).body,compileScore(runtime,b).body);
    assert.deepEqual(compileScore(runtime,a).source,compileScore(runtime,b).source);
    assert.ok(Object.isFrozen(a) && Object.isFrozen(a.notes) && Object.isFrozen(a.notes[0]) && Object.isFrozen(a.captured_body));
  }
  const clamped=createScore(defaults,{energy:Infinity,pressure:-5,color:9});
  assert.deepEqual(clamped.captured_body,{energy:0,pressure:0,color:1});
});
await test('syllable and duration bounds reject before synthesis', () => {
  assert.throws(() => compileScore(runtime,createScore({...defaults,mode:'sing',text:Array(33).fill('we').join(' ')})),/33 syllables/);
  assert.throws(() => compileScore(runtime,createScore({...defaults,mode:'sing',text:Array(20).fill('we').join(' '),bpm:50,melody:'0:4'})),/planned take.*seconds/);
});

const takes = new Map();
for (const [label, patch, sampleRate] of [
  ['speech-48000',{mode:'speech'},48000],
  ['speech-44100',{mode:'speech'},44100],
  ['joke-48000',{mode:'joke',text:'I am jelly. | Well, nearly.',pause:.7},48000],
  ['sing-48000',{mode:'sing',text:'We sing.',melody:'0:1 4:1',bpm:120},48000],
  ['rap-48000',{mode:'rap',text:'Wet bell, slow glow.',bpm:120,feel:'swing'},48000],
  ...['J','F1','F2','F3'].map(actorId => [`actor-${actorId}`,{actorId,mode:'speech'},48000]),
]) {
  await test(`actual WASM render ${label}: finite, nonzero, bounded, truthful duration`, async () => {
    const t0=performance.now();
    const take=await renderTake(runtime,createScore({...defaults,...patch}),sampleRate); takes.set(label,take);
    assert.equal(take.sampleRate,sampleRate); assert.equal(take.duration,take.pcm.length/sampleRate);
    assert.ok(take.pcm.length>0); assert.ok(take.signal.rms>1e-5); assert.ok(take.signal.peak<=.920001);
    assert.equal(take.pcmHash,hash(Buffer.from(take.pcm.buffer)));
    assert.ok(take.pcm.every(Number.isFinite));
    for (const s of take.segments) assert.ok(Number.isFinite(s.t0) && Number.isFinite(s.t1) && s.t0>=0 && s.t1>=s.t0 && s.t1<=take.duration);
    const detail={label,actorId:take.score.actorId,mode:take.score.mode,sampleRate,frames:take.pcm.length,duration:take.duration,peak:take.signal.peak,rms:take.signal.rms,pcmHash:take.pcmHash,renderMs:Math.round(performance.now()-t0)};
    evidence.push(detail); return detail;
  });
}
await test('all five character renders have different PCM hashes (not a listening test)', () => {
  assert.equal(new Set([takes.get('speech-48000'),...['J','F1','F2','F3'].map(a=>takes.get(`actor-${a}`))].map(t=>t.pcmHash)).size,5);
});
await test('same actor plus different body/page at material=0 reproduces exact PCM', async () => {
  const other=await renderTake(runtime,createScore({...defaults,pageId:'different-body'},{energy:1,pressure:.8,color:.7}),48000);
  assert.equal(other.pcmHash,takes.get('speech-48000').pcmHash);
});
await test('WAV decodes every actual sample within signed 16-bit quantization bound at both rates', () => {
  const details=[];
  for (const label of ['speech-44100','speech-48000']) {
    const take=takes.get(label), bytes=encodeWav(take), d=new DataView(bytes), ascii=(at,n)=>String.fromCharCode(...new Uint8Array(bytes,at,n));
    assert.equal(ascii(0,4),'RIFF'); assert.equal(ascii(8,4),'WAVE'); assert.equal(ascii(12,4),'fmt '); assert.equal(ascii(36,4),'data');
    assert.equal(d.getUint32(4,true),bytes.byteLength-8); assert.equal(d.getUint16(20,true),1); assert.equal(d.getUint16(22,true),1);
    assert.equal(d.getUint32(24,true),take.sampleRate); assert.equal(d.getUint32(28,true),take.sampleRate*2); assert.equal(d.getUint16(32,true),2); assert.equal(d.getUint16(34,true),16);
    assert.equal(d.getUint32(40,true),take.pcm.length*2);
    let maxError=0;
    for(let i=0;i<take.pcm.length;i++) { const q=d.getInt16(44+2*i,true), decoded=q/(q<0?32768:32767); maxError=Math.max(maxError,Math.abs(decoded-take.pcm[i])); }
    assert.ok(maxError<=.50001/32767,`${label} error ${maxError}`);
    details.push({sampleRate:take.sampleRate,bytes:bytes.byteLength,maxAbsoluteError:maxError,wavSha256:hash(Buffer.from(bytes))});
  }
  return details;
});
await test('TakePlayer uses one scheduled buffer and current audio clock after an 800 ms graphics stall (clock double)', () => {
  const oldRaf=globalThis.requestAnimationFrame, oldCancel=globalThis.cancelAnimationFrame;
  let seq=0; const raf=new Map(), sources=[], frames=[];
  globalThis.requestAnimationFrame=fn=>{raf.set(++seq,fn);return seq;}; globalThis.cancelAnimationFrame=id=>raf.delete(id);
  const context={currentTime:10,destination:{},createBuffer:(channels,length,rate)=>({length,sampleRate:rate,pcm:new Float32Array(length),copyToChannel(pcm){this.pcm.set(pcm);}}),createBufferSource(){const source={starts:[],stops:0,connect(){},disconnect(){this.disconnected=true;},start(when){this.starts.push(when);},stop(){this.stops++;}};sources.push(source);return source;}};
  try {
    const take=takes.get('speech-48000'), player=new TakePlayer(context,null,{onFrame:f=>frames.push(f)});
    const start=player.play(take); assert.equal(sources.length,1); assert.equal(sources[0].starts.length,1); assert.equal(start,10.06);
    context.currentTime=start+.8; const fn=raf.values().next().value; raf.clear(); fn();
    assert.ok(Math.abs(frames.at(-1).t-.8)<1/take.sampleRate); assert.equal(sources[0].starts.length,1); assert.equal(sources.length,1);
    assert.equal(hash(Buffer.from(sources[0].buffer.pcm.buffer)),take.pcmHash);
    const oldEnd=sources[0].onended; player.stop(); const n=frames.length; oldEnd(); assert.equal(frames.length,n); assert.equal(sources[0].stops,1); assert.equal(raf.size,0);
    player.play(take); assert.equal(sources.length,2); assert.equal(hash(Buffer.from(sources[1].buffer.pcm.buffer)),take.pcmHash); player.stop();
  } finally {globalThis.requestAnimationFrame=oldRaf;globalThis.cancelAnimationFrame=oldCancel;}
});
await test('VoiceRenderer cancel/replacement rejects and ignores injected late results (Worker double)', async () => {
  const original=globalThis.Worker, workers=[];
  class FakeWorker {constructor(){workers.push(this);} terminate(){this.terminated=true;} postMessage(data){this.input=data;} emit(data){this.onmessage?.({data});}}
  globalThis.Worker=FakeWorker;
  try {
    const renderer=new VoiceRenderer(), score=createScore(defaults), p1=renderer.render(score); const reject1=assert.rejects(p1,{name:'AbortError'}); renderer.cancel(); await reject1;
    workers[0].emit({id:workers[0].input.id,take:{id:'late-cancelled'}}); assert.equal(renderer.pending,null);
    const p2=renderer.render(score), reject2=assert.rejects(p2,{name:'AbortError'}), p3=renderer.render(score); await reject2;
    let resolved=false; p3.then(()=>{resolved=true;});
    workers[1].emit({id:workers[1].input.id,take:{id:'late-replaced'}}); await Promise.resolve(); assert.equal(resolved,false);
    workers[2].emit({id:workers[1].input.id,take:{id:'wrong-id'}}); await Promise.resolve(); assert.equal(resolved,false);
    workers[2].emit({id:workers[2].input.id,take:{id:'current'}}); assert.deepEqual(await p3,{id:'current'}); assert.ok(workers.every(w=>w.terminated));
  } finally {globalThis.Worker=original;}
});
await test('frameAt silence before and after take, no stale actor activity', () => {
  const take=takes.get('speech-48000');
  assert.equal(frameAt(take,-.1).active,false);assert.equal(frameAt(take,-.1).level,0);
  assert.equal(frameAt(take,take.duration).active,false);assert.equal(frameAt(take,take.duration).level,0);
  assert.equal(frameAt(take,take.duration+10).t,take.duration);
});
let prior={};try{prior=JSON.parse(await fs.readFile(path.join(base,'tests/jelly-voice/critique.json'),'utf8'));}catch{}
const report={...prior,generatedAt:new Date().toISOString(),baseRevision:'e393e9f940e05d37a13e9af25c7178dcb1cbd817',inspected,results,evidence,limits:['No ears or listening-quality certification.','Clock and Worker adversarial tests use named doubles; browser integration reported separately.']};
await fs.writeFile(path.join(base,'tests/jelly-voice/critique.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,report:'tests/jelly-voice/critique.json'}));
if(results.some(r=>r.status==='FAIL')) process.exitCode=1;
