import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'المرصد الوطني للمؤشرات المغربية',
  description: 'مرصد وطني يتيح الوصول إلى أهم المؤشرات الاقتصادية والاجتماعية والتنموية للمغرب.',
  generator: 'v0.app',
  icons: {
    icon: [{ url: '/pdm-logo.jpg', type: 'image/jpeg' }],
    shortcut: '/pdm-logo.jpg',
    apple: '/pdm-logo.jpg',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ar" dir="rtl" data-scroll-behavior="smooth">
      <body className="antialiased">
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
