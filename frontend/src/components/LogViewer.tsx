import React, { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    Brain,
    ChevronDown,
    ChevronRight,
    Terminal,
    Clock,
    Search,
    AlertCircle,
    Activity
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';

interface LogEntry {
    type: 'tool' | 'thought' | 'info' | 'error' | 'lifecycle';
    timestamp: string;
    agent: string;
    message: string;
    content: string;
    args?: any;
}

interface LogViewerProps {
    sessionId: string;
    initialLogs?: LogEntry[];
    isProcessing?: boolean;
}

// --- Helper to format tool inputs human-readably ---
const formatToolInput = (args: any): string => {
    if (typeof args === 'string') return args;
    if (!args) return '';

    // Logic to make specific tools read better
    if (args.query) return `Searching for: "${args.query}"`;
    if (args.ticker) return `Analyzing ticker: ${args.ticker}`;
    if (args.url) return `Reading URL: ${args.url}`;

    // Fallback: Clean key-value pairs
    try {
        return Object.entries(args)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ');
    } catch (e) {
        return JSON.stringify(args);
    }
};

const ReasoningStep: React.FC<{ log: LogEntry }> = ({ log }) => {
    const isThought = log.type === 'thought';
    const isTool = log.type === 'tool';
    const isError = log.type === 'error';

    const [isOpen, setIsOpen] = useState(isThought || isTool);

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={clsx(
                "group relative border-l-2 pl-4 py-2 transition-all duration-300",
                isThought ? "border-purple-500/50" :
                    isTool ? "border-blue-500/50" :
                        isError ? "border-red-500/50" :
                            "border-white/10"
            )}
        >
            <div
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-start gap-3 cursor-pointer select-none"
            >
                <div className={clsx("mt-0.5 p-1 rounded-md transition-colors",
                    isThought ? "text-purple-400 bg-purple-500/10 group-hover:bg-purple-500/20" :
                        isTool ? "text-blue-400 bg-blue-500/10 group-hover:bg-blue-500/20" :
                            isError ? "text-red-400 bg-red-500/10" : "text-gray-500"
                )}>
                    {isThought ? <Brain className="w-4 h-4" /> :
                        isTool ? <Search className="w-4 h-4" /> :
                            isError ? <AlertCircle className="w-4 h-4" /> :
                                <Activity className="w-4 h-4" />}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-4">
                        <span className={clsx("text-sm font-medium truncate",
                            isThought ? "text-purple-200" :
                                isTool ? "text-blue-200" :
                                    isError ? "text-red-200" : "text-gray-400"
                        )}>
                            {isTool && log.content.includes("Using") ? formatToolInput(log.args) || log.content : log.content.split('\n')[0]}
                        </span>
                        <div className="flex items-center gap-2 text-[10px] text-white/30 whitespace-nowrap">
                            <Clock className="w-3 h-3" />
                            <span>{log.timestamp}</span>
                            {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        </div>
                    </div>
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
                                    {/* Use formatToolInput instead of JSON.stringify */}
                                    {formatToolInput(log.args)}
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
        </motion.div>
    );
};

const LogViewer: React.FC<LogViewerProps> = ({ sessionId, initialLogs = [], isProcessing = false }) => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isExpanded, setIsExpanded] = useState(true);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
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
        if (scrollRef.current && shouldAutoScroll) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs.length, shouldAutoScroll]);

    const handleScroll = () => {
        if (!scrollRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
        setShouldAutoScroll(isAtBottom);
    };

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
                                onScroll={handleScroll}
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

export default LogViewer;
