import {test} from 'node:test';
import assert from 'node:assert/strict';
import {completionBody, messageText, orderedMessages, fileUrl, pcmWav} from '../web/api.mjs';

test('native background turn keeps stable IDs, selected history and tool execution on server',()=>{
  const chat={history:{currentId:'a1',messages:{u1:{id:'u1',role:'user',content:'Moi'},a1:{id:'a1',parentId:'u1',role:'assistant',content:'Hei'},other:{id:'other',role:'user',content:'excluded'}}}};
  const ids={user:'new-user',assistant:'new-answer',session:'preview-session'};
  const body=completionBody('saved-chat',chat,'Mitä kuuluu?','auto',ids);
  assert.equal(body.id,ids.assistant);assert.equal(body.user_message.id,ids.user);
  assert.equal(body.user_message.parentId,'a1');assert.equal(body.session_id,ids.session);
  assert.deepEqual(body.tool_ids,['family_media']);assert.equal(body.params.function_calling,'native');
  assert.deepEqual(body.messages.map(m=>m.content),['Moi','Hei','Mitä kuuluu?']);
});
test('vision attachment remains in both saved message and provider input',()=>{
  const body=completionBody('chat',{},'Mitä kuvassa näkyy?','auto',{user:'u',assistant:'a',session:'s'},['data:image/png;base64,example']);
  assert.equal(body.messages[0].content[1].type,'image_url');
  assert.deepEqual(body.user_message.content,body.messages[0].content);
});
test('only owned application file paths are rendered; remote or executable URLs are rejected',()=>{
  const origin='https://family.test';
  assert.equal(fileUrl({id:'abc',url:'/api/v1/files/abc/content'},origin),'/api/v1/files/abc/content');
  for(const url of ['javascript:alert(1)','https://evil.test/api/v1/files/abc/content','/api/v1/files/other/content','/api/v1/files/abc/content?token=anything'])assert.equal(fileUrl({id:'abc',url},origin),null);
});
test('tool HTML and reasoning are never rendered as assistant output',()=>{
  assert.equal(messageText({output:[{type:'reasoning',content:[{type:'text',text:'private'}]},{type:'function_call_output',output:'<script>bad</script>'},{type:'message',role:'assistant',content:[{type:'output_text',text:'Valmis.'}]}]}),'Valmis.');
});
test('history cycle cannot hang the client',()=>{
  assert.equal(orderedMessages({history:{currentId:'a',messages:{a:{id:'a',parentId:'a'}}}}).length,1);
});
test('microphone produces bounded PCM WAV that the server can validate',()=>{
  const wav=pcmWav(new Float32Array(8000),8000), view=new DataView(wav);
  assert.equal(wav.byteLength,16044);assert.equal(view.getUint32(24,true),8000);
  assert.equal(new TextDecoder().decode(wav.slice(8,12)),'WAVE');
  assert.throws(()=>pcmWav(new Float32Array(8000*31),8000));
});
