from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.storage.db import create_all, make_engine, make_session_factory

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "hcp_responses"
MIXED_DIR = Path(__file__).parent / "fixtures" / "hcp_responses_mixed"

# Mirrors lib/data/hcp-indicators.ts for exactly the 9 test indicators.
# Arabic titles are illustrative placeholders for test purposes; French
# title/unit/frequency/source must match the fixtures generated alongside
# this test suite (see tests/fixtures/hcp_responses/*.json).
_REGISTRY_SUBSET = {
    "I1589": ("معدل النمو السكاني", "Taux d'accroissement (en %)", "Pour cent", "AS", "HCP-CERED"),
    "I2790": ("معدل التمدن", "Taux d'urbanisation", "%", "IR", "Recensement général de la population et de l’habitat"),
    "I1493": ("معدل الفقر", "Taux de pauvreté", "POURCENTAGE", "IR", "Carte de pauvreté monétaire 2014"),
    "I257": ("عدد المستشفيات", "Nombre d'hôpitaux", "NOMBRE", "AS", "Ministère de la Santé"),
    "I3210": ("عدد تلاميذ التعليم الابتدائي العمومي", "Nombre des élèves dans l'enseignement primaire public", "Nombre", "AS", "Ministère de l’Éducation nationale"),
    "I4001": ("معدل البطالة حسب الوسط والجنس والفئة العمرية", "Taux de chômage selon le Milieu, le sexe et le groupe d’âges", "POURCENTAGE", "AS", "MAR_HCP Enquête nationale sur l’emploi"),
    "I4002": ("معدل البطالة حسب الوسط والشهادات", "Taux de chômage selon le Milieu, les diplômes", "POURCENTAGE", "AS", "MAR_HCP Enquête nationale sur l’emploi"),
    "I1887": ("القيمة السوقية للأسهم المغربية حسب القطاع الاقتصادي", "Capitalisation boursière des valeurs marocaines par secteur d'activité économique", "En millions de DH", "AS", "Bourse de Casablanca"),
    "I1886": ("ميزانية بنك المغرب: الأصول", "Bilan de Bank Al-Maghrib (Actif)", "En millions de DH", "AS", "Bank Al-Maghrib"),
}


def make_indicator(indicator_id: str) -> IndicatorDefinition:
    arabic, french, unit, frequency, source = _REGISTRY_SUBSET[indicator_id]
    return IndicatorDefinition(
        id=indicator_id,
        arabicTitle=arabic,
        frenchTitle=french,
        description="",
        domain="test",
        unit=unit,
        frequency=frequency,
        source=source,
        apiUrl=f"https://bds.hcp.ma/api/v1/indicators/{indicator_id}",
    )


@pytest.fixture
def registry():
    return [make_indicator(i) for i in _REGISTRY_SUBSET]


def load_fixture(indicator_id: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{indicator_id}.json").read_text(encoding="utf-8"))


def load_mixed_fixture(name: str) -> dict:
    return json.loads((MIXED_DIR / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture
def db_session():
    engine = make_engine("sqlite:///:memory:")
    create_all(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        yield session
