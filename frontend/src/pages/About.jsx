import React from 'react'

const agents = [
  { name:'PlotAgent',       role:'Narrative Arc',          color:'#c9a84c', icon:'◈', model:'LLaMA 3.3-70B', desc:'Controls story structure, escalation and cause-effect chains' },
  { name:'CharacterAgent',  role:'Character Consistency',  color:'#a87dc4', icon:'◉', model:'LLaMA 3.3-70B', desc:'Maintains psychological consistency of each character' },
  { name:'EmotionAgent',    role:'Emotional Tone',         color:'#e87c6a', icon:'◎', model:'LLaMA 3.1-8B',  desc:'Tracks emotional arc, pacing, tension and relief cycles' },
  { name:'VisualAgent',     role:'Visual Prompts',         color:'#5aabdc', icon:'◇', model:'LLaMA 3.1-8B',  desc:'Designs cinematic scene descriptions for image generation' },
  { name:'AudioAgent',      role:'Audio Atmosphere',       color:'#6ad4a8', icon:'♪', model:'LLaMA 3.1-8B',  desc:'Designs music mood, SFX cues and narration style' },
  { name:'CoordinatorAgent',role:'Proposal Evaluation',   color:'#f0c060', icon:'✦', model:'LLaMA 3.3-70B', desc:'Scores all proposals and selects winner each round' },
]

const pipeline = [
  { phase:'01', label:'Story Generation',   desc:'6 agents negotiate across multiple rounds. Each agent proposes, Coordinator scores and selects winner.' },
  { phase:'02', label:'Scene Pipeline',     desc:'LLM-based segmenter splits story into scenes. Structurer extracts tone, tension, visual prompts, SFX cues.' },
  { phase:'03', label:'Image Generation',   desc:'Pollinations.AI generates cinematic FLUX images for each scene — free, no key required.' },
  { phase:'04', label:'Audio Generation',   desc:'Kokoro TTS generates narration locally. MusicGen creates background music matched to scene emotional tone.' },
  { phase:'05', label:'Video Animation',    desc:'Magic Hour API animates each static image into a 5-second cinematic clip with scene-matched motion.' },
  { phase:'06', label:'Final Assembly',     desc:'FFmpeg merges animated clips with our audio (stripping Magic Hour audio) into the final MP4.' },
]

export default function About() {
  return (
    <div style={{ minHeight:'100vh', padding:'120px 48px 80px', maxWidth:'1100px', margin:'0 auto' }}>

      <div style={{ marginBottom:'80px', animation:'fadeUp 0.6s ease both' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.3em',
          color:'var(--gold)', textTransform:'uppercase', marginBottom:'16px' }}>
          Architecture
        </div>
        <h1 style={{ fontFamily:'var(--font-serif)', fontWeight:300, fontStyle:'italic',
          fontSize:'clamp(36px,5vw,64px)', lineHeight:1.1, marginBottom:'24px' }}>
          How DreamScape Works
        </h1>
        <p style={{ fontFamily:'var(--font-serif)', fontWeight:300, fontSize:'20px',
          color:'var(--muted)', maxWidth:'640px', lineHeight:1.9 }}>
          A novel multi-agent architecture where six specialized AI agents negotiate
          through a round-table protocol — each contributing their domain expertise
          to produce richer stories than any single model could.
        </p>
      </div>

      {/* Agent grid */}
      <section style={{ marginBottom:'80px' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.25em',
          textTransform:'uppercase', color:'var(--muted)', marginBottom:'32px', borderBottom:'1px solid var(--border)', paddingBottom:'16px' }}>
          The Six Agents
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))', gap:'1px',
          background:'var(--border)', border:'1px solid var(--border)', borderRadius:'4px', overflow:'hidden' }}>
          {agents.map((a,i) => (
            <div key={a.name} style={{ padding:'28px', background:'var(--bg2)',
              animation:`fadeUp 0.5s ${i*0.07}s ease both`, opacity:0, animationFillMode:'forwards',
              transition:'background 0.2s' }}
              onMouseOver={e => e.currentTarget.style.background='var(--bg3)'}
              onMouseOut={e => e.currentTarget.style.background='var(--bg2)'}
            >
              <div style={{ display:'flex', alignItems:'center', gap:'12px', marginBottom:'12px' }}>
                <span style={{ fontSize:'20px', color:a.color }}>{a.icon}</span>
                <div>
                  <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px',
                    letterSpacing:'0.1em', color:a.color }}>{a.name}</div>
                  <div style={{ fontFamily:'var(--font-mono)', fontSize:'9px',
                    letterSpacing:'0.15em', color:'var(--muted)', textTransform:'uppercase' }}>{a.model}</div>
                </div>
              </div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'9px', letterSpacing:'0.12em',
                textTransform:'uppercase', color:'rgba(255,255,255,0.4)', marginBottom:'8px' }}>
                {a.role}
              </div>
              <div style={{ fontFamily:'var(--font-serif)', fontSize:'14px',
                color:'rgba(255,255,255,0.55)', lineHeight:1.7, fontWeight:300 }}>
                {a.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section style={{ marginBottom:'80px' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.25em',
          textTransform:'uppercase', color:'var(--muted)', marginBottom:'32px',
          borderBottom:'1px solid var(--border)', paddingBottom:'16px' }}>
          Production Pipeline
        </div>
        <div style={{ display:'flex', flexDirection:'column', gap:'0' }}>
          {pipeline.map((p, i) => (
            <div key={p.phase} style={{
              display:'grid', gridTemplateColumns:'80px 1fr',
              borderBottom:'1px solid var(--border)', padding:'24px 0',
              animation:`fadeUp 0.5s ${i*0.07}s ease both`, opacity:0, animationFillMode:'forwards',
            }}>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'28px',
                color:'rgba(201,168,76,0.2)', fontWeight:700, lineHeight:1 }}>
                {p.phase}
              </div>
              <div>
                <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.15em',
                  textTransform:'uppercase', color:'var(--gold)', marginBottom:'8px' }}>
                  {p.label}
                </div>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:'16px',
                  color:'var(--muted)', lineHeight:1.8, fontWeight:300 }}>
                  {p.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', letterSpacing:'0.25em',
          textTransform:'uppercase', color:'var(--muted)', marginBottom:'32px',
          borderBottom:'1px solid var(--border)', paddingBottom:'16px' }}>
          Tech Stack
        </div>
        <div style={{ display:'flex', flexWrap:'wrap', gap:'8px' }}>
          {['Python 3.13','FastAPI','Groq API','Gemini 2.0 Flash','ChromaDB','Pollinations.AI',
            'Magic Hour API','Kokoro TTS','MusicGen','FFmpeg','React','Vite'].map(t => (
            <span key={t} style={{
              fontFamily:'var(--font-mono)', fontSize:'11px', letterSpacing:'0.1em',
              padding:'6px 14px', border:'1px solid var(--border)', borderRadius:'2px',
              color:'var(--muted)', background:'var(--surface)',
            }}>{t}</span>
          ))}
        </div>
      </section>
    </div>
  )
}
