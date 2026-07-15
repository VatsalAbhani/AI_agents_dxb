import type { Metadata } from "next";
import { Geist, IBM_Plex_Mono } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-geist-mono",
  weight: ["400", "500"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Leadcode Guard — Approvals",
  description:
    "Every AI draft, reviewed by a human before it sends. The Leadcode Guard approval dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
          <div className="mx-auto flex h-14 w-full max-w-2xl items-center gap-3 px-4">
            <span aria-hidden className="inline-block size-3.5 bg-primary" />
            <span className="font-mono text-xs font-medium tracking-[0.18em]">
              LEADCODE GUARD
            </span>
            <span className="font-mono text-xs tracking-[0.18em] text-muted-foreground">
              · APPROVALS
            </span>
            <span className="ml-auto font-mono text-[10px] tracking-widest text-muted-foreground">
              PILOT
            </span>
          </div>
        </header>
        {children}
        <Toaster position="bottom-center" richColors />
      </body>
    </html>
  );
}
