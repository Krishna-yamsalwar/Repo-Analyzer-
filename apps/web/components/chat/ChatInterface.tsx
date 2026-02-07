'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { CodeBlock } from './CodeBlock';
import { FileReference } from './FileReference';
import { RiskAnalysis } from './RiskAnalysis';
import { cn } from '@/lib/utils';
import { chatApi } from '@/lib/api';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    citations?: Array<{ file: string; lines: string }>;
    risk?: { level: 'low' | 'medium' | 'high'; description: string };
    timestamp: Date;
}

interface ChatInterfaceProps {
    repoId?: string;
    repoName?: string;
}

export function ChatInterface({ repoId, repoName }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: `Welcome to Code Architecture Analyzer! 👋\n\nI'm ready to help you understand ${repoName || 'your repository'}. Ask me anything about:\n\n• Code structure and architecture\n• How specific functions work\n• Dependencies between modules\n• Best practices in the codebase`,
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Convert repoId string to number if provided
            const repoIdNum = repoId ? parseInt(repoId, 10) : undefined;
            const response = await chatApi.stream(input, repoIdNum);

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            // Process Server-Sent Events stream
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            let assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '',
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);

            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);

                        if (data === '[DONE]') {
                            break;
                        }

                        try {
                            const chunk = JSON.parse(data);

                            if (chunk.type === 'content') {
                                assistantMessage.content += chunk.content;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            } else if (chunk.type === 'citation') {
                                if (!assistantMessage.citations) {
                                    assistantMessage.citations = [];
                                }
                                assistantMessage.citations.push(chunk.citation);
                            } else if (chunk.type === 'risk') {
                                assistantMessage.risk = chunk.risk;
                            } else if (chunk.type === 'error') {
                                throw new Error(chunk.content);
                            }
                        } catch (e) {
                            console.error('Error parsing chunk:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Messages Area */}
            <div
                className="flex-1 overflow-y-auto overflow-x-hidden p-4 scroll-smooth"
                style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: 'rgba(155, 155, 155, 0.5) transparent'
                }}
                ref={scrollRef}
            >
                <div className="space-y-6 max-w-4xl mx-auto">
                    {messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                    ))}
                    {isLoading && <TypingIndicator />}
                    {/* Scroll anchor */}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="border-t border-border p-4">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                    <div className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about your codebase..."
                            disabled={isLoading}
                            className="flex-1 bg-secondary/50"
                        />
                        <Button type="submit" disabled={isLoading || !input.trim()}>
                            {isLoading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                        </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 text-center">
                        Code Architecture Analyzer uses your repository as the source of truth. All answers are cited.
                    </p>
                </form>
            </div>
        </div>
    );
}

function MessageBubble({ message }: { message: Message }) {
    const isUser = message.role === 'user';

    return (
        <div className={cn('flex gap-3 message-enter', isUser && 'flex-row-reverse')}>
            <Avatar className={cn('w-8 h-8', isUser ? 'bg-primary' : 'bg-secondary')}>
                <AvatarFallback>
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </AvatarFallback>
            </Avatar>

            <div className={cn('flex-1 space-y-2', isUser && 'text-right')}>
                <div
                    className={cn(
                        'inline-block p-4 rounded-2xl max-w-[85%] text-left',
                        isUser ? 'bg-primary text-primary-foreground' : 'glass'
                    )}
                >
                    <MessageContent content={message.content} />
                </div>

                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {message.citations.map((citation, idx) => (
                            <FileReference key={idx} file={citation.file} lines={citation.lines} />
                        ))}
                    </div>
                )}

                {/* Risk Analysis */}
                {message.risk && (
                    <RiskAnalysis level={message.risk.level} description={message.risk.description} />
                )}
            </div>
        </div>
    );
}

function MessageContent({ content }: { content: string }) {
    // Parse content for code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);

    return (
        <div className="prose prose-invert max-w-none">
            {parts.map((part, idx) => {
                if (part.startsWith('```')) {
                    const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
                    if (match) {
                        const [, language, code] = match;
                        return <CodeBlock key={idx} code={code.trim()} language={language || 'text'} />;
                    }
                }
                return (
                    <p key={idx} className="whitespace-pre-wrap mb-2 last:mb-0">
                        {part}
                    </p>
                );
            })}
        </div>
    );
}

function TypingIndicator() {
    return (
        <div className="flex gap-3">
            <Avatar className="w-8 h-8 bg-secondary">
                <AvatarFallback>
                    <Bot className="w-4 h-4" />
                </AvatarFallback>
            </Avatar>
            <div className="glass px-4 py-3 rounded-2xl">
                <div className="flex gap-1">
                    <span className="w-2 h-2 bg-muted-foreground rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-muted-foreground rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-muted-foreground rounded-full typing-dot" />
                </div>
            </div>
        </div>
    );
}
