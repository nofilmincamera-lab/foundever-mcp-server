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
      <body className="bg-fe-midnight text-white antialiased font-fe-secondary">
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-fe-indigo/20 px-6 py-4">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <h1 className="text-lg font-bold tracking-tight font-fe-primary">
                Foundever Proposal Engine
              </h1>
              <nav className="flex gap-6 text-sm text-fe-light-grey/70">
                <a href="/" className="hover:text-fe-indigo transition-colors">Projects</a>
                <a href="/intake" className="hover:text-fe-indigo transition-colors">Intake</a>
                <a href="/review" className="hover:text-fe-indigo transition-colors">Review</a>
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
