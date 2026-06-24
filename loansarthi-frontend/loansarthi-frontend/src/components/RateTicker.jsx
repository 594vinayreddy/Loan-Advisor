import { useEffect, useRef, useState } from 'react'
import { fetchAllRates } from '../api'

export default function RateTicker() {
  const [rates, setRates] = useState([])
  const [offset, setOffset] = useState(0)
  const trackRef = useRef(null)
  const rafRef = useRef(null)

  useEffect(() => {
    fetchAllRates().then(data => {
      const seen = new Set()
      const items = []
      for (const r of data) {
        const key = `${r.bank}-${r.loan_type}`
        if (!seen.has(key)) { seen.add(key); items.push(r) }
      }
      setRates(items)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!trackRef.current || rates.length === 0) return
    let x = 0
    const speed = 0.4
    const step = () => {
      x -= speed
      const w = trackRef.current ? trackRef.current.scrollWidth / 2 : 0
      if (Math.abs(x) >= w) x = 0
      setOffset(x)
      rafRef.current = requestAnimationFrame(step)
    }
    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [rates])

  if (rates.length === 0) return null

  const loanLabel = { home: 'Home', personal: 'Personal', car: 'Car' }
  const items = [...rates, ...rates]

  return (
    <div style={{
      background: '#1A2F54',
      borderBottom: '1px solid rgba(255,255,255,0.08)',
      overflow: 'hidden',
      height: 32,
      display: 'flex',
      alignItems: 'center',
    }}>
      <div style={{
        flexShrink: 0,
        padding: '0 12px',
        borderRight: '1px solid rgba(255,255,255,0.08)',
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.1em',
        color: '#F5A623',
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
      }}>
        LIVE RATES
      </div>
      <div style={{ overflow: 'hidden', flex: 1 }}>
        <div
          ref={trackRef}
          style={{
            display: 'flex',
            transform: `translateX(${offset}px)`,
            willChange: 'transform',
          }}
        >
          {items.map((r, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '0 20px',
              borderRight: '1px solid rgba(255,255,255,0.08)',
              whiteSpace: 'nowrap',
              fontSize: 12,
            }}>
              <span style={{ color: '#A8B4CC' }}>
                {r.bank} {loanLabel[r.loan_type]}
              </span>
              <span style={{ color: '#F5A623', fontWeight: 600 }}>
                {r.rate}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
