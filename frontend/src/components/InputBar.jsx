import { useState, useEffect, useRef } from "react"

const PH=["I have 2 weeks in July and $1500. I like hiking…","Somewhere warm, not too touristy, family friendly…","Beach destination under $100/day for 10 days…","Cultural trip to Asia, budget traveler, solo…","Adventure trip, I love mountains and trekking…"]
const CHIPS=[{label:"🏔️ Adventure",q:"I want an adventure trip with mountains, trekking, and outdoor activities. Budget around $1200 for 10 days."},{label:"🏖️ Beach & Relax",q:"Looking for a beautiful beach destination, relaxing vibe, not too touristy. About 2 weeks, $150/day budget."},{label:"🏛️ Culture",q:"I want a cultural immersion trip — history, art, local food. 10 days in Europe or Asia, mid-range budget."},{label:"💰 Budget",q:"Budget traveler looking for the best destination under $50/day for 2 weeks. Any continent."},{label:"👨‍👩‍👧 Family",q:"Family trip with two kids (ages 7 and 10), looking for safe, fun, family-friendly destination. 10 days, $3000 budget."}]

export default function InputBar({onSend,disabled}) {
  const [text,setText]=useState("")
  const [ph,setPh]=useState(0)
  const ref=useRef(null)

  useEffect(()=>{const id=setInterval(()=>setPh(p=>(p+1)%PH.length),3000);return()=>clearInterval(id)},[])

  const submit=()=>{const q=text.trim();if(!q||disabled)return;setText("");onSend(q);if(ref.current)ref.current.style.height="auto"}
  const onKey=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();submit()}}
  const onInput=e=>{setText(e.target.value);const t=e.target;t.style.height="auto";t.style.height=`${Math.min(t.scrollHeight,140)}px`}

  return(
    <div className="input-area">
      <div className="quick-chips">
        {CHIPS.map(c=><button key={c.label} className="quick-chip" onClick={()=>{setText(c.q);ref.current?.focus()}}>{c.label}</button>)}
      </div>
      <div className="input-bar">
        <textarea ref={ref} value={text} onChange={onInput} onKeyDown={onKey} placeholder={PH[ph]} rows={1} disabled={disabled}/>
        <button className="send-btn" onClick={submit} disabled={disabled||!text.trim()}>✈️</button>
      </div>
      <p className="input-tip">💡 Tip: mention your <span>budget</span>, <span>duration</span>, <span>month</span>, and <span>travel style</span> for the best plan</p>
    </div>
  )
}