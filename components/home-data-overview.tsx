'use client'

import useSWR from 'swr'
import { ArrowUpLeft } from 'lucide-react'
import { Line, LineChart, ResponsiveContainer, Tooltip } from 'recharts'
import { getIndicator } from '@/lib/data/hcp-indicators'
import { latestObservation, type IndicatorData, type HcpObservation } from '@/lib/data/hcp'

type Curated = { id: string; kind: 'card' | 'trend' }
const curated: Curated[] = [
  { id: 'I1589', kind: 'card' }, { id: 'I2790', kind: 'card' }, { id: 'I1481', kind: 'card' },
  { id: 'I3328', kind: 'card' }, { id: 'I3331', kind: 'card' }, { id: 'I4001', kind: 'card' },
  { id: 'I40', kind: 'card' }, { id: 'I1493', kind: 'card' }, { id: 'I257', kind: 'card' },
  { id: 'I3210', kind: 'trend' },
]
const fetcher = (url: string) => fetch(url).then((response) => response.json() as Promise<IndicatorData & { indicator: ReturnType<typeof getIndicator> }>)
const format = (value: number | null) => value === null ? '—' : new Intl.NumberFormat('ar-MA', { maximumFractionDigits: 2 }).format(value)
const validRows = (data: IndicatorData | undefined) => data?.normalized?.observations.filter((row) => row.value !== null) ?? []

function useIndicator(id: string) {
  return useSWR(`/api/hcp/indicator/${encodeURIComponent(id)}`, fetcher, { revalidateOnFocus: false, keepPreviousData: true })
}

function MiniChart({ rows, label }: { rows: HcpObservation[]; label: string }) {
  const points = rows.reduce<Record<string, { period: string; value: number }>>((acc, row) => { if (row.value !== null) acc[row.period] ??= { period: row.period, value: row.value }; return acc }, {})
  const data = Object.values(points).sort((a, b) => Number(a.period) - Number(b.period))
  if (data.length < 2) return <div className="overview-single-value" aria-label="لا توجد بيانات زمنية كافية">لا تتوفر سلسلة زمنية كافية</div>
  return <div className="overview-chart" role="img" aria-label={label}><ResponsiveContainer width="100%" height="100%"><LineChart data={data}><Tooltip formatter={(value) => [format(Number(value)), 'القيمة']} labelFormatter={(period) => `الفترة: ${period}`} /><Line type="monotone" dataKey="value" stroke="var(--gold-dark)" strokeWidth={2.5} dot={false} /></LineChart></ResponsiveContainer></div>
}

function OverviewCard({ id }: { id: string }) {
  const { data, isLoading } = useIndicator(id)
  const definition = getIndicator(id)
  const normalized = data?.normalized
  const latest = normalized ? latestObservation(normalized) : null
  const rows = validRows(data)
  return <a className="data-card" href={`/indicators/${id}`} aria-label={`استكشف ${definition?.arabicTitle ?? id}`}>
    <div className="data-card-top"><span className="data-domain">{definition?.domain}</span><span className="data-id">{id}</span></div>
    <h3>{definition?.arabicTitle}</h3>
    {isLoading ? <div className="data-skeleton" aria-label="جاري تحميل البيانات" /> : data?.error || !normalized ? <p className="data-unavailable">البيانات غير متاحة حالياً</p> : <><div className="data-value">{format(latest?.value ?? null)} <small>{definition?.unit === '%' || definition?.unit.includes('POURCENTAGE') ? '%' : ''}</small></div><div className="data-period">{latest?.period ?? '—'} · {definition?.source}</div><MiniChart rows={rows} label={`التطور الزمني لـ ${definition?.arabicTitle}`} /></>}
    <div className="data-card-link">اكتشف المؤشر <ArrowUpLeft size={15} /></div>
  </a>
}

function TrendPanel({ id }: { id: string }) {
  const { data, isLoading } = useIndicator(id)
  const definition = getIndicator(id)
  const latest = data?.normalized ? latestObservation(data.normalized) : null
  return <a className="trend-panel" href={`/indicators/${id}`}><div><p className="data-domain">{definition?.domain}</p><h3>{definition?.arabicTitle}</h3></div>{isLoading ? <div className="data-skeleton trend-skeleton" /> : data?.error || !data?.normalized ? <p className="data-unavailable">البيانات غير متاحة حالياً</p> : <><div className="trend-value"><strong>{format(latest?.value ?? null)}</strong><span>{latest?.period ?? '—'}</span></div><MiniChart rows={validRows(data)} label={`اتجاه ${definition?.arabicTitle}`} /></>}<span className="data-card-link">استكشف المؤشر <ArrowUpLeft size={15} /></span></a>
}

export default function HomeDataOverview() {
  return <>
    <section className="visual-overview section" aria-labelledby="overview-title"><div className="section-intro"><p className="section-number">03</p><div><p className="eyebrow">قراءة سريعة</p><h2 id="overview-title">المغرب في لمحة</h2><p className="section-subtitle">أهم المؤشرات في صورة واضحة ومبسطة.</p></div></div><div className="data-card-grid">{curated.filter((item) => item.kind === 'card').map(({ id }) => <OverviewCard key={id} id={id} />)}</div></section>
    <section className="trend-section section" aria-labelledby="trend-title"><div className="section-intro"><p className="section-number">04</p><div><p className="eyebrow">قراءة الاتجاهات</p><h2 id="trend-title">اتجاهات مختارة</h2><p className="section-subtitle">كيف تغيرت بعض المؤشرات خلال السنوات الماضية؟</p></div></div><div className="trend-grid">{['I1589', 'I4001', 'I257', 'I3210'].map((id) => <TrendPanel key={id} id={id} />)}</div></section>
    <section className="overview-cta"><p className="eyebrow">المكتبة الكاملة</p><h2>استكشف جميع المؤشرات</h2><p>تصفح المؤشرات حسب الموضوع، وابحث عن البيانات التي تهمك.</p><a href="/indicators">عرض جميع المؤشرات <ArrowUpLeft size={16} /></a></section>
  </>
}
