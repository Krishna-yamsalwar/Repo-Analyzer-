'use client';

import { useState } from 'react';
import { Save, Key, User, Bell, Palette } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function SettingsPage() {
    const [groqApiKey, setGroqApiKey] = useState('');
    const [pineconeApiKey, setPineconeApiKey] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        // TODO: Save settings to backend
        await new Promise((r) => setTimeout(r, 1000));
        setIsSaving(false);
    };

    return (
        <div className="p-6 max-w-2xl">
            <h1 className="text-2xl font-bold mb-2">Settings</h1>
            <p className="text-muted-foreground mb-8">Manage your account and API configurations</p>

            {/* API Keys */}
            <section className="glass rounded-xl p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <Key className="w-5 h-5 text-primary" />
                    <h2 className="text-lg font-semibold">API Keys</h2>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">Groq API Key</label>
                        <Input
                            type="password"
                            value={groqApiKey}
                            onChange={(e) => setGroqApiKey(e.target.value)}
                            placeholder="gsk_..."
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                            Get your API key from{' '}
                            <a href="https://console.groq.com" target="_blank" rel="noopener" className="text-primary hover:underline">
                                console.groq.com
                            </a>
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Pinecone API Key</label>
                        <Input
                            type="password"
                            value={pineconeApiKey}
                            onChange={(e) => setPineconeApiKey(e.target.value)}
                            placeholder="..."
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                            Get your API key from{' '}
                            <a href="https://app.pinecone.io" target="_blank" rel="noopener" className="text-primary hover:underline">
                                app.pinecone.io
                            </a>
                        </p>
                    </div>
                </div>
            </section>

            {/* Profile */}
            <section className="glass rounded-xl p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <User className="w-5 h-5 text-primary" />
                    <h2 className="text-lg font-semibold">Profile</h2>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">Name</label>
                        <Input placeholder="Your name" defaultValue="User" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Email</label>
                        <Input type="email" placeholder="you@example.com" defaultValue="user@example.com" disabled />
                    </div>
                </div>
            </section>

            {/* Appearance */}
            <section className="glass rounded-xl p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <Palette className="w-5 h-5 text-primary" />
                    <h2 className="text-lg font-semibold">Appearance</h2>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium">Dark Mode</p>
                        <p className="text-sm text-muted-foreground">Use dark theme across the application</p>
                    </div>
                    <div className="w-12 h-6 bg-primary rounded-full relative cursor-pointer">
                        <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                    </div>
                </div>
            </section>

            {/* Save Button */}
            <Button onClick={handleSave} disabled={isSaving} className="w-full">
                {isSaving ? (
                    'Saving...'
                ) : (
                    <>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                    </>
                )}
            </Button>
        </div>
    );
}
