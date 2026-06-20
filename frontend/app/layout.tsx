import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicFlow AI — Navigate Public Services with Confidence",
  description:
    "AI-powered guidance for healthcare, benefits, and government services in India, the US, and Brazil.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
