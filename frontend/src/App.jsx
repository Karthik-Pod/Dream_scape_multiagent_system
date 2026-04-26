import React, { useState } from 'react'
import Nav from './components/Nav'
import Home from './pages/Home'
import Generate from './pages/Generate'
import Gallery from './pages/Gallery'
import About from './pages/About'

export default function App() {
  const [page, setPage] = useState('home')

  const pages = { home: Home, generate: Generate, gallery: Gallery, about: About }
  const Page  = pages[page] || Home

  return (
    <div style={{ minHeight: '100vh' }}>
      <Nav current={page} navigate={setPage} />
      <Page navigate={setPage} />
    </div>
  )
}
