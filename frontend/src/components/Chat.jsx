import { useState, useRef, useEffect, useCallback } from "react"
import toast from "react-hot-toast"
import Sidebar from "./Sidebar"
import MessageBubble from "./MessageBubble"
import InputBar from "./InputBar"

const API = "http://localhost:8000"

const WELCOME_CHIPS=[
  {label:"🏔️ Adventure in Patagonia",q:"I want to trek Patagonia for 2 weeks in March. Budget $2000, solo traveler, love outdoor adventures."},
  {label:"🏖️ Beach in Southeast Asia",q:"Beach destination in Southeast Asia, 10 days in January, $80/day budget."},
  {label:"🏛️ European cultural tour",q:"Cultural trip through Southern Europe, museums and history. 14 days, $150/day, couple trip."},
  {label:"🌿 Eco-travel on a budget",q:"Eco-friendly destination, budget under $60/day, 12 days in autumn. I love nature and sustainability."},
]

function StarCanvas() {
  const ref=useRef(null)
  useEffect(()=>{
    const c=ref.current;if(!c)return
    const ctx=c.getContext("2d");let aid
    const stars=Array.from({length:80},()=>({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*1.2+0.2,a:Math.random(),s:Math.random()*0.006+0.002}))
    const resize=()=>{c.width=window.innerWidth;c.height=window.innerHeight}
    resize();window.addEventListener("resize",resize)
    const draw=()=>{
      ctx.clearRect(0,0,c.width,c.height)
      stars.forEach(s=>{s.a+=s.s;if(s.a>1||s.a<0)s.s*=-1;ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fillStyle=`rgba(248,250,252,${Math.abs(Math.sin(s.a))*0.6})`;ctx.fill()})
      aid=requestAnimationFrame(draw)
    }
    draw()
    return()=>{cancelAnimationFrame(aid);window.removeEventListener("resize",resize)}
  },[])
  return <canvas ref={ref} className="star-canvas"/>
}

function WelcomeScreen({onChip}) {
  return(
    <div className="chat-welcome">
      <div className="chat-welcome-icon">🌍</div>
      <h2>Where do you want to go?</h2>
      <p>Tell me your dream destination, budget, and travel style. I will craft the perfect journey for you.</p>
      <div className="welcome-chips">
        {WELCOME_CHIPS.map(c=><button key={c.label} className="welcome-chip" onClick={()=>onChip(c.q)}>{c.label}</button>)}
      </div>
    </div>
  )
}

export default function Chat({token,userEmail,onLogout}) {
  const [messages,setMessages]=useState([])
  const [streaming,setStreaming]=useState(false)
  const [sidebarOpen,setSidebarOpen]=useState(false)
  const endRef=useRef(null)

  useEffect(()=>{endRef.current?.scrollIntoView({behavior:"smooth"})},[messages])

  const handleSelectChat=useCallback((item)=>{
    const ts=new Date(item.created_at).getTime()||Date.now()
    setMessages([
      {id:ts,role:"user",text:item.query,ts},
      {id:ts+1,role:"agent",text:item.answer,tools:[],loading:false,streaming:false,ts}
    ])
  },[])

  const handleSend=useCallback(async(query)=>{
    if(streaming)return
    const uid=Date.now(), aid=uid+1
    setMessages(p=>[...p,{id:uid,role:"user",text:query,ts:uid},{id:aid,role:"agent",text:"",tools:[],loading:true,streaming:false,ts:uid}])
    setStreaming(true)
    try {
      const res=await fetch(`${API}/agent/run/stream`,{method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},body:JSON.stringify({query})})
      if(res.status===401){toast.error("Session expired.");onLogout();return}
      if(!res.ok)throw new Error(`Server error: ${res.status}`)
      const reader=res.body.getReader(), dec=new TextDecoder()
      let buf="", toolsDone=false
      while(true){
        const{done,value}=await reader.read(); if(done)break
        buf+=dec.decode(value,{stream:true})
        const lines=buf.split("\n"); buf=lines.pop()
        for(const line of lines){
          if(!line.startsWith("data: "))continue
          let ev; try{ev=JSON.parse(line.slice(6))}catch{continue}
          if(ev.type==="tool_call"){
            setMessages(p=>p.map(m=>m.id===aid?{...m,loading:true,tools:[...m.tools,ev.data]}:m))
          } else if(ev.type==="token"){
            if(!toolsDone){toolsDone=true;setMessages(p=>p.map(m=>m.id===aid?{...m,loading:false,streaming:true}:m))}
            setMessages(p=>p.map(m=>m.id===aid?{...m,text:m.text+ev.data}:m))
          } else if(ev.type==="done"){
            setMessages(p=>p.map(m=>m.id===aid?{...m,loading:false,streaming:false}:m))
          }
        }
      }
    } catch(err){
      setMessages(p=>p.map(m=>m.id===aid?{...m,loading:false,streaming:false,text:"Sorry, something went wrong. Please try again."}:m))
      toast.error(err.message||"Connection error")
    } finally{setStreaming(false)}
  },[token,streaming,onLogout])

  return(
    <div className="chat-layout">
      <StarCanvas/>
      <button className="mobile-menu-btn" onClick={()=>setSidebarOpen(true)}>☰</button>
      <Sidebar token={token} userEmail={userEmail} onLogout={onLogout} isOpen={sidebarOpen} onClose={()=>setSidebarOpen(false)} onSelectChat={handleSelectChat}/>
      <div className="chat-main">
        <div className="chat-messages">
          {messages.length===0
            ?<WelcomeScreen onChip={handleSend}/>
            :messages.map(m=><MessageBubble key={m.id} msg={m}/>)
          }
          <div ref={endRef}/>
        </div>
        <InputBar onSend={handleSend} disabled={streaming}/>
      </div>
    </div>
  )
}