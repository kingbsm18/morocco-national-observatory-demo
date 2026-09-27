import IndicatorDetailPage from '@/components/indicator-detail-page'

export default async function IndicatorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <IndicatorDetailPage id={id} />
}
