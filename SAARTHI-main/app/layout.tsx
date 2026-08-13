import "./globals.css";
import type { Metadata } from "next";
// import "mapbox-gl/dist/mapbox-gl.css";

export const metadata: Metadata = {
  title: "Saarthi",
  description: "Saarthi agri logistics and ML platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}