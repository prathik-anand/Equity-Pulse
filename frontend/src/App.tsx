import { useState, useEffect } from 'react';
import Search from './components/Search';
import Dashboard from './components/Dashboard';
import LandingPage from './components/LandingPage';
import { triggerAnalysis } from './api';

// Helper function to format relative time
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString + 'Z');
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

function App() {
  const [isLaunched, setIsLaunched] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [history, setHistory] = useState<any[]>([]);

  // Initialize User Session ID (Lazy Initialization)
  const [userSessionId, _setUserSessionId] = useState<string | null>(() => {
    const key = 'equity_pulse_user_id';
    let storedId = localStorage.getItem(key);
    if (!storedId) {
      storedId = crypto.randomUUID();
      localStorage.setItem(key, storedId);
    }
    return storedId;
  });

  // Fetch history logic
  const fetchHistory = async () => {
    if (userSessionId) {
      setHistoryLoading(true);
      try {
        const hist = await import('./api').then(m => m.getUserHistory(userSessionId));
        setHistory(hist);
      } catch (e) {
        console.error("Failed to load history", e);
      } finally {
        setHistoryLoading(false);
      }
    }
  };

  // Load history when userSessionId is available
  useEffect(() => {
    if (userSessionId) {
      fetchHistory();
    }
  }, [userSessionId]);

  const handleSearch = async (ticker: string) => {
    if (!userSessionId) return;
    setLoading(true);
    try {
      const result = await triggerAnalysis(ticker, userSessionId);
      setSessionId(result.id); // Backend now returns 'id'
      fetchHistory(); // Refresh history
    } catch (error) {
      console.error("Failed to start analysis:", error);
      alert("Failed to start analysis. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSessionId(null);
    fetchHistory();
  };

  if (!isLaunched) {
    return <LandingPage onLaunch={() => setIsLaunched(true)} />;
  }

  return (
    <div className="min-h-screen h-screen bg-background text-foreground font-sans selection:bg-primary/20 flex overflow-hidden">
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      {/* Sidebar with Logo + History */}
      <aside className="w-56 border-r border-border/40 bg-card/30 backdrop-blur-sm hidden md:flex flex-col z-20 flex-shrink-0">
        {/* Logo */}
        <div className="p-4 border-b border-border/40">
          <div
            className="font-bold text-xl tracking-tighter cursor-pointer bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500"
            onClick={handleBack}
          >
            EquityPulse
          </div>
          <p className="text-[10px] text-muted-foreground mt-1">AI Investment Research</p>
        </div>

        {/* History */}
        <div className="flex-1 flex flex-col min-h-0 p-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">History</h3>
          <div className="flex-1 overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
            {historyLoading ? (
              <div className="flex items-center justify-center py-4">
                <span className="text-xs text-muted-foreground animate-pulse">Loading...</span>
              </div>
            ) : history.length === 0 ? (
              <p className="text-xs text-muted-foreground px-1">No past reports.</p>
            ) : (
              history.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSessionId(item.id)}
                  className={`w-full text-left p-2.5 rounded-lg text-sm transition-all ${sessionId === item.id
                    ? 'bg-primary/10 text-primary font-medium border border-primary/20'
                    : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="uppercase font-bold text-xs">{item.ticker}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${item.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                      item.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                        'bg-yellow-500/10 text-yellow-500'
                      }`}>{item.status}</span>
                  </div>
                  <div className="text-[10px] opacity-50 mt-0.5">
                    {formatRelativeTime(item.created_at)}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </aside>

      {/* Main Content - Full Width */}
      <main className="relative z-10 flex-1 overflow-y-auto h-screen">
        <div className="w-full max-w-7xl mx-auto px-6 py-6">
          {!sessionId ? (
            <div className="flex flex-col items-center justify-center min-h-[80vh]">
              <Search onSearch={handleSearch} loading={loading} />
            </div>
          ) : (
            <Dashboard sessionId={sessionId} onBack={handleBack} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
