import type { Metadata } from "next";
import Image from "next/image";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import Providers from "./providers";

const bodyFont = Inter({
  variable: "--font-body",
  subsets: ["latin"],
});

const headingFont = Playfair_Display({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["500", "600"],
});

const monoFont = Inter({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NEO Proposal Agent",
  description: "IA para generación de propuestas comerciales",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${bodyFont.variable} ${headingFont.variable} ${monoFont.variable} antialiased`}
      >
        <Providers>
          {children}
          <div className="neo-anniversary-badge" aria-hidden="true">
            <Image src="/logos/neo-25.svg" alt="NEO 25 años" width={92} height={92} />
          </div>
        </Providers>
      </body>
    </html>
  );
}
