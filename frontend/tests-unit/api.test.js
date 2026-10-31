import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api,initializeSession,submitQuiz} from '../src/api.js';

test('parallel protected requests share session initialization and carry its CSRF token',async()=>{
 const original=globalThis.fetch;let release;let initializations=0;const sent=[];
 const gate=new Promise(resolve=>{release=resolve;});
 globalThis.fetch=async(path,options)=>{
  if(path==='/api/session'){initializations++;await gate;return new Response(JSON.stringify({csrf_token:'token-from-session'}));}
  sent.push({path,options});return new Response(JSON.stringify({pick_id:'saved'}));
 };
 try{
  const a=submitQuiz({specialty:'software',answerIndexes:[0,0,0,0,0,0,0],difficulty:'easy',key:'request-key-123456'});
  const b=api('/api/complete',{method:'POST',body:{pick_id:'owned'}});
  release();await Promise.all([a,b]);assert.equal(initializations,1);assert.equal(sent.length,2);
  assert.ok(sent.every(item=>item.options.headers['X-CSRF-Token']==='token-from-session'));
  assert.equal(sent[0].options.headers['Idempotency-Key'],'request-key-123456');
 }finally{globalThis.fetch=original;}
});

test('server error detail is not echoed and failed initialization can be retried',async()=>{
 const original=globalThis.fetch;let attempts=0;
 globalThis.fetch=async()=>{attempts++;return attempts===1?new Response(JSON.stringify({error:'INTERNAL_ERROR',detail:'private database password'}),{status:500}):new Response(JSON.stringify({csrf_token:'new-token'}));};
 try{await assert.rejects(initializeSession(),error=>error.status===500&&!error.message.includes('password'));await initializeSession();assert.equal(attempts,2);}finally{globalThis.fetch=original;}
});
