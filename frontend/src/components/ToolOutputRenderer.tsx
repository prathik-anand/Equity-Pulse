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
                <span className="text-zinc-500 break-words">{String(data)}</span>
            </div>
        );
    }

    // Arrays
    if (Array.isArray(data)) {
        if (data.length === 0) return null;
        return (
            <div className="mt-0.5 mb-1.5">
                {label && <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">{label}</div>}
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
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider group-hover:text-zinc-400">
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

const CollapsibleReport: React.FC<{ sections: any[] }> = ({ sections }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    // Determine a summary title
    const sectionNames = sections.map(s => s.section?.replace(/_/g, ' ')).filter(Boolean);
    const title = sectionNames.length > 0
        ? `Report Loaded: ${sectionNames.slice(0, 2).join(', ')}${sectionNames.length > 2 ? ` +${sectionNames.length - 2} more` : ''}`
        : `Report Content Loaded (${sections.length} sections)`;

    return (
        <div className="mt-1">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors w-full p-2 bg-black/20 hover:bg-white/5 border border-white/5 rounded-md group text-left"
            >
                {isExpanded ? <ChevronDown className="w-4 h-4 shrink-0" /> : <ChevronRight className="w-4 h-4 shrink-0" />}
                <div className="flex flex-col">
                    <span className="font-semibold uppercase tracking-wide text-[10px] text-emerald-500/80 group-hover:text-emerald-400">
                        Report Data
                    </span>
                    <span className="truncate opacity-80">{title}</span>
                </div>
            </button>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="space-y-2.5 mt-2 pt-1">
                            {sections.map((section: any, idx: number) => (
                                <div key={idx} className="bg-black/20 rounded-lg border border-white/5 overflow-hidden">
                                    <div className="bg-white/5 px-2 py-1.5 border-b border-white/5 flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                                        <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wide">
                                            {section.section?.replace(/_/g, ' ') || 'Usage'}
                                        </span>
                                    </div>
                                    <div className="p-2">
                                        <SmartDataRenderer data={section.content} />
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
                <div className="text-sm text-zinc-500 prose prose-invert prose-sm max-w-none bg-black/20 p-2 rounded-md border border-white/5">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {typeof parsedData === 'string' ? parsedData : JSON.stringify(parsedData, null, 2)}
                    </ReactMarkdown>
                </div>
            </div>
        );
    }

    // --- New Financial Tools ---
    if (toolName === 'get_insider_trades') {
        const trades = parsedData.transactions || [];
        return (
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h4 className="text-zinc-200 font-medium text-xs uppercase tracking-wider">Insider Transactions</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${parsedData.summary?.includes('Buying') ? 'bg-emerald-500/20 text-emerald-300' :
                        parsedData.summary?.includes('Selling') ? 'bg-rose-500/20 text-rose-300' : 'bg-zinc-500/20 text-zinc-300'
                        }`}>
                        {parsedData.summary || 'Neutral'}
                    </span>
                </div>
                <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                    {trades.map((t: any, idx: number) => (
                        <div key={idx} className="bg-white/5 p-2 rounded-md flex justify-between items-center text-xs">
                            <div>
                                <div className="font-medium text-zinc-200">{t.insider}</div>
                                <div className="text-zinc-500 text-[10px]">{t.position} • {t.date}</div>
                            </div>
                            <div className="text-right">
                                <div className={t.transaction.includes('Buy') || t.transaction.includes('Purchase') ? 'text-emerald-400' : 'text-rose-400'}>
                                    {t.transaction}
                                </div>
                                <div className="text-zinc-400 text-[10px]">
                                    {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact' }).format(t.value)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (toolName === 'get_ownership_data') {
        return (
            <div className="space-y-2 text-xs">
                <h4 className="text-zinc-200 font-medium uppercase tracking-wider mb-2">Ownership & Short Interest</h4>
                <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Inst. Ownership</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {/* Risk Metrics Output */}
                            {parsedData.altman_z_score !== undefined && (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Altman Z-Score */}
                                        <div className={clsx(
                                            "p-3 rounded-lg border",
                                            parsedData.altman_z_score > 3 ? "bg-emerald-500/10 border-emerald-500/30" :
                                                parsedData.altman_z_score < 1.8 ? "bg-red-500/10 border-red-500/30" :
                                                    "bg-yellow-500/10 border-yellow-500/30"
                                        )}>
                                            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">Altman Z-Score</div>
                                            <div className="flex items-baseline gap-2">
                                                <span className={clsx(
                                                    "text-2xl font-bold",
                                                    parsedData.altman_z_score > 3 ? "text-emerald-400" :
                                                        parsedData.altman_z_score < 1.8 ? "text-red-400" :
                                                            "text-yellow-400"
                                                )}>
                                                    {parsedData.altman_z_score}
                                                </span>
                                                <span className="text-xs text-zinc-500">
                                                    {parsedData.altman_z_score > 3 ? "(Safe)" :
                                                        parsedData.altman_z_score < 1.8 ? "(Distress)" : "(Grey Zone)"}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Beneish M-Score */}
                                        <div className={clsx(
                                            "p-3 rounded-lg border",
                                            parsedData.beneish_m_score < -1.78 ? "bg-emerald-500/10 border-emerald-500/30" :
                                                "bg-red-500/10 border-red-500/30"
                                        )}>
                                            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">Beneish M-Score</div>
                                            <div className="flex items-baseline gap-2">
                                                <span className={clsx(
                                                    "text-2xl font-bold",
                                                    parsedData.beneish_m_score < -1.78 ? "text-emerald-400" : "text-red-400"
                                                )}>
                                                    {parsedData.beneish_m_score}
                                                </span>
                                                <span className="text-xs text-zinc-500">
                                                    {parsedData.beneish_m_score < -1.78 ? "(Unlikely Manipulator)" : "(Possible Manipulator)"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                        <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                                            <div className="text-[10px] text-zinc-500 uppercase">Interest Cov.</div>
                                            <div className="text-sm font-mono text-zinc-200">{parsedData.interest_coverage_ratio}x</div>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                                            <div className="text-[10px] text-zinc-500 uppercase">DSI (Days)</div>
                                            <div className="text-sm font-mono text-zinc-200">{parsedData.days_sales_in_inventory}</div>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                                            <div className="text-[10px] text-zinc-500 uppercase">Current Ratio</div>
                                            <div className="text-sm font-mono text-zinc-200">{parsedData.current_ratio}</div>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                                            <div className="text-[10px] text-zinc-500 uppercase">DSI Change</div>
                                            <div className={clsx(
                                                "text-sm font-mono",
                                                parsedData.dsi_change_pct > 0.2 ? "text-red-400" : "text-zinc-200"
                                            )}>
                                                {parsedData.dsi_change_pct ? `${(parsedData.dsi_change_pct * 100).toFixed(1)}%` : 'N/A'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Advanced Ratios Output (Existing) */}
                            {parsedData.institutional_ownership_pct ? `${(parsedData.institutional_ownership_pct * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Insider Ownership</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.insider_ownership_pct ? `${(parsedData.insider_ownership_pct * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Short Float</div>
                        <div className={`font-mono text-sm ${parsedData.short_percent_of_float > 0.15 ? 'text-amber-400' : 'text-zinc-200'}`}>
                            {parsedData.short_percent_of_float ? `${(parsedData.short_percent_of_float * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Short Ratio</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.short_ratio || 'N/A'}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (toolName === 'get_advanced_ratios') {
        return (
            <div className="space-y-2 text-xs">
                <h4 className="text-zinc-200 font-medium uppercase tracking-wider mb-2">Efficiency & Capital Allocation</h4>
                <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">ROCE</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.return_on_capital_employed ? `${(parsedData.return_on_capital_employed * 100).toFixed(2)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">ROIC (Approx)</div>
                        <div className={`font-mono text-sm ${parsedData.return_on_capital > 0.15 ? 'text-emerald-400' : 'text-zinc-200'}`}>
                            {parsedData.return_on_capital ? `${(parsedData.return_on_capital * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">FCF Yield</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.fcf_yield ? `${(parsedData.fcf_yield * 100).toFixed(2)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Payout Ratio</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.payout_ratio ? `${(parsedData.payout_ratio * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <div className="text-zinc-500 text-[10px]">Rev/Share</div>
                        <div className="text-zinc-200 font-mono text-sm">
                            {parsedData.revenue_per_share || 'N/A'}
                        </div>
                    </div>
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
                                <div className="font-medium text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors line-clamp-2">{article.title}</div>
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
            try { sections = JSON.parse(sections); } catch (e) { }
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
            return <CollapsibleReport sections={sections} />;
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
        <div className="text-sm text-zinc-500 prose prose-invert prose-sm max-w-none break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(parsedData)}</ReactMarkdown>
        </div>
    );
};

export default ToolOutputRenderer;
