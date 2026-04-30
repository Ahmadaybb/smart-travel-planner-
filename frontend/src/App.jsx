import { useState } from "react"
import { Toaster } from "react-hot-toast"
import Auth from "./components/Auth"
import Chat from "./components/Chat"

export default function App() {
  const [token, setToken] = useState(null)
  const [userEmail, setUserEmail] = useState("")
  const handleLogin = (jwt, email) => { setToken(jwt); setUserEmail(email) }
  const handleLogout = () => { setToken(null); setUserEmail("") }
  return (
    <>
      <Toaster position="top-right" toastOptions={{ style: { background: "rgba(15,23,42,0.95)", color: "#f8fafc", border: "1px solid rgba(245,158,11,0.3)", backdropFilter: "blur(12px)", fontFamily: "Inter,sans-serif" }, success: { iconTheme: { primary: "#f59e0b", secondary: "#0f172a" } }, error: { iconTheme: { primary: "#ef4444", secondary: "#0f172a" } } }} />
      {token ? <Chat token={token} userEmail={userEmail} onLogout={handleLogout} /> : <Auth onLogin={handleLogin} />}
    </>
  )
}