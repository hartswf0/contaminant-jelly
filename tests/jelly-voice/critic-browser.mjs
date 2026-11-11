// Independent browser critic; owns a read-only ephemeral loopback server.
// Run: node tests/jelly-voice/critic-browser.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);
const {chromium}=require(require.resolve('playwright',{paths:[process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || '/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules']}));
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.wav':'audio/wav','.mp3':'audio/mpeg'};
const server=http.createServer(async(req,res)=>{
  try {const name=path.resolve(base,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!name.startsWith(base+path.sep))throw Error('outside root');const st=await fs.stat(name);if(!st.isFile())throw Error('not a file');res.writeHead(200,{'content-type':mime[path.extname(name)]||'application/octet-stream','content-length':st.size,'cache-control':'no-store'});createReadStream(name).pipe(res);}
  catch{res.writeHead(404);res.end('missing');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
let browser;
try { browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']}); }
catch(error){
  const reportPath=path.join(base,'tests/jelly-voice/critique.json');let report={};try{report=JSON.parse(await fs.readFile(reportPath,'utf8'));}catch{}
  report.browser={generatedAt:new Date().toISOString(),status:'BLOCKED',stage:'chromium-launch',testsExecuted:0,error:String(error.message),limits:['No browser page was opened; no real browser scheduling, controls, or adapter behavior can be certified.','Actual WASM/Node render results are separate from this environment blocker.']};
  await fs.writeFile(reportPath,JSON.stringify(report,null,2)+'\n');await new Promise(resolve=>server.close(resolve));
  console.error('BLOCKED Chromium launch: '+String(error.message).split('\n').slice(0,2).join(' '));process.exit(2);
}
const results=[],pageEvidence=[],inspected={};
for(const file of ['bonus/jelly-voice/panel.js','bonus/jelly-voice/score.mjs','bonus/jelly-voice/worker.mjs','bonus/jelly-voice/client.mjs','bonus/jelly-voice/performance.mjs',...['realjelly','thinkjelly','jellyjar','jellystudio','wetbell','colloquy','bodies'].map(x=>`bonus/${x}.html`)])inspected[file]=sha(await fs.readFile(path.join(base,file)));
async function test(name,fn){const t0=performance.now();try{const detail=await fn();results.push({name,status:'PASS',elapsedMs:Math.round(performance.now()-t0),detail});}catch(error){results.push({name,status:'FAIL',elapsedMs:Math.round(performance.now()-t0),error:error.stack});}console.log(`${results.at(-1).status} ${name}${results.at(-1).error?': '+results.at(-1).error.split('\n')[0]:''}`);}
async function newPage(route){
  const context=await browser.newContext({viewport:{width:800,height:600},deviceScaleFactor:1,acceptDownloads:true});
  const page=await context.newPage(),errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(origin))failed.push({url:r.url().slice(origin.length),status:r.status()});});
  await page.addInitScript(()=>{
    window.__critic={starts:[],stops:0,workerInputs:[],workerMessages:[],terminations:0};
    const start=AudioBufferSourceNode.prototype.start,stop=AudioBufferSourceNode.prototype.stop;
    AudioBufferSourceNode.prototype.start=function(...args){window.__critic.starts.push({when:args[0]??0,clock:this.context.currentTime,frames:this.buffer?.length,sampleRate:this.buffer?.sampleRate,buffer:this.buffer,context:this.context});return start.apply(this,args);};
    AudioBufferSourceNode.prototype.stop=function(...args){window.__critic.stops++;return stop.apply(this,args);};
    const Base=Worker; window.Worker=class extends Base{constructor(...args){super(...args);this.addEventListener('message',e=>window.__critic.workerMessages.push({id:e.data?.id,status:e.data?.status,error:e.data?.error,hasTake:!!e.data?.take}));}postMessage(data,...args){window.__critic.workerInputs.push({id:data?.id,text:data?.score?.text});return super.postMessage(data,...args);}terminate(){window.__critic.terminations++;return super.terminate();}};
  });
  await page.goto(origin+route,{waitUntil:'domcontentloaded',timeout:25000});
  return {context,page,errors,failed};
}
async function panelReady(page,id){await page.waitForFunction(id=>!!window.JELLY_VOICES?.[id],id,{timeout:25000});}
async function setWords(page,text){await page.locator('jelly-voice-panel #words').fill(text);}
async function prepare(page,id,text='We are jelly.'){
  await page.locator('jelly-voice-panel .toggle').click();
  await page.locator('jelly-voice-panel #actor').selectOption('G');await setWords(page,text);
  await page.locator('jelly-voice-panel #material').focus();await page.locator('jelly-voice-panel #material').press('Home');
  await page.locator('jelly-voice-panel #prepare').click();
  await page.waitForFunction(id=>{const s=window.JELLY_VOICES[id].getState();return !s.busy;},id,{timeout:60000});
  const state=await page.evaluate(id=>window.JELLY_VOICES[id].getState(),id);
  assert.ok(state.take,await page.locator('jelly-voice-panel #status').innerText());return state;
}
let retained;
try{
  for(const [route,id] of [['/bonus/jellyjar.html','jellyjar'],['/bonus/realjelly.html?low','realjelly'],['/bonus/thinkjelly.html','thinkjelly'],['/bonus/wetbell.html','wetbell'],['/bonus/colloquy.html?low&ui','colloquy'],['/bonus/bodies.html?sp=glass','bodies-glass'],['/bonus/jellystudio.html','jellystudio']]){
    await test(`actual adapter mounts and renders once: ${id}`,async()=>{
      const bundle=await newPage(route),{page}=bundle; let keep=false;
      try{
        await panelReady(page,id);
        const initial=await page.evaluate(id=>({state:window.JELLY_VOICES[id].getState(),starts:window.__critic.starts.length,workers:window.__critic.workerInputs.length}),id);
        assert.equal(initial.state.take,null);assert.equal(initial.state.playing,false);assert.equal(initial.workers,0);
        const state=await prepare(page,id);
        assert.equal(state.take.score.actorId,'G');assert.equal(state.take.score.voice_profile_id,'anchor-1');assert.equal(state.take.score.voice_profile_revision,1);
        const observation=await page.evaluate(id=>{
          const c=window.JELLY_VOICES[id],t=c.getTake(),x=window.__critic,matching=x.starts.filter(s=>s.frames===t.pcm.length&&s.sampleRate===t.sampleRate);
          return {state:c.getState(),sampleRate:t.sampleRate,frames:t.pcm.length,matchingSourceStarts:matching.length,workerInputs:x.workerInputs,workerMessages:x.workerMessages,starts:x.starts.length};
        },id);
        assert.equal(observation.matchingSourceStarts,1);assert.equal(observation.workerInputs.length,1);assert.equal(bundle.errors.length,0,JSON.stringify(bundle.errors));
        pageEvidence.push({id,route,...observation,pageErrors:bundle.errors,failedResources:bundle.failed});
        if(id==='jellyjar'){retained=bundle;keep=true;}
        else{await page.evaluate(id=>window.JELLY_VOICES[id].stop(),id);const status=await page.evaluate(id=>window.JELLY_VOICES[id].getState(),id);assert.equal(status.playing,false);}
        return {pcmHash:state.take.pcmHash,sampleRate:observation.sampleRate,duration:state.take.duration,failedResources:bundle.failed};
      }finally{if(!keep)await bundle.context.close();}
    });
  }
  await test('same actor rendered on all seven actual bodies has identical neutral-colour PCM',()=>{
    assert.equal(pageEvidence.length,7,'all seven pages must be executable');
    assert.equal(new Set(pageEvidence.map(p=>p.state.take.pcmHash)).size,1);
    return {hash:pageEvidence[0].state.take.pcmHash,pages:pageEvidence.map(p=>p.id)};
  });
  if(retained){
    const {page}=retained,id='jellyjar';
    await test('replay is the saved PCM; 800 ms main-thread stall does not reschedule source (actual AudioContext)',async()=>{
      await page.locator('jelly-voice-panel #replay').click();
      const evidence=await page.evaluate(async()=>{
        const x=window.__critic,last=x.starts.at(-1),take=window.JELLY_VOICES.jellyjar.getTake(),hash=async buf=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buf)),b=>b.toString(16).padStart(2,'0')).join('');
        const before={starts:x.starts.length,clock:last.context.currentTime,hash:await hash(last.buffer.getChannelData(0).buffer)};
        const until=performance.now()+800;while(performance.now()<until){};
        const after={starts:x.starts.length,clock:last.context.currentTime,hash:await hash(last.buffer.getChannelData(0).buffer)};
        await new Promise(requestAnimationFrame);
        const text=document.querySelector('jelly-voice-panel').shadowRoot.querySelector('#time').textContent;
        return {before,after,start:last.when,display:text,takeHash:take.pcmHash};
      });
      assert.equal(evidence.before.starts,evidence.after.starts);assert.equal(evidence.before.hash,evidence.takeHash);assert.equal(evidence.after.hash,evidence.takeHash);
      assert.ok(evidence.after.clock-evidence.before.clock>.65,'AudioContext must progress while graphics are blocked');
      const shown=Number(evidence.display.split(' ')[0]);assert.ok(shown>.6,'display must read current audio time after blocked RAF');return evidence;
    });
    await test('WAV download uses last prepared take despite edited controls (actual UI download)',async()=>{
      await page.evaluate(()=>window.JELLY_VOICES.jellyjar.stop());
      const expected=await page.evaluate(async()=>{const t=window.JELLY_VOICES.jellyjar.getTake();const {encodeWav}=await import('/bonus/jelly-voice/performance.mjs');const wav=encodeWav(t);return {hash:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',wav)),b=>b.toString(16).padStart(2,'0')).join(''),frames:t.pcm.length,sampleRate:t.sampleRate,pcmHash:t.pcmHash,workers:window.__critic.workerInputs.length};});
      await setWords(page,'Edited words must not affect the saved vocal.');await page.locator('jelly-voice-panel #actor').selectOption('F3');
      const [download]=await Promise.all([page.waitForEvent('download'),page.locator('jelly-voice-panel #wav').click()]);
      const stream=await download.createReadStream(),chunks=[];for await(const c of stream)chunks.push(c);const bytes=Buffer.concat(chunks);
      assert.equal(sha(bytes),expected.hash);assert.equal(bytes.readUInt32LE(24),expected.sampleRate);assert.equal(bytes.readUInt32LE(40),expected.frames*2);
      const current=await page.evaluate(()=>({workers:window.__critic.workerInputs.length,state:window.JELLY_VOICES.jellyjar.getState()}));assert.equal(current.workers,expected.workers);assert.equal(current.state.take.pcmHash,expected.pcmHash);
      return {filename:download.suggestedFilename(),bytes:bytes.length,wavHash:sha(bytes),sampleRate:expected.sampleRate};
    });
    await test('invalid edited score keeps last valid take and schedules no new source (actual UI)',async()=>{
      const before=await page.evaluate(()=>({hash:window.JELLY_VOICES.jellyjar.getState().take.pcmHash,starts:window.__critic.starts.length,workers:window.__critic.workerInputs.length}));
      await setWords(page,'12345');await page.locator('jelly-voice-panel #prepare').click();
      const after=await page.evaluate(()=>({state:window.JELLY_VOICES.jellyjar.getState(),starts:window.__critic.starts.length,workers:window.__critic.workerInputs.length}));
      assert.equal(after.state.take.pcmHash,before.hash);assert.equal(after.starts,before.starts);assert.equal(after.workers,before.workers);assert.match(await page.locator('jelly-voice-panel #status').innerText(),/English phrase/);
    });
    await test('stop during actual worker render prevents late playback and preserves previous take',async()=>{
      const before=await page.evaluate(()=>({hash:window.JELLY_VOICES.jellyjar.getState().take.pcmHash,starts:window.__critic.starts.length,messages:window.__critic.workerMessages.length}));
      await setWords(page,'The little jelly travels across a very quiet river and sings about all the shimmering stones below.');
      await page.locator('jelly-voice-panel #prepare').click();
      await page.waitForFunction(n=>window.__critic.workerMessages.slice(n).some(x=>x.status==='rendering'),before.messages,{timeout:20000});
      await page.locator('jelly-voice-panel #stop').click();await page.waitForTimeout(1000);
      const after=await page.evaluate(()=>({state:window.JELLY_VOICES.jellyjar.getState(),starts:window.__critic.starts.length,terminations:window.__critic.terminations}));
      assert.equal(after.state.busy,false);assert.equal(after.state.playing,false);assert.equal(after.starts,before.starts);assert.equal(after.state.take.pcmHash,before.hash);return after;
    });
    await test('replacement during actual worker render adopts only newest score',async()=>{
      const before=await page.evaluate(()=>({starts:window.__critic.starts.length,messages:window.__critic.workerMessages.length}));
      await setWords(page,'The long old jelly score should never play after a newer and shorter replacement has been requested.');
      await page.locator('jelly-voice-panel #prepare').click();await page.waitForFunction(n=>window.__critic.workerMessages.slice(n).some(x=>x.status==='rendering'),before.messages,{timeout:20000});
      await setWords(page,'Hi.');await page.evaluate(()=>{void window.JELLY_VOICES.jellyjar.prepare();});
      await page.waitForFunction(()=>{const s=window.JELLY_VOICES.jellyjar.getState();return !s.busy&&s.take?.score.text==='Hi.';},null,{timeout:30000});
      const after=await page.evaluate(()=>({state:window.JELLY_VOICES.jellyjar.getState(),starts:window.__critic.starts.length}));assert.equal(after.starts,before.starts+1);assert.equal(after.state.take.score.text,'Hi.');return after;
    });
  }
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
const reportPath=path.join(base,'tests/jelly-voice/critique.json');let report={};try{report=JSON.parse(await fs.readFile(reportPath,'utf8'));}catch{}
report.browser={generatedAt:new Date().toISOString(),browser:'system Chromium via Playwright',inspected,results,pageEvidence,limits:['Headless browser verifies scheduling and buffers, not audible quality or speaker output.','No listener or ASR was used.']};
await fs.writeFile(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:results.filter(x=>x.status==='PASS').length,failed:results.filter(x=>x.status==='FAIL').length,report:'tests/jelly-voice/critique.json'}));
if(results.some(x=>x.status==='FAIL'))process.exitCode=1;
