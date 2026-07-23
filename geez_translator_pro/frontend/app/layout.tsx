import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Gez.AI Studio',
  description: 'Ecclesiastical Ge\'ez Translation Workspace',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}