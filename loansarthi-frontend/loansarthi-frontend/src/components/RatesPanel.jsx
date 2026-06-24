import { useEffect, useState } from 'react'
import { fetchRates } from '../api'

const LOAN_TYPES = ['home', 'personal', 'car']
const LOAN_LABELS = { home: 'Home Loans', personal: 'Personal Loans', car: 'Car Loans' }

function RateCard({ r }) {
  const [min, max] = r.rate.split('–')
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 10,
      padding: '14px 16px',
      display: 'grid',
      gridTemplateColumns: '1fr auto',
      gap: '4px 12px',
      alignItems: 'start',
      transition: 'border-color 0.15s',
      cursor: 'default',
    }}
    onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(245,166,35,0.3)'}
    onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: '#FAFAF8' }}>{r.bank}</div>
      <div style={{
        fontSize: 15,
        fontWeight: 700,
        color: '#F5A623',
        textAlign: 'right',
        fontVariantNumeric: 'tabular-nums',
      }}>
        {r.rate}
      </div>
      <div style={{ fontSize: 11, color: '#6B7A99' }}>
        {r.processing_fee || 'Fee N/A'} · up to {r.max_tenure}
      </div>
      {r.notes && (
        <div style={{ gridColumn: '1/-1', fontSize: 11, color: '#6B7A99', marginTop: 4 }}>
          {r.notes.slice(0, 72)}{r.notes.length > 72 ? '…' : ''}
        </div>
      )}
    </div>
  )
}

export default function RatesPanel() {
  const [activeTab, setActiveTab] = useState('home')
  const [ratesByType, setRatesByType] = useState({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (ratesByType[activeTab]) return
    setLoading(true)
    fetchRates(activeTab)
      .then(data => setRatesByType(prev => ({ ...prev, [activeTab]: data })))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [activeTab])

  const rates = ratesByType[activeTab] || []

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{ padding: '20px 20px 0' }}>
        <h2 style={{
          fontFamily: "'DM Serif Display', serif",
          fontSize: 22,
          fontWeight: 400,
          color: '#FAFAF8',
          marginBottom: 4,
        }}>
          Rate Comparison
        </h2>
        <p style={{ fontSize: 11, color: '#6B7A99', marginBottom: 16 }}>
          Sorted by lowest starting rate · indicative only
        </p>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4 }}>
          {LOAN_TYPES.map(t => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 500,
                fontFamily: 'inherit',
                background: activeTab === t ? '#F5A623' : 'rgba(255,255,255,0.06)',
                color: activeTab === t ? '#0F1E3C' : '#A8B4CC',
                transition: 'all 0.15s',
              }}
            >
              {LOAN_LABELS[t].replace(' Loans', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Cards */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '14px 20px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        {loading && (
          <div style={{ color: '#6B7A99', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            Loading rates…
          </div>
        )}
        {!loading && rates.map((r, i) => <RateCard key={i} r={r} />)}
      </div>

      <div style={{
        padding: '10px 20px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        fontSize: 10,
        color: '#6B7A99',
      }}>
        Rates as of {rates[0]?.last_updated || '—'} · Confirm with bank before applying
      </div>
    </div>
  )
}
