import {useCallback,useEffect,useRef,useState} from 'react';
import SpecialtyPicker from './components/SpecialtyPicker';
import Quiz from './components/Quiz';
import DifficultyPicker from './components/DifficultyPicker';
import Wheel from './components/Wheel';
import ProjectResult from './components/ProjectResult';
import History from './components/History';
import {fetchSpecialties,fetchQuiz,initializeSession,submitQuiz} from './api';

export default function App(){
 const [step,setStep]=useState('specialty');
 const [specialties,setSpecialties]=useState([]),[questions,setQuestions]=useState([]);
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const [specialty,setSpecialty]=useState(null),[answers,setAnswers]=useState([]),[result,setResult]=useState(null);
 const attempt=useRef(null),pending=useRef(false),controller=useRef(null),generation=useRef(0);
 useEffect(()=>{
  const abort=new AbortController();setLoading(true);setError('');
  Promise.all([fetchSpecialties(abort.signal),fetchQuiz(abort.signal),initializeSession()]).then(([s,q])=>{if(!abort.signal.aborted){setSpecialties(s);setQuestions(q);}}).catch(e=>{if(!abort.signal.aborted)setError(e.message);}).finally(()=>{if(!abort.signal.aborted)setLoading(false);});
  return()=>abort.abort();
 },[retry]);
 useEffect(()=>{document.querySelector('main h2')?.focus();},[step]);
 useEffect(()=>()=>controller.current?.abort(),[]);
 const restart=()=>{generation.current++;controller.current?.abort();pending.current=false;attempt.current=null;setResult(null);setAnswers([]);setSpecialty(null);setError('');setStep('specialty');};
 async function selectDifficulty(difficulty){
  if(pending.current)return;
  pending.current=true;setError('');setResult(null);setStep('waiting');
  const payload=JSON.stringify({specialty,answers,difficulty});
  if(attempt.current?.payload!==payload)attempt.current={payload,key:crypto.randomUUID()};
  const current=++generation.current;controller.current=new AbortController();
  try{const data=await submitQuiz({specialty,answerIndexes:answers,difficulty,key:attempt.current.key,signal:controller.current.signal});if(current===generation.current){setResult(data);setStep('spinning');}}
  catch(e){if(current===generation.current){setError(e.message);setStep('difficulty');}}
  finally{if(current===generation.current)pending.current=false;}
 }
 const finished=useCallback(()=>setStep('result'),[]);
 const cancel=()=>{generation.current++;controller.current?.abort();pending.current=false;setStep('difficulty');setError('Stopped waiting. A completed server request may still appear in history; retrying the same selection reuses its request key.');};
 return <div className="app-container">
  <header className="masthead"><h1><a className="brand" href="#main"><span aria-hidden="true">✦</span> <span>MOOD PROJECT PICKER</span></a></h1><p className="app-subtitle">Find your next build, by vibe.</p><div className="top-nav"><button className="top-nav-link" disabled={loading||!['specialty','result','history'].includes(step)} onClick={()=>step==='history'?restart():setStep('history')}>{step==='history'?'Choose a project':'View history'}</button><span className="privacy-pill">Private browser history</span></div></header>
  <main id="main">
   {error&&<div className="error-box" role="alert">{error}</div>}
   {loading?<p role="status" className="loading-text">Loading your project studio…</p>:!specialties.length?<section className="pixel-panel"><h2 tabIndex={-1}>Couldn’t load the project studio</h2><button className="pixel-button" onClick={()=>setRetry(v=>v+1)}>Retry loading</button></section>:<>
    {step==='specialty'&&<><section className="welcome"><span className="eyebrow">SMALL WIN OR NEXT BIG BUILD</span><h2 tabIndex={-1}>A project for the energy<br/>you have today.</h2><p>Seven quick questions. Five specialties. One idea to get you building.</p><p className="muted">Your choices guide a weighted project match. You can always choose a different direction.</p></section><SpecialtyPicker specialties={specialties} onSelect={id=>{attempt.current=null;setSpecialty(id);setStep('quiz');}}/></>}
    {step==='quiz'&&<Quiz questions={questions} answers={answers} onChange={setAnswers} onBack={()=>setStep('specialty')} onComplete={()=>setStep('difficulty')}/>}
    {step==='difficulty'&&<DifficultyPicker onSelect={selectDifficulty} onBack={()=>setStep('quiz')}/>}
    {step==='waiting'&&<section className="pixel-panel"><h2 tabIndex={-1}>Finding your candidates</h2><p role="status">Matching your preferences with the project catalogue…</p><button className="pixel-button secondary" onClick={cancel}>Stop waiting</button></section>}
    {step==='spinning'&&result&&<Wheel candidates={result.candidates} result={result.result} onFinished={finished}/>}
    {step==='result'&&result&&<ProjectResult key={result.pick_id} pickId={result.pick_id} initiallyCompleted={result.completed} moodDescription={result.mood_description} result={result.result} reason={result.reason} onRestart={restart}/>}
    {step==='history'&&<History onBack={()=>setStep(result?'result':'specialty')} onOpen={saved=>{setResult(saved);setStep('result');}} onDeleted={restart}/>}
   </>}
  </main>
  <footer><details><summary>How matching and privacy work</summary><p>The quiz maps your self-reported preferences to energy, creativity and challenge values. Five nearby projects at your chosen difficulty enter a weighted draw. This is an explainable preference tool; there is no trained mood-detection model.</p><p>We keep up to 200 project picks and completion flags under an anonymous 30-day browser session. Raw quiz answers and mood vectors aren’t saved in your history. Export or delete your data in History. No account, camera, or microphone is required.</p></details><p className="muted">Choose something that feels right. Build at your own pace.</p></footer>
 </div>;
}
