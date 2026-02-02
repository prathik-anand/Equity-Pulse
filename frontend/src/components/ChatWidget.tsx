import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, X, Minimize2, Maximize2, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';

interface ChatWidgetProps {
    sessionId: string;
    reportId: string;
    activeTab: string;
    initialContext?: {
        selectedText: string;
    };
    onCloseSelection?: () => void;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    steps?: string[]; // For showing planner steps
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ sessionId, reportId, activeTab, initialContext, onCloseSelection }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [plannerSteps, setPlannerSteps] = useState<string[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Open widget when context is provided (text selected)
    useEffect(() => {
        if (initialContext?.selectedText) {
            setIsOpen(true);
            // Optional: Pre-fill input or show context indicator
        }
    }, [initialContext]);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, plannerSteps, isOpen]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsLoading(true);
        setPlannerSteps([]);

        // Create placeholder for assistant message
        const assistantMsgId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, {
            id: assistantMsgId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true
        }]);

        try {
            const response = await fetch(`${API_BASE_URL}/chat/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    report_id: reportId,
                    message: userMsg.content,
                    active_tab: activeTab,
                    selected_text: initialContext?.selectedText
                })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) throw new Error('No reader available');

            let assistantContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.type === 'token') {
                                assistantContent += data.content;
                                setMessages(prev => prev.map(m =>
                                    m.id === assistantMsgId ? { ...m, content: assistantContent } : m
                                ));
                            } else if (data.type === 'plan') {
                                setPlannerSteps(data.content);
                            } else if (data.type === 'done') {
                                setIsLoading(false);
                                setMessages(prev => prev.map(m =>
                                    m.id === assistantMsgId ? { ...m, isStreaming: false } : m
                                ));
                            }
                        } catch (e) {
                            console.error('Error parsing SSE:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, content: "Error: Could not connect to AI Analyst.", isStreaming: false } : m
            ));
            setIsLoading(false);
        }

        // Clear selection after sending
        if (initialContext?.selectedText && onCloseSelection) {
            onCloseSelection();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!isOpen) {
        return (
            <motion.button
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 z-50 bg-indigo-600 hover:bg-indigo-500 text-white p-4 rounded-full shadow-2xl flex items-center gap-2 group"
            >
                <div className="relative">
                    <MessageSquare className="w-6 h-6" />
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-indigo-600"></span>
                </div>
                <span className="font-semibold pr-2">Ask AI Analyst</span>
            </motion.button>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className={clsx(
                "fixed z-50 bg-slate-900 border border-slate-700 shadow-2xl flex flex-col overflow-hidden transition-all duration-300",
                isExpanded
                    ? "top-6 bottom-6 right-6 w-[600px] rounded-2xl"
                    : "bottom-6 right-6 w-[400px] h-[600px] rounded-2xl"
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 bg-slate-950 border-b border-slate-800">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-indigo-500/20 rounded-lg">
                        <Sparkles className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-100">AI Analyst Team</h3>
                        <p className="text-xs text-indigo-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                            Online • Context: {activeTab}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    <button onClick={() => setIsExpanded(!isExpanded)} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                        {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </button>
                    <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-red-500/20 rounded-lg text-slate-400 hover:text-red-400 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Context Indicator (if text selected) */}
            <AnimatePresence>
                {initialContext?.selectedText && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="bg-indigo-900/20 border-b border-indigo-500/30 px-4 py-2 text-xs text-indigo-300 flex justify-between items-center"
                    >
                        <span className="truncate max-w-[90%]">Using selected context: "{initialContext.selectedText.substring(0, 50)}..."</span>
                        <button onClick={onCloseSelection} className="hover:text-white"><X className="w-3 h-3" /></button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 hover:scrollbar-thumb-slate-600">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50 select-none">
                        <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center">
                            <MessageSquare className="w-8 h-8 text-slate-500" />
                        </div>
                        <div>
                            <p className="font-medium text-slate-300">Ask anything about {activeTab}</p>
                            <p className="text-xs text-slate-500 max-w-[200px] mx-auto mt-1">
                                "What are the key risks here?"
                                <br />
                                "Compare this to competitors"
                            </p>
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={clsx("flex flex-col max-w-[85%]", msg.role === 'user' ? "self-end items-end" : "self-start items-start")}>
                        {/* Planner Steps Hidden as per user preference */}

                        <div className={clsx(
                            "rounded-2xl p-3 text-sm leading-relaxed shadow-sm max-w-full",
                            msg.role === 'user'
                                ? "bg-indigo-600 text-white rounded-tr-sm"
                                : "bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-tl-sm backdrop-blur-md"
                        )}>
                            {msg.role === 'assistant' ? (
                                <div className="prose prose-invert prose-p:my-1 prose-sm max-w-none break-words overflow-hidden">
                                    <ReactMarkdown
                                        components={{
                                            h3: ({ node, ...props }) => <h3 className="text-lg font-bold text-white mt-3 mb-1" {...props} />,
                                            strong: ({ node, ...props }) => <strong className="font-bold text-indigo-200" {...props} />,
                                            ul: ({ node, ...props }) => <ul className="list-disc pl-4 space-y-1 my-2" {...props} />,
                                            li: ({ node, ...props }) => <li className="text-slate-300" {...props} />,
                                            p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                            pre: ({ node, ...props }) => (
                                                <div className="overflow-x-auto w-full my-2 bg-slate-900/50 p-2 rounded-lg border border-slate-700/50">
                                                    <pre className="text-xs font-mono" {...props} />
                                                </div>
                                            ),
                                            code: ({ node, ...props }) => (
                                                <code className="bg-slate-900/50 px-1 py-0.5 rounded text-indigo-300 font-mono text-xs" {...props} />
                                            )
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                msg.content
                            )}
                        </div>
                        <span className="text-[10px] text-slate-500 mt-1 px-1">
                            {msg.role === 'user' ? 'You' : 'AI Analyst'} • {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                ))}

                {isLoading && messages[messages.length - 1]?.role === 'user' && (
                    <div className="self-start bg-slate-800/50 rounded-2xl p-4 border border-slate-700/30 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                        <span className="text-xs text-slate-400 animate-pulse">Analyzing report...</span>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
                <div className="relative flex items-center bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-xl transition-colors shadow-inner focus-within:ring-2 focus-within:ring-indigo-500/50 focus-within:border-indigo-500">
                    <textarea
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={initialContext?.selectedText ? "Ask about this selection..." : "Ask clarify questions about the report..."}
                        className="w-full bg-transparent text-slate-200 placeholder-slate-500 px-4 py-3 min-h-[50px] max-h-[120px] resize-none focus:outline-none scrollbar-hide text-sm"
                        rows={1}
                    />
                    <div className="pr-2 pb-2 self-end">
                        <button
                            onClick={handleSend}
                            disabled={!inputValue.trim() || isLoading}
                            className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white rounded-lg transition-all shadow-lg shadow-indigo-900/20"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
                <div className="text-[10px] text-center text-slate-600 mt-2 flex items-center justify-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-indigo-500/50" />
                    Powered by Gemini 3.0 Pro & Live Market Data
                </div>
            </div>
        </motion.div>
    );
};
