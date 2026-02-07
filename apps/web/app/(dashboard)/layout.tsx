'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Bot,
    MessageSquare,
    FolderGit2,
    FolderTree,
    Settings,
    LogOut,
    Menu,
    X,
    ChevronDown
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

const navigation = [
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Repositories', href: '/repos', icon: FolderGit2 },
    { name: 'Visualizer', href: '/visualizer', icon: FolderTree },
    { name: 'Settings', href: '/settings', icon: Settings },
];

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="flex h-screen">
            {/* Sidebar - Desktop */}
            <aside className="hidden md:flex md:w-64 md:flex-col border-r border-border">
                <div className="flex flex-col flex-1">
                    {/* Logo */}
                    <div className="flex items-center gap-2 h-16 px-6 border-b border-border">
                        <Bot className="w-8 h-8 text-primary" />
                        <span className="text-lg font-bold">Code Architecture Analyzer</span>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-3 py-4 space-y-1">
                        {navigation.map((item) => {
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={cn(
                                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                                        isActive
                                            ? 'bg-primary text-primary-foreground'
                                            : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                                    )}
                                >
                                    <item.icon className="w-5 h-5" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Menu */}
                    <div className="p-3 border-t border-border">
                        <div className="flex items-center gap-3 px-3 py-2">
                            <Avatar className="w-8 h-8">
                                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                                    U
                                </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">User</p>
                                <p className="text-xs text-muted-foreground truncate">user@example.com</p>
                            </div>
                            <Button variant="ghost" size="icon" className="shrink-0">
                                <LogOut className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Mobile Sidebar */}
            <div className={cn(
                'fixed inset-0 z-50 md:hidden transition-opacity',
                sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
            )}>
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
                <aside className={cn(
                    'absolute left-0 top-0 bottom-0 w-64 bg-background border-r border-border transition-transform',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}>
                    <div className="flex items-center justify-between h-16 px-6 border-b border-border">
                        <div className="flex items-center gap-2">
                            <Bot className="w-8 h-8 text-primary" />
                            <span className="text-lg font-bold">Code Architecture Analyzer</span>
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
                            <X className="w-5 h-5" />
                        </Button>
                    </div>
                    <nav className="px-3 py-4 space-y-1">
                        {navigation.map((item) => {
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    onClick={() => setSidebarOpen(false)}
                                    className={cn(
                                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                                        isActive
                                            ? 'bg-primary text-primary-foreground'
                                            : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                                    )}
                                >
                                    <item.icon className="w-5 h-5" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>
                </aside>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Mobile Header */}
                <header className="md:hidden flex items-center gap-4 h-16 px-4 border-b border-border">
                    <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
                        <Menu className="w-5 h-5" />
                    </Button>
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-primary" />
                        <span className="font-bold">Code Architecture Analyzer</span>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
}
