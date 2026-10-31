const ICONS={software:'⌘',security:'◇',data:'▥',azure:'☁',gaming:'✦'};
export default function SpecialtyPicker({specialties,onSelect}){
 return <section className="pixel-panel"><div className="section-intro"><span className="eyebrow">01 / PICK A DIRECTION</span><h2 tabIndex={-1}>Choose your specialty</h2><p className="muted">Where would you like to put your skills to work?</p></div><div className="specialty-grid">{specialties.map(item=><button className="specialty-card" key={item.id} onClick={()=>onSelect(item.id)}><span className="card-icon" aria-hidden="true">{ICONS[item.id]}</span><span>{item.label}</span><span aria-hidden="true">↗</span></button>)}</div></section>;
}
