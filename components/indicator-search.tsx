'use client'

import Link from 'next/link'
import { Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { HCP_INDICATORS } from '@/lib/data/hcp-indicators'

export default function IndicatorSearch({ english = false }: { english?: boolean }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const q = query.trim().toLocaleLowerCase()
  const results = q ? HCP_INDICATORS.filter((item) => `${item.arabicTitle} ${item.frenchTitle} ${item.id} ${item.domain} ${item.source}`.toLocaleLowerCase().includes(q)).slice(0, 8) : []
  useEffect(() => { const close = (event: MouseEvent) => { if (!ref.current?.contains(event.target as Node)) setOpen(false) }; document.addEventListener('mousedown', close); return () => document.removeEventListener('mousedown', close) }, [])
  const select = (id: string) => { setOpen(false); setQuery(''); window.location.href = `${english ? '/en' : ''}/indicators/${id}` }
  return <div className="global-search" ref={ref}><Search size={18} /><input value={query} onChange={(event) => { setQuery(event.target.value); setOpen(true); setActive(0) }} onFocus={() => setOpen(true)} onKeyDown={(event) => { if (event.key === 'Escape') setOpen(false); if (event.key === 'ArrowDown') { event.preventDefault(); setActive((value) => Math.min(value + 1, results.length - 1)) }; if (event.key === 'ArrowUp') { event.preventDefault(); setActive((value) => Math.max(value - 1, 0)) }; if (event.key === 'Enter' && results[active]) { event.preventDefault(); select(results[active].id) } }} placeholder={english ? 'Search for an indicator...' : 'ابحث عن مؤشر...'} aria-label={english ? 'Search for an indicator' : 'ابحث عن مؤشر'} /><button className="search-clear" aria-label={english ? 'Clear search' : 'مسح البحث'} onClick={() => { setQuery(''); setOpen(false) }}>{query ? <X size={15} /> : null}</button>{open && q && <div className="search-results" role="listbox">{results.length ? results.map((item, index) => <button className={index === active ? 'search-result active' : 'search-result'} key={item.id} onMouseDown={() => select(item.id)}><strong>{english ? item.frenchTitle : item.arabicTitle}</strong><span>{item.id} · {english ? item.domain : item.domain}</span></button>) : <p className="search-empty">{english ? 'No matching indicators' : 'لا توجد نتائج مطابقة'}</p>}</div>}</div>
}
