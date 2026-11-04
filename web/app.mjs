import {MODELS, activeStates, request, post, messageText, orderedMessages, fileUrl, completionBody, pcmWav} from './api.mjs';

const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = name => `<svg class="ic" aria-hidden="true"><use href="#i-${name}"/></svg>`;
const usd = value => value == null ? '—' : '$' + Number(value).toFixed(3);
const state = {
  user: null, ready: false, chats: [], chat: null, chatId: null, mode: 'auto', jobs: [], usage: null,
  submitting: false, transportUncertain: false, drawer: false, error: '', files: [],
  session: crypto.randomUUID(), voice: false, recording: null, audio: null, speechRequest: null, speechTurn: null,
};
let refreshRunning = false, recordingTimer;
const renderedMessages = new Map();

function patchThread(html) {
  const root = $('#threadInner'), template = document.createElement('template');
  template.innerHTML = html;
  const existing = new Map([...root.children].map(node => [node.dataset.message || '_empty', node]));
  const wanted = new Set();
  [...template.content.children].forEach((candidate, index) => {
    const key = candidate.dataset.message || '_empty', markup = candidate.outerHTML;
    wanted.add(key);
    let node = existing.get(key);
    if (!node || renderedMessages.get(key) !== markup) {
      if (node) node.replaceWith(candidate);
      node = candidate; renderedMessages.set(key, markup);
    }
    if (root.children[index] !== node) root.insertBefore(node, root.children[index] || null);
  });
  for (const [key, node] of existing) if (!wanted.has(key)) {node.remove();renderedMessages.delete(key);}
}

function notify(error) { state.error = error instanceof Error ? error.message : error; render(); }
function busy() { return state.submitting || state.transportUncertain || orderedMessages(state.chat).some(m => m.role === 'assistant' && m.done === false); }
function rememberChat() { if (state.chatId) location.hash = 'chat=' + encodeURIComponent(state.chatId); else history.replaceState(null, '', location.pathname); }
function renderFiles(files) {
  return (files || []).map(file => {
    const url = fileUrl(file); if (!url) return '';
    const mime = file.content_type || file.meta?.content_type || '';
    if (file.type === 'video' || mime.startsWith('video/')) return `<video controls preload="metadata" src="${esc(url)}" style="max-width:100%;border-radius:12px"></video>`;
    if (file.type === 'audio' || mime.startsWith('audio/')) return `<audio controls preload="none" src="${esc(url)}"></audio>`;
    return `<a href="${esc(url)}" target="_blank" rel="noopener"><img loading="lazy" src="${esc(url)}" alt="${esc(file.name || 'Saved image')}" style="border-radius:12px"></a>`;
  }).join('');
}
function render() {
  $('#banner').hidden = !state.error; $('#banner').textContent = state.error;
  $('#convTitle').textContent = state.chat?.title || 'New chat';
  $('#whoBtn').innerHTML = `<span class="av av-parent">${esc(state.user?.name?.slice(0,1) || '?')}</span><span class="w-t">${esc(state.user?.name || 'Family AI')}<small>${esc(state.user?.role || 'Sign in required')}</small></span>`;
  const filter = $('#search').value.toLowerCase();
  $('#convlist').innerHTML = state.chats.filter(c => (c.title || '').toLowerCase().includes(filter)).map(c => `<div class="ci-row ${c.id === state.chatId ? 'on' : ''}"><button class="ci" data-chat="${esc(c.id)}"><span class="ci-t">${esc(c.title || 'Untitled chat')}</span></button></div>`).join('') || '<p class="side-empty">Your saved chats appear here.</p>';
  $('#routeLbl').textContent = MODELS[state.mode][1];
  $('#pillWrap').innerHTML = `<button class="pill" data-act="act-toggle">${icon('pulse')} Activity${state.jobs.some(j=>activeStates.has(j.state)) ? ' · working' : ''}</button>`;
  $('#input').disabled = !state.ready;
  $('#sendBtn').disabled = !state.ready || (!busy() && !$('#input').value.trim());
  $('#sendBtn').type = busy() ? 'button' : 'submit'; $('#sendBtn').dataset.act = busy() ? 'stop' : '';
  $('#sendBtn').setAttribute('aria-label', busy() ? 'Stop generation' : 'Send');
  $('#sendBtn').innerHTML = icon(busy() ? 'stop' : 'send');
  $('#cNote').textContent = !state.ready ? 'Sign in through Open WebUI to use this preview.' : state.transportUncertain ? 'Delivery is uncertain. Check Activity before sending again.' : busy() ? 'Working on the server. You can reopen this conversation.' : state.files.length ? 'Image attached · Auto uses the larger Gemma.' : '';
  $('#attachRow').hidden = !state.files.length;
  $('#attachRow').innerHTML = state.files.map(f => `<span class="chip">${esc(f.name)} <button type="button" data-act="clear-attach" aria-label="Remove attachment">×</button></span>`).join('');
  const messages = orderedMessages(state.chat);
  const thread = $('#thread'), nearEnd = thread.scrollHeight-thread.scrollTop-thread.clientHeight < 100;
  const html = messages.length ? messages.map(m => {
    const text = messageText(m);
    const ownedJobs = state.jobs.filter(j => j.conversation === state.chatId && j.turn === m.id);
    const generated = ownedJobs.flatMap(j => j.output?.file ? [j.output.file] : []);
    const files = [...(m.files || [])]; for (const f of generated) if (!files.some(x => x.id === f.id)) files.push(f);
    const progress = ownedJobs.filter(j => activeStates.has(j.state)).map(j => `<div class="pc"><b>${esc(j.capability)} · ${esc(j.state)}</b><span>Reserved estimate ${usd(j.reserved_usd)}</span><button class="mini" data-cancel="${esc(j.id)}">Request cancellation</button></div>`).join('');
    return `<article class="msg ${m.role === 'user' ? 'user' : ''}" data-message="${esc(m.id)}">${m.role === 'user' ? `<div class="bubble">${esc(text)}</div>` : `<div class="m-body" style="white-space:pre-wrap">${esc(text || (m.done === false ? 'Waiting for the model…' : ''))}</div>`}${m.error ? `<div class="card err">${esc(m.error.content || m.error)}</div>` : ''}${progress}<div class="m-media">${renderFiles(files)}</div>${m.role === 'assistant' && m.done && text ? `<div class="m-foot"><button class="act" data-copy="${esc(m.id)}">${icon('copy')}Copy</button><button class="act" data-read="${esc(m.id)}">${icon('speaker')}Play · Piper</button></div>` : ''}</article>`;
  }).join('') : `<div class="hello"><h2>What can I help with?</h2><p>Suomi · Svenska · English</p><p>Chat, ask for a picture, or work through something difficult.</p>${!state.user ? '<a class="btn primary" href="/auth?redirect=%2Fpreview%2F">Sign in to Family AI</a>' : ''}</div>`;
  // Preserve media playback and focus when a polling response has no changes.
  patchThread(html); if (nearEnd) thread.scrollTop=thread.scrollHeight;
  $('#activity').hidden = !state.drawer; $('#app').classList.toggle('act-open', state.drawer);
  $('#actBody').innerHTML = `<p class="hint">Governed estimates only. Hosting and direct Open WebUI calls are separate.</p>${state.usage ? Object.entries(state.usage.periods).map(([k,v])=>`<p>${esc(k)}: ${usd(v.estimated_and_reserved_usd)} estimated and reserved / ${usd(v.limit_usd)}</p>`).join('') : ''}${state.jobs.map(j=>`<div class="card"><div class="c-t"><b>${esc(j.capability)} · ${esc(j.state)}</b><span>${usd(j.estimated_charge_usd)} estimated; ${usd(j.reserved_usd)} reserved</span><small>${esc(j.cancel_requested ? 'Cancellation requested; waiting for confirmation.' : j.state === 'unknown' ? 'Outcome uncertain. Inspect before retrying.' : '')}</small></div>${activeStates.has(j.state) ? `<button class="mini" data-cancel="${esc(j.id)}">Cancel</button>` : ''}${j.state === 'unknown' ? `<button class="mini" data-refresh="${esc(j.id)}">Check provider result</button>` : ''}</div>`).join('') || '<p>No governed jobs yet.</p>'}`;
}
async function loadChat(id) {
  if (state.voice && id !== state.chatId) await closeVoice();
  state.chatId = id; state.chat = id ? (await request('/api/v1/chats/' + encodeURIComponent(id))).chat : null;
  state.transportUncertain = false; state.error = ''; rememberChat(); render();
}
async function ensureChat() {
  if (state.chatId) return;
  const result = await post('/api/v1/chats/new', {chat:{title:'New chat',models:[MODELS[state.mode][0]],history:{messages:{},currentId:null},messages:[],files:[]}});
  state.chatId=result.id; state.chat=result.chat; rememberChat();
}
async function refresh() {
  if (!state.ready || refreshRunning || document.hidden) return;
  refreshRunning=true;
  const id=state.chatId;
  try {
    const values = await Promise.all([request('/api/v1/chats/list'),request('/api/v1/family/jobs'),request('/api/v1/family/usage'),id ? request('/api/v1/chats/'+encodeURIComponent(id)) : null]);
    state.chats=values[0]; state.jobs=values[1].jobs; state.usage=values[2];
    if (id && state.chatId === id) state.chat=values[3].chat;
    render();
  } catch (error) { if (error.status === 401) {state.ready=false;state.user=null;} notify(error); }
  finally {refreshRunning=false;}
}
async function send(text) {
  text=text.trim(); if (!text || busy() || !state.ready) return;
  state.submitting=true; state.error=''; render();
  let submitted=false;
  try {
    await ensureChat();
    // Fetch authoritative history before constructing this turn; never overwrite the full saved chat.
    state.chat=(await request('/api/v1/chats/'+encodeURIComponent(state.chatId))).chat;
    if (orderedMessages(state.chat).some(m=>m.done===false)) throw new Error('This conversation already has an unfinished answer. Inspect Activity first.');
    const images=state.files.map(f=>f.data);
    if (images.length && state.mode==='fast') throw new Error('Choose Auto or Finnish / Swedish for image understanding.');
    const body=completionBody(state.chatId,state.chat,text,state.mode,{user:crypto.randomUUID(),assistant:crypto.randomUUID(),session:state.session},images);
    $('#input').value=''; state.files=[];
    submitted=true;
    await post('/api/chat/completions',body);
    // One submission only. Background processing persists native tools and output;
    // polling the saved chat also survives a page reload and proxy timeout.
  } catch (error) { state.transportUncertain=submitted; notify(error); }
  finally {state.submitting=false;await refresh();render();}
}
async function stop() {
  if (!state.chatId) return;
  stopAudio();
  const active=state.jobs.filter(j=>j.conversation===state.chatId && activeStates.has(j.state));
  const results=await Promise.allSettled([post('/api/tasks/chat/'+encodeURIComponent(state.chatId)+'/stop',{}),...active.map(j=>post('/api/v1/family/jobs/'+j.id+'/cancel',{}))]);
  const failed=results.find(r=>r.status==='rejected'); if (failed) notify(failed.reason); else state.transportUncertain=false;
  await refresh();
}
function stopAudio() { if (state.audio) {state.audio.pause();state.audio=null;} if (state.speechRequest) {state.speechRequest.abort();state.speechRequest=null;} }
function language() {return $('#speechLanguage').value;}
async function openVoice() {
  if (!state.ready || busy()) return;
  await ensureChat();
  await post(`/api/v1/family/voice/session?chat_id=${encodeURIComponent(state.chatId)}&turn=${crypto.randomUUID()}`,{});
  state.voice=true; $('#voice').hidden=false; $('#vState').textContent='Voice enabled · 5 minutes';
  $('#vSay').textContent='Press Record to speak, or Play beside an answer.';
  $('#vHint').textContent='Whisper transcribes; Piper reads answers. Recording stops after 30 seconds. No automatic playback.';
  $('#vAloud').hidden=true;$('#vStop').disabled=false;$('#vMic').setAttribute('aria-label','Record up to 30 seconds');$('#vMic').setAttribute('aria-pressed','false');
  const quote=await post('/api/v1/family/quote',{endpoint:'b8yk3ju5yc5kqx',timeout_seconds:180});
  $('#vJobs').textContent=`Each transcription or playback reserves up to ${usd(quote.estimated_usd)} (estimate, including idle time).`;
}
async function closeVoice() {
  state.voice=false;
  if (state.recording) {state.recording.discard=true;state.recording.recorder.stop();}
  stopAudio();$('#voice').hidden=true;
  await request('/api/v1/family/voice/session',{method:'DELETE'});
}
async function record() {
  if (!state.voice || state.speechRequest) return;
  if (state.recording) {state.recording.recorder.stop();return;}
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  if (!state.voice) {stream.getTracks().forEach(t=>t.stop());return;}
  const recorder=new MediaRecorder(stream), recording={recorder,stream,chunks:[],discard:false}; state.recording=recording;
  $('#vMic').setAttribute('aria-pressed','true');$('#vSay').textContent='Recording… press Record again to finish.';
  recorder.ondataavailable=e=>{if(e.data.size)recording.chunks.push(e.data);};
  recorder.onstop=async()=>{
    clearTimeout(recordingTimer);stream.getTracks().forEach(t=>t.stop());state.recording=null;$('#vMic').setAttribute('aria-pressed','false');
    if(recording.discard)return;
    let context;
    try {
      $('#vSay').textContent='Transcribing…';context=new AudioContext({sampleRate:24000});
      const audio=await context.decodeAudioData(await new Blob(recording.chunks,{type:recorder.mimeType}).arrayBuffer());
      const samples=audio.getChannelData(0); // mono is sufficient for Whisper
      const bytes=pcmWav(samples,audio.sampleRate),turn=crypto.randomUUID();state.speechTurn=turn;state.speechRequest=new AbortController();
      const result=await request(`/api/v1/family/voice/transcriptions?chat_id=${encodeURIComponent(state.chatId)}&turn=${turn}&language=${language()}`,{method:'POST',headers:{'Content-Type':'audio/wav'},body:bytes,signal:state.speechRequest.signal});
      $('#input').value=result.text;$('#vSay').textContent=result.text || 'No speech recognised.';
      $('#vHint').textContent='Review the transcript, then press Send in the conversation.';$('#voice').hidden=true;
    } catch(error) {notify(error);$('#vSay').textContent='Transcription did not finish. Check Activity before retrying.';}
    finally {state.speechRequest=null;if(context)await context.close();await refresh();}
  };
  recorder.start();recordingTimer=setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},29000);
}
async function read(messageId) {
  if (!state.voice) {await openVoice(); if (!state.voice) return;}
  const message=orderedMessages(state.chat).find(m=>m.id===messageId),text=messageText(message || {});
  if (!text || state.speechRequest)return;
  if(text.length>2000)throw new Error('Select a shorter answer for playback (maximum 2,000 characters).');
  stopAudio();state.speechTurn=messageId;state.speechRequest=new AbortController();
  try {
    $('#vSay').textContent='Preparing Piper playback…';
    const result=await post(`/api/v1/family/voice/speech?chat_id=${encodeURIComponent(state.chatId)}&turn=${messageId}&language=${language()}`,{input:text},{signal:state.speechRequest.signal});
    const url=fileUrl(result.file); if(!url)throw new Error('The saved audio URL was invalid.');
    state.audio=new Audio(url);
    try {await state.audio.play();$('#vSay').textContent='Playing · press Interrupt to stop';}
    catch {$('#vSay').textContent='Audio is saved. Press Play on the audio player below.';$('#vJobs').innerHTML=`<audio controls src="${esc(url)}"></audio>`;state.audio=$('#vJobs audio');}
  } finally {state.speechRequest=null;await refresh();}
}
async function settings() {
  if (!state.ready) return;
  $('#settings').hidden=false;$('#setTabs').innerHTML='';
  $('#setBody').innerHTML='<p>Loading spending policy…</p>';
  const policy=state.user.role==='admin'?await request('/api/v1/family/policy'):null;
  $('#setBody').innerHTML=`<p>Governed estimates are separate from your provider invoice. Direct models and native Open WebUI audio bypass these limits.</p>${policy ? `<form id="policyForm"><label class="field">Daily USD<input name="daily_usd" type="number" min="0.01" step="0.01" value="${esc(policy.daily_usd)}"></label><label class="field">Monthly USD<input name="monthly_usd" type="number" min="0.01" step="0.01" value="${esc(policy.monthly_usd)}"></label><p>Concurrent operations: ${esc(policy.max_concurrent)} · video maximum: ${esc(policy.max_video_seconds)} seconds.</p><button class="btn" type="submit">Save limits</button></form>` : '<p>Only the administrator can change household limits.</p>'}<p><a href="/">Open WebUI</a> · <button class="mini" data-act="theme">Switch theme</button></p>`;
}
document.addEventListener('click',event=>{
  const target=event.target.closest('button,[data-act]');if(!target)return;
  const act=target.dataset.act;
  (async()=>{
    if(target.dataset.chat){await loadChat(target.dataset.chat);$('#app').classList.remove('side-open');}
    else if(target.dataset.cancel){await post('/api/v1/family/jobs/'+target.dataset.cancel+'/cancel',{});await refresh();}
    else if(target.dataset.refresh){await post('/api/v1/family/jobs/'+target.dataset.refresh+'/refresh',{});await refresh();}
    else if(target.dataset.read)await read(target.dataset.read);
    else if(target.dataset.copy)await navigator.clipboard.writeText(messageText(orderedMessages(state.chat).find(m=>m.id===target.dataset.copy)));
    else if(target.dataset.mode){state.mode=target.dataset.mode;$('#menu').hidden=true;render();}
    else if(act==='new'){if(state.voice)await closeVoice();await loadChat(null);}
    else if(act==='stop')await stop();
    else if(act==='side-toggle'){$('#app').classList.toggle(matchMedia('(max-width:899px)').matches?'side-open':'side-collapsed');}
    else if(act==='act-toggle'){state.drawer=!state.drawer;render();}
    else if(act==='attach')$('#file').click();
    else if(act==='clear-attach'){state.files=[];render();}
    else if(act==='voice-open')await openVoice();
    else if(act==='voice-close')await closeVoice();
    else if(act==='v-mic')await record();
    else if(act==='v-interrupt'||act==='orb'){if(state.recording){state.recording.discard=true;state.recording.recorder.stop();}stopAudio();$('#vSay').textContent='Stopped. Provider work may still need cancellation in Activity.';if(state.speechTurn){const job=state.jobs.find(j=>j.turn===state.speechTurn&&activeStates.has(j.state));if(job)await post('/api/v1/family/jobs/'+job.id+'/cancel',{});}}
    else if(act==='settings'||act==='profile-menu')await settings();
    else if(act==='modal-close')$('#settings').hidden=true;
    else if(act==='theme'){document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';}
    else if(act==='route-menu'){
      $('#menu').innerHTML=Object.entries(MODELS).map(([k,v])=>`<button class="mi" data-mode="${k}">${esc(v[1])}</button>`).join('');$('#menu').hidden=!$('#menu').hidden;
      const r=target.getBoundingClientRect();$('#menu').style.left=Math.max(8,r.left)+'px';$('#menu').style.bottom=(innerHeight-r.top+5)+'px';$('#menu').style.top='auto';
    }
  })().catch(notify);
});
$('#composer').addEventListener('submit',event=>{event.preventDefault();send($('#input').value);});
$('#input').addEventListener('input',render);$('#search').addEventListener('input',render);
$('#input').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();send($('#input').value);}});
$('#vForm').addEventListener('submit',event=>{event.preventDefault();$('#input').value=$('#vInput').value;$('#voice').hidden=true;render();});
document.addEventListener('submit',event=>{if(event.target.id==='policyForm'){event.preventDefault();const form=new FormData(event.target);post('/api/v1/family/policy',{daily_usd:form.get('daily_usd'),monthly_usd:form.get('monthly_usd')}).then(()=>{$('#settings').hidden=true;return refresh();}).catch(notify);}});
$('#file').accept='image/jpeg,image/png,image/webp';
$('#file').addEventListener('change',async()=>{try{
  const file=$('#file').files[0];if(!file)return;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>8*1024*1024)throw new Error('Choose a JPEG, PNG or WebP image smaller than 8 MB.');
  const reader=new FileReader();reader.onload=()=>{state.files=[{name:file.name,data:reader.result}];render();};reader.readAsDataURL(file);
}catch(error){notify(error);}finally{$('#file').value='';}});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){$('#settings').hidden=true;$('#menu').hidden=true;}});
window.addEventListener('pagehide',()=>{if(state.recording){state.recording.discard=true;state.recording.stream.getTracks().forEach(t=>t.stop());}stopAudio();});
document.addEventListener('play',event=>{if(event.target instanceof HTMLAudioElement){if(state.audio && state.audio!==event.target)state.audio.pause();state.audio=event.target;}},true);
window.addEventListener('online',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});

async function start(){
  render();
  try {
    const user=await request('/api/v1/auths/');
    state.user={id:user.id,name:user.name,role:user.role}; // Do not retain the token returned by the native session API.
    if(!['admin','user'].includes(user.role))throw new Error('Your account is waiting for administrator approval.');
    await request('/api/v1/family/capabilities');state.ready=true;
    const match=location.hash.match(/^#chat=([^&]+)$/);if(match)await loadChat(decodeURIComponent(match[1]));
    await refresh();
  }catch(error){notify(error);}
}
start();
async function poll(){await refresh();setTimeout(poll,busy()||state.speechRequest?1500:10000);}
setTimeout(poll,1500);
