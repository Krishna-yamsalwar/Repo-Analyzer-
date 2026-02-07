'use client';

import { useState, useEffect } from 'react';
import { FolderTree, ChevronRight, ChevronDown, File, Folder, RefreshCw, Loader2, Search, FileCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { reposApi } from '@/lib/api';
import { cn } from '@/lib/utils';

interface TreeNode {
    name: string;
    type: 'file' | 'folder';
    path: string;
    children?: TreeNode[];
    size?: number;
    language?: string;
}

interface Repository {
    id: number;
    name: string;
}

// File type colors
const languageColors: Record<string, string> = {
    typescript: 'text-blue-400',
    javascript: 'text-yellow-400',
    python: 'text-green-400',
    rust: 'text-orange-400',
    go: 'text-cyan-400',
    java: 'text-red-400',
    css: 'text-pink-400',
    html: 'text-orange-300',
    json: 'text-yellow-300',
    markdown: 'text-gray-400',
};

function getLanguageFromFile(filename: string | undefined): string {
    if (!filename) return 'text';

    const ext = filename.split('.').pop()?.toLowerCase();
    const extMap: Record<string, string> = {
        ts: 'typescript',
        tsx: 'typescript',
        js: 'javascript',
        jsx: 'javascript',
        py: 'python',
        rs: 'rust',
        go: 'go',
        java: 'java',
        css: 'css',
        html: 'html',
        json: 'json',
        md: 'markdown',
    };
    return extMap[ext || ''] || 'text';
}

function TreeNodeComponent({ node, depth = 0, searchTerm = '' }: { node: TreeNode; depth?: number; searchTerm?: string }) {
    const [isOpen, setIsOpen] = useState(depth < 2);
    const isFolder = node.type === 'folder';
    const language = getLanguageFromFile(node.name);
    const colorClass = languageColors[language] || 'text-muted-foreground';

    // Check if matches search
    const matchesSearch = searchTerm
        ? node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        node.path.toLowerCase().includes(searchTerm.toLowerCase())
        : true;

    const hasMatchingChildren = node.children?.some(
        (child) =>
            child.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            child.path.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (searchTerm && !matchesSearch && !hasMatchingChildren) {
        return null;
    }

    return (
        <div className="select-none">
            <div
                className={cn(
                    'flex items-center gap-2 py-1 px-2 rounded hover:bg-secondary/50 cursor-pointer transition-colors',
                    matchesSearch && searchTerm && 'bg-primary/20'
                )}
                style={{ paddingLeft: `${depth * 16 + 8}px` }}
                onClick={() => isFolder && setIsOpen(!isOpen)}
            >
                {isFolder ? (
                    <>
                        {isOpen ? (
                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        ) : (
                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                        )}
                        <Folder className="w-4 h-4 text-yellow-500" />
                    </>
                ) : (
                    <>
                        <span className="w-4" />
                        <FileCode className={cn('w-4 h-4', colorClass)} />
                    </>
                )}
                <span className={cn('text-sm', matchesSearch && searchTerm && 'font-medium text-primary')}>
                    {node.name}
                </span>
                {node.size && (
                    <span className="text-xs text-muted-foreground ml-auto">
                        {(node.size / 1024).toFixed(1)}KB
                    </span>
                )}
            </div>
            {isFolder && isOpen && node.children && (
                <div>
                    {node.children.map((child, idx) => (
                        <TreeNodeComponent key={`${child.path}-${idx}`} node={child} depth={depth + 1} searchTerm={searchTerm} />
                    ))}
                </div>
            )}
        </div>
    );
}

// Demo tree structure
const demoTree: TreeNode = {
    name: 'repopilot-ai',
    type: 'folder',
    path: '/',
    children: [
        {
            name: 'apps',
            type: 'folder',
            path: '/apps',
            children: [
                {
                    name: 'api',
                    type: 'folder',
                    path: '/apps/api',
                    children: [
                        { name: 'main.py', type: 'file', path: '/apps/api/main.py', size: 2048 },
                        { name: 'requirements.txt', type: 'file', path: '/apps/api/requirements.txt', size: 512 },
                        {
                            name: 'app',
                            type: 'folder',
                            path: '/apps/api/app',
                            children: [
                                { name: '__init__.py', type: 'file', path: '/apps/api/app/__init__.py', size: 128 },
                                {
                                    name: 'routers',
                                    type: 'folder',
                                    path: '/apps/api/app/routers',
                                    children: [
                                        { name: 'auth.py', type: 'file', path: '/apps/api/app/routers/auth.py', size: 3072 },
                                        { name: 'chat.py', type: 'file', path: '/apps/api/app/routers/chat.py', size: 4096 },
                                        { name: 'repos.py', type: 'file', path: '/apps/api/app/routers/repos.py', size: 2560 },
                                    ],
                                },
                                {
                                    name: 'core',
                                    type: 'folder',
                                    path: '/apps/api/app/core',
                                    children: [
                                        { name: 'config.py', type: 'file', path: '/apps/api/app/core/config.py', size: 1024 },
                                        { name: 'database.py', type: 'file', path: '/apps/api/app/core/database.py', size: 1536 },
                                        { name: 'security.py', type: 'file', path: '/apps/api/app/core/security.py', size: 2048 },
                                    ],
                                },
                            ],
                        },
                    ],
                },
                {
                    name: 'web',
                    type: 'folder',
                    path: '/apps/web',
                    children: [
                        { name: 'package.json', type: 'file', path: '/apps/web/package.json', size: 1024 },
                        { name: 'next.config.ts', type: 'file', path: '/apps/web/next.config.ts', size: 256 },
                        {
                            name: 'app',
                            type: 'folder',
                            path: '/apps/web/app',
                            children: [
                                { name: 'layout.tsx', type: 'file', path: '/apps/web/app/layout.tsx', size: 2048 },
                                { name: 'page.tsx', type: 'file', path: '/apps/web/app/page.tsx', size: 3072 },
                                { name: 'globals.css', type: 'file', path: '/apps/web/app/globals.css', size: 4096 },
                            ],
                        },
                        {
                            name: 'components',
                            type: 'folder',
                            path: '/apps/web/components',
                            children: [
                                {
                                    name: 'ui',
                                    type: 'folder',
                                    path: '/apps/web/components/ui',
                                    children: [
                                        { name: 'button.tsx', type: 'file', path: '/apps/web/components/ui/button.tsx', size: 1536 },
                                        { name: 'input.tsx', type: 'file', path: '/apps/web/components/ui/input.tsx', size: 1024 },
                                    ],
                                },
                                {
                                    name: 'chat',
                                    type: 'folder',
                                    path: '/apps/web/components/chat',
                                    children: [
                                        { name: 'ChatInterface.tsx', type: 'file', path: '/apps/web/components/chat/ChatInterface.tsx', size: 8192 },
                                        { name: 'CodeBlock.tsx', type: 'file', path: '/apps/web/components/chat/CodeBlock.tsx', size: 2048 },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        { name: 'package.json', type: 'file', path: '/package.json', size: 768 },
        { name: 'turbo.json', type: 'file', path: '/turbo.json', size: 512 },
        { name: 'README.md', type: 'file', path: '/README.md', size: 4096 },
    ],
};

export default function VisualizerPage() {
    const [repos, setRepos] = useState<Repository[]>([]);
    const [selectedRepo, setSelectedRepo] = useState<number | null>(null);
    const [treeData, setTreeData] = useState<TreeNode | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchRepos();
    }, []);

    useEffect(() => {
        if (selectedRepo) {
            loadRepoStructure(selectedRepo);
        }
    }, [selectedRepo]);

    const fetchRepos = async () => {
        try {
            const response = await reposApi.getAll();
            if (response.ok) {
                const data = await response.json();
                setRepos(data);
                if (data.length > 0) {
                    setSelectedRepo(data[0].id);
                    // Load real structure for first repo
                    await loadRepoStructure(data[0].id);
                }
            }
        } catch (error) {
            console.error('Failed to fetch repos:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const loadRepoStructure = async (repoId: number) => {
        setIsLoading(true);
        try {
            const response = await reposApi.getStructure(repoId);
            if (response.ok) {
                const data = await response.json();
                // API returns {repository, total_files, tree}, extract tree
                setTreeData(data.tree || null);
            } else {
                console.error('Failed to load structure');
                setTreeData(null);
            }
        } catch (error) {
            console.error('Error loading repo structure:', error);
            setTreeData(null);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefresh = async () => {
        if (!selectedRepo) return;
        await loadRepoStructure(selectedRepo);
    };

    // Count files/folders
    const countNodes = (node: TreeNode): { files: number; folders: number } => {
        if (node.type === 'file') return { files: 1, folders: 0 };
        let files = 0;
        let folders = 1;
        node.children?.forEach((child) => {
            const counts = countNodes(child);
            files += counts.files;
            folders += counts.folders;
        });
        return { files, folders };
    };

    const stats = treeData ? countNodes(treeData) : { files: 0, folders: 0 };

    return (
        <div className="p-6 h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <FolderTree className="w-6 h-6 text-primary" />
                        Folder Structure
                    </h1>
                    <p className="text-muted-foreground">Visualize and explore your repository structure</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        className="bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
                        value={selectedRepo || ''}
                        onChange={(e) => setSelectedRepo(Number(e.target.value))}
                    >
                        {repos.map((repo) => (
                            <option key={repo.id} value={repo.id}>
                                {repo.name}
                            </option>
                        ))}
                    </select>
                    <Button variant="outline" size="icon" onClick={handleRefresh} disabled={isLoading}>
                        <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
                    </Button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="glass rounded-xl p-4">
                    <div className="text-2xl font-bold text-primary">{stats.files}</div>
                    <div className="text-sm text-muted-foreground">Files</div>
                </div>
                <div className="glass rounded-xl p-4">
                    <div className="text-2xl font-bold text-yellow-500">{stats.folders}</div>
                    <div className="text-sm text-muted-foreground">Folders</div>
                </div>
                <div className="glass rounded-xl p-4">
                    <div className="text-2xl font-bold text-green-500">
                        {((treeData?.children?.length || 0) > 0 ? 'Ready' : 'Empty')}
                    </div>
                    <div className="text-sm text-muted-foreground">Status</div>
                </div>
            </div>

            {/* Search */}
            <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                    placeholder="Search files and folders..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                />
            </div>

            {/* Tree View */}
            <div className="flex-1 glass rounded-xl overflow-hidden">
                <div className="h-full overflow-auto p-4">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-64">
                            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : treeData ? (
                        <TreeNodeComponent node={treeData} searchTerm={searchTerm} />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                            <FolderTree className="w-12 h-12 mb-4" />
                            <p>No repository selected or structure unavailable</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                    <FileCode className="w-3 h-3 text-blue-400" /> TypeScript
                </div>
                <div className="flex items-center gap-1">
                    <FileCode className="w-3 h-3 text-yellow-400" /> JavaScript
                </div>
                <div className="flex items-center gap-1">
                    <FileCode className="w-3 h-3 text-green-400" /> Python
                </div>
                <div className="flex items-center gap-1">
                    <FileCode className="w-3 h-3 text-pink-400" /> CSS
                </div>
                <div className="flex items-center gap-1">
                    <Folder className="w-3 h-3 text-yellow-500" /> Folder
                </div>
            </div>
        </div>
    );
}
