from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_pipeline.registry.models import IndicatorDefinition
from data_pipeline.storage.db import create_all, make_engine, make_session_factory

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "hcp_responses"
MIXED_DIR = Path(__file__).parent / "fixtures" / "hcp_responses_mixed"

# Mirrors lib/data/hcp-indicators.ts -- the real, production registry (28
# indicators). This is the one place in the test suite this list is
# hand-transcribed; production code (cli.py / ingestion/run.py) never
# hardcodes indicator ids -- it always resolves them from the live registry
# via registry/client.py. Keep this in sync with the TS file if it changes.
_REGISTRY_SUBSET = {
    'I1587': ('توقعات سكان الجهات حسب الوسط 2014–2030', 'Projections de la population des régions par milieu 2014 à 2030', 'Nombre', 'AS', 'HCP-CERED'),
    'I1589': ('معدل النمو السكاني', "Taux d'accroissement (en %)", 'Pour cent', 'AS', 'HCP-CERED'),
    'I1590': ('السكان حسب الفئة العمرية والجنس والوسط', 'Population  par groupe d’âge , sexe et le milieu (en milliers et au milieu de l’année) : 1960-2050', 'En milliers', 'AS', 'HCP-CERED'),
    'I1594': ('السكان في سن النشاط', "Population en âge d'activité", 'En milliers', 'AS', 'HCP-CERED'),
    'I1599': ('معدل الولادات الخام', 'Taux brut de natalité', 'Pour mille', 'AI', 'HCP-CERED'),
    'I1600': ('معدل الوفيات الخام', 'Taux brut de mortalité', 'Pour mille', 'AI', 'HCP-CERED'),
    'I2790': ('معدل التمدن', "Taux d'urbanisation", '%', 'IR', 'Recensement général de la population et de l’habitat'),
    'I1481': ('السكان حسب الفئات العمرية والجنس', "Population selon les groupes d'âge et le sexe", 'Nombre', 'AS', 'Haut Commissariat au Plan'),
    'I2090': ('الواردات حسب الموردين الرئيسيين', 'Importations par principaux fournisseurs', 'en millions de DH', 'AS', 'Office des changes'),
    'I2084': ('الصادرات حسب الزبائن الرئيسيين', 'Exportations par principaux clients', 'en millions de DH', 'AS', 'Office des changes'),
    'I1887': ('القيمة السوقية للأسهم المغربية حسب القطاع الاقتصادي', "Capitalisation boursière des valeurs marocaines par secteur d'activité économique", 'En millions de DH', 'AS', 'Bourse de Casablanca'),
    'I1886': ('ميزانية بنك المغرب: الأصول', 'Bilan de Bank Al-Maghrib (Actif)', 'En millions de DH', 'AS', 'Bank Al-Maghrib'),
    'I1889': ('ميزانية بنك المغرب: الخصوم', 'Bilan de Bank Al-Maghrib (Passif)', 'En millions de DH', 'AS', 'Bank Al-Maghrib'),
    'I3328': ('رقم المعاملات', "Chiffre d'affaires", 'En millions de DH', 'AS', 'Ministère de l’Industrie et du Commerce'),
    'I3331': ('الصادرات', 'Exportation', 'En millions de DH', 'AS', 'Ministère de l’Industrie et du Commerce'),
    'I4217': ('عدد السجناء', 'Population Pénale', 'NOMBRE', 'AS', 'Délégation Générale de l’Administration Pénitentiaire'),
    'I1493': ('معدل الفقر', 'Taux de pauvreté', 'POURCENTAGE', 'IR', 'Carte de pauvreté monétaire 2014'),
    'I3242': ('عدم المساواة في مستوى المعيشة: معامل جيني', 'Inégalité de vie : coefficient de Gini', '%', 'IR', 'HCP'),
    'I257': ('عدد المستشفيات', "Nombre d'hôpitaux", 'NOMBRE', 'AS', 'Ministère de la Santé'),
    'I259': ('الطاقة الاستيعابية للأسرة', 'Capacité litière existante', 'Nombre', 'AS', 'Ministère de la Santé et de la Protection sociale'),
    'I238': ('عدد المراكز الصحية', 'Nombre de centres de santé', 'NOMBRE', 'AS', 'Ministère de la Santé et de la Protection sociale'),
    'I3210': ('عدد تلاميذ التعليم الابتدائي العمومي', "Nombre des élèves dans l'enseignement primaire public", 'Nombre', 'AS', 'Ministère de l’Éducation nationale'),
    'I1762': ('هيئة التدريس بالتعليم الابتدائي العمومي', "Personnel enseignant de l'enseignement primaire public", 'NOMBRE', 'AS', 'Ministère de l’Éducation nationale'),
    'I1821': ('ميزانية التعليم الوطني', "Budget de l'éducation nationale (en millions de dh)", 'Millions de dh', 'AS', 'Ministère de l’Enseignement supérieur'),
    'I4002': ('معدل البطالة حسب الوسط والشهادات', 'Taux de chômage selon le Milieu, les diplômes', 'POURCENTAGE', 'AS', 'MAR_HCP Enquête nationale sur l’emploi'),
    'I4001': ('معدل البطالة حسب الوسط والجنس والفئة العمرية', 'Taux de chômage selon le Milieu, le sexe et le groupe d’âges', 'POURCENTAGE', 'AS', 'MAR_HCP Enquête nationale sur l’emploi'),
    'I40': ('معدل النشاط الصافي', 'Taux net d’activité', 'POURCENTAGE', 'AS', 'MAR_HCP Enquête nationale sur l’emploi'),
    'IMT_TXEMP_02': ('معدل التشغيل حسب الأقاليم والوسط', 'Taux d’emploi selon les Provinces/Préfectures et le Milieu', 'POURCENTAGE', 'AS', 'MAR_HCP Enquête nationale sur l’emploi'),
}

# The original 9 indicators from Phase 1's first pass remain the dedicated
# regression/parser fixture set called out by name in earlier requirements.
TEST_FIXTURE_IDS = [
    'I1589',
    'I2790',
    'I1493',
    'I257',
    'I3210',
    'I4001',
    'I4002',
    'I1887',
    'I1886',
]


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
    """All 28 -- the real, full production registry."""
    return [make_indicator(i) for i in _REGISTRY_SUBSET]


@pytest.fixture
def registry_test_subset():
    """Just the original 9 regression-fixture indicators."""
    return [make_indicator(i) for i in TEST_FIXTURE_IDS]


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
