import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gez.AI Studio",
  description: "Advanced Ge'ez Philology & Translation Workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}