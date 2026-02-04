import React, { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    Brain,
    ChevronDown,
    ChevronRight,
    Terminal,
    CheckCircle2,
    Clock,
    Search,
    AlertCircle,
    Loader2,
    Activity
} from 'lucide-react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';

// --- Types ---

interface LogEntry {
    type: 'thought' | 'tool' | 'lifecycle' | 'error' | 'info';
    timestamp: string;
    agent: string;
    message: string;
    content: string;
    // New fields from backend refactor
    tool_name?: string;
    status?: 'start' | 'end' | 'error';
    args?: any;
}

interface LogViewerProps {
    sessionId: string | null;
    initialLogs?: (string | LogEntry)[];
    isProcessing?: boolean;
}

// --- Helper Components ---

const StatusIcon = ({ type, isRunning }: { type: LogEntry['type'], isRunning?: boolean }) => {
    if (isRunning) return <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />;

    switch (type) {
        case 'thought': return <Brain className="w-4 h-4 text-purple-400" />;
        case 'tool': return <Search className="w-4 h-4 text-blue-400" />;
        case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
        case 'lifecycle': return <Activity className="w-4 h-4 text-emerald-400" />;
        default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
};

const ReasoningStep = ({
    log,
    previousLog
}: {
    log: LogEntry,
    previousLog?: LogEntry
}) => {
    // Determine if this is a "Thought Block" (long reasoning) or a "Action" (quick tool use)
    const isThought = log.type === 'thought';
    const isTool = log.type === 'tool';
    const [isOpen, setIsOpen] = useState(false);

    // Auto-expand errors or active thoughts if desired
    // For OpenAI style, thoughts are usually collapsed by default ("Thinking...")

    const timeDisplay = log.timestamp ? log.timestamp.split('.')[0] : '';

    return (
        <div className="group border-l-2 border-white/5 pl-4 ml-2 relative py-2">
            {/* Timeline Dot */}
            <div className={clsx(
                "absolute -left-[5px] top-3 w-2.5 h-2.5 rounded-full border-2 border-[#111]",
                isThought ? "bg-purple-500/50" :
                    isTool ? "bg-blue-500/50" :
                        log.type === 'error' ? "bg-red-500" : "bg-gray-600"
            )} />

            {/* Header / Summary Line */}
            <div
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-start gap-3 cursor-pointer select-none"
            >
                <div className="mt-0.5 opacity-70 group-hover:opacity-100 transition-opacity">
                    <StatusIcon type={log.type} />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-mono text-white/40 uppercase tracking-wider">
                            {log.agent}
                        </span>
                        <span className="text-xs text-white/20">•</span>
                        <span className="text-xs font-mono text-white/20">
                            {timeDisplay}
                        </span>
                    </div>

                    <div className={clsx(
                        "text-sm font-medium leading-relaxed truncate pr-4",
                        isThought ? "text-purple-200" :
                            isTool ? "text-blue-200" :
                                "text-gray-300"
                    )}>
                        {isThought ? "Reasoning Process..." :
                            isTool ? `Running ${log.tool_name || 'Tool'}...` :
                                log.content}
                    </div>
                </div>

                <div className="text-white/20 group-hover:text-white/60 transition-colors">
                    {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="mt-3 bg-white/5 rounded-lg border border-white/5 overflow-hidden">
                            {isTool && log.args ? (
                                <div className="p-3 bg-black/20 font-mono text-xs text-blue-300/80 break-all whitespace-pre-wrap">
                                    {/* Try to pretty print args if they are an object */}
                                    {typeof log.args === 'object' ? JSON.stringify(log.args, null, 2) : log.content}
                                </div>
                            ) : (
                                <div className="p-4 text-sm text-gray-300 leading-relaxed font-sans prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-black/30 prose-pre:border prose-pre:border-white/10">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                    >
                                        {log.content}
                                    </ReactMarkdown>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};


const LogViewer: React.FC<LogViewerProps> = ({ sessionId, initialLogs = [], isProcessing = false }) => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isExpanded, setIsExpanded] = useState(true); // Default to expanded for visibility
    const scrollRef = useRef<HTMLDivElement>(null);

    const tryParseLog = (logItem: any): LogEntry => {
        if (typeof logItem === 'object' && logItem !== null && 'type' in logItem) return logItem;
        if (typeof logItem === 'string') {
            try {
                const parsed = JSON.parse(logItem);
                if (parsed && typeof parsed === 'object' && 'type' in parsed) return parsed;
            } catch (e) { }
        }

        // Legacy/Fallback
        const logStr = String(logItem);
        let type: LogEntry['type'] = 'info';
        if (logStr.includes("Insight:")) type = 'thought';
        if (logStr.includes("Tool Usage:")) type = 'tool';
        if (logStr.includes("ERROR")) type = 'error';

        return {
            type,
            timestamp: new Date().toLocaleTimeString(),
            agent: "System",
            message: logStr,
            content: logStr.replace("Insight:", "").replace("Tool Usage:", "").trim() || logStr
        };
    };

    useEffect(() => {
        if (initialLogs.length > 0) {
            setLogs(initialLogs.map(tryParseLog));
        }
    }, [initialLogs]);

    // SSE Connection
    useEffect(() => {
        if (!isProcessing || !sessionId) return;

        const eventSource = new EventSource(`${API_BASE_URL}/analysis/${sessionId}/stream`);
        eventSource.onmessage = (event) => {
            setLogs(prev => [...prev, tryParseLog(event.data)]);
        };
        eventSource.onerror = () => eventSource.close();
        return () => eventSource.close();
    }, [sessionId, isProcessing]);

    // Auto-scroll logic
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs.length]);

    // Filter out boring logs if needed, or group
    // For now, let's just show them all but styled beautifully

    return (
        <div className="mt-8 mb-12">
            <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" />
                Reasoning Engine
                {isProcessing && <span className="flex h-2 w-2 rounded-full bg-purple-500 animate-pulse ml-2" />}
            </h3>

            <div className="bg-[#0A0A0A] rounded-xl border border-white/10 overflow-hidden shadow-2xl">
                {/* Header Control */}
                <div
                    className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/5 cursor-pointer hover:bg-white/10 transition-colors"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <div className="flex items-center gap-2 text-sm text-white/60">
                        <Terminal className="w-4 h-4" />
                        <span>Analysis Trace</span>
                        <span className="bg-white/10 px-2 py-0.5 rounded-full text-xs text-white/40">
                            {logs.length} steps
                        </span>
                    </div>
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-white/40" /> : <ChevronRight className="w-4 h-4 text-white/40" />}
                </div>

                {/* Log Stream */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                        >
                            <div
                                ref={scrollRef}
                                className="max-h-[500px] overflow-y-auto p-4 space-y-1 font-sans"
                            >
                                {logs.length === 0 ? (
                                    <div className="text-center py-12 text-white/20 text-sm">
                                        Waiting for agent activity...
                                    </div>
                                ) : (
                                    logs.map((log, idx) => (
                                        <ReasoningStep
                                            key={idx}
                                            log={log}
                                            previousLog={logs[idx - 1]}
                                        />
                                    ))
                                )}

                                {isProcessing && (
                                    <div className="pl-6 ml-2 border-l-2 border-dashed border-white/10 py-3 flex items-center gap-3 animate-pulse">
                                        <div className="w-2 h-2 rounded-full bg-purple-500" />
                                        <span className="text-sm text-white/40 italic">Thinking...</span>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

// Assuming API_BASE_URL is defined in parent or global context. 
// If it was imported, we need to keep the import. 
// Based on previous file, it seemed to rely on a global or was missing.
// I will assume standard Vite/Env setup or local declaration.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default LogViewer;
