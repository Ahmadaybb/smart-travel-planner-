import { useEffect, useState } from "react"
import toast from "react-hot-toast"
const API = "http://localhost:8000"

export default function Sidebar({token,userEmail,onLogout,isOpen,onClose}) {
  const [history,setHistory]=useState([])
  useEffect(()=>{
    if(!token)return
    fetch(`${API}/agent/history`,{headers:{Authorization:`Bearer ${token}`}})
      .then(r=>{if(r.status===401){onLogout();return null}return r.json()})
      .then(d=>{if(d)setHistory(d)}).catch(()=>{})
  },[token])
  const handleLogout=()=>{toast.success("Safe travels! ✈️");onLogout()}
  const letter=userEmail?userEmail[0].toUpperCase():"?"
  return (
    <>
      {isOpen&&<div className="mobile-overlay" onClick={onClose}/>}
      <aside className={`sidebar${isOpen?" open":""}`}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-row">
            <span className="sidebar-logo-icon">🌍</span>
            <div><h2>Smart Travel</h2><p>Night Explorer</p></div>
          </div>
        </div>
        <div className="sidebar-section-title">Past Journeys</div>
        <div className="sidebar-history">
          {history.length===0
            ?<p className="history-empty">No journeys yet — start planning!</p>
            :history.map(item=>(
              <div key={item.id} className="history-item">
                <span className="hi-icon">📍</span>
                <span className="hi-text">{item.query.slice(0,40)}{item.query.length>40?"…":""}</span>
              </div>
            ))}
        </div>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{letter}</div>
            <span className="sidebar-user-email">{userEmail}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>🚪 Sign Out</button>
        </div>
      </aside>
    </>
  )
}