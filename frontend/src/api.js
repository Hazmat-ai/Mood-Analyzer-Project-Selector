let csrf = '';
let sessionRequest;
const messages = {SESSION_REQUIRED:'Your browser session expired. Retry to reconnect.', CSRF_INVALID:'Your session needs to reconnect. Please retry.', RATE_LIMIT:'Too many requests. Wait a minute, then retry.', SESSION_RATE_LIMIT:'Please wait a minute before starting another session.', IDEMPOTENCY_CONFLICT:'This request changed. Start a new quiz.', PICK_NOT_FOUND:'That saved pick is unavailable.'};
async function raw(path, options = {}) {
  const timeout = AbortSignal.timeout(12000);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;
  let response;
  try { response=await fetch(path,{...options,credentials:'same-origin',signal}); }
  catch(error){ if(options.signal?.aborted) throw error; throw new Error('Could not reach the server. Check your connection and retry. Your previous selections are retained.'); }
  const data=await response.json().catch(()=>({}));
  if(!response.ok){const error=new Error(messages[data.error]??`The request could not be completed (${response.status}). Please retry.`);error.status=response.status;throw error;}
  return data;
}
export function initializeSession(){
  if(!sessionRequest)sessionRequest=raw('/api/session').then(data=>{csrf=data.csrf_token;}).finally(()=>{sessionRequest=undefined;});
  return sessionRequest;
}
export async function api(path,{method='GET',body,key,signal}={}){
  if(path!=='/api/specialties'&&path!=='/api/quiz')await initializeSession();
  return raw(path,{method,signal,headers:{...(body?{'Content-Type':'application/json'}:{}),...(method!=='GET'?{'X-CSRF-Token':csrf}:{}),...(key?{'Idempotency-Key':key}:{})},body:body?JSON.stringify(body):undefined});
}
export const fetchSpecialties=(signal)=>api('/api/specialties',{signal});
export const fetchQuiz=(signal)=>api('/api/quiz',{signal});
export const fetchHistory=(signal)=>api('/api/history',{signal});
export const markComplete=({pickId})=>api('/api/complete',{method:'POST',body:{pick_id:pickId}});
export const submitQuiz=({specialty,answerIndexes,difficulty,key,signal})=>api('/api/submit-quiz',{method:'POST',body:{specialty,answer_indexes:answerIndexes,difficulty},key,signal});
export function download(name, data, type='application/json'){
 const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
