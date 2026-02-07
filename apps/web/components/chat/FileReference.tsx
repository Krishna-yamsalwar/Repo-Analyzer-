import { FileCode, ExternalLink } from 'lucide-react';

interface FileReferenceProps {
    file: string;
    lines?: string;
}

export function FileReference({ file, lines }: FileReferenceProps) {
    return (
        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary/50 hover:bg-secondary rounded-lg text-xs font-mono transition-colors group">
            <FileCode className="w-3.5 h-3.5 text-primary" />
            <span className="text-foreground">{file}</span>
            {lines && <span className="text-muted-foreground">:{lines}</span>}
            <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </button>
    );
}
