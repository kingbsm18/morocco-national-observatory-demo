import { HCP_BASE_URL, HCP_INDICATORS, type IndicatorDefinition } from './hcp-indicators'

export type HcpDimension = { id: string; label: string; modalities: { id: string; label: string; total: boolean }[] }
export type HcpObservation = { period: string; value: number | null; dimensions: Record<string, string>; dimensionIds: Record<string, string>; footNote: unknown }
export type NormalizedIndicator = {
  indicatorId: string
  label: string
  metadata: { unit?: string; frequency?: string; source?: string; definition?: string; footnotes?: unknown; methodology?: string; updatingDate?: string }
  periods: string[]
  dimensions: HcpDimension[]
  observations: HcpObservation[]
}
export type IntegrityResult = { valid: boolean; reason?: string; metadataValid?: boolean; dataValid?: boolean }
export type IndicatorData = { normalized: NormalizedIndicator | null; endpoint: string; responseCode?: string; responseLabel?: string; integrity: IntegrityResult; cacheKey?: string; error?: 'request' | 'parser' | 'integrity' }
export type IndicatorAuditRow = { id: string; apiCode?: string; apiLabel?: string; registryTitle: string; displayedTitle: string; status: 'VALID' | 'MISMATCH' | 'API_ERROR' | 'PARSER_ERROR' }

export function validateIndicatorIntegrity(indicator: IndicatorDefinition, response: unknown): IntegrityResult {
  if (!indicator.id) return { valid: false, reason: 'missing-registry-id' }
  if (!indicator.apiUrl.endsWith(`/${encodeURIComponent(indicator.id)}`)) return { valid: false, reason: 'registry-endpoint-mismatch' }
  if (!response || typeof response !== 'object') return { valid: false, reason: 'missing-response' }
  const payload = response as Record<string, any>
  const responseCode = clean(payload.code)
  const responseLabel = clean(payload.label)
  if (responseCode !== indicator.id) return { valid: false, reason: `response-code-mismatch:${responseCode}`, metadataValid: false, dataValid: false }
  if (!responseLabel) return { valid: false, reason: 'missing-response-label', metadataValid: false, dataValid: false }
  if (!payload.data || typeof payload.data !== 'object') return { valid: false, reason: 'missing-response-data', metadataValid: true, dataValid: false }
  const metadataValid = normalizeIdentity(responseLabel) === normalizeIdentity(indicator.frenchTitle)
  return { valid: metadataValid, reason: metadataValid ? undefined : `response-label-mismatch:${responseLabel}`, metadataValid, dataValid: true }
}

const base = HCP_BASE_URL
const clean = (value: unknown) => String(value ?? '').trim()
const normalizeIdentity = (value: string) => value.replace(/[’]/g, "'").replace(/\s+/g, ' ').trim().toLocaleLowerCase()
const numeric = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(String(value).replace(',', '.'))
  return Number.isFinite(parsed) ? parsed : null
}

export function normalizeHcpIndicator(response: unknown): NormalizedIndicator | null {
  if (!response || typeof response !== 'object') return null
  const payload = response as Record<string, any>
  if (!payload.data || typeof payload.data !== 'object' || Array.isArray(payload.data)) return null
  const rawDimensions = Array.isArray(payload.dimensions) ? payload.dimensions : []
  const dimensions: HcpDimension[] = rawDimensions.map((dimension: any) => ({
    id: clean(dimension.id), label: clean(dimension.label),
    modalities: Array.isArray(dimension.modalites) ? dimension.modalites.map((modalite: any) => ({ id: clean(modalite.id), label: clean(modalite.label), total: modalite.total === true })) : [],
  }))
  const modalityLookup = new Map<string, { dimension: HcpDimension; label: string; total: boolean }>()
  for (const dimension of dimensions) for (const modality of dimension.modalities) modalityLookup.set(modality.id, { dimension, label: modality.label, total: modality.total })
  const observations: HcpObservation[] = Object.entries(payload.data).map(([key, raw]: [string, any]) => {
    const [encodedIds, period = ''] = key.split('_')
    const ids = encodedIds ? encodedIds.split('.') : []
    const resolved: Record<string, string> = {}
    const dimensionIds: Record<string, string> = {}
    ids.forEach((id, index) => {
      const match = modalityLookup.get(id) ?? (dimensions[index]?.modalities.find((item) => item.id === id) ? { dimension: dimensions[index], label: dimensions[index].modalities.find((item) => item.id === id)!.label, total: dimensions[index].modalities.find((item) => item.id === id)!.total } : undefined)
      if (match) { resolved[match.dimension.label] = match.label; dimensionIds[match.dimension.id] = id }
    })
    return { period: clean(period), value: numeric(raw?.value), dimensions: resolved, dimensionIds, footNote: raw?.footNote ?? null }
  })
  const periods = (Array.isArray(payload.periods) ? payload.periods : observations.map((item) => item.period)).map(clean).filter(Boolean).sort((a, b) => Number(a) - Number(b))
  const metadata = payload.metaData && typeof payload.metaData === 'object' ? payload.metaData : {}
  return { indicatorId: clean(payload.code), label: clean(payload.label), metadata: { unit: clean(metadata.unit), frequency: clean(metadata.frequency), source: clean(metadata.source), definition: clean(metadata.definitionFr), footnotes: metadata.footNotesFr ?? null, methodology: clean(metadata.methodOfCalculationFr) }, periods: Array.from(new Set(periods)), dimensions, observations }
}

export async function fetchIndicator(indicator: IndicatorDefinition): Promise<IndicatorData> {
  const endpoint = `${base}/${encodeURIComponent(indicator.id)}`
  const cacheKey = `indicator-data-${indicator.id}`
  if (indicator.apiUrl !== endpoint) return { normalized: null, endpoint, cacheKey, integrity: { valid: false, reason: 'registry-endpoint-mismatch' }, error: 'integrity' }
  try {
    const response = await fetch(endpoint, { next: { revalidate: 3600, tags: [`hcp-indicator-${indicator.id}`] } })
    if (!response.ok) return { normalized: null, endpoint, integrity: { valid: false, reason: `http-${response.status}` }, error: 'request' }
    const payload = await response.json()
    const integrity = validateIndicatorIntegrity(indicator, payload)
    const responseCode = clean(payload?.code)
    const responseLabel = clean(payload?.label)
    if (!integrity.valid) return { normalized: null, endpoint, responseCode, responseLabel, integrity, error: 'integrity' }
    const normalized = normalizeHcpIndicator(payload)
    return normalized ? { normalized, endpoint, responseCode, responseLabel, integrity } : { normalized: null, endpoint, responseCode, responseLabel, integrity: { valid: false, reason: 'parser' }, error: 'parser' }
  } catch { return { normalized: null, endpoint, integrity: { valid: false, reason: 'request-failed' }, error: 'request' } }
}

export async function auditAllIndicators(): Promise<IndicatorAuditRow[]> {
  const rows = await Promise.all(HCP_INDICATORS.map(async (indicator) => {
    const result = await fetchIndicator(indicator)
    const status: IndicatorAuditRow['status'] = result.error === 'request' ? 'API_ERROR' : result.error === 'parser' ? 'PARSER_ERROR' : result.integrity.valid ? 'VALID' : 'MISMATCH'
    return { id: indicator.id, apiCode: result.responseCode, apiLabel: result.responseLabel, registryTitle: indicator.frenchTitle, displayedTitle: indicator.arabicTitle, status }
  }))
  return rows
}

export function latestObservation(data: NormalizedIndicator) {
  const periods = new Set(data.periods)
  const valid = data.observations.filter((observation) => observation.value !== null && periods.has(observation.period))
  if (!valid.length) return null
  const latestPeriod = [...new Set(valid.map((item) => item.period))].sort((a, b) => Number(b) - Number(a))[0]
  const candidates = valid.filter((item) => item.period === latestPeriod)
  const totalIds = new Set(data.dimensions.flatMap((dimension) => dimension.modalities.filter((modality) => modality.total).map((modality) => `${dimension.id}:${modality.id}`)))
  const aggregate = candidates.filter((item) => [...totalIds].every((token) => { const [dimensionId, modalityId] = token.split(':'); return !item.dimensionIds[dimensionId] || item.dimensionIds[dimensionId] === modalityId }))
  return (aggregate.length === 1 ? aggregate[0] : candidates.length === 1 ? candidates[0] : null)
}
