import React, { useState, useEffect, useRef } from 'react';
import { Search as SearchIcon, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getTickers } from '../api';


interface SearchProps {
    onSearch: (ticker: string) => void;
    loading: boolean;
}

interface Ticker {
    ticker: string;
    company_name: string;
    sector: string;
    exchange: string;
}

const CACHE_KEY = 'equitypulse_tickers';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

const Search: React.FC<SearchProps> = ({ onSearch, loading }) => {
    const [query, setQuery] = useState('');
    const [tickers, setTickers] = useState<Ticker[]>([]);
    const [suggestions, setSuggestions] = useState<Ticker[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Load tickers on mount (Cache First)
    useEffect(() => {
        const loadTickers = async () => {
            const cached = localStorage.getItem(CACHE_KEY);
            if (cached) {
                const { data, timestamp } = JSON.parse(cached);
                if (Date.now() - timestamp < CACHE_DURATION) {
                    setTickers(data);
                    return;
                }
            }

            try {
                const data = await getTickers();
                setTickers(data);
                localStorage.setItem(CACHE_KEY, JSON.stringify({ data, timestamp: Date.now() }));
            } catch (error) {
                console.error("Failed to load tickers:", error);
            }
        };
        loadTickers();
    }, []);

    // Filter suggestions
    useEffect(() => {
        if (!query) {
            setSuggestions([]);
            return;
        }
        const lowerQuery = query.toLowerCase();
        const filtered = tickers.filter(t =>
            (t.ticker ?? '').toLowerCase().includes(lowerQuery) ||
            (t.company_name ?? '').toLowerCase().includes(lowerQuery)
        ).slice(0, 5); // Limit to 5 suggestions
        setSuggestions(filtered);
    }, [query, tickers]);

    // Click outside to close
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query.toUpperCase().split(' - ')[0]); // Handle "AAPL - Apple" format if manually typed
            setShowSuggestions(false);
        }
    };

    const handleSelect = (ticker: Ticker) => {
        setQuery(ticker.ticker);
        onSearch(ticker.ticker);
        setShowSuggestions(false);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-lg text-center"
            >
                <div className="mb-8 space-y-4">
                    <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
                        EquityPulse
                    </h1>
                    <p className="text-xl text-muted-foreground font-light">
                        AI-Powered Investment Intelligence
                    </p>
                </div>

                <div className="relative z-50" ref={containerRef}>
                    <form onSubmit={handleSubmit} className="relative group">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500"></div>
                        <div className="relative flex items-center bg-card/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl transition-all duration-300 focus-within:ring-2 focus-within:ring-primary/50 focus-within:border-primary/50">
                            <SearchIcon className="ml-4 text-muted-foreground w-6 h-6" />
                            <input
                                type="text"
                                placeholder="Search Ticker (e.g. AAPL)..."
                                className="w-full px-4 py-3 bg-transparent border-none outline-none text-lg placeholder:text-muted-foreground/50 text-foreground"
                                value={query}
                                onChange={(e) => {
                                    setQuery(e.target.value);
                                    setShowSuggestions(true);
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                disabled={loading}
                            />
                            <button
                                type="submit"
                                disabled={loading || !query}
                                className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-primary/25"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Analyze'}
                            </button>
                        </div>
                    </form>

                    {/* Autocomplete Dropdown */}
                    <AnimatePresence>
                        {showSuggestions && suggestions.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="absolute top-full left-0 right-0 mt-2 bg-card/90 backdrop-blur-md border border-white/10 rounded-xl shadow-2xl overflow-hidden"
                            >
                                {suggestions.map((ticker) => (
                                    <div
                                        key={ticker.ticker}
                                        className="flex items-center justify-between px-5 py-3 hover:bg-white/5 cursor-pointer transition-colors border-b border-white/5 last:border-0"
                                        onClick={() => handleSelect(ticker)}
                                    >
                                        <div className="flex flex-col text-left">
                                            <span className="font-bold text-foreground">{ticker.ticker}</span>
                                            <span className="text-xs text-muted-foreground">{ticker.company_name} • {ticker.sector}</span>
                                        </div>
                                        <span className="text-xs text-muted-foreground px-2 py-1 bg-secondary rounded-md">{ticker.exchange}</span>
                                    </div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="mt-8 flex gap-3 justify-center text-sm text-muted-foreground/60">
                    <span>Popular:</span>
                    {['AAPL', 'TSLA', 'NVDA', 'MSFT'].map(t => (
                        <button key={t} onClick={() => { setQuery(t); onSearch(t); }} className="hover:text-primary transition-colors cursor-pointer underline decoration-dotted">
                            {t}
                        </button>
                    ))}
                </div>

            </motion.div>
        </div>
    );
};

export default Search;
