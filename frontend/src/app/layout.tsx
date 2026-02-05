import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Foundever Proposal Engine",
  description: "RFP/RFI/Orals proposal generation and review",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 antialiased">
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-gray-800 px-6 py-4">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <h1 className="text-lg font-semibold tracking-tight">
                Foundever Proposal Engine
              </h1>
              <nav className="flex gap-6 text-sm text-gray-400">
                <a href="/" className="hover:text-white">Projects</a>
                <a href="/intake" className="hover:text-white">Intake</a>
                <a href="/review" className="hover:text-white">Review</a>
              </nav>
            </div>
          </header>
          <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
