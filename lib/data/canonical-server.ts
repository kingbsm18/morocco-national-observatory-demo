'use server'

import { type IndicatorDefinition } from './hcp-indicators'
import { getCanonicalIndicator } from './observatory'

export async function fetchCanonicalIndicator(indicator: IndicatorDefinition) {
  return getCanonicalIndicator(indicator)
}
