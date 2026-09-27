import { getIndicator } from '@/lib/data/hcp-indicators'
import { fetchIndicator } from '@/lib/data/hcp'

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const indicator = getIndicator(id)
  if (!indicator) return Response.json({ error: 'Indicator not found' }, { status: 404 })
  return Response.json({ indicator, ...(await fetchIndicator(indicator)) })
}
