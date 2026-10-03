import { Pool } from 'pg'
import type { IndicatorDefinition } from './hcp-indicators'
import type { IndicatorData, NormalizedIndicator } from './hcp'

let pool: Pool | undefined

function getPool() {
  if (!process.env.DATABASE_URL) return null
  pool ??= new Pool({ connectionString: process.env.DATABASE_URL, max: 5 })
  return pool
}

export async function getCanonicalIndicator(indicator: IndicatorDefinition): Promise<IndicatorData> {
  const endpoint = `canonical://observations/${encodeURIComponent(indicator.id)}`
  const database = getPool()
  if (!database) return { normalized: null, endpoint, integrity: { valid: false, reason: 'database-not-configured' }, error: 'request' }

  try {
    const result = await database.query<{
      indicator_id: string
      period: string
      value: string | number | null
      unit: string | null
      dimension_ids: Record<string, string> | null
      dimension_labels: Record<string, string> | null
      source_name: string | null
      frequency: string | null
      updated_at: string | null
    }>(`SELECT o.indicator_id, o.period, o.value, o.unit, o.dimension_ids, o.dimension_labels,
              s.name AS source_name, i.frequency, COALESCE(i.updated_at, o.vintage) AS updated_at
       FROM observations o
       JOIN indicators i ON i.id = o.indicator_id AND i.is_active = true
       LEFT JOIN sources s ON s.id = i.source_id
       WHERE o.indicator_id = $1
       ORDER BY o.period ASC, o.dimension_key ASC`, [indicator.id])

    if (!result.rows.length) return { normalized: null, endpoint, integrity: { valid: false, reason: 'canonical-data-unavailable', dataValid: false }, error: 'request' }
    const first = result.rows[0]
    const dimensionsById = new Map<string, Map<string, { label: string; total: boolean }>>()
    for (const row of result.rows) {
      for (const [dimensionId, modalityId] of Object.entries(row.dimension_ids ?? {})) {
        const label = row.dimension_labels?.[dimensionId] ?? modalityId
        const modalities = dimensionsById.get(dimensionId) ?? new Map()
        modalities.set(modalityId, { label, total: false })
        dimensionsById.set(dimensionId, modalities)
      }
    }
    const normalized: NormalizedIndicator = {
      indicatorId: first.indicator_id,
      label: indicator.frenchTitle,
      metadata: { unit: first.unit ?? indicator.unit, frequency: first.frequency ?? indicator.frequency, source: first.source_name ?? 'Phase 1 canonical observations', definition: indicator.description, updatingDate: first.updated_at ?? undefined },
      periods: [...new Set(result.rows.map((row) => row.period))],
      dimensions: [...dimensionsById.entries()].map(([id, modalities]) => ({ id, label: id, modalities: [...modalities.entries()].map(([modalityId, item]) => ({ id: modalityId, label: item.label, total: item.total })) })),
      observations: result.rows.map((row) => ({ period: row.period, value: row.value === null ? null : Number(row.value), dimensions: row.dimension_labels ?? {}, dimensionIds: row.dimension_ids ?? {}, footNote: null })),
    }
    return { normalized, endpoint, responseCode: first.indicator_id, responseLabel: first.indicator_id, integrity: { valid: true, metadataValid: true, dataValid: true } }
  } catch {
    return { normalized: null, endpoint, integrity: { valid: false, reason: 'canonical-query-failed' }, error: 'request' }
  }
}
