"use client"

import { useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HcpDimension, HcpObservation } from '@/lib/data/hcp'

const translations: Record<string, string> = { Total: 'المجموع', total: 'المجموع', Urbain: 'حضري', Rural: 'قروي', Male: 'ذكور', Female: 'إناث', Homme: 'ذكور', Femme: 'إناث' }
const arabic = (value: string) => translations[value] || value
const fmt = (value: number | null, unit = '') => value === null ? '—' : `${new Intl.NumberFormat('ar-MA', { maximumFractionDigits: 2 }).format(value)}${unit ? ` ${unit}` : ''}`

export function getRecommendedChartType(indicator: { id: string }, dimensions: HcpDimension[], observations: HcpObservation[]) {
  const labels = dimensions.flatMap((dimension) => dimension.modalities.map((modality) => `${dimension.label} ${modality.label}`)).join(' ').toLowerCase()
  if (/(region|région|جهة)/.test(labels)) return 'regional'
  if (/(age|âge|سن|عمر)/.test(labels)) return 'age'
  if (/(male|female|homme|femme|ذكر|أنثى)/.test(labels)) return 'gender'
  if (observations.length > 1) return 'line'
  return 'bar'
}

export default function IndicatorVisuals({ rows, dimensions, unit, indicatorId }: { rows: HcpObservation[]; dimensions: HcpDimension[]; unit?: string; indicatorId: string }) {
  const valid = rows.filter((row) => row.value !== null)
  const latestPeriod = [...new Set(valid.map((row) => row.period))].sort((a, b) => Number(b) - Number(a))[0]
  const latestRows = valid.filter((row) => row.period === latestPeriod)
  const [selected, setSelected] = useState<Record<string, string>>({})
  const chartType = getRecommendedChartType({ id: indicatorId }, dimensions, valid)
  const series = useMemo(() => {
    if (!dimensions.length) return valid.map((row) => ({ period: row.period, value: row.value }))
    const active = dimensions.map((dimension) => selected[dimension.id] || dimension.modalities.find((item) => item.total)?.id || dimension.modalities[0]?.id).filter(Boolean)
    return valid.filter((row) => dimensions.every((dimension, index) => !active[index] || row.dimensionIds[dimension.id] === active[index])).map((row) => ({ period: row.period, value: row.value }))
  }, [dimensions, selected, valid])
  const timeline = [...series].sort((a, b) => Number(a.period) - Number(b.period))
  const earliest = timeline[0]?.value ?? null
  const latest = timeline.at(-1)?.value ?? null
  const delta = earliest !== null && latest !== null ? latest - earliest : null
  const categoryData = latestRows.map((row) => ({ label: Object.values(row.dimensions).map(arabic).join(' · ') || 'المجموع', value: row.value }))
  const isLine = chartType === 'line' || chartType === 'gender'
  return <>
    {dimensions.length > 0 && <div className="dimension-controls" aria-label="اختيار الأبعاد">{dimensions.map((dimension) => <div key={dimension.id} className="dimension-control"><span>{arabic(dimension.label)}</span><div>{dimension.modalities.map((modality) => <button type="button" key={modality.id} className={(selected[dimension.id] || dimension.modalities.find((item) => item.total)?.id) === modality.id ? 'selected' : ''} onClick={() => setSelected((current) => ({ ...current, [dimension.id]: modality.id }))}>{arabic(modality.label)}</button>)}</div></div>)}</div>}
    <div className="visual-chart" role="img" aria-label={isLine ? 'رسم بياني للتطور عبر الزمن' : 'رسم بياني للمقارنة'}><ResponsiveContainer width="100%" height={350}>{isLine ? <LineChart data={timeline}><CartesianGrid stroke="var(--line)" strokeDasharray="2 4" /><XAxis dataKey="period" tick={{ fill: 'var(--muted)', fontSize: 12 }} /><YAxis tick={{ fill: 'var(--muted)', fontSize: 12 }} /><Tooltip formatter={(value) => [fmt(Number(value), unit), 'القيمة']} labelFormatter={(label) => `السنة: ${label}`} /><Line type="monotone" dataKey="value" stroke="var(--gold-dark)" strokeWidth={3} dot={{ r: 4, fill: 'var(--gold)' }} connectNulls={false} /></LineChart> : <BarChart data={categoryData} layout={chartType === 'regional' ? 'vertical' : 'horizontal'}><CartesianGrid stroke="var(--line)" strokeDasharray="2 4" /><XAxis type={chartType === 'regional' ? 'number' : 'category'} tick={{ fill: 'var(--muted)', fontSize: 12 }} /><YAxis type={chartType === 'regional' ? 'category' : 'number'} dataKey={chartType === 'regional' ? 'label' : undefined} width={chartType === 'regional' ? 150 : 40} tick={{ fill: 'var(--muted)', fontSize: 12 }} /><Tooltip formatter={(value) => [fmt(Number(value), unit), 'القيمة']} /><Bar dataKey="value" fill="var(--gold)" radius={[0, 4, 4, 0]} /></BarChart>}</ResponsiveContainer></div>
    <div className="change-summary"><div><span>البداية</span><strong>{fmt(earliest, unit)}</strong></div><b>→</b><div><span>النهاية</span><strong>{fmt(latest, unit)}</strong></div><p>{delta === null ? 'لا تتوفر فترة كافية للمقارنة.' : `التغير خلال الفترة المتاحة: ${fmt(delta, unit)}`}</p></div>
    <div className="takeaways"><h3>أبرز الأرقام</h3><ul>{valid.length > 0 && <><li>القيمة الأخيرة المتاحة: <strong>{fmt(latest, unit)}</strong> ({timeline.at(-1)?.period})</li><li>أعلى قيمة مسجلة: <strong>{fmt(Math.max(...valid.map((row) => row.value as number)), unit)}</strong></li><li>أدنى قيمة مسجلة: <strong>{fmt(Math.min(...valid.map((row) => row.value as number)), unit)}</strong></li></>}</ul></div>
  </>
}
