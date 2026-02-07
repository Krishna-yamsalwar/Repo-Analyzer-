'use client';

import { useState, useEffect } from 'react';
import { ChatInterface } from '@/components/chat';
import { reposApi } from '@/lib/api';

interface Repository {
    id: number;
    name: string;
    status: string;
}

export default function ChatPage() {
    const [repos, setRepos] = useState<Repository[]>([]);
    const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);

    useEffect(() => {
        loadRepositories();
    }, []);

    const loadRepositories = async () => {
        try {
            const response = await reposApi.getAll();
            if (response.ok) {
                const data = await response.json();
                const readyRepos = data.filter((r: Repository) => r.status === 'ready');
                setRepos(readyRepos);
                if (readyRepos.length > 0) {
                    setSelectedRepo(readyRepos[0]);
                }
            }
        } catch (error) {
            console.error('Failed to load repositories:', error);
        }
    };

    if (repos.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-muted-foreground mb-2">No indexed repositories found</p>
                    <p className="text-sm text-muted-foreground">Add and index a repository first</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {repos.length > 1 && (
                <div className="p-4 border-b shrink-0">
                    <select
                        className="bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
                        value={selectedRepo?.id || ''}
                        onChange={(e) => {
                            const repo = repos.find(r => r.id === Number(e.target.value));
                            if (repo) setSelectedRepo(repo);
                        }}
                    >
                        {repos.map((repo) => (
                            <option key={repo.id} value={repo.id}>
                                {repo.name}
                            </option>
                        ))}
                    </select>
                </div>
            )}
            <div className="flex-1 min-h-0">
                {selectedRepo && (
                    <ChatInterface
                        repoId={selectedRepo.id.toString()}
                        repoName={selectedRepo.name}
                    />
                )}
            </div>
        </div>
    );
}
