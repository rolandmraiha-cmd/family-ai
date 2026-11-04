export const MODELS = {
  auto: ['family-auto', 'Auto'], fast: ['family_router.fast', 'Fast'],
  pro: ['family_router.pro', 'Pro'], language: ['family_router.language', 'Finnish / Swedish · vision'],
};
export const activeStates = new Set(['reserved', 'submitting', 'queued', 'running', 'unknown', 'cancel_requested']);

export async function request(path, options = {}) {
  const response = await fetch(path, {credentials: 'same-origin', ...options});
  if (!response.ok) {
    const error = new Error(response.status === 401 ? 'Sign in with your existing Open WebUI account.' : `Request failed (${response.status}).`);
    error.status = response.status;
    try {
      const data = await response.json();
      const detail = data.error?.message || data.detail;
      if (typeof detail === 'string') error.message = detail;
    } catch {}
    throw error;
  }
  return response.status === 204 ? null : response.json();
}
export const post = (path, body, options = {}) => request(path, {
  method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), ...options,
});

export function messageText(message) {
  if (Array.isArray(message.output) && message.output.length) {
    // Native content aggregates pre-tool narration and the final answer. Use
    // only public message items after the last tool boundary, including for TTS.
    const boundary = message.output.findLastIndex(item => item.type === 'function_call' || item.type === 'function_call_output');
    return message.output.slice(boundary + 1).filter(item => item.type === 'message' && item.role !== 'user')
      .flatMap(item => item.content || []).filter(p => p.type === 'output_text' || p.type === 'text')
      .map(p => p.text || '').join('\n');
  }
  if (typeof message.content === 'string' && message.content) return message.content;
  if (Array.isArray(message.content)) return message.content.filter(p => p.type === 'text').map(p => p.text || '').join('\n');
  return '';
}

export function orderedMessages(chat) {
  const history = chat?.history || {}, messages = history.messages || {};
  let id = history.currentId;
  const ordered = [], seen = new Set();
  while (id && messages[id] && !seen.has(id)) {
    seen.add(id); ordered.unshift(messages[id]); id = messages[id].parentId;
  }
  return ordered.length ? ordered : (chat?.messages || []);
}

export function fileUrl(file, origin = globalThis.location?.origin) {
  if (!file || typeof file.id !== 'string' || !/^[a-zA-Z0-9-]+$/.test(file.id)) return null;
  const expected = `/api/v1/files/${file.id}/content`;
  if (!file.url) return expected;
  try {
    const parsed = new URL(file.url, origin);
    return parsed.origin === origin && parsed.pathname === expected && !parsed.search && !parsed.hash ? expected : null;
  } catch { return null; }
}

export function completionBody(chatId, chat, text, mode, ids, images = []) {
  if (!MODELS[mode]) throw new Error('Unknown model choice');
  const previous = orderedMessages(chat);
  const content = images.length ? [{type: 'text', text}, ...images.map(url => ({type: 'image_url', image_url: {url}}))] : text;
  const userMessage = {
    id: ids.user, parentId: previous.at(-1)?.id || null, childrenIds: [ids.assistant],
    role: 'user', content, timestamp: Math.floor(Date.now() / 1000), models: [MODELS[mode][0]],
  };
  return {
    model: MODELS[mode][0], chat_id: chatId, id: ids.assistant, user_message: userMessage,
    messages: [...previous.filter(m => ['user', 'assistant', 'system'].includes(m.role))
      .filter(m => !m.error).map(m => ({role: m.role, content: m.role === 'user' ? m.content : messageText(m)})),
      {role: 'user', content}],
    stream: true, session_id: ids.session,
    tool_ids: ['family_media'], params: {function_calling: 'native'},
    background_tasks: {title_generation: false, tags_generation: false, follow_up_generation: false},
  };
}

// PCM input has a real, server-verifiable duration bound, unlike a client-supplied duration field.
export function pcmWav(samples, sampleRate) {
  if (!samples.length || samples.length / sampleRate > 30 || sampleRate < 8000 || sampleRate > 48000) throw new Error('Record at most 30 seconds.');
  const result = new ArrayBuffer(44 + samples.length * 2), view = new DataView(result);
  const word = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  word(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); word(8, 'WAVE'); word(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true); word(36, 'data'); view.setUint32(40, samples.length * 2, true);
  samples.forEach((value, i) => view.setInt16(44 + i * 2, Math.round(Math.max(-1, Math.min(1, value)) * (value < 0 ? 32768 : 32767)), true));
  return result;
}
