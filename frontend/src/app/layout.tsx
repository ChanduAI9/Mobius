import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MOBIUS — Personal AI Operating System",
  description: "Your intelligent partner for engineering, startups, and life.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
