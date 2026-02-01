import { useState, useEffect } from 'react';
import Search from './components/Search';
import Dashboard from './components/Dashboard';
import { triggerAnalysis } from './api';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);

  // Initialize User Session ID (Lazy Initialization)
  const [userSessionId, setUserSessionId] = useState<string | null>(() => {
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
      try {
        const hist = await import('./api').then(m => m.getUserHistory(userSessionId));
        setHistory(hist);
      } catch (e) {
        console.error("Failed to load history", e);
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

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 flex">
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      {/* Sidebar History */}
      <aside className="w-64 border-r border-border/40 bg-card/30 backdrop-blur-sm p-4 hidden md:flex flex-col z-20">
        <h2 className="text-lg font-bold mb-4 px-2">History</h2>
        <div className="flex-1 overflow-y-auto space-y-2">
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground px-2">No past reports.</p>
          ) : (
            history.map((item) => (
              <button
                key={item.id}
                onClick={() => setSessionId(item.id)}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${sessionId === item.id
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'hover:bg-accent text-muted-foreground hover:text-foreground'
                  }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="uppercase font-bold">{item.ticker}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${item.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                    item.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                      'bg-yellow-500/10 text-yellow-500'
                    }`}>{item.status}</span>
                </div>
                <div className="text-xs opacity-60">
                  {new Date(item.created_at + "Z").toLocaleDateString()}
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      <main className="relative z-10 flex-1 container mx-auto px-4 py-8 overflow-y-auto h-screen">
        <header className="flex justify-between items-center py-4 mb-8">
          <div className="font-bold text-xl tracking-tighter cursor-pointer" onClick={handleBack}>EquityPulse</div>
          <nav className="text-sm text-muted-foreground gap-4 flex">
            <span className="text-xs px-2 py-1 bg-secondary/50 rounded text-muted-foreground">Session: {userSessionId?.slice(0, 8)}...</span>
          </nav>
        </header>

        {!sessionId ? (
          <div className="max-w-2xl mx-auto mt-20">
            <h1 className="text-4xl font-bold text-center mb-8 tracking-tight">
              AI-Powered <span className="text-primary">Investment Research</span>
            </h1>
            <Search onSearch={handleSearch} loading={loading} />
          </div>
        ) : (
          <Dashboard sessionId={sessionId} onBack={handleBack} />
        )}
      </main>
    </div>
  );
}

export default App;
