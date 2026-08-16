import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Middle East Geopolitical Intelligence Platform",
  description: "Evidence-led geopolitical intelligence and monitoring platform",
  icons: {
    icon: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col bg-[#06080f] text-slate-100 font-sans">{children}</body>
    </html>
  );
}
