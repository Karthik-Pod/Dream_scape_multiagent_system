import React, { useState, useEffect } from 'react'

export default function Nav({ current, navigate }) {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  const links = [
    { id: 'home', label: 'Home' },
    { id: 'generate', label: 'Generate' },
    { id: 'gallery', label: 'Gallery' },
    { id: 'about', label: 'About' },
  ]

  return (
    <nav style={{
      position:'fixed', top:0, left:0, right:0, zIndex:100,
      padding:'20px 48px', display:'flex', alignItems:'center', justifyContent:'space-between',
      background: scrolled ? 'rgba(8,8,16,0.92)' : 'transparent',
      backdropFilter: scrolled ? 'blur(12px)' : 'none',
      borderBottom: scrolled ? '1px solid rgba(201,168,76,0.15)' : 'none',
      transition:'all 0.4s ease',
    }}>
      <button onClick={() => navigate('home')} style={{
        fontFamily:'var(--font-serif)', fontSize:'22px', fontWeight:600,
        letterSpacing:'0.12em', color:'var(--gold)', background:'none', textTransform:'uppercase',
      }}>DreamScape</button>
      <div style={{ display:'flex', gap:'36px' }}>
        {links.map(l => (
          <button key={l.id} onClick={() => navigate(l.id)} style={{
            fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.18em',
            textTransform:'uppercase', background:'none',
            color: current === l.id ? 'var(--gold)' : 'var(--muted)',
            borderBottom: current === l.id ? '1px solid var(--gold)' : '1px solid transparent',
            transition:'all 0.2s', padding:'4px 0',
          }}>{l.label}</button>
        ))}
      </div>
    </nav>
  )
}
