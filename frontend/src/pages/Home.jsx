import React, { useEffect, useRef } from 'react'

export default function Home({ navigate }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let W = canvas.width  = window.innerWidth
    let H = canvas.height = window.innerHeight
    let frame = 0

    const stars = Array.from({length:120}, () => ({
      x: Math.random()*W, y: Math.random()*H,
      r: Math.random()*1.5+0.3, s: Math.random()*0.3+0.1,
      o: Math.random(),
    }))

    const draw = () => {
      ctx.clearRect(0,0,W,H)
      stars.forEach(s => {
        s.o += s.s * 0.01
        const o = (Math.sin(s.o)+1)/2 * 0.7 + 0.1
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.r, 0, Math.PI*2)
        ctx.fillStyle = `rgba(201,168,76,${o})`
        ctx.fill()
      })
      frame = requestAnimationFrame(draw)
    }
    draw()

    const resize = () => {
      W = canvas.width  = window.innerWidth
      H = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', resize)
    return () => { cancelAnimationFrame(frame); window.removeEventListener('resize', resize) }
  }, [])

  return (
    <div style={{ position:'relative', minHeight:'100vh', overflow:'hidden' }}>
      <canvas ref={canvasRef} style={{ position:'absolute', inset:0, zIndex:0 }}/>

      {/* Radial glow */}
      <div style={{
        position:'absolute', top:'40%', left:'50%', transform:'translate(-50%,-50%)',
        width:'600px', height:'600px', borderRadius:'50%',
        background:'radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%)',
        pointerEvents:'none',
      }}/>

      {/* Hero content */}
      <div style={{
        position:'relative', zIndex:1, display:'flex', flexDirection:'column',
        alignItems:'center', justifyContent:'center', minHeight:'100vh',
        padding:'80px 24px 60px',
        animation:'fadeUp 1s ease both',
      }}>
        <div style={{
          fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.3em',
          color:'var(--gold)', textTransform:'uppercase', marginBottom:'32px', opacity:0.8,
        }}>
          Multi-Agent AI Storytelling Platform
        </div>

        <h1 style={{
          fontFamily:'var(--font-serif)', fontWeight:300, fontStyle:'italic',
          fontSize:'clamp(56px, 10vw, 120px)', lineHeight:1, textAlign:'center',
          letterSpacing:'-0.02em', marginBottom:'24px',
          background:'linear-gradient(135deg, #fff 0%, var(--gold2) 50%, var(--gold) 100%)',
          WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent',
        }}>
          DreamScape
        </h1>

        <p style={{
          fontFamily:'var(--font-serif)', fontWeight:300, fontSize:'22px',
          color:'var(--muted)', textAlign:'center', maxWidth:'560px',
          lineHeight:1.8, marginBottom:'64px',
        }}>
          Six AI agents collaborate in real-time to write, illustrate,
          and narrate your story — then render it as a cinematic video.
        </p>

        <div style={{ display:'flex', gap:'16px', flexWrap:'wrap', justifyContent:'center' }}>
          <button onClick={() => navigate('generate')} style={{
            padding:'16px 48px', background:'var(--gold)',
            color:'#080810', fontFamily:'var(--font-mono)', fontSize:'12px',
            letterSpacing:'0.2em', textTransform:'uppercase', fontWeight:700,
            borderRadius:'2px', transition:'all 0.2s',
          }}
            onMouseOver={e => e.target.style.background='var(--gold2)'}
            onMouseOut={e => e.target.style.background='var(--gold)'}
          >
            Create Story
          </button>
          <button onClick={() => navigate('about')} style={{
            padding:'16px 48px', background:'transparent',
            color:'var(--muted)', fontFamily:'var(--font-mono)', fontSize:'12px',
            letterSpacing:'0.2em', textTransform:'uppercase',
            border:'1px solid rgba(255,255,255,0.15)', borderRadius:'2px', transition:'all 0.2s',
          }}
            onMouseOver={e => { e.target.style.borderColor='var(--gold)'; e.target.style.color='var(--gold)' }}
            onMouseOut={e => { e.target.style.borderColor='rgba(255,255,255,0.15)'; e.target.style.color='var(--muted)' }}
          >
            Learn More
          </button>
        </div>

        {/* Features row */}
        <div style={{
          display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'1px',
          marginTop:'100px', width:'100%', maxWidth:'860px',
          border:'1px solid var(--border)', borderRadius:'4px', overflow:'hidden',
          background:'var(--border)',
        }}>
          {[
            { icon:'◈', label:'6 AI Agents', desc:'Round-table negotiation protocol' },
            { icon:'◎', label:'Multimodal Output', desc:'Image · Narration · Music · Video' },
            { icon:'◉', label:'Vector Memory', desc:'ChromaDB semantic story consistency' },
          ].map(f => (
            <div key={f.label} style={{
              padding:'32px 28px', background:'var(--bg2)',
              transition:'background 0.2s',
            }}
              onMouseOver={e => e.currentTarget.style.background='var(--bg3)'}
              onMouseOut={e => e.currentTarget.style.background='var(--bg2)'}
            >
              <div style={{ fontSize:'28px', marginBottom:'12px', color:'var(--gold)' }}>{f.icon}</div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.15em',
                textTransform:'uppercase', color:'var(--gold)', marginBottom:'8px' }}>{f.label}</div>
              <div style={{ fontSize:'15px', color:'var(--muted)', fontWeight:300 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
