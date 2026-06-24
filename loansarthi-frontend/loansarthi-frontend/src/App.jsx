import RateTicker from './components/RateTicker'
import RatesPanel from './components/RatesPanel'
import ChatPanel from './components/ChatPanel'

export default function App() {
  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Top bar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        height: 52,
        background: '#0F1E3C',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        flexShrink: 0,
        zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 30,
            height: 30,
            borderRadius: 8,
            background: '#F5A623',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 16,
          }}>
            ₹
          </div>
          <div>
            <span style={{
              fontFamily: "'DM Serif Display', serif",
              fontSize: 18,
              color: '#FAFAF8',
              letterSpacing: '-0.01em',
            }}>
              LoanSarthi
            </span>
            <span style={{
              fontSize: 10,
              color: '#6B7A99',
              marginLeft: 8,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}>
              Indian Loan Advisor
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {['HDFC', 'SBI', 'ICICI', 'Axis', '+9 banks'].map(b => (
            <span key={b} style={{
              fontSize: 10,
              color: '#6B7A99',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 4,
              padding: '2px 6px',
            }}>
              {b}
            </span>
          ))}
        </div>
      </header>

      {/* Ticker */}
      <RateTicker />

      {/* Main split */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '380px 1fr',
        overflow: 'hidden',
      }}>
        {/* Left: Rates */}
        <div style={{
          borderRight: '1px solid rgba(255,255,255,0.08)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <RatesPanel />
        </div>

        {/* Right: Chat */}
        <div style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <ChatPanel />
        </div>
      </div>
    </div>
  )
}
