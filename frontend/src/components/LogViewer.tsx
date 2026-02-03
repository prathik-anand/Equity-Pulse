import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Maximize2, Minimize2, ArrowDownCircle, BrainCircuit, Wrench, Activity, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';

interface LogViewerProps {
    sessionId: string;
    initialLogs?: any[]; // Now accepts objects or strings from legacy
    isProcessing?: boolean;
}

interface LogEntry {
    type: 'thought' | 'tool' | 'lifecycle' | 'info' | 'error';
    timestamp: string;
    agent: string;
    message: string;
    content: string;
}

const LogViewer: React.FC<LogViewerProps> = ({ sessionId, initialLogs = [], isProcessing = false }) => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isExpanded, setIsExpanded] = useState(isProcessing);
    const [autoScroll, setAutoScroll] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Initial load & formatting
    useEffect(() => {
        if (initialLogs.length > 0) {
            setLogs(prev => {
                // Parse legacy strings if necessary, or dedupe objects
                const parsedInitial = initialLogs.map(log =>
                    typeof log === 'string' ? parseLegacyLog(log) : log
                );
                return parsedInitial; // Simplified replace behavior for simplicity
            });
        }
    }, [initialLogs]);

    const parseLegacyLog = (logStr: string): LogEntry => {
        // Fallback parser for old string logs if any
        let type: LogEntry['type'] = 'info';
        if (logStr.includes("Insight:")) type = 'thought';
        if (logStr.includes("Tool Usage:")) type = 'tool';
        if (logStr.includes("ERROR")) type = 'error';

        return {
            type,
            timestamp: new Date().toLocaleTimeString(),
            agent: "System",
            message: logStr,
            content: logStr
        };
    };

    // SSE Connection
    useEffect(() => {
        if (!isProcessing) return;

        console.log("Connecting to EventSource...");
        const eventSource = new EventSource(`${API_BASE_URL}/analysis/${sessionId}/stream`);

        eventSource.onmessage = (event) => {
            try {
                // Try JSON first
                const data = JSON.parse(event.data);
                if (data.type) {
                    setLogs(prev => [...prev, data]);
                } else {
                    // Fallback if JSON but not our schema
                    setLogs(prev => [...prev, parseLegacyLog(event.data)]);
                }
            } catch (e) {
                // Is plain string
                setLogs(prev => [...prev, parseLegacyLog(event.data)]);
            }
        };

        eventSource.onerror = (err) => {
            console.error("EventSource failed:", err);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId, isProcessing]);

    // Auto-scroll
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    const handleScroll = () => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 20;
            setAutoScroll(isAtBottom);
        }
    };

    return (
        <div className={clsx(
            "rounded-xl border border-white/10 bg-black/90 shadow-2xl overflow-hidden transition-all duration-300 flex flex-col",
            isExpanded ? "h-[600px]" : "h-[60px]"
        )}>
            {/* Header */}
            <div
                className="h-[60px] min-h-[60px] px-6 flex items-center justify-between cursor-pointer bg-white/5 hover:bg-white/10 transition-colors border-b border-white/5"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <div className={clsx("p-2 rounded-lg", isProcessing ? "bg-purple-500/20 text-purple-400" : "bg-white/10 text-white/60")}>
                        <BrainCircuit className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                            AGENT REASONING ENGINE
                            {isProcessing && <span className="inline-block w-2 h-2 rounded-full bg-purple-500 animate-pulse" />}
                        </h3>
                        <p className="text-xs text-white/40 font-mono">
                            {isProcessing ? "Streaming real-time thoughts..." : `${logs.length} events recorded`}
                        </p>
                    </div>
                </div>

                <button className="text-white/40 hover:text-white transition-colors">
                    {isExpanded ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
            </div>

            {/* Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex-1 relative overflow-hidden"
                    >
                        <div
                            ref={scrollRef}
                            onScroll={handleScroll}
                            className="h-full overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-white/5"
                        >
                            {logs.length === 0 && (
                                <div className="text-white/20 italic text-center mt-10">Waiting for agent activity...</div>
                            )}

                            {logs.map((log, index) => (
                                <LogItem key={index} log={log} />
                            ))}

                            {!autoScroll && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setAutoScroll(true);
                                    }}
                                    className="absolute bottom-6 right-6 p-3 bg-purple-600 text-white rounded-full shadow-lg hover:scale-110 transition-transform z-10"
                                >
                                    <ArrowDownCircle className="w-5 h-5" />
                                </button>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const LogItem: React.FC<{ log: LogEntry }> = ({ log }) => {
    const isTool = log.type === 'tool';
    const isThought = log.type === 'thought';
    const isLifecycle = log.type === 'lifecycle';
    const isError = log.type === 'error';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={clsx(
                "group relative pl-4 border-l-2 p-3 rounded-r-md transition-all",
                isTool ? "border-blue-500/50 bg-blue-500/5 hover:bg-blue-500/10" :
                    isThought ? "border-purple-500/50 bg-purple-500/5 hover:bg-purple-500/10" :
                        isLifecycle ? "border-green-500/50 bg-green-500/5" :
                            isError ? "border-red-500 bg-red-500/10" :
                                "border-gray-500/30 text-white/60"
            )}
        >
            {/* Metadata Line */}
            <div className="flex items-center gap-2 mb-1 opacity-70">
                <span className="text-[10px] font-mono uppercase tracking-wider opacity-60 bg-white/5 px-1 rounded">
                    {log.timestamp}
                </span>

                <span className={clsx(
                    "text-xs font-bold",
                    isTool ? "text-blue-400" :
                        isThought ? "text-purple-400" :
                            isLifecycle ? "text-green-400" : "text-gray-400"
                )}>
                    {log.agent}
                </span>

                {isTool && <Wrench className="w-3 h-3 text-blue-400/50" />}
                {isThought && <BrainCircuit className="w-3 h-3 text-purple-400/50" />}
                {isLifecycle && <Activity className="w-3 h-3 text-green-400/50" />}
            </div>

            {/* Content */}
            <div className={clsx(
                "text-sm font-mono whitespace-pre-wrap break-words",
                isTool ? "text-blue-100/90" :
                    isThought ? "text-purple-100/90 italic" :
                        isLifecycle ? "text-green-100/90 font-bold" :
                            "text-white/80"
            )}>
                {log.content}
            </div>
        </motion.div>
    );
}

export default LogViewer;
