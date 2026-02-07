import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Code Architecture Analyzer - Repository Intelligence',
    description: 'Multi-agent RAG system for deep repository understanding',
    keywords: ['AI', 'repository', 'code analysis', 'RAG', 'chat'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.className} antialiased`}>
                <div className="min-h-screen gradient-bg">
                    {children}
                </div>
            </body>
        </html>
    );
}
