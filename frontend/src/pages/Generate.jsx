import React, { useState, useEffect, useRef } from 'react'

const API = 'http://localhost:8000'

const PHASES = [
  { id:'story',       label:'Story Generation',    icon:'✦' },
  { id:'scenes',      label:'Scene Pipeline',       icon:'◈' },
  { id:'images',      label:'Image Generation',     icon:'◎' },
  { id:'audio',       label:'Audio Generation',     icon:'♪' },
  { id:'video_clips', label:'Video Clip Animation', icon:'◉' },
  { id:'assembly',    label:'Final Assembly',       icon:'▶' },
]

export default function Generate() {
  const [prompt,   setPrompt]   = useState('')
  const [rounds,   setRounds]   = useState(3)
  const [storyId,  setStoryId]  = useState(null)
  const [status,   setStatus]   = useState('idle') // idle|running|review|complete|error
  const [phases,   setPhases]   = useState({})
  const [story,    setStory]    = useState('')
  const [logs,     setLogs]     = useState([])
  const [videoUrl, setVideoUrl] = useState(null)
  const wsRef = useRef(null)
  const logsRef = useRef(null)

  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight
  }, [logs])

  const startGeneration = async () => {
    if (!prompt.trim()) return
    setStatus('running')
    setPhases({})
    setLogs([])
    setStory('')
    setVideoUrl(null)

    const res  = await fetch(`${API}/api/story`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ prompt, rounds }),
    })
    const data = await res.json()
    const sid  = data.story_id
    setStoryId(sid)

    // Connect WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/${sid}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      setLogs(prev => [...prev, msg])
      setPhases(prev => ({ ...prev, [msg.phase]: msg.status }))

      if (msg.phase === 'story' && msg.status === 'complete') {
        setStory(msg.detail)
      }
      if (msg.phase === 'done' && msg.status === 'complete') {
        setStatus('complete')
        setVideoUrl(`${API}/api/story/${sid}/video`)
        ws.close()
      }
      if (msg.phase === 'error') {
        setStatus('error')
        ws.close()
      }
    }
  }

  const phaseColor = (s) => s === 'complete' ? '#4ade80' : s === 'running' ? 'var(--gold)' : s === 'failed' ? '#f87171' : 'var(--muted)'

  return (
    <div style={{ minHeight:'100vh', padding:'120px 48px 80px', maxWidth:'1100px', margin:'0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom:'64px', animation:'fadeUp 0.6s ease both' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.3em',
          color:'var(--gold)', textTransform:'uppercase', marginBottom:'16px' }}>
          Story Generation
        </div>
        <h1 style={{ fontFamily:'var(--font-serif)', fontWeight:300, fontStyle:'italic',
          fontSize:'clamp(36px,5vw,64px)', lineHeight:1.1 }}>
          Begin Your Story
        </h1>
      </div>

      {status === 'idle' && (
        <div style={{ animation:'fadeUp 0.6s 0.2s ease both', opacity:0, animationFillMode:'forwards' }}>
          {/* Prompt input */}
          <div style={{ marginBottom:'32px' }}>
            <label style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.2em',
              textTransform:'uppercase', color:'var(--muted)', display:'block', marginBottom:'12px' }}>
              Story Prompt
            </label>
            <textarea value={prompt} onChange={e=>setPrompt(e.target.value)}
              placeholder="A lone astronaut discovers an ancient signal deep in the asteroid belt..."
              style={{
                width:'100%', minHeight:'140px', background:'var(--surface)',
                border:'1px solid var(--border)', borderRadius:'4px',
                padding:'20px', color:'var(--text)', fontSize:'18px',
                fontFamily:'var(--font-serif)', resize:'vertical',
                transition:'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor='var(--gold)'}
              onBlur={e => e.target.style.borderColor='var(--border)'}
            />
          </div>

          {/* Rounds */}
          <div style={{ marginBottom:'48px', display:'flex', alignItems:'center', gap:'24px' }}>
            <label style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.2em',
              textTransform:'uppercase', color:'var(--muted)' }}>
              Agent Rounds
            </label>
            {[2,3,5].map(n => (
              <button key={n} onClick={() => setRounds(n)} style={{
                padding:'8px 24px', fontFamily:'var(--font-mono)', fontSize:'12px',
                letterSpacing:'0.1em', borderRadius:'2px', transition:'all 0.2s',
                background: rounds===n ? 'var(--gold)' : 'transparent',
                color: rounds===n ? '#080810' : 'var(--muted)',
                border: `1px solid ${rounds===n ? 'var(--gold)' : 'var(--border)'}`,
              }}>{n} Rounds</button>
            ))}
          </div>

          <button onClick={startGeneration} disabled={!prompt.trim()} style={{
            padding:'18px 56px', background: prompt.trim() ? 'var(--gold)' : 'rgba(201,168,76,0.2)',
            color: prompt.trim() ? '#080810' : 'rgba(255,255,255,0.2)',
            fontFamily:'var(--font-mono)', fontSize:'12px', letterSpacing:'0.2em',
            textTransform:'uppercase', fontWeight:700, borderRadius:'2px',
            transition:'all 0.2s',
          }}>
            Generate Story
          </button>
        </div>
      )}

      {(status === 'running' || status === 'complete' || status === 'error') && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'24px', animation:'fadeUp 0.5s ease both' }}>

          {/* Left: Phase progress */}
          <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
            borderRadius:'4px', padding:'32px' }}>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.25em',
              textTransform:'uppercase', color:'var(--muted)', marginBottom:'28px' }}>
              Pipeline Status
            </div>
            {PHASES.map((p, i) => {
              const ps = phases[p.id]
              return (
                <div key={p.id} style={{ display:'flex', alignItems:'center', gap:'16px',
                  padding:'14px 0', borderBottom:'1px solid var(--border)',
                  opacity: ps ? 1 : 0.35,
                }}>
                  <div style={{ width:'28px', height:'28px', borderRadius:'50%',
                    background: ps === 'complete' ? 'rgba(74,222,128,0.1)' :
                                ps === 'running'  ? 'rgba(201,168,76,0.15)' : 'transparent',
                    border: `1px solid ${phaseColor(ps)}`,
                    display:'flex', alignItems:'center', justifyContent:'center',
                    fontSize:'12px', color: phaseColor(ps),
                    animation: ps === 'running' ? 'pulse 1.5s infinite' : 'none',
                  }}>
                    {ps === 'complete' ? '✓' : ps === 'running' ? '◌' : p.icon}
                  </div>
                  <div>
                    <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px',
                      letterSpacing:'0.1em', color: phaseColor(ps) }}>
                      {p.label}
                    </div>
                  </div>
                  {ps === 'running' && (
                    <div style={{ marginLeft:'auto', width:'16px', height:'16px',
                      border:'2px solid var(--gold)', borderTopColor:'transparent',
                      borderRadius:'50%', animation:'spin 0.8s linear infinite' }}/>
                  )}
                </div>
              )
            })}

            {status === 'complete' && (
              <div style={{ marginTop:'28px' }}>
                <a href={videoUrl} download style={{
                  display:'block', padding:'14px', background:'var(--gold)',
                  color:'#080810', textAlign:'center', borderRadius:'2px',
                  fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.15em',
                  textTransform:'uppercase', fontWeight:700,
                }}>
                  ↓ Download Video
                </a>
                {videoUrl && (
                  <video controls style={{ width:'100%', marginTop:'16px', borderRadius:'4px',
                    border:'1px solid var(--border)' }} src={videoUrl}/>
                )}
              </div>
            )}
          </div>

          {/* Right: Live log + story */}
          <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>
            <div ref={logsRef} style={{
              background:'var(--bg)', border:'1px solid var(--border)', borderRadius:'4px',
              padding:'20px', height:'280px', overflowY:'auto',
              fontFamily:'var(--font-mono)', fontSize:'12px', lineHeight:1.8,
            }}>
              {logs.length === 0 && (
                <div style={{ color:'var(--muted)' }}>Connecting to pipeline...</div>
              )}
              {logs.map((l,i) => (
                <div key={i} style={{ color: l.status==='complete' ? '#4ade80' :
                  l.status==='running' ? 'var(--gold)' :
                  l.status==='failed'  ? '#f87171' : 'var(--muted)',
                  marginBottom:'4px',
                }}>
                  <span style={{ opacity:0.5 }}>[{l.phase}]</span> {l.detail || l.status}
                </div>
              ))}
            </div>

            {story && (
              <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
                borderRadius:'4px', padding:'24px', flex:1, overflowY:'auto', maxHeight:'360px' }}>
                <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.25em',
                  textTransform:'uppercase', color:'var(--gold)', marginBottom:'16px' }}>
                  Generated Story
                </div>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:'16px',
                  color:'rgba(255,255,255,0.75)', lineHeight:1.9, fontWeight:300 }}>
                  {story}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {status !== 'idle' && (
        <button onClick={() => { setStatus('idle'); setPrompt('') }}
          style={{ marginTop:'32px', padding:'12px 32px', background:'transparent',
            color:'var(--muted)', fontFamily:'var(--font-mono)', fontSize:'11px',
            letterSpacing:'0.15em', textTransform:'uppercase',
            border:'1px solid var(--border)', borderRadius:'2px',
          }}>
          ← New Story
        </button>
      )}
    </div>
  )
}
