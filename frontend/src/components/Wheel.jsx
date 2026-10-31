import {useEffect,useRef,useState} from 'react';
export default function Wheel({candidates,result,onFinished}){
 const [display,setDisplay]=useState(candidates[0]?.title??result.title);const callback=useRef(onFinished);callback.current=onFinished;
 useEffect(()=>{let timer,cancelled=false,tick=0;const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const next=()=>{if(cancelled)return;if(reduced||tick>=16){setDisplay(result.title);timer=setTimeout(()=>callback.current(),reduced?0:500);return;}setDisplay(candidates[tick%candidates.length]?.title??result.title);tick++;timer=setTimeout(next,65+tick*9);};timer=setTimeout(next,0);return()=>{cancelled=true;clearTimeout(timer);};
 },[candidates,result.id,result.title]);
 return <section className="pixel-panel wheel-stage"><span className="eyebrow">YOUR NEXT BUILD IS ON ITS WAY</span><h2 tabIndex={-1}>A little inspiration roulette</h2><p role="status">Revealing the project chosen by your preference match…</p><div className="wheel-scroll-window" aria-hidden="true"><div className="wheel-title">{display}</div></div><button className="pixel-button secondary" onClick={onFinished}>Skip animation</button></section>;
}
