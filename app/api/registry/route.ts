// Phase 1 data-pipeline integration point.
//
// This route does not introduce a new registry: it re-exports the existing,
// hand-maintained HCP_INDICATORS array from lib/data/hcp-indicators.ts as JSON.
// It exists so the Python ingestion pipeline (see /data-pipeline) has exactly
// one source of truth for indicator definitions, read over HTTP instead of
// copy-pasted into a second, manually maintained file. No existing file is
// modified by this addition.
import { HCP_INDICATORS } from '@/lib/data/hcp-indicators'

export async function GET() {
  return Response.json(HCP_INDICATORS)
}
