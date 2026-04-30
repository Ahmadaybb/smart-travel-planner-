import { useState, useEffect, useRef } from "react"
import toast from "react-hot-toast"

const API = "http://localhost:8000"
const FLOAT_ICONS = ["✈️","🌍","🗺️","🧭","🏔️","🏖️","🌊","⛵","🚂","🌅"]

function StarCanvas() {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current; if (!c) return
    const ctx = c.getContext("2d"); let aid
    const stars = Array.from({length:120},()=>({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*1.5+0.3,a:Math.random(),s:Math.random()*0.008+0.002}))
    const resize = () => { c.width = window.innerWidth; c.height = window.innerHeight }
    resize(); window.addEventListener("resize", resize)
    const draw = () => {
      ctx.clearRect(0,0,c.width,c.height)
      stars.forEach(s => {
        s.a += s.s; if(s.a>1||s.a<0) s.s*=-1
        ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,Math.PI*2)
        ctx.fillStyle=`rgba(248,250,252,${Math.abs(Math.sin(s.a))})`; ctx.fill()
      })
      for(let i=0;i<stars.length-1;i+=12){
        const a=stars[i],b=stars[i+1],d=Math.hypot(b.x-a.x,b.y-a.y)
        if(d<120){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=`rgba(245,158,11,${0.06*(1-d/120)})`;ctx.lineWidth=0.5;ctx.stroke()}
      }
      aid=requestAnimationFrame(draw)
    }
    draw()
    return()=>{cancelAnimationFrame(aid);window.removeEventListener("resize",resize)}
  },[])
  return <canvas ref={ref} className="star-canvas" />
}

function FloatingIcons() {
  return (
    <div className="floating-icons">
      {FLOAT_ICONS.map((ic,i)=>(
        <span key={i} className="float-icon" style={{left:`${5+(i*9.5)%90}%`,bottom:"-40px",fontSize:`${22+(i%3)*8}px`,animationDuration:`${14+(i%5)*3}s`,animationDelay:`${i*1.3}s`}}>{ic}</span>
      ))}
    </div>
  )
}

function Field({label,type,value,onChange,autoComplete}) {
  return (
    <div className="field-wrap">
      <input type={type} value={value} onChange={onChange} placeholder=" " autoComplete={autoComplete} />
      <label>{label}</label>
    </div>
  )
}

export default function Auth({onLogin}) {
  const [mode,setMode]=useState("login")
  const [email,setEmail]=useState("")
  const [password,setPassword]=useState("")
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  const submit = async e => {
    e.preventDefault(); setError("")
    if(!email||!password){setError("Please fill in all fields.");return}
    setLoading(true)
    try {
      const res = await fetch(`${API}${mode==="login"?"/auth/login":"/auth/register"}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})})
      const data = await res.json()
      if(!res.ok) throw new Error(data.detail||"Something went wrong")
      if(mode==="register"){toast.success("Account created! Please log in.");setMode("login");setPassword("")}
      else{toast.success("Welcome back, explorer! 🌍");onLogin(data.access_token,email)}
    } catch(err){setError(err.message)}
    finally{setLoading(false)}
  }

  return (
    <div className="auth-page">
      <StarCanvas /><FloatingIcons />
      <div className="auth-card">
        <div className="auth-logo">
          <span className="auth-logo-icon">🌍</span>
          <h1>Smart Travel Planner</h1>
          <p>Your AI-powered journey companion</p>
        </div>
        <div className="auth-tabs">
          <button className={`auth-tab${mode==="login"?" active":""}`} onClick={()=>{setMode("login");setError("")}}>Sign In</button>
          <button className={`auth-tab${mode==="register"?" active":""}`} onClick={()=>{setMode("register");setError("")}}>Create Account</button>
        </div>
        <form onSubmit={submit}>
          {error&&<div className="auth-error">{error}</div>}
          <Field label="Email address" type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" />
          <Field label="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==="login"?"current-password":"new-password"} />
          <button type="submit" className="btn-gold auth-btn" disabled={loading}>
            {loading?"✈️ Taking off...":mode==="login"?"🚀 Start Exploring":"🌍 Create Account"}
          </button>
        </form>
      </div>
    </div>
  )
}