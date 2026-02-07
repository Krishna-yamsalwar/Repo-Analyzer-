import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RiskAnalysisProps {
    level: 'low' | 'medium' | 'high';
    description: string;
}

export function RiskAnalysis({ level, description }: RiskAnalysisProps) {
    const config = {
        low: {
            icon: CheckCircle,
            bg: 'bg-green-500/10 border-green-500/20',
            text: 'text-green-500',
            label: 'Low Risk',
        },
        medium: {
            icon: AlertCircle,
            bg: 'bg-yellow-500/10 border-yellow-500/20',
            text: 'text-yellow-500',
            label: 'Medium Risk',
        },
        high: {
            icon: AlertTriangle,
            bg: 'bg-red-500/10 border-red-500/20',
            text: 'text-red-500',
            label: 'High Risk',
        },
    };

    const { icon: Icon, bg, text, label } = config[level];

    return (
        <div className={cn('flex items-start gap-2 p-3 rounded-lg border', bg)}>
            <Icon className={cn('w-4 h-4 mt-0.5 shrink-0', text)} />
            <div className="flex-1 min-w-0">
                <p className={cn('text-xs font-medium', text)}>[RISK ANALYSIS] {label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
            </div>
        </div>
    );
}
