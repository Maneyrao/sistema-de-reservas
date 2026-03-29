import type React from "react"
import type { Metadata } from "next"
import { Bebas_Neue, Manrope } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
})

const bebas = Bebas_Neue({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-bebas",
})

export const metadata: Metadata = {
  title: "Club Amsterdam | Reservas Online",
  description:
    "Reserva tu turno online en Club Amsterdam. Experiencia premium en cada corte.",
  icons: {
    icon: [
      {
        url: "/club-amsterdam-monogram.svg",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/club-amsterdam-monogram.svg",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/club-amsterdam-monogram.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/club-amsterdam-monogram.svg",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es">
      <body className={`${manrope.variable} ${bebas.variable} font-sans antialiased`}>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
