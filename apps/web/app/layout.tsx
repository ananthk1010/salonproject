import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ABC-Salon — Phase 1 Jev Demo",
  description:
    "Interactive demo of Jev (TypeSafe AI) classifying salon customer messages, Phase 1 of the ABC-Salon project.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
