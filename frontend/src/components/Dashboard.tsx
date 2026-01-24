import React, { useEffect, useState } from 'react';
import { getAnalysisResult } from '../api';
import { motion } from 'framer-motion';
import { Activity, BarChart3, TrendingUp, Users, AlertCircle, CheckCircle2, FileText } from 'lucide-react';
import clsx from 'clsx';

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
        interval = setInterval(fetchData, 2000); // Poll every 2s

        return () => clearInterval(interval);
    }, [sessionId]);

    if (!data || status === 'processing') {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 border-4 border-muted rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
                <div>
                    <p className="text-muted-foreground animate-pulse text-center mb-4">Running Multi-Agent Analysis...</p>
                    {/* Live Logs View */}
                    <div className="w-full max-w-md h-48 bg-black/50 rounded-lg p-4 font-mono text-xs text-green-400 overflow-y-auto border border-white/10 shadow-inner">
                        {data?.report?.logs?.map((log: string, i: number) => (
                            <div key={i} className="mb-1 opacity-80">&gt; {log}</div>
                        ))}
                        <div className="animate-pulse">&gt; ...</div>
                    </div>
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
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 rounded-xl bg-black/80 border border-white/10 font-mono text-sm text-green-400/90 shadow-inner">
                        <h3 className="text-white font-sans text-lg font-semibold mb-4 flex items-center gap-2">
                            System Logs
                        </h3>
                        <div className="space-y-1">
                            {logs.map((log: string, i: number) => (
                                <div key={i} className="border-b border-white/5 pb-1 last:border-0 border-dashed">
                                    <span className="text-white/30 mr-2">[{i + 1}]</span>
                                    {log}
                                </div>
                            ))}
                        </div>
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
                            {/* Quick stats mini-cards can go here */}
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Technical Signal</div>
                                <div className={clsx("font-semibold", getSignalColor(details?.technical?.signal))}>{details?.technical?.signal}</div>
                            </div>
                            <div className="p-4 rounded-xl bg-secondary/20 border border-border/50">
                                <div className="text-sm text-muted-foreground">Fundamental Signal</div>
                                <div className={clsx("font-semibold", getSignalColor(details?.fundamental?.signal))}>{details?.fundamental?.signal}</div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {activeTab !== 'summary' && activeTab !== 'logs' && details && details[activeTab] && (
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
                                <p className="bg-secondary/20 p-4 rounded-lg text-lg leading-relaxed">
                                    {details[activeTab].reasoning || details[activeTab].summary || "No detailed reasoning provided."}
                                </p>
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
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
