import { useEffect, useRef, useState } from 'react'
import { sendChat, clearSession } from '../api'
import { Send, Trash2, Bot, User, Loader } from 'lucide-react'

const SESSION_ID = `session_${Math.random().toString(36).slice(2, 9)}`

const SUGGESTIONS = [
  'Compare home loan rates',
  'HDFC vs ICICI personal loan',
  'Minimum CIBIL for car loan',
  'SBI home loan eligibility',
  'Which bank has the lowest rate?',
]

function Message({ msg }) {
  const isBot = msg.role === 'assistant'
  return (
    <div style={{
      display: 'flex',
      gap: 10,
      alignItems: 'flex-start',
      flexDirection: isBot ? 'row' : 'row-reverse',
    }}>
      <div style={{
        flexShrink: 0,
        width: 28,
        height: 28,
        borderRadius: '50%',
        background: isBot ? '#1A2F54' : '#F5A623',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: 2,
      }}>
        {isBot
          ? <Bot size={14} color="#A8B4CC" />
          : <User size={14} color="#0F1E3C" />
        }
      </div>
      <div style={{
        maxWidth: '80%',
        background: isBot ? 'rgba(255,255,255,0.05)' : 'rgba(245,166,35,0.12)',
        border: `1px solid ${isBot ? 'rgba(255,255,255,0.08)' : 'rgba(245,166,35,0.2)'}`,
        borderRadius: isBot ? '4px 12px 12px 12px' : '12px 4px 12px 12px',
        padding: '10px 14px',
        fontSize: 13,
        lineHeight: 1.6,
        color: isBot ? '#FAFAF8' : '#F5D89A',
        whiteSpace: 'pre-wrap',
      }}>
        {msg.content}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <div style={{
        flexShrink: 0, width: 28, height: 28, borderRadius: '50%',
        background: '#1A2F54', display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Bot size={14} color="#A8B4CC" />
      </div>
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '4px 12px 12px 12px',
        padding: '12px 16px',
        display: 'flex', gap: 4, alignItems: 'center',
      }}>
        {[0,1,2].map(i => (
          <div key={i} style={{
            width: 6, height: 6, borderRadius: '50%',
            background: '#6B7A99',
            animation: 'pulse 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: 'Namaste! 🙏 I\'m LoanSarthi, your personal loan advisor for Indian banks.\n\nI can help you compare rates, check eligibility criteria, and guide you through the application process for home, personal, and car loans across 12 major banks.\n\nWhat would you like to know?',
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const reply = await sendChat(SESSION_ID, msg)
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } catch (err) {
      const isTimeout = err.code === 'ECONNABORTED' || err.message?.includes('timeout')
      const isNetwork = err.message?.includes('Network Error') || err.code === 'ERR_NETWORK'
      let errMsg
      if (isTimeout) {
        errMsg = '⏱️ The request timed out — the LLM is taking longer than usual. Please try again.'
      } else if (isNetwork) {
        errMsg = '🔌 Cannot reach the backend. Make sure:\n1. LoanSarthi server is running: python main.py serve\n2. It\'s on port 8000\n3. No firewall is blocking it'
      } else {
        errMsg = `❌ Error: ${err.response?.data?.detail || err.message || 'Unknown error'}`
      }
      setMessages(prev => [...prev, { role: 'assistant', content: errMsg }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const handleClear = () => {
    clearSession(SESSION_ID).catch(() => {})
    setMessages([{
      role: 'assistant',
      content: 'Conversation cleared. How can I help you?',
    }])
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>

      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h2 style={{
            fontFamily: "'DM Serif Display', serif",
            fontSize: 20,
            fontWeight: 400,
            color: '#FAFAF8',
          }}>
            Ask LoanSarthi
          </h2>
          <div style={{ fontSize: 11, color: '#6B7A99', marginTop: 1 }}>
            Powered by Groq · llama-3.3-70b
          </div>
        </div>
        <button
          onClick={handleClear}
          title="Clear conversation"
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 8,
            padding: '6px 8px',
            cursor: 'pointer',
            color: '#6B7A99',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            fontFamily: 'inherit',
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#FAFAF8'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)' }}
          onMouseLeave={e => { e.currentTarget.style.color = '#6B7A99'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)' }}
        >
          <Trash2 size={13} /> Clear
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}>
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Quick suggestions */}
      {messages.length === 1 && (
        <div style={{
          padding: '0 20px 12px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
        }}>
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => send(s)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 20,
                padding: '5px 12px',
                fontSize: 11,
                color: '#A8B4CC',
                cursor: 'pointer',
                fontFamily: 'inherit',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(245,166,35,0.1)'; e.currentTarget.style.borderColor = 'rgba(245,166,35,0.3)'; e.currentTarget.style.color = '#F5A623' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#A8B4CC' }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '12px 20px 16px',
        borderTop: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{
          display: 'flex',
          gap: 8,
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12,
          padding: '8px 8px 8px 14px',
          transition: 'border-color 0.15s',
        }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'rgba(245,166,35,0.4)'}
        onBlurCapture={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about eligibility, rates, or how to apply…"
            rows={1}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#FAFAF8',
              fontFamily: 'inherit',
              fontSize: 13,
              resize: 'none',
              lineHeight: 1.5,
              maxHeight: 100,
              overflowY: 'auto',
              paddingTop: 2,
            }}
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            style={{
              flexShrink: 0,
              width: 34,
              height: 34,
              borderRadius: 8,
              border: 'none',
              background: input.trim() && !loading ? '#F5A623' : 'rgba(255,255,255,0.08)',
              color: input.trim() && !loading ? '#0F1E3C' : '#6B7A99',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s',
            }}
          >
            {loading ? <Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={15} />}
          </button>
        </div>
        <div style={{ fontSize: 10, color: '#6B7A99', marginTop: 6, textAlign: 'center' }}>
          Enter to send · Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}
