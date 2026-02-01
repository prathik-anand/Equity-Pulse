import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Maximize2, Minimize2, ArrowDownCircle } from 'lucide-react';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';

interface LogViewerProps {
    sessionId: string;
    initialLogs?: string[];
    isProcessing?: boolean;
}

const LogViewer: React.FC<LogViewerProps> = ({ sessionId, initialLogs = [], isProcessing = false }) => {
    const [logs, setLogs] = useState<string[]>(initialLogs);
    const [isExpanded, setIsExpanded] = useState(isProcessing); // Auto-expand if processing
    const [autoScroll, setAutoScroll] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Sync initialLogs when they update (e.g. from polling fallback or re-renders)
    useEffect(() => {
        if (initialLogs.length > logs.length) {
            // Avoid duplicate logs if we are already streaming, 
            // but if initialLogs comes from DB (historical) and we have more there, sync it.
            // Simple approach: merge unique or just allow append if streaming is not active.
            // For simplicity, if we are not processing, we fully trust initialLogs.
            if (!isProcessing) {
                setLogs(initialLogs);
            }
        }
    }, [initialLogs, isProcessing]);


    // SSE Connection
    useEffect(() => {
        if (!isProcessing) return;

        console.log("Connecting to EventSource...");
        const eventSource = new EventSource(`${API_BASE_URL}/analysis/${sessionId}/stream`);

        eventSource.onopen = () => {
            console.log("EventSource connected.");
        };

        eventSource.onmessage = (event) => {
            // console.log("New log:", event.data);
            setLogs((prev) => [...prev, event.data]);
        };

        eventSource.onerror = (err) => {
            console.error("EventSource failed:", err);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId, isProcessing]);

    // Auto-scroll logic
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    const handleScroll = () => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            // Add a small tolerance (e.g. 10px) to account for sub-pixel rendering or browser quirks
            const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
            setAutoScroll(isAtBottom);
        }
    };

    return (
        <div className={clsx(
            "rounded-xl border border-white/10 bg-black/90 shadow-2xl overflow-hidden transition-all duration-300",
            isExpanded ? "h-[500px]" : "h-[60px]"
        )}>
            {/* Header */}
            <div
                className="h-[60px] px-6 flex items-center justify-between cursor-pointer bg-white/5 hover:bg-white/10 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <div className={clsx("p-2 rounded-lg", isProcessing ? "bg-green-500/20 text-green-400" : "bg-white/10 text-white/60")}>
                        <Terminal className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-white tracking-wide">
                            AGENT SCRATCHPAD
                            {isProcessing && <span className="ml-2 inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />}
                        </h3>
                        <p className="text-xs text-white/40 font-mono">
                            {isProcessing ? "Streaming real-time execution..." : `${logs.length} lines stored`}
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
                        className="h-[calc(100%-60px)] relative"
                    >
                        <div
                            ref={scrollRef}
                            onScroll={handleScroll}
                            className="h-full overflow-y-auto p-6 font-mono text-xs md:text-sm space-y-1.5 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-white/5"
                        >
                            {logs.length === 0 && (
                                <div className="text-white/20 italic text-center mt-10">Waiting for agent activity...</div>
                            )}

                            {logs.map((log, index) => {
                                // Simple syntax highlighting
                                const isError = log.includes("ERROR");
                                const isWarning = log.includes("WARNING");
                                const isTool = log.includes("Tool Call");
                                const isThought = log.includes("Thought:");
                                const isKeyStep = log.includes("Starting analysis") || log.includes("Analysis complete");

                                return (
                                    <div key={index} className={clsx(
                                        "break-words leading-relaxed",
                                        isError ? "text-red-400 font-bold" :
                                            isWarning ? "text-yellow-400" :
                                                isTool ? "text-blue-400" :
                                                    isThought ? "text-purple-300 italic pl-4 border-l-2 border-purple-500/30" :
                                                        isKeyStep ? "text-white font-bold bg-white/5 p-1 rounded" :
                                                            "text-green-400/80"
                                    )}>
                                        <span className="text-white/20 mr-3 select-none text-[10px]">{index + 1}</span>
                                        {log}
                                    </div>
                                );
                            })}

                            {!autoScroll && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setAutoScroll(true);
                                    }}
                                    className="absolute bottom-6 right-6 p-2 bg-primary text-primary-foreground rounded-full shadow-lg hover:scale-110 transition-transform z-10"
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

export default LogViewer;
