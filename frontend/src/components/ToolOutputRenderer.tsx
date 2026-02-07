import React, { useState } from 'react';
import { ExternalLink, Search, Newspaper, Activity, ChevronDown, ChevronRight, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';

interface ToolOutputRendererProps {
    data: any;
    toolName?: string;
}

const safeParseJSON = (input: any): any => {
    if (typeof input === 'object' && input !== null) return input;
    try {
        const parsed = JSON.parse(input);
        if (typeof parsed === 'string' && (parsed.trim().startsWith('{') || parsed.trim().startsWith('['))) {
            return safeParseJSON(parsed);
        }
        return parsed;
    } catch (e) {
        return input;
    }
};

// --- Recursive Smart Data Renderer ---
const SmartDataRenderer: React.FC<{ data: any; depth?: number; label?: string }> = ({ data, depth = 0, label }) => {
    const [isOpen, setIsOpen] = useState(true);

    if (data === null || data === undefined) return null;

    // Primitives
    if (typeof data !== 'object') {
        return (
            <div className="flex items-start gap-2 text-sm leading-relaxed">
                {label && <span className="text-zinc-500 font-medium min-w-[120px]">{label}:</span>}
                <span className="text-zinc-300 break-words">{String(data)}</span>
            </div>
        );
    }

    // Arrays
    if (Array.isArray(data)) {
        if (data.length === 0) return null;
        return (
            <div className="mt-0.5 mb-1.5">
                {label && <div className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-0.5">{label}</div>}
                <ul className="space-y-0.5 pl-2 border-l border-zinc-700/50">
                    {data.map((item, i) => (
                        <li key={i} className="text-sm">
                            <SmartDataRenderer data={item} depth={depth + 1} />
                        </li>
                    ))}
                </ul>
            </div>
        );
    }

    // Objects
    const keys = Object.keys(data);
    if (keys.length === 0) return null;

    return (
        <div className={clsx("w-full transition-all", depth > 0 && "ml-1 mt-0.5")}>
            {label && (
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-1.5 w-full text-left py-0.5 hover:bg-white/5 rounded px-1 -ml-1 group"
                >
                    {isOpen ?
                        <ChevronDown className="w-3 h-3 text-zinc-500 group-hover:text-zinc-300" /> :
                        <ChevronRight className="w-3 h-3 text-zinc-500 group-hover:text-zinc-300" />
                    }
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider group-hover:text-zinc-200">
                        {label.replace(/_/g, ' ')}
                    </span>
                </button>
            )}

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={label ? { height: 0, opacity: 0 } : false}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className={clsx("space-y-1", label && "pl-3 border-l-2 border-zinc-800/50 py-0.5")}>
                            {keys.map(key => (
                                <SmartDataRenderer key={key} data={data[key]} depth={depth + 1} label={key} />
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const ToolOutputRenderer: React.FC<ToolOutputRendererProps> = ({ data, toolName }) => {
    let parsedData = safeParseJSON(data);

    // Unwrap generic wrappers
    if (parsedData && typeof parsedData === 'object' && !Array.isArray(parsedData)) {
        if (parsedData.results) parsedData = safeParseJSON(parsedData.results);
        else if (parsedData.execution_results) parsedData = safeParseJSON(parsedData.execution_results);
    }

    if (!parsedData) return <span className="text-zinc-500 italic text-xs">No output</span>;

    // --- 1. Web Search ---
    if (['web_search', 'search_market_trends', 'search_governance_issues'].includes(toolName || '')) {
        return (
            <div className="space-y-1.5 mt-0.5">
                <div className="flex items-center gap-2 text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">
                    <Search className="w-3 h-3" />
                    <span>Search Results</span>
                </div>
                <div className="text-sm text-zinc-300 prose prose-invert prose-sm max-w-none bg-black/20 p-2 rounded-md border border-white/5">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {typeof parsedData === 'string' ? parsedData : JSON.stringify(parsedData, null, 2)}
                    </ReactMarkdown>
                </div>
            </div>
        );
    }

    // --- 2. Company News ---
    if (toolName === 'get_company_news') {
        const articles = Array.isArray(parsedData) ? parsedData : (parsedData.articles || []);
        if (Array.isArray(articles) && articles.length > 0) {
            return (
                <div className="space-y-2 mt-0.5">
                    <div className="flex items-center gap-2 text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">
                        <Newspaper className="w-3 h-3" />
                        <span>Latest News</span>
                    </div>
                    <div className="grid gap-1.5">
                        {articles.slice(0, 3).map((article: any, i: number) => (
                            <a key={i} href={article.link} target="_blank" rel="noopener noreferrer" className="block group p-2 bg-black/20 hover:bg-white/5 border border-white/5 hover:border-white/10 rounded-lg transition-all">
                                <div className="font-medium text-xs text-zinc-200 group-hover:text-sky-400 transition-colors line-clamp-2">{article.title}</div>
                                <div className="flex items-center gap-2 mt-1 text-[10px] text-zinc-500">
                                    <span className="truncate max-w-[100px]">{article.publisher}</span>
                                    <span>•</span>
                                    <span>{article.providerPublishTime ? new Date(article.providerPublishTime * 1000).toLocaleDateString() : 'Recent'}</span>
                                    <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
                                </div>
                            </a>
                        ))}
                    </div>
                </div>
            );
        }
    }

    // --- 3. Report Data (Structured Analysis) ---
    // Check by tool name OR structure (Duck Typing)
    const isReportData = (data: any) => {
        if (!data) return false;
        if (Array.isArray(data) && data.length > 0 && data[0].section && data[0].content) return true;
        return false;
    };

    if (toolName === 'read_report' || isReportData(parsedData)) {
        // Handle explicit error
        if (parsedData.error) {
            return (
                <div className="p-2 bg-red-500/10 border border-red-500/20 rounded-md text-red-200 text-xs flex items-center gap-2">
                    <Info className="w-4 h-4" />
                    {parsedData.error}
                </div>
            );
        }

        // Robust unpacking: Try to find the array of sections
        let sections = parsedData;
        
        // 1. If it's a string, try to parse it again (double encoding protection)
        if (typeof sections === 'string') {
            try { sections = JSON.parse(sections); } catch(e) {}
        }
        
        // 2. If it's an object with a wrapper key, unwrap it
        if (!Array.isArray(sections) && typeof sections === 'object' && sections !== null) {
            if (Array.isArray(sections.content)) sections = sections.content;
            else if (Array.isArray(sections.data)) sections = sections.data;
            else if (Array.isArray(sections.result)) sections = sections.result;
            else if (Array.isArray(sections.sections)) sections = sections.sections;
        }

        // Handle Array of Sections (New Format)
        if (Array.isArray(sections)) {
            return (
                <div className="space-y-2.5 mt-1">
                    {sections.map((section: any, idx: number) => (
                        <div key={idx} className="bg-black/20 rounded-lg border border-white/5 overflow-hidden">
                            <div className="bg-white/5 px-2 py-1.5 border-b border-white/5 flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                                <span className="text-[10px] font-semibold text-zinc-300 uppercase tracking-wide">
                                    {section.section?.replace(/_/g, ' ') || 'Usage'}
                                </span>
                            </div>
                            <div className="p-2">
                                <SmartDataRenderer data={section.content} />
                            </div>
                        </div>
                    ))}
                </div>
            );
        }

        // Fallback for old string format (Try to render markdown)
        return (
            <div className="space-y-1.5 mt-0.5">
                <div className="text-[10px] text-zinc-400/80 prose prose-invert prose-xs max-w-none bg-black/20 p-2 rounded-md border border-white/5 italic">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {typeof parsedData === 'string' ? parsedData : JSON.stringify(parsedData)}
                    </ReactMarkdown>
                </div>
            </div>
        );
    }

    // --- 4. Financial Data ---
    if (['get_financials', 'get_price_history_stats', 'get_valuation_ratios', 'get_fundamental_growth_stats'].includes(toolName || '')) {
        return (
            <div className="space-y-1.5 mt-0.5">
                <div className="flex items-center gap-2 text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">
                    <Activity className="w-3 h-3" />
                    <span>Financial Metrics</span>
                </div>
                <div className="bg-black/20 rounded-lg border border-white/5 p-2">
                    <SmartDataRenderer data={parsedData} />
                </div>
            </div>
        );
    }

    // --- Default Fallback ---
    // Try smart render first if object
    if (typeof parsedData === 'object' && parsedData !== null) {
        return (
            <div className="bg-black/20 rounded-lg border border-white/5 p-2">
                <SmartDataRenderer data={parsedData} />
            </div>
        );
    }

    return (
        <div className="text-sm text-zinc-300 prose prose-invert prose-sm max-w-none break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(parsedData)}</ReactMarkdown>
        </div>
    );
};

export default ToolOutputRenderer;
