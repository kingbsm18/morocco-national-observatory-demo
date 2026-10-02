"""Pydantic mirror of the TypeScript IndicatorDefinition type
(lib/data/hcp-indicators.ts). Field names are kept identical (camelCase)
so a registry payload fetched from /api/registry maps onto this model
with no translation layer that could itself introduce drift.
"""
from __future__ import annotations

from pydantic import BaseModel


class IndicatorDefinition(BaseModel):
    id: str
    arabicTitle: str
    frenchTitle: str
    description: str
    domain: str
    unit: str
    frequency: str
    source: str
    apiUrl: str
