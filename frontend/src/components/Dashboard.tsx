
import React, { useEffect, useState } from 'react';
import { getAnalysisResult } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Activity, BarChart3, TrendingUp, Users, AlertCircle, CheckCircle2, ArrowUpRight, ArrowDownRight, Minus, Sparkles } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell } from 'recharts';
import clsx from 'clsx';
import LogViewer from './LogViewer';
import { ChatWidget } from './ChatWidget';

interface DashboardProps {
    sessionId: string;
    onBack: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ sessionId, onBack }) => {
    const [data, setData] = useState<any>(null);
    const [status, setStatus] = useState<string>('processing');
    const [activeTab, setActiveTab] = useState('summary');

    // --- Chat Selection Logic ---
    const [selectionTooltip, setSelectionTooltip] = useState<{ x: number, y: number, text: string } | null>(null);
    const [chatContext, setChatContext] = useState<{ selectedText: string } | undefined>(undefined);

    useEffect(() => {
        const handleMouseUp = (e: MouseEvent) => {
            // Ignore clicks on the tooltip itself or inside the Chat Widget
            if ((e.target as HTMLElement).closest('#ask-ai-tooltip')) return;
            if ((e.target as HTMLElement).closest('#chat-widget-container')) return;

            const selection = window.getSelection();
            if (selection && selection.toString().trim().length > 5) {
                // Position relative to cursor with a slight offset
                setSelectionTooltip({
                    x: e.clientX,
                    y: e.clientY - 40, // Above the cursor
                    text: selection.toString().trim()
                });
            } else {
                setSelectionTooltip(null);
            }
        };

        // Only listen for selection inside the dashboard
        const dashboardEl = document.getElementById('dashboard-content');
        if (dashboardEl) {
            dashboardEl.addEventListener('mouseup', handleMouseUp);
        } else {
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);

    const handleAskAI = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        if (selectionTooltip) {
            setChatContext({ selectedText: selectionTooltip.text });
            setSelectionTooltip(null);
            // Clear browser selection
            window.getSelection()?.removeAllRanges();
        }
    };
    // ----------------------------

    useEffect(() => {
        let interval: any;

        const fetchData = async () => {
            try {
                const result = await getAnalysisResult(sessionId);
                setData(result);
                setStatus(result.status);

                if (result.status === 'completed' || result.status === 'failed') {
                    clearInterval(interval);
                }
            } catch (error) {
                console.error("Error fetching status:", error);
            }
        };

        fetchData();
        interval = setInterval(fetchData, 3000); // Poll every 3s

        return () => clearInterval(interval);
    }, [sessionId]);

    if (!data || status === 'processing') {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 w-full max-w-4xl mx-auto">
                <div className="text-center space-y-4">
                    <div className="relative w-16 h-16 mx-auto">
                        <div className="absolute inset-0 border-4 border-muted rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                    </div>
                    <p className="text-xl font-medium animate-pulse">Running Multi-Agent Analysis...</p>
                    <p className="text-muted-foreground text-sm">Please wait while our AI analysts research and synthesize data.</p>
                </div>

                {/* Live Scratchpad */}
                <div className="w-full">
                    <LogViewer sessionId={sessionId} initialLogs={data?.logs || []} isProcessing={true} />
                </div>
            </div>
        );
    }

    if (status === 'failed') {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4 text-destructive">
                <AlertCircle className="w-12 h-12" />
                <p>Analysis Generation Failed.</p>
                <div className="w-full max-w-md h-32 bg-secondary/20 rounded p-2 text-xs overflow-auto font-mono text-foreground text-left">
                    {data?.report?.logs?.map((log: string, i: number) => (
                        <div key={i} className="mb-1 text-muted-foreground">&gt; {log}</div>
                    ))}
                </div>
                <button onClick={onBack} className="text-sm underline">Go Back</button>
            </div>
        );
    }

    const report = data.report || {};
    const { detailed_breakdown: details, final_signal, overall_confidence, summary } = report;
    const logs = data.logs || [];

    const getSignalColor = (signal: string) => {
        if (!signal) return "text-gray-500";
        const s = signal.toUpperCase();
        if (s === 'BUY' || s === 'BULLISH' || s === 'STRONG') return "text-emerald-400";
        if (s === 'SELL' || s === 'BEARISH' || s === 'WEAK') return "text-rose-400";
        return "text-amber-400";
    };

    const getSentimentStyles = (signal: string | number) => {
        // Handle numeric scores (0-10)
        if (typeof signal === 'number') {
            if (signal >= 7) return "bg-slate-950/50 border-l-4 border-l-emerald-500 border-y border-r border-slate-800/50";
            if (signal <= 4) return "bg-slate-950/50 border-l-4 border-l-rose-500 border-y border-r border-slate-800/50";
            return "bg-slate-950/50 border-l-4 border-l-amber-500 border-y border-r border-slate-800/50";
        }

        if (!signal) return "bg-slate-950/50 border border-slate-800/50";
        const s = String(signal).toUpperCase();

        if (s === 'BUY' || s === 'BULLISH' || s === 'STRONG' || s === 'ACCELERATING' || s === 'UNDERVALUED')
            return "bg-slate-950/50 border-l-4 border-l-emerald-500 border-y border-r border-slate-800/50";

        if (s === 'SELL' || s === 'BEARISH' || s === 'WEAK' || s === 'STAGNANT' || s === 'OVERVALUED')
            return "bg-slate-950/50 border-l-4 border-l-rose-500 border-y border-r border-slate-800/50";

        return "bg-slate-950/50 border-l-4 border-l-amber-500 border-y border-r border-slate-800/50";
    };

    const getBadgeStyles = (signal: string) => {
        if (!signal) return "bg-gray-500/10 text-gray-400 border-gray-500/20";
        const s = String(signal).toUpperCase();

        if (s === 'BUY' || s === 'BULLISH' || s === 'STRONG' || s === 'ACCELERATING' || s === 'UNDERVALUED')
            return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]";

        if (s === 'SELL' || s === 'BEARISH' || s === 'WEAK' || s === 'STAGNANT' || s === 'OVERVALUED')
            return "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.1)]";

        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    };

    const getRadarData = (details: any) => {
        if (!details || !details.fundamental || !details.fundamental.details) return [];

        const d = details.fundamental.details;
        const score = (val: string) => {
            const v = (val || '').toLowerCase();
            if (v.includes('strong') || v.includes('accelerating') || v.includes('undervalued')) return 90;
            if (v.includes('stable') || v.includes('fair')) return 70;
            if (v.includes('weak') || v.includes('slowing') || v.includes('overvalued')) return 40;
            return 60; // Default
        };

        const profitMargin = parseFloat(d.profit_margin) || 0;

        return [
            { subject: 'Health', A: score(d.financial_health), fullMark: 100 },
            { subject: 'Growth', A: score(d.growth_trajectory), fullMark: 100 },
            { subject: 'Value', A: score(d.valuation), fullMark: 100 },
            { subject: 'Moat', A: profitMargin > 20 ? 85 : profitMargin > 10 ? 65 : 40, fullMark: 100 },
            { subject: 'Safety', A: (parseFloat(d.debt_to_equity) || 0) < 0.5 ? 90 : (parseFloat(d.debt_to_equity) || 0) < 1.0 ? 65 : 40, fullMark: 100 },
        ];
    };



    const tabs = [
        { id: 'summary', label: 'Summary', icon: FileText },
        { id: 'technical', label: 'Technical', icon: Activity },
        { id: 'fundamental', label: 'Fundamental', icon: BarChart3 },
        { id: 'sector', label: 'Sector', icon: TrendingUp },
        { id: 'management', label: 'Management', icon: Users },
        { id: 'quant', label: 'Quant', icon: BarChart3 },
        { id: 'risk', label: 'Risk', icon: AlertCircle },
        { id: 'logs', label: 'Agent Logs', icon: FileText },
    ];

    return (
        <div className="w-full max-w-6xl mx-auto px-4 pb-20">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-8">
                <button onClick={onBack} className="text-sm text-muted-foreground hover:text-foreground mb-4">
                    &larr; Analyze Another
                </button>
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-5xl font-black tracking-tighter text-white mb-2">{data.ticker}</h1>
                        <p className="text-slate-500 text-sm font-medium tracking-wide uppercase">Analysis Report • {new Date(data.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                        <div className={clsx("text-4xl font-bold", getSignalColor(final_signal))}>
                            {final_signal}
                        </div>
                        <div className="text-sm text-muted-foreground">
                            Confidence: {(overall_confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Tabs */}
            <div className="flex space-x-2 overflow-x-auto pb-2 mb-6 border-b border-border/50">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap",
                                activeTab === tab.id
                                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105"
                                    : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                            )}
                        >
                            <Icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    )
                })}
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'logs' && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                        <LogViewer sessionId={sessionId} initialLogs={logs} isProcessing={false} />
                    </motion.div>
                )}

                {activeTab === 'summary' && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                        <div className={clsx("p-6 rounded-xl backdrop-blur-sm transition-all duration-500", getSentimentStyles(final_signal))}>
                            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-400">
                                <CheckCircle2 className={clsx("w-5 h-5", getSignalColor(final_signal))} />
                                Executive Summary
                            </h3>
                            <p className="leading-relaxed text-slate-400 text-[15px] max-w-4xl">{summary}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Quick stats mini-cards */}
                            <div className={clsx("p-4 rounded-xl border transition-colors", getSentimentStyles(details?.technical?.signal))}>
                                <div className="text-sm text-muted-foreground mb-1">Technical Signal</div>
                                <div className={clsx("font-semibold text-lg", getSignalColor(details?.technical?.signal))}>{details?.technical?.signal}</div>
                            </div>
                            <div className={clsx("p-4 rounded-xl border transition-colors", getSentimentStyles(details?.fundamental?.signal))}>
                                <div className="text-sm text-muted-foreground mb-1">Fundamental Signal</div>
                                <div className={clsx("font-semibold text-lg", getSignalColor(details?.fundamental?.signal))}>{details?.fundamental?.signal}</div>
                            </div>
                            <div className={clsx("p-4 rounded-xl border transition-colors", getSentimentStyles(details?.risk?.bear_case_probability > 50 ? 'WEAK' : 'STRONG'))}>
                                <div className="text-sm text-muted-foreground mb-1">Risk Level</div>
                                <div className={clsx("font-semibold text-lg", details?.risk?.bear_case_probability > 50 ? "text-rose-400" : "text-emerald-400")}>
                                    {details?.risk?.bear_case_probability}% Downside Prob
                                </div>
                            </div>
                            <div className={clsx("p-4 rounded-xl border transition-colors", getSentimentStyles(details?.quant?.valuation_score))}>
                                <div className="text-sm text-muted-foreground mb-1">Quant Score</div>
                                <div className="font-semibold text-lg text-blue-400">
                                    Val: {details?.quant?.valuation_score}/10 • Grow: {details?.quant?.growth_score}/10
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* QUANT TAB SPECIFIC RENDERER */}
                {activeTab === 'quant' && details?.quant && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className={clsx("p-6 rounded-xl shadow-sm transition-all", getSentimentStyles(details.quant.valuation_score))}>
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-bold capitalize text-indigo-400">Quantitative Analysis</h3>
                            <div className="flex gap-4">
                                <div className="text-center">
                                    <div className={clsx("text-2xl font-bold", getSignalColor(details.quant.valuation_score > 7 ? 'STRONG' : details.quant.valuation_score < 4 ? 'WEAK' : 'NEUTRAL'))}>{details.quant.valuation_score}/10</div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-1">Valuation</div>
                                </div>
                                <div className="text-center">
                                    <div className={clsx("text-2xl font-bold", getSignalColor(details.quant.growth_score > 7 ? 'STRONG' : details.quant.growth_score < 4 ? 'WEAK' : 'NEUTRAL'))}>{details.quant.growth_score}/10</div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-1">Growth</div>
                                </div>
                                <div className="text-center">
                                    <div className={clsx("text-2xl font-bold", getSignalColor(details.quant.financial_health_score > 7 ? 'STRONG' : details.quant.financial_health_score < 4 ? 'WEAK' : 'NEUTRAL'))}>{details.quant.financial_health_score}/10</div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-1">Health</div>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-6">
                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Summary</h4>
                                <p className="bg-slate-900 border border-slate-800 p-5 rounded-lg text-lg leading-relaxed text-slate-400 font-serif shadow-inner">
                                    {details.quant.summary}
                                </p>
                            </div>
                            {details.quant.key_metrics && (
                                <div>
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 mt-6">Key Data</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {Object.entries(details.quant.key_metrics).map(([key, value]) => (
                                            <div key={key} className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors group">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-2 group-hover:text-slate-400" title={key.replace(/_/g, ' ')}>{key.replace(/_/g, ' ')}</div>
                                                <div className="font-mono text-sm font-semibold truncate text-slate-200 group-hover:text-white" title={String(value)}>{String(value)}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* RISK TAB SPECIFIC RENDERER */}
                {activeTab === 'risk' && details?.risk && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className={clsx("p-6 rounded-xl border shadow-sm transition-all", getSentimentStyles(details?.risk?.bear_case_probability > 50 ? 'WEAK' : 'STRONG'))}>
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-semibold capitalize text-rose-400">Risk Assessment</h3>
                            <span className={clsx("px-3 py-1 rounded-full text-sm font-bold border", details.risk.bear_case_probability > 50 ? "bg-rose-500/10 text-rose-400 border-rose-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20")}>
                                Bear Probability: {details.risk.bear_case_probability}%
                            </span>
                        </div>

                        <div className="space-y-6">
                            {/* Worst Case */}
                            <div className="border-l-4 border-red-500 pl-4 py-1">
                                <h4 className="text-lg font-medium text-red-500 uppercase tracking-wider mb-1">Worst Case Scenario</h4>
                                <p className="text-lg leading-relaxed italic text-muted-foreground">
                                    "{details.risk.worst_case_scenario}"
                                </p>
                            </div>

                            {/* Downside Risks */}
                            <div>
                                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Downside Risks</h4>
                                <ul className="space-y-2">
                                    {details.risk.downside_risks?.map((risk: string, i: number) => (
                                        <li key={i} className="flex items-start gap-2 p-3 bg-transparent border border-white/5 rounded-md hover:bg-white/5 transition-colors">
                                            <AlertCircle className="w-5 h-5 text-red-500/80 shrink-0 mt-0.5" />
                                            <span className="text-slate-300 text-sm leading-relaxed">{risk}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Macro Threats */}
                            {details.risk.macro_threats && (
                                <div>
                                    <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-2">Macro Threats</h4>
                                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {details.risk.macro_threats.map((threat: string, i: number) => (
                                            <li key={i} className="flex items-center gap-2 p-2 border border-border/30 rounded-md text-sm">
                                                <TrendingUp className="w-4 h-4 text-orange-400 rotate-180" />
                                                {threat}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Fraud Risk */}
                            {details.risk.fraud_risk && (
                                <div className="mt-4 p-4 bg-red-900/10 border border-red-900/20 rounded-lg">
                                    <h4 className="text-red-500 font-bold flex items-center gap-2 mb-2">
                                        <Activity className="w-5 h-5" />
                                        Forensic Analysis
                                    </h4>
                                    <p className="text-red-300/80">{details.risk.fraud_risk}</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* TECHNICAL TAB SPECIFIC RENDERER */}
                {activeTab === 'technical' && details?.technical && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
                        {/* Signal Header with Gauge */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className={clsx("md:col-span-2 p-6 rounded-xl shadow-sm transition-all", getSentimentStyles(details.technical.signal))}>
                                <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-indigo-400">
                                    <Activity className={clsx("w-5 h-5", getSignalColor(details.technical.signal))} />
                                    Technical Analysis
                                </h3>
                                <div className="bg-slate-900/50 border border-white/5 p-5 rounded-lg text-lg leading-relaxed text-slate-300 whitespace-pre-line font-serif">
                                    {details.technical.reasoning}
                                </div>
                            </div>
                            <div className="p-6 rounded-xl bg-card border border-border/50 flex flex-col items-center justify-center relative">
                                <div className="text-sm text-muted-foreground absolute top-4 left-4">Trend Signal</div>
                                <div className="h-32 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={[
                                                    { name: 'Bearish', value: 1 },
                                                    { name: 'Neutral', value: 1 },
                                                    { name: 'Bullish', value: 1 }
                                                ]}
                                                cx="50%"
                                                cy="50%"
                                                startAngle={180}
                                                endAngle={0}
                                                innerRadius={40}
                                                outerRadius={60}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                <Cell fill={details.technical.signal === 'SELL' ? '#ef4444' : '#334155'} />
                                                <Cell fill={details.technical.signal === 'HOLD' ? '#eab308' : '#334155'} />
                                                <Cell fill={details.technical.signal === 'BUY' ? '#22c55e' : '#334155'} />
                                            </Pie>
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className={clsx("text-2xl font-bold -mt-8", getSignalColor(details.technical.signal))}>
                                    {details.technical.signal}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                    Confidence: {(details.technical.confidence * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>

                        {/* Indicators Grid */}
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            {/* Current Price */}
                            <div className="p-4 rounded-xl bg-secondary/10 border border-border/30">
                                <div className="text-xs text-muted-foreground uppercase">Current Price</div>
                                <div className="text-2xl font-mono font-bold mt-1">${details.technical.metrics.current_price?.toFixed(2)}</div>
                                <div className="flex items-center gap-1 text-xs mt-2 text-muted-foreground">
                                    Trend: <span className={details.technical.metrics.trend === 'Uptrend' ? "text-green-500" : "text-red-500"}>{details.technical.metrics.trend}</span>
                                </div>
                            </div>

                            {/* RSI */}
                            <div className="p-4 rounded-xl bg-secondary/10 border border-border/30">
                                <div className="text-xs text-muted-foreground uppercase flex justify-between">
                                    <span>RSI (14)</span>
                                    <span className={clsx("font-bold", (details.technical.metrics.rsi > 70 || details.technical.metrics.rsi < 30) ? "text-yellow-500" : "text-green-500")}>
                                        {details.technical.metrics.rsi > 70 ? "Overbought" : details.technical.metrics.rsi < 30 ? "Oversold" : "Neutral"}
                                    </span>
                                </div>
                                <div className="text-2xl font-mono font-bold mt-1">{details.technical.metrics.rsi?.toFixed(1) || "N/A"}</div>
                                {/* RSI Bar */}
                                <div className="w-full h-2 bg-slate-800 rounded-full mt-2 overflow-hidden relative">
                                    <div className="absolute top-0 bottom-0 w-full flex">
                                        <div className="w-[30%] bg-green-900/30 border-r border-slate-700"></div>
                                        <div className="w-[40%] bg-slate-800"></div>
                                        <div className="w-[30%] bg-red-900/30 border-l border-slate-700"></div>
                                    </div>
                                    <div
                                        className="h-full w-1 bg-white absolute top-0"
                                        style={{ left: `${Math.min(Math.max(details.technical.metrics.rsi || 50, 0), 100)}% ` }}
                                    ></div>
                                </div>
                            </div>

                            {/* MACD */}
                            <div className="p-4 rounded-xl bg-secondary/10 border border-border/30">
                                <div className="text-xs text-muted-foreground uppercase">MACD Signal</div>
                                <div className={clsx("text-2xl font-mono font-bold mt-1 uppercase",
                                    details.technical.metrics.macd_signal === 'Bullish' ? "text-green-500" :
                                        details.technical.metrics.macd_signal === 'Bearish' ? "text-red-500" : "text-yellow-500")}>
                                    {details.technical.metrics.macd_signal || "N/A"}
                                </div>
                                <div className="text-xs text-muted-foreground mt-2">
                                    Momentum Indicator
                                </div>
                            </div>

                            {/* Volume */}
                            <div className="p-4 rounded-xl bg-secondary/10 border border-border/30">
                                <div className="text-xs text-muted-foreground uppercase">Volume Intensity</div>
                                <div className="text-2xl font-mono font-bold mt-1">{details.technical.metrics.volume_analysis || "Neutral"}</div>
                                <div className="text-xs text-muted-foreground mt-2">
                                    Relative Volume
                                </div>
                            </div>
                        </div>

                        {/* Moving Averages Signals */}
                        {details.technical.metrics.moving_average_signals && Object.keys(details.technical.metrics.moving_average_signals).length > 0 && (
                            <div className="grid grid-cols-3 gap-4">
                                {Object.entries(details.technical.metrics.moving_average_signals).map(([ma, signal]: [string, any]) => (
                                    <div key={ma} className="flex items-center justify-between p-3 bg-secondary/10 rounded-lg border border-border/30">
                                        <span className="text-sm font-medium uppercase text-muted-foreground">{ma.replace('_', ' ')}</span>
                                        <span className={clsx("flex items-center gap-1 text-sm font-bold",
                                            signal === 'Bullish' ? "text-green-500" : signal === 'Bearish' ? "text-red-500" : "text-yellow-500"
                                        )}>
                                            {signal === 'Bullish' ? <ArrowUpRight className="w-4 h-4" /> :
                                                signal === 'Bearish' ? <ArrowDownRight className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                                            {signal}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Support/Resistance */}
                        <div className="p-6 rounded-xl bg-secondary/5 border border-border/30 relative mt-4">
                            <h4 className="text-sm font-semibold uppercase text-muted-foreground mb-6">Key Levels</h4>
                            <div className="relative h-20 w-full flex items-center mt-8">
                                {/* Base Line */}
                                <div className="absolute w-full h-1 bg-slate-800 rounded-full"></div>

                                {/* Support Marker */}
                                {details.technical.metrics.support_level && (
                                    <div className="absolute flex flex-col items-center top-1/2 mt-2" style={{ left: '20%', transform: 'translateX(-50%)' }}>
                                        <div className="w-2 h-2 bg-green-500 rounded-full mb-1"></div>
                                        <div className="text-xs text-green-500 font-mono">${details.technical.metrics.support_level}</div>
                                        <div className="text-[10px] text-muted-foreground uppercase mt-1">Support</div>
                                    </div>
                                )}

                                {/* Price Marker */}
                                <div className="absolute flex flex-col-reverse items-center z-10 bottom-1/2 mb-2" style={{
                                    left: `${details.technical.metrics.support_level && details.technical.metrics.resistance_level
                                        ? Math.max(0, Math.min(100, 20 + ((details.technical.metrics.current_price - details.technical.metrics.support_level) / (details.technical.metrics.resistance_level - details.technical.metrics.support_level)) * 60))
                                        : 50
                                        }% `,
                                    transform: 'translateX(-50%)'
                                }}>
                                    <div className="w-4 h-4 bg-white rounded-full border-4 border-slate-900 mt-1 shadow-[0_0_10px_rgba(255,255,255,0.5)]"></div>
                                    <div className="text-sm font-bold font-mono">${details.technical.metrics.current_price}</div>
                                    <div className="text-[10px] text-muted-foreground uppercase mb-1">Current</div>
                                </div>

                                {/* Resistance Marker */}
                                {details.technical.metrics.resistance_level && (
                                    <div className="absolute flex flex-col items-center top-1/2 mt-2" style={{ left: '80%', transform: 'translateX(-50%)' }}>
                                        <div className="w-2 h-2 bg-red-500 rounded-full mb-1"></div>
                                        <div className="text-xs text-red-500 font-mono">${details.technical.metrics.resistance_level}</div>
                                        <div className="text-[10px] text-muted-foreground uppercase mt-1">Resistance</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* FUNDAMENTAL TAB SPECIFIC RENDERER */}
                {activeTab === 'fundamental' && details?.fundamental && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className={clsx("lg:col-span-2 p-6 rounded-xl shadow-sm flex flex-col transition-all", getSentimentStyles(details.fundamental.signal))}>
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-xl font-bold flex items-center gap-2 text-indigo-400">
                                        <BarChart3 className={clsx("w-5 h-5", getSignalColor(details.fundamental.signal))} />
                                        Fundamental Analysis
                                    </h3>
                                    <span className={clsx("px-3 py-1 rounded-full text-xs font-bold border", getBadgeStyles(details.fundamental.signal))}>
                                        {details.fundamental.signal}
                                    </span>
                                </div>
                                <div className="bg-slate-900/50 border border-slate-800/50 p-5 rounded-lg text-lg leading-relaxed text-slate-400 whitespace-pre-line font-serif shadow-inner">
                                    {details.fundamental.reasoning}
                                </div>
                            </div>

                            {/* RADAR CHART & STATUS CARD */}
                            <div className="lg:col-span-1 p-6 rounded-xl bg-slate-950/50 border border-slate-800/50 flex flex-col justify-between">
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 text-center">Quality Profile</h4>
                                <div className="h-64 w-full relative">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={getRadarData(details)}>
                                            <PolarGrid stroke="#334155" />
                                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                            <Radar
                                                name="Fundamentals"
                                                dataKey="A"
                                                stroke="#10b981"
                                                strokeWidth={2}
                                                fill="#10b981"
                                                fillOpacity={0.3}
                                            />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="space-y-3 mt-4 px-2">
                                    <div className="flex justify-between items-center text-sm border-b border-slate-800 pb-2">
                                        <span className="text-slate-500">Health</span>
                                        <span className={clsx("font-bold", details.fundamental.details.financial_health === 'Strong' ? "text-emerald-400" : "text-amber-400")}>{details.fundamental.details.financial_health}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm border-b border-slate-800 pb-2">
                                        <span className="text-slate-500">Growth</span>
                                        <span className={clsx("font-bold", details.fundamental.details.growth_trajectory === 'Accelerating' ? "text-emerald-400" : "text-amber-400")}>{details.fundamental.details.growth_trajectory}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-500">Valuation</span>
                                        <span className={clsx("font-bold", details.fundamental.details.valuation === 'Undervalued' ? "text-emerald-400" : details.fundamental.details.valuation === 'Fair' ? "text-amber-400" : "text-rose-400")}>{details.fundamental.details.valuation}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Ratios Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">P/E Ratio</div>
                                <div className={clsx("text-lg font-mono font-bold mt-1",
                                    (details.fundamental.details.pe_ratio > 30) ? "text-red-400" : "text-green-400")}>
                                    {details.fundamental.details.pe_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">P/B Ratio</div>
                                <div className="text-lg font-mono font-bold text-foreground mt-1">
                                    {details.fundamental.details.pb_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">PEG</div>
                                <div className={clsx("text-lg font-mono font-bold mt-1",
                                    (details.fundamental.details.peg_ratio < 1.0) ? "text-green-400" : "text-yellow-400")}>
                                    {details.fundamental.details.peg_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Debt/Eq</div>
                                <div className="text-lg font-mono font-bold text-foreground mt-1">
                                    {details.fundamental.details.debt_to_equity || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Rev Growth</div>
                                <div className="text-lg font-mono font-bold text-green-400 mt-1">
                                    {details.fundamental.details.revenue_growth ? `${details.fundamental.details.revenue_growth}% ` : "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Profit Margin</div>
                                <div className="text-lg font-mono font-bold text-green-400 mt-1">
                                    {details.fundamental.details.profit_margin ? `${details.fundamental.details.profit_margin}% ` : "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-transparent border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Div Yield</div>
                                <div className="text-lg font-mono font-bold text-green-400 mt-1">
                                    {details.fundamental.details.dividend_yield ? `${details.fundamental.details.dividend_yield}% ` : "N/A"}
                                </div>
                            </div>
                        </div>

                        {/* Advanced Efficiency & Risk Metrics (NEW) */}
                        <div className="mt-4">
                            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Advanced Efficiency & Risk Keys</h4>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                                {/* ROCE */}
                                <div className="p-3 bg-slate-900/30 border border-indigo-500/20 rounded-lg">
                                    <div className="text-[10px] text-indigo-300 uppercase tracking-wider">ROCE (Return on Cap)</div>
                                    <div className={clsx("text-lg font-mono font-bold mt-1",
                                        (details.fundamental.details.return_on_capital_employed > 20) ? "text-emerald-400" :
                                            (details.fundamental.details.return_on_capital_employed > 10) ? "text-emerald-200" : "text-slate-400"
                                    )}>
                                        {details.fundamental.details.return_on_capital_employed ? `${details.fundamental.details.return_on_capital_employed}%` : "N/A"}
                                    </div>
                                </div>

                                {/* Altman Z-Score */}
                                <div className={clsx("p-3 border rounded-lg",
                                    details.fundamental.details.altman_z_score > 3 ? "bg-emerald-900/10 border-emerald-500/30" :
                                        details.fundamental.details.altman_z_score < 1.8 ? "bg-rose-900/10 border-rose-500/30" : "bg-slate-900/30 border-white/10"
                                )}>
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Altman Z-Score</div>
                                    <div className={clsx("text-lg font-mono font-bold mt-1",
                                        details.fundamental.details.altman_z_score > 3 ? "text-emerald-400" :
                                            details.fundamental.details.altman_z_score < 1.8 ? "text-rose-400" : "text-yellow-400"
                                    )}>
                                        {details.fundamental.details.altman_z_score || "N/A"}
                                    </div>
                                    <div className="text-[10px] text-slate-500">
                                        {details.fundamental.details.altman_z_score > 3 ? "Safe Zone" :
                                            details.fundamental.details.altman_z_score < 1.8 ? "Distress Risk" : "Grey Zone"}
                                    </div>
                                </div>

                                {/* Beneish M-Score */}
                                <div className={clsx("p-3 border rounded-lg",
                                    details.fundamental.details.beneish_m_score < -1.78 ? "bg-emerald-900/10 border-emerald-500/30" :
                                        "bg-rose-900/10 border-rose-500/30"
                                )}>
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Beneish M-Score</div>
                                    <div className={clsx("text-lg font-mono font-bold mt-1",
                                        details.fundamental.details.beneish_m_score < -1.78 ? "text-emerald-400" : "text-rose-400"
                                    )}>
                                        {details.fundamental.details.beneish_m_score || "N/A"}
                                    </div>
                                    <div className="text-[10px] text-slate-500">
                                        {details.fundamental.details.beneish_m_score < -1.78 ? "Unlikely Fraud" : "Check Accruals"}
                                    </div>
                                </div>

                                {/* Interest Coverage */}
                                <div className="p-3 bg-slate-900/30 border border-white/10 rounded-lg">
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Interest Cov.</div>
                                    <div className={clsx("text-lg font-mono font-bold mt-1",
                                        (details.fundamental.details.interest_coverage > 5) ? "text-emerald-400" :
                                            (details.fundamental.details.interest_coverage < 1.5) ? "text-rose-400" : "text-slate-200"
                                    )}>
                                        {details.fundamental.details.interest_coverage ? `${details.fundamental.details.interest_coverage}x` : "N/A"}
                                    </div>
                                </div>

                                {/* DSI */}
                                <div className="p-3 bg-slate-900/30 border border-white/10 rounded-lg">
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Inv Days (DSI)</div>
                                    <div className="text-lg font-mono font-bold text-slate-200 mt-1">
                                        {details.fundamental.details.days_sales_in_inventory ? Math.round(details.fundamental.details.days_sales_in_inventory) : "N/A"}
                                    </div>
                                </div>
                            </div>
                        </div>

                    </motion.div>
                )}

                {/* STANDARD RENDERER FOR OTHER TABS */}
                {activeTab !== 'summary' && activeTab !== 'logs' && activeTab !== 'quant' && activeTab !== 'risk' && activeTab !== 'technical' && activeTab !== 'fundamental' && details && details[activeTab] && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className={clsx("p-6 rounded-xl border shadow-sm transition-all", getSentimentStyles(details[activeTab].signal))}>
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-bold capitalize text-indigo-400">{activeTab} Analysis</h3>
                            <span className={clsx("px-3 py-1 rounded-full text-xs font-bold border", getBadgeStyles(details[activeTab].signal))}>
                                {details[activeTab].signal}
                            </span>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Reasoning</h4>
                                <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg text-lg leading-relaxed text-slate-400 whitespace-pre-line font-serif shadow-inner">
                                    {details[activeTab].reasoning || details[activeTab].summary || "No detailed reasoning provided."}
                                </div>
                            </div>

                            {details[activeTab].metrics && (
                                <div>
                                    <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <Activity className="w-4 h-4" />
                                        Key Metrics
                                    </h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {Object.entries(details[activeTab].metrics).map(([key, value]) => {
                                            const isLongText = String(value).length > 20;
                                            const isNumber = /^\d/.test(String(value));

                                            return (
                                                <div key={key} className="p-5 bg-slate-900/40 border border-slate-800/60 rounded-xl hover:bg-slate-900/60 hover:border-indigo-500/30 transition-all duration-300 group">
                                                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 group-hover:text-indigo-400 transition-colors">
                                                        {key.replace(/_/g, ' ')}
                                                    </div>
                                                    <div className={clsx(
                                                        "text-slate-200 leading-relaxed",
                                                        isNumber ? "font-mono text-xl font-medium" : "font-sans text-base font-normal text-slate-300",
                                                        isLongText ? "text-sm" : ""
                                                    )}>
                                                        {String(value)}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                            {/* Specific rendering for Management Risks if mostly standard but has extra list */}
                            {activeTab === 'management' && details.management.risks && (
                                <div className="mt-6 border-t border-slate-800 pt-6">
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Identified Risks</h4>
                                    <ul className="space-y-3">
                                        {details.management.risks.map((r: string, i: number) => (
                                            <li key={i} className="flex items-start gap-3 text-slate-400 text-sm leading-relaxed">
                                                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-rose-500/50 shrink-0"></span>
                                                {r}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Selection Tooltip */}
            <AnimatePresence>
                {selectionTooltip && (
                    <motion.button
                        initial={{ opacity: 0, scale: 0.8, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        id="ask-ai-tooltip"
                        onClick={handleAskAI}
                        style={{ top: selectionTooltip.y, left: selectionTooltip.x }}
                        className="fixed z-[100] transform -translate-x-1/2 -translate-y-full mb-2 bg-indigo-600 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 hover:bg-indigo-500 hover:scale-105 transition-all"
                    >
                        <Sparkles className="w-3 h-3" />
                        Ask AI
                    </motion.button>
                )}
            </AnimatePresence>

            {/* Chat Widget */}
            <ChatWidget
                sessionId={sessionId} // This is the user session ID (client side)
                reportId={data.id}    // This is the backend Report ID
                activeTab={activeTab}
                initialContext={chatContext}
                onCloseSelection={() => setChatContext(undefined)}
            />
        </div>
    );
};

export default Dashboard;
