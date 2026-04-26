import React, { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

export default function Gallery({ navigate }) {
  const [stories, setStories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/api/gallery`)
      .then(r => r.json())
      .then(d => { setStories(d.stories || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div style={{ minHeight:'100vh', padding:'120px 48px 80px', maxWidth:'1200px', margin:'0 auto' }}>
      <div style={{ marginBottom:'64px', animation:'fadeUp 0.6s ease both' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.3em',
          color:'var(--gold)', textTransform:'uppercase', marginBottom:'16px' }}>
          Story Archive
        </div>
        <h1 style={{ fontFamily:'var(--font-serif)', fontWeight:300, fontStyle:'italic',
          fontSize:'clamp(36px,5vw,64px)' }}>
          Gallery
        </h1>
      </div>

      {loading && (
        <div style={{ textAlign:'center', padding:'80px', color:'var(--muted)',
          fontFamily:'var(--font-mono)', fontSize:'12px', letterSpacing:'0.2em' }}>
          Loading stories...
        </div>
      )}

      {!loading && stories.length === 0 && (
        <div style={{ textAlign:'center', padding:'80px',
          border:'1px solid var(--border)', borderRadius:'4px' }}>
          <div style={{ fontSize:'48px', marginBottom:'24px', opacity:0.3 }}>◎</div>
          <div style={{ fontFamily:'var(--font-serif)', fontSize:'22px',
            color:'var(--muted)', fontWeight:300, marginBottom:'24px' }}>
            No stories generated yet
          </div>
          <button onClick={() => navigate('generate')} style={{
            padding:'14px 40px', background:'var(--gold)', color:'#080810',
            fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.2em',
            textTransform:'uppercase', fontWeight:700, borderRadius:'2px',
          }}>
            Create First Story
          </button>
        </div>
      )}

      {stories.length > 0 && (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(320px,1fr))', gap:'16px' }}>
          {stories.map((s, i) => (
            <div key={s.story_id} style={{
              background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:'4px', padding:'28px', cursor:'pointer',
              transition:'all 0.25s', animation:`fadeUp 0.5s ${i*0.08}s ease both`,
              opacity:0, animationFillMode:'forwards',
            }}
              onMouseOver={e => { e.currentTarget.style.borderColor='var(--gold)';
                e.currentTarget.style.background='var(--bg3)' }}
              onMouseOut={e => { e.currentTarget.style.borderColor='var(--border)';
                e.currentTarget.style.background='var(--surface)' }}
            >
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px',
                letterSpacing:'0.15em', textTransform:'uppercase',
                color:'var(--gold)', marginBottom:'12px', opacity:0.7 }}>
                {s.story_id} · {s.scenes} scenes
              </div>
              <div style={{ fontFamily:'var(--font-serif)', fontStyle:'italic',
                fontSize:'15px', color:'var(--muted)', marginBottom:'16px',
                lineHeight:1.7, fontWeight:300 }}>
                "{s.prompt}"
              </div>
              <div style={{ fontFamily:'var(--font-serif)', fontSize:'14px',
                color:'rgba(255,255,255,0.5)', lineHeight:1.8, fontWeight:300 }}>
                {s.story}...
              </div>
              {s.has_video && (
                <div style={{ marginTop:'20px', display:'flex', alignItems:'center', gap:'8px' }}>
                  <div style={{ width:'6px', height:'6px', borderRadius:'50%',
                    background:'#4ade80' }}/>
                  <span style={{ fontFamily:'var(--font-mono)', fontSize:'10px',
                    letterSpacing:'0.1em', color:'#4ade80', textTransform:'uppercase' }}>
                    Video Ready
                  </span>
                  <a href={`${API}/api/story/${s.story_id}/video`} download
                    onClick={e => e.stopPropagation()}
                    style={{ marginLeft:'auto', fontFamily:'var(--font-mono)', fontSize:'10px',
                      letterSpacing:'0.1em', color:'var(--gold)', textTransform:'uppercase',
                      textDecoration:'underline' }}>
                    Download
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
