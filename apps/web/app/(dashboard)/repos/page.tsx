'use client';

import { useState, useEffect } from 'react';
import { Plus, FolderGit2, Clock, Loader2, Trash2, RefreshCw, FolderOpen, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { reposApi } from '@/lib/api';

interface Repository {
    id: number;
    name: string;
    description?: string;
    url?: string;
    local_path?: string;
    status: string;
    indexed_files: number;
    total_files: number;
    languages?: Record<string, number>;
    created_at: string;
}

export default function ReposPage() {
    const [repos, setRepos] = useState<Repository[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newRepoName, setNewRepoName] = useState('');
    const [newRepoUrl, setNewRepoUrl] = useState('');
    const [newRepoPath, setNewRepoPath] = useState('');
    const [error, setError] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    useEffect(() => {
        fetchRepos();
    }, []);

    const fetchRepos = async () => {
        try {
            const response = await reposApi.getAll();
            if (response.ok) {
                const data = await response.json();
                setRepos(data);
            } else if (response.status === 401) {
                // Unauthorized - redirect to login
                console.error('Unauthorized - redirecting to login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
            } else {
                console.error('Failed to fetch repos:', response.status);
            }
        } catch (error) {
            console.error('Failed to fetch repos:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const createRepo = async () => {
        if (!newRepoName) return;
        setError('');
        setIsCreating(true);

        try {
            const response = await reposApi.create(
                newRepoName,
                newRepoUrl || undefined,
                undefined,
                newRepoPath || undefined
            );

            if (response.ok) {
                const newRepo = await response.json();
                setRepos([newRepo, ...repos]);
                setShowCreateModal(false);
                setNewRepoName('');
                setNewRepoUrl('');
                setNewRepoPath('');
            } else {
                const data = await response.json();
                setError(data.detail || 'Failed to create repository');
            }
        } catch (error) {
            console.error('Failed to create repo:', error);
            setError('Network error. Please try again.');
        } finally {
            setIsCreating(false);
        }
    };

    const deleteRepo = async (repoId: number) => {
        if (!confirm('Are you sure you want to delete this repository?')) return;

        setDeletingId(repoId);
        try {
            const response = await reposApi.delete(repoId);
            if (response.ok) {
                setRepos(repos.filter(r => r.id !== repoId));
            } else {
                const data = await response.json();
                alert(data.detail || 'Failed to delete repository');
            }
        } catch (error) {
            console.error('Failed to delete repo:', error);
            alert('Network error. Please try again.');
        } finally {
            setDeletingId(null);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ready': return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'cloning': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
            case 'indexing': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
            case 'error': return 'bg-red-500/10 text-red-500 border-red-500/20';
            default: return 'bg-muted text-muted-foreground border-border';
        }
    };

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold">Repositories</h1>
                    <p className="text-muted-foreground">Manage your indexed codebases</p>
                </div>
                <Button onClick={() => setShowCreateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Repository
                </Button>
            </div>

            {/* Repository Grid */}
            {isLoading ? (
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                </div>
            ) : repos.length === 0 ? (
                <div className="glass rounded-xl p-12 text-center">
                    <FolderGit2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No repositories yet</h3>
                    <p className="text-muted-foreground mb-6">
                        Add your first repository to start asking questions about your code.
                    </p>
                    <Button onClick={() => setShowCreateModal(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Repository
                    </Button>
                </div>
            ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {repos.map((repo) => (
                        <div key={repo.id} className="glass rounded-xl p-5 hover:border-primary/50 transition-colors group">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                                        <FolderGit2 className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{repo.name}</h3>
                                        <span className={`inline-block px-2 py-0.5 text-xs rounded-full border ${getStatusColor(repo.status)}`}>
                                            {repo.status}
                                        </span>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={() => deleteRepo(repo.id)}
                                    disabled={deletingId === repo.id}
                                >
                                    {deletingId === repo.id ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Trash2 className="w-4 h-4" />
                                    )}
                                </Button>
                            </div>

                            {repo.description && (
                                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                                    {repo.description}
                                </p>
                            )}

                            {repo.local_path && (
                                <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1 truncate">
                                    <FolderOpen className="w-3 h-3 shrink-0" />
                                    <span className="truncate">{repo.local_path}</span>
                                </p>
                            )}

                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {new Date(repo.created_at).toLocaleDateString()}
                                </span>
                                <span>{repo.indexed_files}/{repo.total_files} files</span>
                            </div>

                            {repo.languages && Object.keys(repo.languages).length > 0 && (
                                <div className="flex gap-2 mt-3 flex-wrap">
                                    {Object.entries(repo.languages).slice(0, 3).map(([lang, count]) => (
                                        <span key={lang} className="text-xs bg-secondary px-2 py-1 rounded">
                                            {lang}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="glass rounded-2xl p-6 w-full max-w-md mx-4">
                        <h2 className="text-xl font-bold mb-4">Add Repository</h2>

                        {error && (
                            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-destructive text-sm">
                                <AlertCircle className="w-4 h-4 shrink-0" />
                                {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Repository Name *</label>
                                <Input
                                    value={newRepoName}
                                    onChange={(e) => setNewRepoName(e.target.value)}
                                    placeholder="my-awesome-project"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Git URL</label>
                                <Input
                                    value={newRepoUrl}
                                    onChange={(e) => setNewRepoUrl(e.target.value)}
                                    placeholder="https://github.com/user/repo"
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                    Repository will be cloned automatically
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Local Path (optional)</label>
                                <Input
                                    value={newRepoPath}
                                    onChange={(e) => setNewRepoPath(e.target.value)}
                                    placeholder="D:/projects/my-repo"
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                    Use local path if repository is already on your machine
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => {
                                    setShowCreateModal(false);
                                    setError('');
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                className="flex-1"
                                onClick={createRepo}
                                disabled={!newRepoName || isCreating}
                            >
                                {isCreating ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    'Create'
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
