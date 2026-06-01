import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SecureTheCloud AI Control Plane",
  description: "Governed AI access, policy, and evidence lab platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
