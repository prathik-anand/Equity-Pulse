import React from 'react';

interface LandingPageProps {
    onLaunch: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onLaunch }) => {
    return (
        <div className="landing-page-root">
            <style>{`
                :root {
                    --bg-dark: #020305;
                    --card-base: #0d0e12;
                    --item-matte: #15171c;
                    /* Solid, dark matte for rows */
                    --accent-quant: #4f46e5;
                    --wire-glow: rgba(79, 70, 229, 0.4);
                }

                .landing-page-root {
                    height: 100vh;
                    margin: 0;
                    overflow: hidden;
                    font-family: 'Inter', sans-serif;
                    background-color: var(--bg-dark);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: space-between;
                    padding: 2.5rem 4rem; /* py-10 px-16 equivalent */
                }

                /* SVG Wiring - Matte Contrast */
                .wiring-container {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 1;
                    pointer-events: none;
                }

                .wire {
                    stroke: var(--accent-quant);
                    fill: none;
                    stroke-width: 2;
                    stroke-opacity: 0.25;
                    filter: drop-shadow(0 0 8px var(--wire-glow));
                }

                /* 3D Stack - Realigned and Scaled */
                .agent-perspective {
                    perspective: 1500px;
                    position: relative;
                    transform: scale(0.82);
                    transform-origin: center right;
                }

                .glass-card-back {
                    position: absolute;
                    top: 20px;
                    right: -25px;
                    width: 100%;
                    height: 100%;
                    background: #050608;
                    border: 1px solid rgba(255, 255, 255, 0.03);
                    border-radius: 32px;
                    transform: rotateY(-18deg) rotateX(6deg) translateZ(-60px);
                    z-index: 5;
                }

                .glass-card-front {
                    position: relative;
                    z-index: 10;
                    background: var(--card-base);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 32px;
                    transform: rotateY(-18deg) rotateX(6deg);
                    box-shadow: -40px 50px 100px rgba(0, 0, 0, 0.95);
                }

                /* Matte Agent Rows - No Bubbles */
                .agent-item {
                    background: var(--item-matte);
                    border: 1px solid rgba(255, 255, 255, 0.04);
                    padding: 0.7rem 1.2rem;
                    border-radius: 12px;
                    margin-bottom: 0.4rem;
                }

                /* High-Visibility Quant Agent */
                .agent-active {
                    background: #1a1c24;
                    /* Slightly lighter matte */
                    border: 2px solid var(--accent-quant);
                    box-shadow: 0 0 25px rgba(79, 70, 229, 0.3);
                    padding: 0.85rem 1.4rem;
                }

                .text-gradient {
                    background: linear-gradient(to bottom, #FFFFFF 40%, #94a3b8 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
            `}</style>

            <div className="wiring-container">
                <svg width="100%" height="100%" viewBox="0 0 1440 900" preserveAspectRatio="none">
                    <path className="wire" d="M1000,450 C1000,650 300,600 300,820" />
                    <path className="wire" d="M1050,500 C1050,700 720,650 720,820" />
                    <path className="wire" d="M1100,450 C1100,650 1140,650 1140,820" />
                </svg>
            </div>

            {/* Header / Logo */}
            <header className="w-full max-w-7xl flex justify-start items-center z-50">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.4)]">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-black text-lg tracking-tighter uppercase leading-none">EquityPulse</span>
                        <span className="text-[9px] text-indigo-400 font-bold tracking-[0.2em] uppercase">Intelligence</span>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl w-full grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-6 items-center flex-1 relative z-20">

                <div className="space-y-10">
                    <div className="inline-flex items-center px-4 py-1.5 rounded-full border border-indigo-500/20 bg-indigo-500/10">
                        <span className="text-indigo-400 text-[10px] font-bold tracking-[0.3em] uppercase">✦ NEXT-GEN QUANTITATIVE
                            INTELLIGENCE</span>
                    </div>

                    <h1 className="text-6xl font-black tracking-tighter leading-[1.05]">
                        The Hedge Fund <br />
                        <span className="text-gradient">In Your Pocket.</span>
                    </h1>

                    <p className="text-gray-400 text-lg max-w-md leading-relaxed">
                        91% of retail traders lose money because they are outgunned.
                        <span className="text-white font-semibold">EquityPulse</span> gives you an <span
                            className="text-indigo-400">Autonomous AI Investment Committee</span>.
                    </p>

                    <button
                        onClick={onLaunch}
                        className="px-12 py-4 bg-white text-black font-black rounded-full text-lg shadow-[0_0_40px_rgba(255,255,255,0.25)] hover:scale-105 transition-all">
                        Launch App →
                    </button>
                </div>

                <div className="agent-perspective flex justify-start pl-8">
                    <div className="glass-card-back"></div>

                    <div className="glass-card-front p-8 w-full max-w-[370px]">
                        <div className="flex justify-between items-center mb-6">
                            <span className="text-[9px] font-bold text-gray-500 tracking-widest uppercase">AI Investment
                                Committee</span>
                            <div className="flex gap-1.5">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></div>
                                <div className="w-2 h-2 rounded-full bg-gray-800"></div>
                                <div className="w-2 h-2 rounded-full bg-gray-800"></div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">TECHNICAL AGENT</span>
                            <div
                                className="w-9 h-9 bg-[#1e1b4b] rounded-lg flex items-center justify-center text-amber-500 text-sm">
                                ⚡</div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">FUNDAMENTAL AGENT</span>
                            <div
                                className="w-9 h-9 bg-[#064e3b] rounded-lg flex items-center justify-center text-emerald-400 text-sm">
                                📊</div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">SECTOR AGENT</span>
                            <div className="w-9 h-9 bg-[#1e293b] rounded-lg flex items-center justify-center text-blue-400 text-sm">
                                🌐</div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">MANAGEMENT AGENT</span>
                            <div
                                className="w-9 h-9 bg-[#312e81] rounded-lg flex items-center justify-center text-indigo-300 text-sm">
                                👥</div>
                        </div>

                        <div className="flex items-center justify-between agent-active rounded-xl">
                            <span className="text-[10px] font-extrabold text-white">QUANT AGENT</span>
                            <div
                                className="w-11 h-11 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-[0_0_20px_rgba(79,70,229,0.9)]">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"
                                        d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                                </svg>
                            </div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">RISK AGENT</span>
                            <div className="w-9 h-9 bg-[#451a1a] rounded-lg flex items-center justify-center text-red-500 text-sm">⚠
                            </div>
                        </div>

                        <div className="flex items-center justify-between agent-item">
                            <span className="text-[10px] font-bold text-gray-400">PORTFOLIO MANAGER</span>
                            <div
                                className="w-9 h-9 bg-[#422006] rounded-lg flex items-center justify-center text-amber-600 text-sm">
                                ⚖</div>
                        </div>
                    </div>
                </div>
            </main>

            <section className="max-w-7xl w-full grid grid-cols-1 md:grid-cols-3 gap-8 relative z-30 pb-2">
                <div className="bg-[#08090c] p-8 rounded-[40px] border border-white/5">
                    <div
                        className="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center text-indigo-400 border border-indigo-500/20 mb-5">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z">
                            </path>
                        </svg>
                    </div>
                    <h4 className="text-xl font-bold mb-2">Institutional Grade</h4>
                    <p className="text-gray-500 text-sm leading-relaxed">Specialized AI analysts working around the clock to debate
                        every trade.</p>
                </div>

                <div className="bg-[#08090c] p-8 rounded-[40px] border border-white/5">
                    <div
                        className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400 border border-blue-500/20 mb-5">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                    <h4 className="text-xl font-bold mb-2">Deep Research</h4>
                    <p className="text-gray-500 text-sm leading-relaxed">Analyzing thousands of pages of financial documents in
                        seconds.</p>
                </div>

                <div className="bg-[#08090c] p-8 rounded-[40px] border border-white/5">
                    <div
                        className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center text-purple-400 border border-purple-500/20 mb-5">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z">
                            </path>
                        </svg>
                    </div>
                    <h4 className="text-xl font-bold mb-2">Unbiased & Clear</h4>
                    <p className="text-gray-500 text-sm leading-relaxed">Synthesizing high-conviction investment signals from
                        conflicting data.</p>
                </div>
            </section>
        </div>
    );
};

export default LandingPage;
