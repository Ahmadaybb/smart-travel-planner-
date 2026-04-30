import { useEffect, useRef } from "react"
import ToolCard from "./ToolCard"

const fmtTime = ts => new Date(ts).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})

function LoadingPlane() {
  return(
    <div className="loading-plane-wrap">
      <div className="plane-track"><span className="flying-plane">✈️</span></div>
      <span className="loading-text">Planning your journey…</span>
    </div>
  )
}

export default function MessageBubble({msg}) {
  const ref=useRef(null)
  useEffect(()=>{ref.current?.scrollIntoView({behavior:"smooth",block:"end"})},[msg.text,msg.loading])

  if(msg.role==="user") return(
    <div className="message-row user" ref={ref}>
      <div className="message-bubble user">{msg.text}</div>
      <div className="message-time">{fmtTime(msg.ts)}</div>
    </div>
  )

  return(
    <div className="message-row agent" ref={ref}>
      {msg.tools?.length>0&&(
        <div className="tool-cards-group" style={{marginBottom:8}}>
          {msg.tools.map((t,i)=><ToolCard key={i} tool={t} index={i}/>)}
        </div>
      )}
      {msg.loading
        ?<LoadingPlane/>
        :<div className="message-bubble agent">
          {msg.text.split("\n").map((line,i,arr)=><span key={i}>{line}{i<arr.length-1&&<br/>}</span>)}
          {msg.streaming&&<span className="cursor"/>}
        </div>
      }
      {!msg.loading&&!msg.streaming&&<div className="message-time">{fmtTime(msg.ts)}</div>}
    </div>
  )
}