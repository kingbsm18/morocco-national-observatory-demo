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
  if (!database) return { normalized: null, endpoint, integrity: { valid: false, reason: 'database-unavailable' }, error: 'request', dataStatus: 'database-unavailable' }

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
    }>(`WITH ranked AS (
         SELECT o.*, ROW_NUMBER() OVER (
           PARTITION BY o.period, o.dimension_key
           ORDER BY r.started_at DESC, o.vintage DESC, o.created_at DESC
         ) AS row_rank
         FROM observations o
         JOIN ingestion_runs r ON r.id = o.ingestion_run_id
         WHERE o.indicator_id = $1
       )
       SELECT ranked.indicator_id, ranked.period, ranked.value, ranked.unit,
              ranked.dimension_ids, ranked.dimension_labels,
              s.name AS source_name, i.frequency,
              COALESCE(i.updated_at, ranked.vintage) AS updated_at
       FROM ranked
       JOIN indicators i ON i.id = ranked.indicator_id AND i.is_active = true
       LEFT JOIN sources s ON s.id = i.source_id
       WHERE ranked.row_rank = 1
       ORDER BY ranked.period ASC, ranked.dimension_key ASC`, [indicator.id])

    if (!result.rows.length) {
      const validation = await database.query<{ has_error: boolean }>(
        `SELECT EXISTS (
           SELECT 1 FROM validation_results
           WHERE indicator_id = $1 AND severity = 'ERROR'
         ) AS has_error`,
        [indicator.id],
      )
      const hasValidationError = validation.rows[0]?.has_error === true
      return {
        normalized: null,
        endpoint,
        integrity: { valid: false, reason: hasValidationError ? 'validation-error' : 'not-ingested', dataValid: false },
        error: 'request',
        dataStatus: hasValidationError ? 'validation-error' : 'not-ingested',
      }
    }
    const first = result.rows[0]
    const dimensionsById = new Map<string, Map<string, { label: string; total: boolean }>>()
    for (const row of result.rows) {
      const dimensionIds = Object.entries(row.dimension_ids ?? {})
      const dimensionLabels = Object.entries(row.dimension_labels ?? {})
      dimensionIds.forEach(([dimensionId, modalityId], index) => {
        const modalityLabel = dimensionLabels[index]?.[1] ?? modalityId
        const dimensionLabel = dimensionLabels[index]?.[0] ?? dimensionId
        const modalities = dimensionsById.get(dimensionId) ?? new Map()
        modalities.set(modalityId, { label: modalityLabel, total: false })
        dimensionsById.set(dimensionId, modalities)
        if (!dimensionsById.has(`${dimensionId}:label`)) dimensionsById.set(`${dimensionId}:label`, new Map([['label', { label: dimensionLabel, total: false }]]))
      })
    }
    const normalized: NormalizedIndicator = {
      indicatorId: first.indicator_id,
      label: indicator.frenchTitle,
      metadata: { unit: first.unit ?? indicator.unit, frequency: first.frequency ?? indicator.frequency, source: first.source_name ?? 'Phase 1 canonical observations', definition: indicator.description, updatingDate: first.updated_at ?? undefined },
      periods: [...new Set(result.rows.map((row) => row.period))],
      dimensions: [...dimensionsById.entries()].filter(([id]) => !id.endsWith(':label')).map(([id, modalities]) => ({ id, label: dimensionsById.get(`${id}:label`)?.get('label')?.label ?? id, modalities: [...modalities.entries()].map(([modalityId, item]) => ({ id: modalityId, label: item.label, total: item.total })) })),
      observations: result.rows.map((row) => ({ period: row.period, value: row.value === null ? null : Number(row.value), dimensions: row.dimension_labels ?? {}, dimensionIds: row.dimension_ids ?? {}, footNote: null })),
    }
    return { normalized, endpoint, responseCode: first.indicator_id, responseLabel: first.indicator_id, integrity: { valid: true, metadataValid: true, dataValid: true }, dataStatus: 'available' }
  } catch {
    return { normalized: null, endpoint, integrity: { valid: false, reason: 'database-unavailable' }, error: 'request', dataStatus: 'database-unavailable' }
  }
}
