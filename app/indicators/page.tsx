'use client'

import Link from 'next/link'
import { Search, ArrowUpLeft } from 'lucide-react'
import { Suspense, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { HCP_INDICATORS } from '@/lib/data/hcp-indicators'

const categoryOrder = ['الكل', 'السكان والديموغرافيا', 'الاقتصاد والتجارة', 'المال والأسواق', 'الفقر وعدم المساواة', 'الصحة', 'التعليم', 'العمل والتشغيل', 'العدالة والمجتمع', 'أخرى']
const categoryAliases: Record<string, string> = { 'التعليم والثقافة': 'التعليم', 'المجتمع': 'الفقر وعدم المساواة', 'الشغل': 'العمل والتشغيل' }

function IndicatorsCatalog() {
  const searchParams = useSearchParams()
  const domainParam = searchParams.get('domain')
  const domainLabels: Record<string, string> = { economy: 'الاقتصاد والتجارة', society: 'الفقر وعدم المساواة', education: 'التعليم', health: 'الصحة', employment: 'العمل والتشغيل', population: 'السكان والديموغرافيا' }
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState(domainLabels[domainParam || ''] || 'الكل')
  const effectiveCategory = domainLabels[domainParam || ''] || category
  const filtered = useMemo(() => HCP_INDICATORS.filter((indicator) => {
    const normalizedCategory = categoryAliases[indicator.domain] || indicator.domain
    const haystack = `${indicator.arabicTitle} ${indicator.frenchTitle} ${indicator.id} ${indicator.domain} ${normalizedCategory}`.toLocaleLowerCase('ar')
    return (effectiveCategory === 'الكل' || normalizedCategory === effectiveCategory) && haystack.includes(query.trim().toLocaleLowerCase('ar'))
  }), [category, query])
  const grouped = categoryOrder.slice(1).map((name) => ({ name, items: filtered.filter((item) => (categoryAliases[item.domain] || item.domain) === name) })).filter((group) => group.items.length)
  return <main dir="rtl" lang="ar" className="catalog-page">
    <header className="catalog-header"><div className="catalog-shell"><Link className="catalog-back" href="/#indicators">← العودة إلى المؤشرات المختارة</Link><p className="eyebrow">المرصد الوطني للمؤشرات المغربية</p><h1>جميع المؤشرات</h1><p>استكشف جميع المؤشرات المتاحة من المصادر الرسمية.</p><div className="catalog-count">{HCP_INDICATORS.length} مؤشراً متاحاً</div></div></header>
    <section className="catalog-shell catalog-tools"><label className="catalog-search"><Search size={19} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ابحث عن مؤشر..." aria-label="ابحث عن مؤشر" /></label><div className="catalog-filters" aria-label="تصفية حسب المجال">{categoryOrder.map((item) => <button key={item} className={category === item ? 'selected' : ''} onClick={() => setCategory(item)}>{item}</button>)}</div></section>
    <section className="catalog-shell catalog-results"><p className="result-count">{filtered.length} من {HCP_INDICATORS.length} مؤشراً</p>{grouped.length ? grouped.map((group) => <div className="catalog-group" key={group.name}><div className="catalog-group-heading"><span>مجال البيانات</span><h2>{group.name}</h2></div><div className="catalog-grid">{group.items.map((indicator) => <Link className="catalog-card" href={`/indicators/${indicator.id}`} key={indicator.id}><span className="catalog-domain">{indicator.domain}</span><h3>{indicator.arabicTitle}</h3><div><b>{indicator.id}</b><span>عرض البيانات <ArrowUpLeft size={15} /></span></div></Link>)}</div></div>) : <div className="catalog-empty"><h2>لم نعثر على مؤشرات</h2><p>جرّب البحث باسم المؤشر أو رمزه.</p></div>}</section>
  </main>
}

export default function Page() { return <Suspense fallback={<main className="catalog-page"><div className="catalog-shell catalog-empty">جارٍ تحميل المؤشرات...</div></main>}><IndicatorsCatalog /></Suspense> }
export const dynamic = 'force-dynamic'
