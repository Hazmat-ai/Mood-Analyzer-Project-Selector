import {Component} from 'react';
export default class ErrorBoundary extends Component{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true};}
 render(){return this.state.failed?<main className="app-container"><section className="pixel-panel"><h1>The project studio couldn’t display this screen</h1><p>Your saved server history is retained. Reload to reconnect.</p><button className="pixel-button" onClick={()=>window.location.reload()}>Reload project studio</button></section></main>:this.props.children;}
}
