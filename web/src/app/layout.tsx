import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dash Pivot CND",
  description: "BI Central Norte — matriz pivotante",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
