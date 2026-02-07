import Link from 'next/link';
import { Bot, Github, Zap, Brain, Code2, Shield } from 'lucide-react';

export default function HomePage() {
    return (
        <main className="min-h-screen">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                {/* Animated background */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-glow" />
                    <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '1s' }} />
                </div>

                <div className="container mx-auto px-4 py-20">
                    {/* Header */}
                    <nav className="flex items-center justify-between mb-20">
                        <div className="flex items-center gap-2">
                            <Bot className="w-8 h-8 text-primary" />
                            <span className="text-xl font-bold">Code Architecture Analyzer</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link
                                href="/login"
                                className="text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Sign In
                            </Link>
                            <Link
                                href="/register"
                                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                            >
                                Get Started
                            </Link>
                        </div>
                    </nav>

                    {/* Hero Content */}
                    <div className="text-center max-w-4xl mx-auto">
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 rounded-full text-sm text-primary mb-6">
                            <Zap className="w-4 h-4" />
                            Powered by Groq LPU - Ultra-fast inference
                        </div>

                        <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-foreground via-primary to-purple-400 bg-clip-text text-transparent">
                            Your AI-Powered
                            <br />
                            Code Companion
                        </h1>

                        <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
                            Deep repository intelligence with multi-agent reasoning.
                            Ask questions, understand codebases, and get cited answers in real-time.
                        </p>

                        <div className="flex items-center justify-center gap-4">
                            <Link
                                href="/register"
                                className="px-8 py-4 bg-primary text-primary-foreground rounded-xl font-semibold text-lg hover:opacity-90 transition-all hover:scale-105"
                            >
                                Start for Free
                            </Link>
                            <Link
                                href="https://github.com"
                                className="px-8 py-4 glass rounded-xl font-semibold text-lg hover:bg-secondary/50 transition-all flex items-center gap-2"
                            >
                                <Github className="w-5 h-5" />
                                View on GitHub
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <section className="container mx-auto px-4 py-20">
                <h2 className="text-3xl font-bold text-center mb-12">
                    Intelligent Code Understanding
                </h2>

                <div className="grid md:grid-cols-3 gap-8">
                    <FeatureCard
                        icon={<Brain className="w-8 h-8" />}
                        title="Multi-Agent Reasoning"
                        description="Planner, Retriever, Generator, and Verifier agents work together for accurate answers."
                    />
                    <FeatureCard
                        icon={<Code2 className="w-8 h-8" />}
                        title="AST-Powered Analysis"
                        description="Tree-sitter parsing understands code structure, not just text patterns."
                    />
                    <FeatureCard
                        icon={<Shield className="w-8 h-8" />}
                        title="Hallucination Detection"
                        description="Every response is verified against actual source code with risk analysis."
                    />
                </div>
            </section>

            {/* CTA Section */}
            <section className="container mx-auto px-4 py-20">
                <div className="glass rounded-2xl p-12 text-center">
                    <h2 className="text-3xl font-bold mb-4">Ready to explore your codebase?</h2>
                    <p className="text-muted-foreground mb-8">
                        Index your repository and start asking questions in natural language.
                    </p>
                    <Link
                        href="/register"
                        className="inline-block px-8 py-4 bg-primary text-primary-foreground rounded-xl font-semibold hover:opacity-90 transition-opacity"
                    >
                        Get Started Now
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className="container mx-auto px-4 py-8 border-t border-border">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <p>© 2026 Code Architecture Analyzer. All rights reserved.</p>
                    <div className="flex items-center gap-4">
                        <Link href="#" className="hover:text-foreground transition-colors">Privacy</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">Terms</Link>
                    </div>
                </div>
            </footer>
        </main>
    );
}

function FeatureCard({ icon, title, description }: {
    icon: React.ReactNode;
    title: string;
    description: string;
}) {
    return (
        <div className="glass rounded-xl p-6 hover:border-primary/50 transition-colors group">
            <div className="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                {icon}
            </div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-muted-foreground">{description}</p>
        </div>
    );
}
