import { useState } from "react"

function RagContent({output}) {
  let dest="Destination",score=0
  try{const p=typeof output==="string"?JSON.parse(output):output;if(p?.destination)dest=p.destination;if(p?.similarity_score!=null)score=Math.round(p.similarity_score*100);else if(p?.score!=null)score=Math.round(p.score*100)}catch{}
  return(<div><div className="rag-dest">📍 {dest}</div><div className="rag-score-row"><div className="rag-score-bar"><div className="rag-score-fill" style={{width:`${score}%`}}/></div><span className="rag-score-label">{score}% match</span></div></div>)
}

function ClassifierContent({output}) {
  let style="Unknown",conf=0
  try{const p=typeof output==="string"?JSON.parse(output):output;if(p?.travel_style)style=p.travel_style;if(p?.confidence!=null)conf=Math.round(p.confidence*100)}catch{}
  return(<div><div className="classifier-style">🧭 {style}</div><div className="classifier-bar"><div className="classifier-fill" style={{width:`${conf}%`}}/></div><div className="classifier-conf-label">Confidence: {conf}%</div></div>)
}

function WeatherContent({output}) {
  let temp="—",desc="",hum=null,icon="🌤️"
  const WI={clear:"☀️",sunny:"☀️",cloud:"⛅",rain:"🌧️",storm:"⛈️",snow:"❄️",fog:"🌫️"}
  try{const p=typeof output==="string"?JSON.parse(output):output;if(p){if(p.temperature!=null)temp=`${Math.round(p.temperature)}°C`;else if(p.temp!=null)temp=`${Math.round(p.temp)}°C`;if(p.description){desc=p.description;for(const[k,v]of Object.entries(WI)){if(desc.toLowerCase().includes(k)){icon=v;break}}}if(p.humidity!=null)hum=`${p.humidity}%`}}catch{}
  return(<div><div className="weather-main"><span className="weather-icon">{icon}</span><div><div className="weather-temp">{temp}</div>{desc&&<div className="weather-desc">{desc}</div>}</div></div>{hum&&<div className="weather-meta"><span className="weather-tag">💧 Humidity {hum}</span></div>}</div>)
}

function GenericContent({output}) {
  let d=""
  try{d=JSON.stringify(typeof output==="string"?JSON.parse(output):output,null,2)}catch{d=String(output)}
  return<pre className="tool-json">{d.slice(0,600)}</pre>
}

const META={rag_search:{icon:"🗺️",label:"Knowledge Base",badge:"badge-rag"},retrieve_destination_info:{icon:"🗺️",label:"Destination RAG",badge:"badge-rag"},classify_travel_style:{icon:"🧭",label:"Travel Style",badge:"badge-classifier"},get_weather:{icon:"🌤️",label:"Weather",badge:"badge-weather"}}
const getMeta=n=>{const k=Object.keys(META).find(k=>n.toLowerCase().includes(k.toLowerCase()));return k?META[k]:{icon:"🔧",label:n.replace(/_/g," "),badge:"badge-generic"}}

export default function ToolCard({tool,index}) {
  const [open,setOpen]=useState(false)
  const m=getMeta(tool.tool_name)
  const n=tool.tool_name.toLowerCase()
  const isRag=n.includes("rag")||n.includes("destination")
  const isClassifier=n.includes("classif")||n.includes("style")
  const isWeather=n.includes("weather")
  return(
    <div className="tool-card" style={{animationDelay:`${index*0.12}s`}}>
      <div className="tool-card-header" onClick={()=>setOpen(p=>!p)}>
        <span className="tool-card-icon">{m.icon}</span>
        <span className="tool-card-title">{m.label}</span>
        <span className={`tool-card-badge ${m.badge}`}>Tool</span>
        <span className={`tool-card-chevron${open?" open":""}`}>▼</span>
      </div>
      {open&&<div className="tool-card-body"><div className="tool-card-content">
        {isRag&&<RagContent output={tool.tool_output}/>}
        {isClassifier&&<ClassifierContent output={tool.tool_output}/>}
        {isWeather&&<WeatherContent output={tool.tool_output}/>}
        {!isRag&&!isClassifier&&!isWeather&&<GenericContent output={tool.tool_output}/>}
      </div></div>}
    </div>
  )
}