import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, X, Minimize2, Maximize2, Loader2, Sparkles, Brain, ChevronDown, Plus, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { API_BASE_URL } from '../api';
import VoiceInput from './VoiceInput';
import ImageUpload, { type ImageUploadRef } from './ImageUpload';
import ToolOutputRenderer from './ToolOutputRenderer';

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
    type: 'thought' | 'tool' | 'plan' | 'query_rewrite' | 'image_analysis' | 'execution' | 'tool_start' | 'tool_end';
    content: string;
    toolName?: string;
    toolInput?: string;
    toolOutput?: string;
    node?: string; // e.g., 'validator', 'planner'
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
    image_urls?: string[]; // Attached images
}

// Helper to safely parse JSON, handling double-encoding
const safeParseJSON = (input: any): any => {
    if (typeof input === 'object' && input !== null) return input;
    try {
        const parsed = JSON.parse(input);
        // Recursively unwrap if the result is still a string that looks like JSON
        if (typeof parsed === 'string' && (parsed.trim().startsWith('{') || parsed.trim().startsWith('['))) {
            return safeParseJSON(parsed);
        }
        return parsed;
    } catch (e) {
        return input;
    }
};

// Helper to format thought content (Text/Paragraph style)
const FormatThought: React.FC<{ step: ThoughtStep }> = ({ step }) => {
    try {
        // Use recursive parser to handle double-encoded strings
        const parsed = safeParseJSON(step.content);
        // Fallback for empty/string content if parsing fails or is just a string
        const isString = typeof parsed === 'string';

        // --- 0. Running State Handling (Hide Raw JSON) ---
        if (step.status === 'running' && step.type === 'thought') {
            // If content looks like JSON start, show loading indicator instead of raw text
            if (isString && (parsed.trim().startsWith('{') || parsed.trim().startsWith('```'))) {
                return (
                    <div className="text-zinc-400 italic flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Generating analysis...
                    </div>
                );
            }
        }

        // --- 0.5. Validator/Replanning Feedback ---
        if (step.node === 'validator' || (step.content?.startsWith('Validation:'))) {
            return (
                <div className="text-amber-300/90 mb-3 text-sm px-3 py-2 border-l-2 border-amber-500/40 bg-amber-500/5 rounded-r">
                    <div className="flex items-center gap-2 mb-1 text-[10px] font-bold text-amber-500 uppercase tracking-widest">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                        Methodology Check
                    </div>
                    <div className="italic opacity-90 leading-relaxed font-mono text-xs">
                        {step.content}
                    </div>
                </div>
            );
        }

        // --- 1. Execution Plan ---
        if (step.type === 'plan' || parsed.plan) {
            const planData = parsed.plan || parsed;
            // Handle if planData is the array itself or an object with plan key
            const steps = Array.isArray(planData) ? planData : (planData.plan || []);

            if (!Array.isArray(steps) && isString) return <div className="text-zinc-500 italic">{String(parsed)}</div>;

            return (
                <div className="text-zinc-200 mb-2">
                    <div className="flex items-center gap-2 mb-1.5 text-[10px] font-bold text-blue-300 uppercase tracking-widest bg-blue-900/20 p-1 rounded w-fit border border-blue-700/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                        Execution Plan
                    </div>
                    <ul className="space-y-1 text-sm pl-1 border-l border-white/10 ml-1">
                        {Array.isArray(steps) && steps.map((s: any, i: number) => {
                            // Map technical tool names to human actions
                            let action = s.tool?.replace(/_/g, ' ') || 'Action';
                            let details = '';

                            if (s.tool === 'web_search') action = "Searching web for";
                            else if (s.tool === 'get_company_news') action = "Checking news regarding";
                            else if (s.tool === 'search_market_trends') action = "Analyzing trends for";
                            else if (s.tool === 'get_financials') action = "Fetching financials for";
                            else if (s.tool === 'get_price_history_stats') action = "Pulling price stats for";
                            else if (s.tool === 'param_extractor') action = "Extracting parameters";
                            else if (s.tool === 'search_governance_issues') action = "Checking governance for";
                            else if (s.tool === 'read_report') action = "Reading report section";

                            const args = s.args || {};
                            if (args.query) details = `"${args.query}"`;
                            else if (args.section) details = args.section;
                            else if (args.ticker) details = args.ticker;

                            return (
                                <li key={i} className="flex gap-3 items-start pl-3 text-zinc-200">
                                    <span className="font-mono text-[10px] opacity-50 mt-1">{i + 1}.</span>
                                    <div>
                                        <span className="font-medium text-zinc-200">{action}</span>
                                        {details && <span className="text-zinc-400 ml-1.5 font-light">{details}</span>}
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            );
        }

        // --- 2. Query Rewrite ---
        if (step.type === 'query_rewrite' || parsed.rewritten_query) {
            return (
                <div className="text-zinc-200 mb-2 text-sm">
                    <div className="flex items-center gap-2 mb-1.5 text-[10px] font-bold text-blue-300 uppercase tracking-widest bg-blue-900/20 p-1 rounded w-fit border border-blue-700/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500/50"></span>
                        Context Analysis
                    </div>
                    <div className="pl-3 border-l border-white/10 ml-1">
                        <span className="text-zinc-500 text-[10px] uppercase tracking-wide">Intent</span>
                        <div className="italic text-zinc-200 mt-0.5 mb-1">"{parsed.rewritten_query || step.content}"</div>

                        {parsed.sub_queries && parsed.sub_queries.length > 0 && (
                            <div className="mt-1 text-xs grid gap-0.5">
                                {parsed.sub_queries.map((q: string, i: number) => (
                                    <div key={i} className="flex gap-2 text-zinc-400">
                                        <span>•</span>
                                        <span>{q}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        // --- 3. Image Analysis ---
        if (step.type === 'image_analysis') {
            return (
                <div className="text-zinc-200 mb-2 text-sm">
                    <div className="flex items-center gap-2 mb-1 text-[10px] font-bold text-blue-300 uppercase tracking-widest bg-blue-900/20 p-1 rounded w-fit border border-blue-700/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500/50"></span>
                        Visual Analysis
                    </div>
                    <div className="pl-3 border-l border-white/10 ml-1 leading-relaxed prose prose-invert prose-sm max-w-none text-zinc-200 [&_strong]:text-white [&_p]:my-1.5">
                        <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({node, ...props}) => <p className="leading-relaxed mb-2 last:mb-0" {...props} />,
                                strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                            }}
                        >
                            {typeof parsed === 'string' ? parsed : (parsed.content || step.content)}
                        </ReactMarkdown>
                    </div>
                </div>
            );
        }

        // --- 4. Tool Execution Results (Generic Wrapper) ---
        if (step.type === 'execution' || parsed.execution_results) {
            const results = parsed.execution_results || parsed;
            return (
                <div className="text-zinc-200 mb-1.5 text-sm">
                    <div className="flex items-center gap-2 mb-1 text-[10px] font-bold text-blue-300 uppercase tracking-widest bg-blue-900/20 p-1 rounded w-fit border border-blue-700/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500/50"></span>
                        Observation
                    </div>
                    <div className="space-y-1.5 pl-3 border-l border-white/10 ml-1">
                        {Object.entries(results).map(([key, result]: [string, any]) => {
                            // --- Aggressive JSON Unwrapping ---
                            let data = safeParseJSON(result);

                            // If data is now an object with a single key that looks like a step name, unwrap it again
                            if (data && typeof data === 'object' && !Array.isArray(data)) {
                                const keys = Object.keys(data);
                                if (keys.length === 1 && keys[0].includes('step_')) {
                                    data = safeParseJSON(data[keys[0]]);
                                }
                            }

                            // Clean tool name from step_N_toolname
                            const cleanToolName = key.replace(/^step_\d+_/, '');

                            return (
                                <div key={key}>
                                    <ToolOutputRenderer data={data} toolName={cleanToolName} />
                                </div>
                            );
                        })}
                    </div>
                </div>
            );
        }

        // --- 5. Tool Call (Step) ---
        if (step.type === 'tool') {
            return (
                <div className="text-zinc-200 mb-2 pl-3 border-l-2 border-white/10 border-dashed ml-1">
                    <span className="font-mono text-[10px] opacity-75 mr-2 uppercase tracking-wider text-blue-300">[{step.toolName}]</span>
                    <span className="text-xs">{step.content}</span>
                </div>
            )
        }

        // Fallback: If it's a string, render Markdown
        if (isString) {
            return (
                <div className="text-sm text-zinc-200 prose prose-invert prose-sm max-w-none leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{parsed}</ReactMarkdown>
                </div>
            );
        }

        // Fallback for objects: Tool Renderer
        return <ToolOutputRenderer data={parsed} />;
    } catch (e) {
        // Render unstructured text with Markdown support
        return (
            <div className="text-sm text-zinc-200 prose prose-invert prose-sm max-w-none leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{step.content}</ReactMarkdown>
            </div>
        );
    }
};

// --- Accordion Component ---
const LoadingDots = () => (
    <div className="flex space-x-1 items-center px-1 py-2">
        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"></div>
    </div>
);

const ThinkingAccordion: React.FC<{ steps: ThoughtStep[], hasContent?: boolean }> = ({ steps, hasContent }) => {
    const [isOpen, setIsOpen] = useState(true);

    // Auto-collapse REMOVED as per user feedback ("I think that should not happen")
    // useEffect(() => {
    //     if (hasContent && isOpen) {
    //         setIsOpen(false);
    //     }
    // }, [hasContent]);

    if (steps.length === 0) return null;

    const activeStep = steps.find(s => s.status === 'running');
    const isThinking = !!activeStep;

    return (
        <div className="mb-3 bg-white/5 rounded-lg border border-white/5 overflow-hidden">
            <div className="flex items-center gap-3 px-3 py-2 bg-white/5">
                {/* Header Label */}
                <div className="flex items-center gap-2 text-xs text-blue-300 font-medium select-none uppercase tracking-widest">
                    <Sparkles className="w-3 h-3 text-blue-400" />
                    <span>EquityPulse AI</span>
                </div>

                {/* Separator */}
                <div className="h-3 w-px bg-white/10" />

                {/* Toggle Button */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={clsx(
                        "flex items-center gap-1.5 text-[10px] uppercase tracking-wider font-bold transition-colors select-none ml-auto",
                        isOpen ? "text-zinc-200" : "text-zinc-500 hover:text-zinc-200"
                    )}
                >
                    {isThinking && !hasContent ? (
                        <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                    ) : (
                        <Brain className={clsx("w-3 h-3", isOpen ? "text-blue-400" : "opacity-70")} />
                    )}
                    <span>Analysis Trace ({steps.length})</span>
                    <ChevronDown className={clsx("w-3 h-3 transition-transform", isOpen ? "rotate-180" : "")} />
                </button>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-[#0a0a0a]/50"
                    >
                        <div className="p-4 space-y-4 text-sm text-zinc-200 font-sans">
                            {steps.map((step, idx) => (
                                <div key={idx} className="relative">
                                    <FormatThought step={step} />
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

// Generate unique session ID
const generateSessionId = () => `chat_${Date.now()}_${Math.random().toString(36).substring(7)}`;

export const ChatWidget: React.FC<ChatWidgetProps> = ({ sessionId: initialSessionId, reportId, activeTab, initialContext, onCloseSelection }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(true);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [pendingImages, setPendingImages] = useState<string[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState(initialSessionId);
    const [historyOpen, setHistoryOpen] = useState(false);
    const [sessions, setSessions] = useState<any[]>([]);
    const [previewImage, setPreviewImage] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const imageUploadRef = useRef<ImageUploadRef>(null);

    // Load sessions list
    const loadSessions = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/sessions/${reportId}`);
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
                return data;
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
        return [];
    };

    // Load messages for a specific session
    const loadSessionMessages = async (sid: string) => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/chat/history/${sid}`);
            if (response.ok) {
                const history = await response.json();
                setMessages(history.map((msg: any) => ({
                    id: msg.id,
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.created_at),
                    image_urls: msg.image_urls,
                    thoughts: (msg.thoughts || []).map((t: any) => {
                        // Hydrate 'content' for tool steps if missing (DB persistence mismatch)
                        if (t.type === 'tool' && !t.content && t.toolInput) {
                            return { ...t, content: formatToolInput(t.toolName || '', t.toolInput) };
                        }
                        return t;
                    })
                })));
                setCurrentSessionId(sid);
                setHistoryOpen(false);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle new chat creation
    const handleNewChat = () => {
        const newSessionId = generateSessionId();
        setCurrentSessionId(newSessionId);
        setMessages([]);
        setInputValue('');
        imageUploadRef.current?.clearAll();
        setHistoryOpen(false);
        loadSessions();
    };

    // Initial Load
    useEffect(() => {
        const initChat = async () => {
            const sessionsList = await loadSessions();
            if (sessionsList && sessionsList.length > 0) {
                // Load the most recent session
                loadSessionMessages(sessionsList[0].session_id);
            } else {
                // No sessions, start fresh
                handleNewChat();
            }
        };
        if (reportId) initChat();
    }, [reportId]);

    // Handle paste event for clipboard images
    useEffect(() => {
        const handlePaste = async (e: ClipboardEvent) => {
            const items = e.clipboardData?.items;
            if (!items) return;

            const imageFiles: File[] = [];
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.startsWith('image/')) {
                    const file = items[i].getAsFile();
                    if (file) imageFiles.push(file);
                }
            }

            if (imageFiles.length > 0 && imageUploadRef.current) {
                e.preventDefault();
                await imageUploadRef.current.addFiles(imageFiles);
            }
        };

        document.addEventListener('paste', handlePaste);
        return () => document.removeEventListener('paste', handlePaste);
    }, []);

    // Open widget when context is provided (text selected)
    useEffect(() => {
        if (initialContext?.selectedText) {
            setIsOpen(true);
            // Optional: Pre-fill input or show context indicator
        }
    }, [initialContext]);

    // Scroll to bottom on new messages
    useEffect(() => {
        if (messages.length === 0) return;

        // Only scroll if we are streaming OR if a new message was added
        const lastMsg = messages[messages.length - 1];
        if (lastMsg?.isStreaming || isOpen) {
            // Only auto-scroll if near bottom or if it's the very start of a response
            // For now, simpler: scroll to bottom if streaming
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        } else {
            // If not streaming (e.g. implementation), scroll once
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages.length, isOpen]); // Removed 'messages' content dependency to avoid jitters on every token, only unpredictable length changes

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'; // Reset height
            // Allow it to grow up to a large size, CSS max-height will handle the ultimate limit
            inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
        }
    }, [inputValue]);

    const handleTranscription = (text: string) => {
        const trimmed = inputValue.trim();
        const fullText = trimmed ? `${trimmed} ${text}` : text;

        setInputValue(fullText);
        // Auto-send the voice input immediately
        handleSend(fullText);
    };

    const handleSend = async (overrideContent?: string) => {
        const contentToSend = overrideContent || inputValue;
        if (!contentToSend.trim() || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: contentToSend,
            timestamp: new Date(),
            image_urls: pendingImages.length > 0 ? pendingImages : undefined
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setPendingImages([]);
        imageUploadRef.current?.clearAll();
        setIsLoading(true);

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
                    session_id: currentSessionId,
                    report_id: reportId,
                    message: userMsg.content,
                    active_tab: activeTab,
                    selected_text: initialContext?.selectedText,
                    image_urls: userMsg.image_urls
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
                                    const thoughts = m.thoughts || [];
                                    const lastThought = thoughts[thoughts.length - 1];
                                    if (lastThought && lastThought.type === 'tool' && lastThought.status === 'running') {
                                        lastThought.status = 'completed';
                                        lastThought.toolOutput = data.output;
                                        return { ...m, thoughts: [...thoughts] };
                                    }
                                    return m;
                                }));
                            }
                            // Trace Events (Query Rewrite, Plan, Analysis, Execution)
                            else if (['query_rewrite', 'image_analysis', 'plan', 'execution'].includes(data.type)) {
                                setMessages(prev => prev.map(m => {
                                    if (m.id !== assistantMsgId) return m;

                                    // Construct content object based on type to match FormatThought expectations
                                    let contentObj: any = {};
                                    if (data.type === 'query_rewrite') {
                                        contentObj = {
                                            rewritten_query: data.rewritten_query,
                                            sub_queries: data.sub_queries,
                                            needs_web_search: data.needs_web_search
                                        };
                                    } else if (data.type === 'image_analysis') {
                                        contentObj = { type: 'image_analysis', content: data.content };
                                    } else if (data.type === 'plan') {
                                        contentObj = { plan: data.content };
                                    } else if (data.type === 'execution') {
                                        contentObj = { execution_results: data.content };
                                    }

                                    const thoughts = m.thoughts || [];
                                    const lastThought = thoughts[thoughts.length - 1];

                                    // If we have a running thought, UPDATE it instead of appending
                                    if (lastThought && lastThought.type === 'thought' && lastThought.status === 'running') {
                                        // Replace the running "raw JSON" thought with the structured event
                                        const updatedThoughts = [...thoughts];
                                        updatedThoughts[updatedThoughts.length - 1] = {
                                            type: data.type === 'thought' ? 'thought' : data.type as any, // Use actual type
                                            content: JSON.stringify(contentObj),
                                            status: 'completed',
                                            timestamp: new Date()
                                        };
                                        return { ...m, thoughts: updatedThoughts };
                                    } else {
                                        // Fallback: Append new if no running thought (shouldn't happen with correct stream)
                                        return {
                                            ...m,
                                            thoughts: [...thoughts, {
                                                type: data.type === 'thought' ? 'thought' : data.type as any,
                                                content: JSON.stringify(contentObj),
                                                node: data.node,
                                                status: 'completed',
                                                timestamp: new Date()
                                            }]
                                        };
                                    }
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
                isExpanded ? "w-[80vw] h-[80vh] max-w-6xl" : "w-[450px] h-[700px]"
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
                    {/* History Toggle */}
                    <button
                        onClick={() => {
                            setHistoryOpen(!historyOpen);
                            if (!historyOpen) loadSessions();
                        }}
                        className={`p-1.5 rounded-md transition-colors ${historyOpen ? 'text-white bg-white/10' : 'text-white/40 hover:text-white/80 hover:bg-white/10'}`}
                        title="Chat History"
                    >
                        <Clock className="w-4 h-4" />
                    </button>
                    {/* New Chat Button */}
                    <button
                        onClick={handleNewChat}
                        className="p-1.5 text-white/40 hover:text-white/80 hover:bg-white/10 rounded-md transition-colors"
                        title="New Chat"
                    >
                        <Plus className="w-4 h-4" />
                    </button>
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

            {/* History Sidebar */}
            <AnimatePresence>
                {historyOpen && (
                    <motion.div
                        initial={{ x: '100%', opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: '100%', opacity: 0 }}
                        className="absolute top-[50px] bottom-0 right-0 w-64 bg-[#0F1117] border-l border-white/10 z-20 shadow-[-10px_0_20px_rgba(0,0,0,0.5)] flex flex-col"
                    >
                        <div className="p-3 border-b border-white/5 flex justify-between items-center text-xs font-medium text-white/50">
                            HISTORY
                            <button onClick={handleNewChat} className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300">
                                <Plus className="w-3 h-3" /> New
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-2 space-y-1">
                            {sessions.length === 0 && (
                                <div className="text-center text-white/30 text-xs py-4">No history yet</div>
                            )}
                            {sessions.map((session) => (
                                <button
                                    key={session.session_id}
                                    onClick={() => loadSessionMessages(session.session_id)}
                                    className={clsx(
                                        "w-full text-left p-2.5 rounded-lg text-xs transition-colors group",
                                        currentSessionId === session.session_id
                                            ? "bg-indigo-500/20 border border-indigo-500/30 text-white"
                                            : "text-white/60 hover:bg-white/5 border border-transparent"
                                    )}
                                >
                                    <div className="font-medium truncate mb-0.5">{session.title}</div>
                                    <div className="flex justify-between items-center">
                                        <div className="text-[10px] opacity-50">
                                            {new Date(session.created_at).toLocaleDateString()}
                                        </div>
                                        {/* Delete button could go here */}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

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
                        <div key={turn.assistant?.id || `turn-${idx}`} className="w-full bg-transparent border-b border-white/5 p-4 mb-2">
                            {/* User Header Section (Top Right) */}
                            <div className="flex flex-col items-end mb-4 space-y-2">
                                {turn.user.map(msg => (
                                    <div key={msg.id} className="max-w-[80%] bg-purple-500/10 border border-purple-500/20 text-purple-100 rounded-2xl rounded-tr-sm px-5 py-3 text-sm leading-relaxed shadow-sm">
                                        {/* Display attached images */}
                                        {msg.image_urls && msg.image_urls.length > 0 && (
                                            <div className="flex flex-wrap gap-2 mb-2">
                                                {msg.image_urls.map((url, imgIdx) => (
                                                    <img
                                                        key={imgIdx}
                                                        src={url}
                                                        alt={`Attachment ${imgIdx + 1}`}
                                                        className="w-20 h-20 object-cover rounded-lg border border-white/10 cursor-pointer hover:opacity-80 transition-opacity"
                                                        onClick={() => setPreviewImage(url)}
                                                    />
                                                ))}
                                            </div>
                                        )}
                                        {msg.content}
                                    </div>
                                ))}
                            </div>

                            {/* Assistant Body Section (Full Width, below User) */}
                            {turn.assistant ? (
                                <div className="w-full pl-0 md:pl-2">
                                    {/* Header & Reasoning */}
                                    {turn.assistant.thoughts && turn.assistant.thoughts.length > 0 ? (
                                        <ThinkingAccordion
                                            steps={turn.assistant.thoughts}
                                            hasContent={!!turn.assistant.content && turn.assistant.content.trim().length > 0}
                                        />
                                    ) : (
                                        <div className="flex items-center gap-2 mb-3 text-xs text-blue-300 font-medium select-none uppercase tracking-widest">
                                            <Sparkles className="w-3 h-3 text-blue-400" />
                                            <span>EquityPulse AI</span>
                                        </div>
                                    )}

                                    {/* Content */}
                                    <div className="prose prose-invert prose-p:my-3 prose-sm max-w-none break-words overflow-hidden text-zinc-200">
                                        {!turn.assistant.content && turn.assistant.isStreaming && (!turn.assistant.thoughts || turn.assistant.thoughts.length === 0) ? (
                                            <LoadingDots />
                                        ) : (
                                            <ReactMarkdown
                                                components={{
                                                    h3: ({ node, ...props }) => <h3 className="text-sm font-bold text-white mt-6 mb-3 uppercase tracking-wide" {...props} />,
                                                    strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-5 space-y-2 my-3 marker:text-zinc-500" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-5 space-y-2 my-3 marker:text-zinc-500" {...props} />,
                                                    li: ({ node, ...props }) => <li className="pl-1 text-sm leading-7" {...props} />,
                                                    p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-7 text-sm" {...props} />,
                                                    pre: ({ node, ...props }) => (
                                                        <div className="overflow-x-auto w-full my-4 bg-zinc-900/50 p-3 rounded-md border border-white/5">
                                                            <pre className="text-xs font-mono text-zinc-200" {...props} />
                                                        </div>
                                                    ),
                                                    code: ({ node, ...props }) => <code className="bg-white/5 px-1.5 py-0.5 rounded text-xs font-mono text-zinc-200 border border-white/5" {...props} />
                                                }}
                                                remarkPlugins={[remarkGfm]}
                                            >
                                                {turn.assistant.content || (turn.assistant.isStreaming ? ' ' : '')}
                                            </ReactMarkdown>
                                        )}
                                    </div>

                                    <div className="mt-4 pt-2 flex justify-start">
                                        <span className="text-[10px] text-zinc-600 font-mono">
                                            GENERATED AT {turn.assistant.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="w-full flex flex-col items-start gap-1 pl-2">
                                    <div className="flex items-center gap-2 text-blue-400">
                                        <LoadingDots />
                                    </div>
                                    <span className="text-[10px] text-blue-400 font-medium tracking-wider uppercase ml-1">Analyzing Market Data...</span>
                                </div>
                            )}
                        </div>
                    ));
                })()}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-[#0F1117] border-t border-white/5">
                {/* Image Preview Area - appears above input when images attached */}
                <ImageUpload ref={imageUploadRef} onImagesChange={setPendingImages} />

                {/* Input Row */}
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
                        className="w-full bg-transparent border-none focus:ring-0 text-white placeholder-white/30 text-sm resize-none max-h-[30vh] min-h-[20px] py-2 overflow-y-auto"
                        rows={1}
                        style={{ height: 'auto', minHeight: '40px' }}
                    />
                    <button
                        onClick={() => handleSend()}
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

            {/* Lightbox Modal for Chat History Images */}
            <AnimatePresence>
                {previewImage && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4 backdrop-blur-sm"
                        onClick={() => setPreviewImage(null)}
                    >
                        <button
                            className="absolute top-4 right-4 text-white/50 hover:text-white p-2 bg-white/10 rounded-full transition-colors"
                            onClick={() => setPreviewImage(null)}
                        >
                            <X className="w-6 h-6" />
                        </button>
                        <motion.img
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            src={previewImage}
                            alt="Full View"
                            className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
                            onClick={(e) => e.stopPropagation()}
                        />
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};
