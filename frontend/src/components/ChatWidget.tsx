import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, X, Minimize2, Maximize2, Loader2, Sparkles, Brain, ChevronDown, ChevronRight, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';
import VoiceInput from './VoiceInput';

interface ChatWidgetProps {
    sessionId: string;
    reportId: string;
    activeTab: string;
    initialContext?: {
        selectedText: string;
    };
    onCloseSelection?: () => void;
}

interface ThoughtStep {
    type: 'thought' | 'tool';
    content: string;
    toolName?: string;
    toolInput?: string;
    toolOutput?: string;
    status: 'running' | 'completed' | 'failed';
    timestamp: Date;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    steps?: string[]; // Legacy planner steps
    thoughts?: ThoughtStep[]; // New Reasoning Traces
}

// --- Accordion Component ---
const ThinkingAccordion: React.FC<{ steps: ThoughtStep[] }> = ({ steps }) => {
    const [isOpen, setIsOpen] = useState(true);
    // If we have active steps, it's nice to auto-expand, but allow user toggle.
    // Default open is good for transparency.

    if (steps.length === 0) return null;

    const activeStep = steps.find(s => s.status === 'running');
    const isThinking = !!activeStep;

    return (
        <div className="mt-2 mb-2 border border-white/10 rounded-lg overflow-hidden bg-black/20">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-white/50 hover:bg-white/5 transition-colors"
            >
                <div className="flex items-center gap-2">
                    {isThinking ? (
                        <Loader2 className="w-3 h-3 animate-spin text-purple-400" />
                    ) : (
                        <Brain className="w-3 h-3 text-purple-400" />
                    )}
                    <span>
                        {isThinking
                            ? "Reasoning..."
                            : `Reasoned for ${steps.length} steps`}
                    </span>
                </div>
                {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="px-3 py-2 space-y-3 bg-black/10 text-xs text-gray-300 font-sans border-t border-white/5 max-h-[300px] overflow-y-auto">
                            {steps.map((step, idx) => (
                                <div key={idx} className="flex gap-2">
                                    <div className="mt-0.5 min-w-[12px]">
                                        {step.type === 'tool' ? (
                                            <Search className="w-3 h-3 text-blue-400" />
                                        ) : (
                                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500/50 mt-1" />
                                        )}
                                    </div>
                                    <div className="flex-1 overflow-hidden">
                                        <div className="font-medium text-white/70 mb-0.5">
                                            {step.toolName || "Thought Process"}
                                        </div>
                                        <div className="prose prose-invert prose-xs max-w-none prose-p:leading-relaxed prose-pre:bg-black/30 prose-pre:p-2 prose-pre:rounded-md whitespace-pre-wrap break-words">
                                            {/* Here is the fix: Use formatToolInput for thoughts too if they look like JSON */}
                                            {step.type === 'tool' ? (
                                                step.content // Already formatted in the handler
                                            ) : (
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {formatToolInput('thought', step.content)}
                                                </ReactMarkdown>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// --- Helper to format tools and inputs human-readably ---
const formatToolInput = (tool: string, input: any): string => {
    // 1. Handle JSON strings that might be "Thoughts" or "Plans"
    if (typeof input === 'string') {
        const trimmed = input.trim();
        // Detect if it consumes a code block like ```json ... ```
        const jsonMatch = trimmed.match(/^```json\s*([\s\S]*?)\s*```$/) || trimmed.match(/^```\s*([\s\S]*?)\s*```$/);

        let contentToParse = jsonMatch ? jsonMatch[1] : trimmed;

        // Try parsing if it looks like an object
        if (contentToParse.startsWith('{') && contentToParse.endsWith('}')) {
            try {
                const parsed = JSON.parse(contentToParse);
                // Schema: { intent: string, plan: string[] }
                if (parsed.plan && Array.isArray(parsed.plan)) {
                    return `**Plan:**\n${parsed.plan.map((p: string) => `- ${p}`).join('\n')}`;
                }
                if (parsed.intent) {
                    return `**Intent:** ${parsed.intent}\n${parsed.plan ? `**Plan:**\n${parsed.plan.map((p: string) => `- ${p}`).join('\n')}` : ''}`;
                }
            } catch (e) {
                // Not valid JSON, just return original
            }
        }
        return input;
    }

    if (!input) return '';

    // Logic to make specific tools read better
    if (tool.includes('search') && input.query) return `Searching for: "${input.query}"`;
    if (input.ticker) return `Analyzing ticker: ${input.ticker}`;
    if (input.url) return `Reading URL: ${input.url}`;

    // Fallback: Clean key-value pairs
    try {
        return Object.entries(input)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ');
    } catch (e) {
        return JSON.stringify(input);
    }
};

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

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'; // Reset height
            // Allow it to grow up to a large size, CSS max-height will handle the ultimate limit
            inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
        }
    }, [inputValue]);

    const handleTranscription = (text: string) => {
        setInputValue(prev => {
            const trimmed = prev.trim();
            return trimmed ? `${trimmed} ${text}` : text;
        });
        // Optional: Auto-focus the input
        inputRef.current?.focus();
    };

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
            isStreaming: true,
            thoughts: [] // Initialize empty thoughts
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
                // Handle potentially multiple messages in one chunk, split by double newline usually
                // But SSE spec requires data: prefix. 
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            // Token Stream (Final Answer)
                            if (data.type === 'token') {
                                assistantContent += data.content;
                                setMessages(prev => prev.map(m => {
                                    if (m.id !== assistantMsgId) return m;

                                    // Check if we need to close a lingering running thought
                                    let newThoughts = m.thoughts;
                                    if (newThoughts && newThoughts.length > 0) {
                                        const last = newThoughts[newThoughts.length - 1];
                                        if (last.status === 'running') {
                                            newThoughts = [...newThoughts];
                                            newThoughts[newThoughts.length - 1] = { ...last, status: 'completed' };
                                        }
                                    }

                                    return {
                                        ...m,
                                        content: assistantContent,
                                        thoughts: newThoughts
                                    };
                                }));
                            }
                            // Thoughts (Planner)
                            else if (data.type === 'thought') {
                                setMessages(prev => prev.map(m => {
                                    if (m.id !== assistantMsgId) return m;
                                    const thoughts = m.thoughts || [];

                                    const lastThought = thoughts[thoughts.length - 1];
                                    if (lastThought && lastThought.type === 'thought' && lastThought.status === 'running') {
                                        lastThought.content += data.content;
                                        return { ...m, thoughts: [...thoughts] };
                                    } else {
                                        // New thought block
                                        return {
                                            ...m,
                                            thoughts: [...thoughts, {
                                                type: 'thought',
                                                content: data.content,
                                                status: 'running',
                                                timestamp: new Date()
                                            }]
                                        };
                                    }
                                }));
                            }
                            // Tool Start
                            else if (data.type === 'tool_start') {
                                setMessages(prev => prev.map(m => {
                                    if (m.id !== assistantMsgId) return m;
                                    return {
                                        ...m,
                                        thoughts: [...(m.thoughts || []), {
                                            type: 'tool',
                                            content: formatToolInput(data.tool, data.input), // Use helper here
                                            toolName: data.tool,
                                            status: 'running',
                                            timestamp: new Date()
                                        }]
                                    };
                                }));
                            }
                            // Tool End
                            else if (data.type === 'tool_end') {
                                setMessages(prev => prev.map(m => {
                                    if (m.id !== assistantMsgId) return m;
                                    // Find and complete the tool step
                                    const thoughts = m.thoughts || [];
                                    const lastThought = thoughts[thoughts.length - 1];
                                    if (lastThought && lastThought.type === 'tool' && lastThought.status === 'running') {
                                        lastThought.status = 'completed';
                                        lastThought.toolOutput = data.output;
                                        return { ...m, thoughts: [...thoughts] }; // mutate copy
                                    }
                                    return m;
                                }));
                            }

                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, content: 'Sorry, I encountered an error receiving the response.', isStreaming: false } : m
            ));
        } finally {
            setIsLoading(false);
            setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, isStreaming: false } : m
            ));
        }
    };

    if (!isOpen) {
        // Minimal Button to open chat
        return (
            <motion.div
                className="fixed bottom-6 right-6 z-50 pointer-events-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                whileHover={{ scale: 1.05 }}
            >
                <button
                    onClick={() => setIsOpen(true)}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-full p-4 shadow-lg flex items-center gap-2 transition-all"
                >
                    <MessageSquare className="w-6 h-6" />
                    <span className="font-medium pr-1">Ask Analyst</span>
                </button>
            </motion.div>
        );
    }

    return (
        <motion.div
            id="chat-widget-container"
            className={clsx(
                "fixed bottom-6 right-6 z-50 pointer-events-auto flex flex-col bg-[#0F1117] border border-white/10 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl",
                isExpanded ? "w-[80vw] h-[80vh] max-w-6xl" : "w-[400px] h-[600px]"
            )}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/5 select-none">
                <div className="flex items-center gap-2">
                    <div className="bg-indigo-500/20 p-1.5 rounded-lg">
                        <Sparkles className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-white">AI Analyst Team</h3>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[10px] text-white/50">Online • Context: {initialContext ? initialContext.selectedText.substring(0, 15) + '...' : activeTab}</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="p-1.5 text-white/40 hover:text-white/80 hover:bg-white/10 rounded-md transition-colors"
                    >
                        {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </button>
                    <button
                        onClick={() => { setIsOpen(false); onCloseSelection?.(); }}
                        className="p-1.5 text-white/40 hover:text-white/80 hover:bg-white/10 rounded-md transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Context Indicator */}
            {initialContext && (
                <div className="bg-indigo-500/10 border-b border-indigo-500/20 px-4 py-2 flex items-start gap-2">
                    <div className="mt-0.5 min-w-[16px]">
                        <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-xs text-indigo-200 line-clamp-1">
                            Using selected context: "{initialContext.selectedText}"
                        </p>
                    </div>
                    <button onClick={() => onCloseSelection?.()} className="text-indigo-400/60 hover:text-indigo-400">
                        <X className="w-3 h-3" />
                    </button>
                </div>
            )}

            {/* Messages Area - Unified Turn Cards */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50 mt-10">
                        <div className="p-4 bg-white/5 rounded-full">
                            <MessageSquare className="w-8 h-8 text-indigo-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-white">How can I help you today?</p>
                            <p className="text-xs text-white/40 mt-1 max-w-[200px]">
                                Ask about the generated report, or select text to analyze specific sections.
                            </p>
                        </div>
                    </div>
                )}

                {(() => {
                    // Group messages into unified turns (User -> Assistant)
                    const turns: { user: Message[], assistant: Message | null }[] = [];
                    let currentUserMsgs: Message[] = [];

                    messages.forEach(msg => {
                        if (msg.role === 'user') {
                            currentUserMsgs.push(msg);
                        } else {
                            turns.push({ user: currentUserMsgs, assistant: msg });
                            currentUserMsgs = [];
                        }
                    });

                    if (currentUserMsgs.length > 0) {
                        turns.push({ user: currentUserMsgs, assistant: null });
                    }

                    return turns.map((turn, idx) => (
                        <div key={turn.assistant?.id || `turn-${idx}`} className="w-full bg-white/5 border border-white/5 rounded-2xl p-3 mb-4 backdrop-blur-sm">
                            {/* User Header Section (Top Right) */}
                            <div className="flex flex-col items-end mb-3 space-y-2">
                                {turn.user.map(msg => (
                                    <div key={msg.id} className="max-w-[70%] bg-indigo-600/20 border border-indigo-500/30 text-indigo-100 rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed shadow-sm backdrop-blur-sm">
                                        {msg.content}
                                        <div className="text-[10px] text-indigo-300/50 mt-1 text-right">
                                            {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Assistant Body Section (Full Width, below User) */}
                            {turn.assistant ? (
                                <div className="w-[85%] bg-slate-900/50 rounded-xl p-4 border border-white/5 shadow-inner">
                                    <div className="flex items-center gap-2 mb-3 text-xs text-indigo-400 font-medium select-none">
                                        <Sparkles className="w-3.5 h-3.5" />
                                        <span>AI Analyst</span>
                                    </div>

                                    {/* Reasoning */}
                                    {turn.assistant.thoughts && turn.assistant.thoughts.length > 0 && (
                                        <ThinkingAccordion steps={turn.assistant.thoughts} />
                                    )}

                                    {/* Content */}
                                    <div className="prose prose-invert prose-p:my-1 prose-sm max-w-none break-words overflow-hidden text-slate-300">
                                        <ReactMarkdown
                                            components={{
                                                h3: ({ node, ...props }) => <h3 className="text-lg font-bold text-white mt-4 mb-2 border-b border-white/10 pb-1" {...props} />,
                                                strong: ({ node, ...props }) => <strong className="font-bold text-indigo-200" {...props} />,
                                                ul: ({ node, ...props }) => <ul className="list-disc pl-4 space-y-1 my-2 marker:text-indigo-500" {...props} />,
                                                li: ({ node, ...props }) => <li className="pl-1 text-sm leading-relaxed" {...props} />,
                                                p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed text-sm" {...props} />,
                                                pre: ({ node, ...props }) => (
                                                    <div className="overflow-x-auto w-full my-3 bg-black/30 p-3 rounded-lg border border-white/10 shadow-sm">
                                                        <pre className="text-xs font-mono" {...props} />
                                                    </div>
                                                ),
                                                code: ({ node, ...props }) => <code className="bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono text-indigo-200" {...props} />
                                            }}
                                            remarkPlugins={[remarkGfm]}
                                        >
                                            {turn.assistant.content || (turn.assistant.isStreaming ? ' ' : '')}
                                        </ReactMarkdown>
                                    </div>

                                    <div className="mt-3 pt-3 border-t border-white/5 flex justify-end">
                                        <span className="text-[10px] text-white/20">
                                            {turn.assistant.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="w-full bg-slate-900/30 rounded-xl p-4 border border-white/5 border-dashed animate-pulse flex items-center gap-2 text-white/20">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm">Generating response...</span>
                                </div>
                            )}
                        </div>
                    ));
                })()}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-[#0F1117] border-t border-white/5">
                <div className="relative flex items-end gap-2 bg-white/5 rounded-xl border border-white/10 p-2 focus-within:border-indigo-500/50 transition-colors">
                    <VoiceInput onTranscriptionComplete={handleTranscription} />
                    <textarea
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask clarify questions about the report..."
                        className="w-full bg-transparent border-none focus:ring-0 text-white placeholder-white/30 text-sm resize-none max-h-[30vh] min-h-[20px] py-2 overflow-y-auto" // Increased max-height
                        rows={1}
                        style={{ height: 'auto', minHeight: '40px' }} // Dynamic height
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !inputValue.trim()}
                        className={clsx(
                            "p-2 rounded-lg transition-all mb-0.5",
                            isLoading || !inputValue.trim()
                                ? "bg-white/5 text-white/20 cursor-not-allowed"
                                : "bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-500/20"
                        )}
                    >
                        {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </button>
                </div>
                <div className="text-center mt-2">
                    <span className="text-[10px] text-indigo-400/40 flex items-center justify-center gap-1.5">
                        <Sparkles className="w-3 h-3" />
                        Powered by Gemini 3.0 Pro & Live Market Data
                    </span>
                </div>
            </div>
        </motion.div>
    );
};
