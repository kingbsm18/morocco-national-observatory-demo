'use client'

import { useState } from 'react'
import { ArrowUpLeft, Menu, Search, X } from 'lucide-react'
import IndicatorSearch from '@/components/indicator-search'

const logoUrl = 'https://hebbkx1anhila5yf.public.blob.vercel-storage.com/PDM-03-CrS4QAfSnxTmubUftRMxezAw71LmMS.png'

const indicators = [
  ['معدل النمو السكاني (%)', 'I1589', 'السكان والديموغرافيا'],
  ['معدل التمدن', 'I2790', 'السكان والديموغرافيا'],
  ['معدل الفقر', 'I1493', 'المجتمع'],
  ['عدد المستشفيات', 'I257', 'الصحة'],
  ['عدد تلاميذ التعليم الابتدائي العمومي', 'I3210', 'التعليم والثقافة'],
  ['معدل البطالة حسب الوسط والجنس والفئة العمرية', 'I4001', 'الشغل'],
]

const categories = [
  ['01', 'الاقتصاد والتجارة', 'الواردات، الصادرات، ميزانية بنك المغرب'],
  ['02', 'المجتمع', 'الفقر، اللامساواة، السجناء'],
  ['03', 'التعليم والثقافة', 'التلاميذ، هيئة التدريس، الميزانية'],
  ['04', 'الصحة', 'المستشفيات، الأسرة، المراكز الصحية'],
  ['05', 'الشغل', 'البطالة، النشاط، التشغيل'],
  ['06', 'السكان والديموغرافيا', 'السكان، المواليد، الوفيات، التمدن'],
]

const nationalHeadlineStats = [
  { key: 'population', label: 'إجمالي سكان المغرب', value: 38430770, display: '38.43 مليون', period: '2025', source: 'البنك الدولي', indicator: 'Population, total' },
  { key: 'gdp', label: 'الناتج الداخلي الخام', value: 182370000000, display: '182.37 مليار دولار', period: '2025', source: 'البنك الدولي', indicator: 'GDP (current US$)' },
  { key: 'growth', label: 'نمو الناتج الداخلي الخام', value: 4.6, display: '4.6%', period: '2025', source: 'البنك الدولي', indicator: 'GDP growth (annual %)' },
] as const

export default function Page() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')
  const filtered = indicators.filter(([name, id, category]) => `${name} ${id} ${category}`.includes(query))
  return <main dir="rtl" lang="ar">
    <header className="site-header"><div className="header-inner">
      <div className="header-search"><Search size={18} /><a className="language-switch" href="/en" aria-label="English version">العربية <span>| EN</span></a></div>
      <nav className={menuOpen ? 'main-nav nav-open' : 'main-nav'}>{[['الرئيسية','/'],['المؤشرات','/indicators'],['الاقتصاد','/indicators?domain=economy'],['المجتمع','/indicators?domain=society'],['التعليم','/indicators?domain=education'],['الصحة','/indicators?domain=health'],['الشغل','/indicators?domain=employment'],['السكان','/indicators?domain=population'],['المنهجية','/#section-8']].map(([item, href]) => <a key={item} href={href} onClick={() => setMenuOpen(false)}>{item}</a>)}</nav>
      <a className="party-lockup" href="#about"><img src={logoUrl} alt="مشروع حزب اليمين المغربي" /></a><button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="القائمة">{menuOpen ? <X /> : <Menu />}</button>
    </div></header>
    <div className="demo-ribbon">نسخة تجريبية — القيم المعروضة لأغراض العرض</div>
    <section className="hero" id="home"><div className="hero-copy"><p className="eyebrow">المرصد الوطني للمؤشرات</p><h1>المغرب<br /><em>بالأرقام.</em></h1><p className="hero-lead">مرصد وطني يتيح الوصول إلى أهم المؤشرات الاقتصادية والاجتماعية والتنموية للمغرب.</p><p className="hero-note">نجمع البيانات من مصادر موثوقة، ونقدمها بوضوح وإتاحة للمواطنين والباحثين والصحفيين.</p><IndicatorSearch /></div><div className="hero-geometry" aria-hidden="true"><div className="circle circle-a" /><div className="circle circle-b" /><div className="crosshair" /><span>بيانات موثقة</span><div className="watermark"><img src={logoUrl} alt="" /></div></div></section>
    <section className="national-overview" aria-labelledby="national-overview-title"><div className="national-overview-heading"><div><p className="eyebrow">نظرة وطنية</p><h2 id="national-overview-title">المغرب في أرقام</h2></div><p>ثلاثة أرقام أساسية لفهم المغرب اليوم، مع سنة القياس ومصدرها الظاهر.</p></div><div className="headline-grid">{nationalHeadlineStats.map((stat, index) => <article className={`headline-card headline-card-${index + 1}`} key={stat.key}><p className="headline-label">{stat.label}</p><strong>{stat.display}</strong><div className="headline-meta"><span>{stat.period} · {stat.source}</span><span>المصدر: {stat.indicator}</span></div></article>)}</div></section>
    <section className="section categories" id="section-1"><div className="section-intro"><p className="section-number">01</p><div><p className="eyebrow">استكشف البيانات</p><h2>مجالات المؤشرات</h2></div></div><div className="category-list">{categories.map(([number, title, description]) => <a href="#indicators" className="category-row" key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p><ArrowUpLeft size={19} /></a>)}</div></section>
    <section className="section indicator-section" id="indicators"><div className="section-intro"><p className="section-number">02</p><div><p className="eyebrow">بيانات رسمية</p><h2>مؤشرات مختارة</h2></div><p className="intro-note">استكشف المؤشرات كما تنشرها المندوبية السامية للتخطيط، مع المصدر ورمز المؤشر.</p></div><div className="indicator-grid">{(filtered.length ? filtered : indicators).map(([name, id, category]) => <a className="indicator-item" href={`/indicateurs/${id}`} key={id}><p>{category}</p><h3>{name}</h3><div><span>{id}</span><span>عرض البيانات <ArrowUpLeft size={14} /></span></div></a>)}</div><div className="catalog-cta"><a href="/indicators">عرض جميع المؤشرات <ArrowUpLeft size={16} /></a></div></section>
    <section className="methodology" id="section-8"><div className="section method-inner"><p className="section-number">03</p><div><p className="eyebrow">المنهجية</p><h2>من المصدر إلى المؤشر</h2><p>بيانات موثقة، معالجة واضحة، ومؤشرات قابلة للمقارنة. لا نعرض قيمة إلا مع مصدرها وتعريفها.</p></div><div className="method-steps"><span>المصدر</span><i /><span>التوحيد</span><i /><span>التحقق</span><i /><span>النشر</span></div></div></section>
    <footer className="site-footer" id="about"><img src={logoUrl} alt="مشروع حزب اليمين المغربي" /><div><strong>المرصد الوطني للمؤشرات المغربية</strong><p>منصة وطنية لعرض المؤشرات الاقتصادية والاجتماعية والتنموية للمغرب.</p></div></footer>
  </main>
}
