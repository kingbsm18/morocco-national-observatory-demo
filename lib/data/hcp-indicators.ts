export type IndicatorDefinition = {
  id: string
  arabicTitle: string
  frenchTitle: string
  description: string
  domain: string
  unit: string
  frequency: string
  source: string
  apiUrl: string
}

const HCP_BASE_URL = 'https://bds.hcp.ma/api/v1/indicators'

const definitions: Omit<IndicatorDefinition, 'apiUrl'>[] = [
  { id: 'I1587', arabicTitle: 'توقعات سكان الجهات حسب الوسط 2014–2030', frenchTitle: 'Projections de la population des régions par milieu 2014 à 2030', description: 'توقعات عدد السكان حسب الجهات والوسط.', domain: 'السكان والديموغرافيا', unit: 'Nombre', frequency: 'AS', source: 'HCP-CERED' },
  { id: 'I1589', arabicTitle: 'معدل النمو السكاني', frenchTitle: "Taux d'accroissement (en %)", description: 'نسبة التغير السنوي في عدد السكان.', domain: 'السكان والديموغرافيا', unit: 'Pour cent', frequency: 'AS', source: 'HCP-CERED' },
  { id: 'I1590', arabicTitle: 'السكان حسب الفئة العمرية والجنس والوسط', frenchTitle: "Population  par groupe d’âge , sexe et le milieu (en milliers et au milieu de l’année) : 1960-2050", description: 'توزيع السكان حسب العمر والجنس والوسط.', domain: 'السكان والديموغرافيا', unit: 'En milliers', frequency: 'AS', source: 'HCP-CERED' },
  { id: 'I1594', arabicTitle: 'السكان في سن النشاط', frenchTitle: "Population en âge d'activité", description: 'السكان الذين هم في سن النشاط الاقتصادي.', domain: 'السكان والديموغرافيا', unit: 'En milliers', frequency: 'AS', source: 'HCP-CERED' },
  { id: 'I1599', arabicTitle: 'معدل الولادات الخام', frenchTitle: 'Taux brut de natalité', description: 'عدد الولادات لكل ألف نسمة.', domain: 'السكان والديموغرافيا', unit: 'Pour mille', frequency: 'AI', source: 'HCP-CERED' },
  { id: 'I1600', arabicTitle: 'معدل الوفيات الخام', frenchTitle: 'Taux brut de mortalité', description: 'عدد الوفيات لكل ألف نسمة.', domain: 'السكان والديموغرافيا', unit: 'Pour mille', frequency: 'AI', source: 'HCP-CERED' },
  { id: 'I2790', arabicTitle: 'معدل التمدن', frenchTitle: "Taux d'urbanisation", description: 'حصة السكان المقيمين في الوسط الحضري.', domain: 'السكان والديموغرافيا', unit: '%', frequency: 'IR', source: 'Recensement général de la population et de l’habitat' },
  { id: 'I1481', arabicTitle: 'السكان حسب الفئات العمرية والجنس', frenchTitle: "Population selon les groupes d'âge et le sexe", description: 'توزيع السكان حسب العمر والجنس.', domain: 'الاقتصاد والتجارة', unit: 'Nombre', frequency: 'AS', source: 'Haut Commissariat au Plan' },
  { id: 'I2090', arabicTitle: 'الواردات حسب الموردين الرئيسيين', frenchTitle: 'Importations par principaux fournisseurs', description: 'قيمة الواردات حسب الموردين الرئيسيين.', domain: 'الاقتصاد والتجارة', unit: 'en millions de DH', frequency: 'AS', source: 'Office des changes' },
  { id: 'I2084', arabicTitle: 'الصادرات حسب الزبائن الرئيسيين', frenchTitle: 'Exportations par principaux clients', description: 'قيمة الصادرات حسب الزبائن الرئيسيين.', domain: 'الاقتصاد والتجارة', unit: 'en millions de DH', frequency: 'AS', source: 'Office des changes' },
  { id: 'I1887', arabicTitle: 'القيمة السوقية للأسهم المغربية حسب القطاع الاقتصادي', frenchTitle: "Capitalisation boursière des valeurs marocaines par secteur d'activité économique", description: 'القيمة السوقية للأسهم حسب النشاط الاقتصادي.', domain: 'المال والأسواق', unit: 'En millions de DH', frequency: 'AS', source: 'Bourse de Casablanca' },
  { id: 'I1886', arabicTitle: 'ميزانية بنك المغرب: الأصول', frenchTitle: 'Bilan de Bank Al-Maghrib (Actif)', description: 'الأصول ضمن ميزانية بنك المغرب.', domain: 'الاقتصاد والتجارة', unit: 'En millions de DH', frequency: 'AS', source: 'Bank Al-Maghrib' },
  { id: 'I1889', arabicTitle: 'ميزانية بنك المغرب: الخصوم', frenchTitle: 'Bilan de Bank Al-Maghrib (Passif)', description: 'الخصوم ضمن ميزانية بنك المغرب.', domain: 'الاقتصاد والتجارة', unit: 'En millions de DH', frequency: 'AS', source: 'Bank Al-Maghrib' },
  { id: 'I3328', arabicTitle: 'رقم المعاملات', frenchTitle: "Chiffre d'affaires", description: 'رقم المعاملات المسجل في القطاع الصناعي والتجاري.', domain: 'المال والأسواق', unit: 'En millions de DH', frequency: 'AS', source: 'Ministère de l’Industrie et du Commerce' },
  { id: 'I3331', arabicTitle: 'الصادرات', frenchTitle: 'Exportation', description: 'قيمة الصادرات المسجلة في القطاع الصناعي والتجاري.', domain: 'المال والأسواق', unit: 'En millions de DH', frequency: 'AS', source: 'Ministère de l’Industrie et du Commerce' },
  { id: 'I4217', arabicTitle: 'عدد السجناء', frenchTitle: 'Population Pénale', description: 'عدد الأشخاص الموجودين بالمؤسسات السجنية.', domain: 'العدالة والمجتمع', unit: 'NOMBRE', frequency: 'AS', source: 'Délégation Générale de l’Administration Pénitentiaire' },
  { id: 'I1493', arabicTitle: 'معدل الفقر', frenchTitle: 'Taux de pauvreté', description: 'نسبة السكان الذين يعيشون تحت عتبة الفقر.', domain: 'المجتمع', unit: 'POURCENTAGE', frequency: 'IR', source: 'Carte de pauvreté monétaire 2014' },
  { id: 'I3242', arabicTitle: 'عدم المساواة في مستوى المعيشة: معامل جيني', frenchTitle: 'Inégalité de vie : coefficient de Gini', description: 'مؤشر يقيس توزيع الدخل أو الثروة بين السكان.', domain: 'المجتمع', unit: '%', frequency: 'IR', source: 'HCP' },
  { id: 'I257', arabicTitle: 'عدد المستشفيات', frenchTitle: "Nombre d'hôpitaux", description: 'عدد المستشفيات العاملة في المغرب.', domain: 'الصحة', unit: 'NOMBRE', frequency: 'AS', source: 'Ministère de la Santé' },
  { id: 'I259', arabicTitle: 'الطاقة الاستيعابية للأسرة', frenchTitle: 'Capacité litière existante', description: 'عدد الأسرة الاستشفائية المتاحة.', domain: 'الصحة', unit: 'Nombre', frequency: 'AS', source: 'Ministère de la Santé et de la Protection sociale' },
  { id: 'I238', arabicTitle: 'عدد المراكز الصحية', frenchTitle: 'Nombre de centres de santé', description: 'عدد المراكز الصحية المتاحة.', domain: 'الصحة', unit: 'NOMBRE', frequency: 'AS', source: 'Ministère de la Santé et de la Protection sociale' },
  { id: 'I3210', arabicTitle: 'عدد تلاميذ التعليم الابتدائي العمومي', frenchTitle: "Nombre des élèves dans l'enseignement primaire public", description: 'عدد التلاميذ المسجلين في التعليم الابتدائي العمومي.', domain: 'التعليم والثقافة', unit: 'Nombre', frequency: 'AS', source: 'Ministère de l’Éducation nationale' },
  { id: 'I1762', arabicTitle: 'هيئة التدريس بالتعليم الابتدائي العمومي', frenchTitle: "Personnel enseignant de l'enseignement primaire public", description: 'عدد هيئة التدريس في التعليم الابتدائي العمومي.', domain: 'التعليم والثقافة', unit: 'NOMBRE', frequency: 'AS', source: 'Ministère de l’Éducation nationale' },
  { id: 'I1821', arabicTitle: 'ميزانية التعليم الوطني', frenchTitle: "Budget de l'éducation nationale (en millions de dh)", description: 'الاعتمادات المالية المرصودة لتشغيل وتطوير منظومة التعليم.', domain: 'التعليم والثقافة', unit: 'Millions de dh', frequency: 'AS', source: 'Ministère de l’Enseignement supérieur' },
  { id: 'I4002', arabicTitle: 'معدل البطالة حسب الوسط والشهادات', frenchTitle: 'Taux de chômage selon le Milieu, les diplômes', description: 'نسبة العاطلين حسب الوسط والشهادات.', domain: 'الشغل', unit: 'POURCENTAGE', frequency: 'AS', source: 'MAR_HCP Enquête nationale sur l’emploi' },
  { id: 'I4001', arabicTitle: 'معدل البطالة حسب الوسط والجنس والفئة العمرية', frenchTitle: 'Taux de chômage selon le Milieu, le sexe et le groupe d’âges', description: 'نسبة العاطلين من السكان النشيطين حسب الوسط والجنس والعمر.', domain: 'الشغل', unit: 'POURCENTAGE', frequency: 'AS', source: 'MAR_HCP Enquête nationale sur l’emploi' },
  { id: 'I40', arabicTitle: 'معدل النشاط الصافي', frenchTitle: 'Taux net d’activité', description: 'نسبة السكان النشيطين في سن العمل.', domain: 'السكان والديموغرافيا', unit: 'POURCENTAGE', frequency: 'AS', source: 'MAR_HCP Enquête nationale sur l’emploi' },
  { id: 'IMT_TXEMP_02', arabicTitle: 'معدل التشغيل حسب الأقاليم والوسط', frenchTitle: 'Taux d’emploi selon les Provinces/Préfectures et le Milieu', description: 'نسبة المشتغلين حسب الأقاليم والوسط.', domain: 'الشغل', unit: 'POURCENTAGE', frequency: 'AS', source: 'MAR_HCP Enquête nationale sur l’emploi' },
]

export const HCP_INDICATORS: IndicatorDefinition[] = definitions.map((definition) => ({ ...definition, apiUrl: `${HCP_BASE_URL}/${encodeURIComponent(definition.id)}` }))
export const HCP_INDICATORS_BY_ID = Object.fromEntries(HCP_INDICATORS.map((indicator) => [indicator.id, indicator])) as Record<string, IndicatorDefinition>
export function getIndicator(id: string) { return HCP_INDICATORS_BY_ID[id] }
export function isIndicatorId(id: string) { return /^I[A-Z0-9_]+$/.test(id) }
export { HCP_BASE_URL }
export const HCP_INDICATOR_IDS = HCP_INDICATORS.map((indicator) => indicator.id)
