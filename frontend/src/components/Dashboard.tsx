import React, { useEffect, useState } from 'react';
import { getAnalysisResult } from '../api';
import { motion } from 'framer-motion';
import { Activity, BarChart3, TrendingUp, Users, AlertCircle, CheckCircle2, FileText, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import clsx from 'clsx';
import LogViewer from './LogViewer';

interface DashboardProps {
    sessionId: string;
    onBack: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ sessionId, onBack }) => {
    const [data, setData] = useState<any>(null);
    const [status, setStatus] = useState<string>('processing');
    const [activeTab, setActiveTab] = useState('summary');

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
        interval = setInterval(fetchData, 15000); // Poll every 15s

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
                    <LogViewer sessionId={sessionId} isProcessing={true} />
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
        if (s === 'BUY' || s === 'BULLISH') return "text-green-500";
        if (s === 'SELL' || s === 'BEARISH') return "text-red-500";
        return "text-yellow-500";
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
        <div className="w-full max-w-5xl mx-auto p-4 pb-20">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-8">
                <button onClick={onBack} className="text-sm text-muted-foreground hover:text-foreground mb-4">
                    &larr; Analyze Another
                </button>
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">{data.ticker}</h1>
                        <p className="text-muted-foreground text-sm">Analysis Report • {new Date(data.created_at).toLocaleDateString()}</p>
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
                                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
                                activeTab === tab.id
                                    ? "bg-primary/10 text-primary"
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
                        <div className="p-6 rounded-xl bg-card border border-border/50 shadow-sm">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-primary" />
                                Executive Summary
                            </h3>
                            <p className="leading-relaxed text-muted-foreground">{summary}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Quick stats mini-cards */}
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Technical Signal</div>
                                <div className={clsx("font-semibold", getSignalColor(details?.technical?.signal))}>{details?.technical?.signal}</div>
                            </div>
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Fundamental Signal</div>
                                <div className={clsx("font-semibold", getSignalColor(details?.fundamental?.signal))}>{details?.fundamental?.signal}</div>
                            </div>
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Risk Level</div>
                                <div className={clsx("font-semibold", details?.risk?.bear_case_probability > 50 ? "text-red-500" : "text-green-500")}>
                                    {details?.risk?.bear_case_probability}% Downside Prob
                                </div>
                            </div>
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Quant Score</div>
                                <div className="font-semibold text-blue-500">
                                    Val: {details?.quant?.valuation_score}/10 • Grow: {details?.quant?.growth_score}/10
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* QUANT TAB SPECIFIC RENDERER */}
                {activeTab === 'quant' && details?.quant && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="p-6 rounded-xl bg-card border border-border/50">
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-semibold capitalize">Quantitative Analysis</h3>
                            <div className="flex gap-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold">{details.quant.valuation_score}/10</div>
                                    <div className="text-xs text-muted-foreground">Valuation</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold">{details.quant.growth_score}/10</div>
                                    <div className="text-xs text-muted-foreground">Growth</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold">{details.quant.financial_health_score}/10</div>
                                    <div className="text-xs text-muted-foreground">Health</div>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-6">
                            <div>
                                <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-2">Summary</h4>
                                <p className="bg-secondary/20 p-4 rounded-lg text-lg leading-relaxed">
                                    {details.quant.summary}
                                </p>
                            </div>
                            {details.quant.key_metrics && (
                                <div>
                                    <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-3">Key Data</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {Object.entries(details.quant.key_metrics).map(([key, value]) => (
                                            <div key={key} className="p-3 bg-secondary/10 rounded-lg border border-border/30 overflow-hidden">
                                                <div className="text-xs text-muted-foreground capitalize truncate" title={key.replace(/_/g, ' ')}>{key.replace(/_/g, ' ')}</div>
                                                <div className="font-mono text-sm font-medium mt-1 truncate" title={String(value)}>{String(value)}</div>
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
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="p-6 rounded-xl bg-card border border-border/50">
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-semibold capitalize text-red-500">Risk Assessment</h3>
                            <span className="px-3 py-1 rounded-full text-sm font-bold bg-red-100 text-red-700">
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
                                <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-2">Downside Risks</h4>
                                <ul className="space-y-2">
                                    {details.risk.downside_risks?.map((risk: string, i: number) => (
                                        <li key={i} className="flex items-start gap-2 p-2 bg-secondary/10 rounded-md">
                                            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                                            <span>{risk}</span>
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
                            <div className="md:col-span-2 p-6 rounded-xl bg-card border border-border/50">
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-primary" />
                                    Technical Analysis
                                </h3>
                                <div className="bg-secondary/20 p-5 rounded-lg text-lg leading-relaxed text-muted-foreground whitespace-pre-line font-serif">
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
                                        style={{ left: `${Math.min(Math.max(details.technical.metrics.rsi || 50, 0), 100)}%` }}
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
                            <div className="relative h-12 w-full flex items-center">
                                {/* Base Line */}
                                <div className="absolute w-full h-1 bg-slate-800 rounded-full"></div>

                                {/* Support Marker */}
                                {details.technical.metrics.support_level && (
                                    <div className="absolute flex flex-col items-center" style={{ left: '20%' }}>
                                        <div className="w-2 h-2 bg-green-500 rounded-full mb-1"></div>
                                        <div className="text-xs text-green-500 font-mono">${details.technical.metrics.support_level}</div>
                                        <div className="text-[10px] text-muted-foreground uppercase mt-1">Support</div>
                                    </div>
                                )}

                                {/* Price Marker */}
                                <div className="absolute flex flex-col items-center z-10" style={{ left: '50%' }}>
                                    <div className="w-4 h-4 bg-white rounded-full border-4 border-slate-900 mb-1 shadow-[0_0_10px_rgba(255,255,255,0.5)]"></div>
                                    <div className="text-sm font-bold font-mono">${details.technical.metrics.current_price}</div>
                                    <div className="text-[10px] text-muted-foreground uppercase mt-1">Current</div>
                                </div>

                                {/* Resistance Marker */}
                                {details.technical.metrics.resistance_level && (
                                    <div className="absolute flex flex-col items-center" style={{ left: '80%' }}>
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
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="md:col-span-2 p-6 rounded-xl bg-card border border-border/50 flex flex-col">
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-primary" />
                                    Fundamental Analysis
                                </h3>
                                <div className="bg-secondary/20 p-5 rounded-lg text-lg leading-relaxed text-muted-foreground whitespace-pre-line font-serif">
                                    {details.fundamental.reasoning}
                                </div>
                            </div>

                            {/* RADAR CHART & STATUS CARD */}
                            <div className="p-6 rounded-xl bg-card border border-border/50 flex flex-col justify-between">
                                <div className="h-64 w-full -ml-4">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={[
                                            {
                                                subject: 'Health',
                                                A: details.fundamental.details.financial_health === 'Strong' ? 100 : details.fundamental.details.financial_health === 'Stable' ? 70 : 40,
                                                fullMark: 100,
                                            },
                                            {
                                                subject: 'Growth',
                                                A: details.fundamental.details.growth_trajectory === 'Accelerating' ? 100 : details.fundamental.details.growth_trajectory === 'Stagnant' ? 50 : 30,
                                                fullMark: 100,
                                            },
                                            {
                                                subject: 'Value',
                                                A: details.fundamental.details.valuation === 'Undervalued' ? 100 : details.fundamental.details.valuation === 'Fair' ? 70 : 40,
                                                fullMark: 100,
                                            },
                                            {
                                                subject: 'Moat',
                                                A: details.fundamental.details.financial_health === 'Strong' ? 90 : 60, // Proxy derived
                                                fullMark: 100,
                                            },
                                            {
                                                subject: 'Safety',
                                                A: details.fundamental.details.debt_to_equity && details.fundamental.details.debt_to_equity < 50 ? 90 : 60,
                                                fullMark: 100,
                                            }
                                        ]}>
                                            <PolarGrid stroke="#334155" />
                                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
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

                                <div className="space-y-3 mt-2">
                                    <div className="flex justify-between items-center px-2">
                                        <span className="text-sm text-muted-foreground">Health</span>
                                        <span className={clsx("font-bold text-sm", details.fundamental.details.financial_health === 'Strong' ? "text-green-500" : "text-yellow-500")}>
                                            {details.fundamental.details.financial_health}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center px-2">
                                        <span className="text-sm text-muted-foreground">Growth</span>
                                        <span className={clsx("font-bold text-sm", details.fundamental.details.growth_trajectory === 'Accelerating' ? "text-green-500" : "text-yellow-500")}>
                                            {details.fundamental.details.growth_trajectory}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center px-2">
                                        <span className="text-sm text-muted-foreground">Valuation</span>
                                        <span className={clsx("font-bold text-sm", details.fundamental.details.valuation === 'Undervalued' ? "text-green-500" : details.fundamental.details.valuation === 'Fair' ? "text-yellow-500" : "text-red-500")}>
                                            {details.fundamental.details.valuation}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Ratios Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">P/E Ratio</div>
                                <div className={clsx("text-lg font-mono font-bold",
                                    (details.fundamental.details.pe_ratio > 30) ? "text-red-400" : "text-green-400")}>
                                    {details.fundamental.details.pe_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">P/B Ratio</div>
                                <div className="text-lg font-mono font-bold text-foreground">
                                    {details.fundamental.details.pb_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">PEG</div>
                                <div className={clsx("text-lg font-mono font-bold",
                                    (details.fundamental.details.peg_ratio < 1.0) ? "text-green-400" : "text-yellow-400")}>
                                    {details.fundamental.details.peg_ratio || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">Debt/Eq</div>
                                <div className="text-lg font-mono font-bold text-foreground">
                                    {details.fundamental.details.debt_to_equity || "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">Rev Growth</div>
                                <div className="text-lg font-mono font-bold text-green-400">
                                    {details.fundamental.details.revenue_growth ? `${details.fundamental.details.revenue_growth}%` : "N/A"}
                                </div>
                            </div>
                            <div className="p-3 bg-secondary/10 rounded-lg border border-border/30">
                                <div className="text-[10px] text-muted-foreground uppercase">Profit Margin</div>
                                <div className="text-lg font-mono font-bold text-green-400">
                                    {details.fundamental.details.profit_margin ? `${details.fundamental.details.profit_margin}%` : "N/A"}
                                </div>
                            </div>
                        </div>

                    </motion.div>
                )}

                {/* STANDARD RENDERER FOR OTHER TABS */}
                {activeTab !== 'summary' && activeTab !== 'logs' && activeTab !== 'quant' && activeTab !== 'risk' && activeTab !== 'technical' && activeTab !== 'fundamental' && details && details[activeTab] && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="p-6 rounded-xl bg-card border border-border/50">
                        <div className="flex justify-between items-start mb-6">
                            <h3 className="text-xl font-semibold capitalize">{activeTab} Analysis</h3>
                            <span className={clsx("px-3 py-1 rounded-full text-xs font-semibold bg-secondary", getSignalColor(details[activeTab].signal))}>
                                {details[activeTab].signal}
                            </span>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-2">Reasoning</h4>
                                <div className="bg-secondary/20 p-5 rounded-lg text-lg leading-relaxed whitespace-pre-line font-serif">
                                    {details[activeTab].reasoning || details[activeTab].summary || "No detailed reasoning provided."}
                                </div>
                            </div>

                            {details[activeTab].metrics && (
                                <div>
                                    <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-3">Key Metrics</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                        {Object.entries(details[activeTab].metrics).map(([key, value]) => (
                                            <div key={key} className="p-4 bg-secondary/10 rounded-lg border border-border/30">
                                                <div className="text-base text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</div>
                                                <div className="font-mono text-xl font-medium mt-1">{String(value)}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {/* Specific rendering for Management Risks if mostly standard but has extra list */}
                            {activeTab === 'management' && details.management.risks && (
                                <div className="mt-4">
                                    <h4 className="text-lg font-medium text-muted-foreground uppercase tracking-wider mb-2">Identified Risks</h4>
                                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                        {details.management.risks.map((r: string, i: number) => (
                                            <li key={i}>{r}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
