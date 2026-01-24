import { useState } from 'react';
import Search from './components/Search';
import Dashboard from './components/Dashboard';
import { triggerAnalysis } from './api';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    try {
      const result = await triggerAnalysis(ticker);
      setSessionId(result.session_id);
    } catch (error) {
      console.error("Failed to start analysis:", error);
      alert("Failed to start analysis. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSessionId(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <main className="relative z-10 container mx-auto px-4 py-8">
        <header className="flex justify-between items-center py-4 mb-8">
          <div className="font-bold text-xl tracking-tighter">EquityPulse</div>
          <nav className="text-sm text-muted-foreground gap-4 flex">
            <a href="#" className="hover:text-primary transition-colors">About</a>
            <a href="#" className="hover:text-primary transition-colors">Github</a>
          </nav>
        </header>

        {!sessionId ? (
          <Search onSearch={handleSearch} loading={loading} />
        ) : (
          <Dashboard sessionId={sessionId} onBack={handleBack} />
        )}
      </main>
    </div>
  );
}

export default App;
