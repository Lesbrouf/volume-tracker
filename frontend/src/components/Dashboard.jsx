import React, { useState, useEffect } from 'react';
import { useTranslation, Trans } from 'react-i18next';
import { Activity, Settings, Play, Square, Layers, Coffee, X, Table } from 'lucide-react';
import LogViewer from './LogViewer';
import ResultsTable from './ResultsTable';
import SupportModal from './SupportModal';
import LanguageSelector from './LanguageSelector';

const API_BASE = "http://localhost:8000/api";

const Dashboard = () => {
    const { t } = useTranslation();
    const [config, setConfig] = useState({
        vol_cutoff: 1.8,
        cap_cutoff: 1_000_000_000,
        max_insider: 0.50,
        drop_cutoff: -50.0,
        use_us_market: true,
        use_ca_market: true,
        use_euronext: false,
        use_lse: false,
        use_hkex: false,
        use_china: false,
        use_krx: false,
        use_jpx: false,
        custom_tickers: ""
    });

    const [status, setStatus] = useState({
        progress: 0,
        is_running: false,
        total_tickers: 0,
        scanned_count: 0,
        logs: [],
        results: []
    });

    const [polling, setPolling] = useState(false);
    const [stopping, setStopping] = useState(false);
    const [showSupport, setShowSupport] = useState(false);

    // Poll status
    useEffect(() => {
        let interval;
        if (polling) {
            interval = setInterval(async () => {
                try {
                    const res = await fetch(`${API_BASE}/scan/status`);
                    const data = await res.json();
                    setStatus(data);

                    if (!data.is_running && status.is_running) {
                        setPolling(false); // Scan finished
                        setStopping(false);
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [polling, status.is_running]);

    const startScan = async () => {
        try {
            const payload = {
                ...config,
                custom_tickers: config.custom_tickers.split(',').map(t => t.trim()).filter(Boolean)
            };

            const res = await fetch(`${API_BASE}/scan/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.status === "started") {
                setPolling(true);
            }
        } catch (e) {
            alert("Failed to start scan: " + e.message);
        }
    };

    const stopScan = async () => {
        setStopping(true);
        await fetch(`${API_BASE}/scan/stop`);
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setConfig(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    // Helper for Market Cap Input (Comma separation)
    const handleCapChange = (e) => {
        // Remove commas to get raw number
        const rawValue = e.target.value.replace(/,/g, '');
        if (!isNaN(rawValue) && rawValue !== "") {
            setConfig(prev => ({ ...prev, cap_cutoff: Number(rawValue) }));
        } else if (rawValue === "") {
            setConfig(prev => ({ ...prev, cap_cutoff: 0 }));
        }
    };

    const formatNumber = (num) => {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    const [showTickerModal, setShowTickerModal] = useState(false);
    const [cachedTickers, setCachedTickers] = useState({});
    const [tickerSearch, setTickerSearch] = useState("");

    const fetchCachedTickers = async () => {
        try {
            const res = await fetch(`${API_BASE}/tickers`);
            if (!res.ok) throw new Error(`API Error: ${res.status}`);

            const data = await res.json();

            // Validate structure (should be an object of lists)
            if (typeof data !== 'object' || data === null) throw new Error("Invalid data format");

            setCachedTickers(data);
            setShowTickerModal(true);
        } catch (e) {
            console.error("Failed to fetch tickers:", e);
            alert("Could not fetch ticker list. Ensure backend is running and a scan has completed at least once.");
        }
    };

    const handleToggleChecked = async (ticker, checked) => {
        // Optimistic update
        setStatus(prev => ({
            ...prev,
            results: prev.results.map(r => r.ticker === ticker ? { ...r, checked } : r)
        }));

        try {
            await fetch(`${API_BASE}/results/toggle-checked`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ticker, checked })
            });
        } catch (e) {
            console.error("Failed to toggle checked:", e);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 font-sans selection:bg-blue-500 selection:text-white">
            {/* Ticker Check Modal */}
            {showTickerModal && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
                    <div className="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl border border-gray-700">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-900/50 rounded-t-xl">
                            <h3 className="font-bold text-lg flex items-center gap-2">
                                <span className="text-blue-400">🔍</span> {t('check_ticker_list')}
                            </h3>
                            <button onClick={() => setShowTickerModal(false)} className="text-gray-400 hover:text-white hover:bg-gray-700 p-1 rounded-full transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="bg-blue-900/20 border-b border-blue-900/30 p-3 text-xs text-blue-300 text-center" dangerouslySetInnerHTML={{ __html: t('ticker_update_note') }}>
                        </div>

                        <div className="p-4 border-b border-gray-700 bg-gray-800">
                            <input
                                type="text"
                                placeholder={t('search_placeholder')}
                                className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                value={tickerSearch}
                                onChange={(e) => setTickerSearch(e.target.value.toUpperCase())}
                                autoFocus
                            />
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                            {Object.keys(cachedTickers).length === 0 ? (
                                <div className="text-center text-gray-500 py-8">
                                    {t('no_tickers_cached')}
                                </div>
                            ) : (
                                Object.entries(cachedTickers).map(([market, tickers]) => {
                                    const filtered = tickers.filter(t => t.includes(tickerSearch));
                                    if (filtered.length === 0 && tickerSearch) return null;

                                    return (
                                        <div key={market} className="animate-fade-in">
                                            <h4 className="font-bold text-gray-400 mb-2 sticky top-0 bg-gray-800 py-1 flex justify-between items-center">
                                                {market}
                                                <span className="text-xs bg-gray-700 px-2 py-0.5 rounded-full text-gray-300">{filtered.length} / {tickers.length}</span>
                                            </h4>
                                            <div className="flex flex-wrap gap-2">
                                                {filtered.slice(0, 50).map(t => (
                                                    <span key={t} className="bg-gray-700/50 hover:bg-gray-600/80 text-xs px-2 py-1 rounded cursor-default border border-gray-700 transition-colors">
                                                        {t}
                                                    </span>
                                                ))}
                                                {filtered.length > 50 && (
                                                    <span className="text-xs text-gray-500 py-1 italic">{t('and_more', { count: filtered.length - 50 })}</span>
                                                )}
                                            </div>
                                            {filtered.length === 0 && !tickerSearch && (
                                                <p className="text-xs text-gray-600 italic">{t('tickers_found')}</p>
                                            )}
                                        </div>
                                    );
                                })
                            )}
                            {tickerSearch && Object.values(cachedTickers).flat().filter(t => t.includes(tickerSearch)).length === 0 && (
                                <div className="text-center text-gray-500 mt-4">
                                    {t('no_matches')} "{tickerSearch}"
                                </div>
                            )}
                        </div>
                        <div className="p-3 border-t border-gray-700 bg-gray-900/30 text-xs text-gray-500 text-center rounded-b-xl">
                            {t('showing_cache_note')}
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <header className="bg-gray-900 border-b border-gray-800 p-6 shadow-lg">
                <div className="max-w-7xl mx-auto flex items-center gap-3">
                    {/* Logo Icon */}
                    <div className="p-2 bg-gradient-to-tr from-purple-600 to-blue-500 rounded-lg shadow-purple-500/30 shadow-lg">
                        <Activity size={28} className="text-white" />
                    </div>
                    <div>
                        {/* Title matching user request */}
                        <h1 className="text-2xl font-bold text-gray-100 tracking-tight">
                            {t('app_title')}
                        </h1>
                    </div>

                    <div className="ml-auto flex items-center gap-4">
                        <LanguageSelector />

                        <button
                            onClick={() => setShowSupport(true)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-[#FFDD00] hover:bg-[#FFEA00] text-gray-900 rounded-full font-bold text-sm transition-transform hover:scale-105 shadow-lg shadow-yellow-500/20"
                        >
                            <Coffee size={16} />
                            <span className="hidden sm:inline">{t('fuel_the_dev')}</span>
                        </button>
                    </div>
                </div>
            </header>

            <SupportModal isOpen={showSupport} onClose={() => setShowSupport(false)} />

            <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left Column: Configuration */}
                <section className="space-y-6">
                    <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6 shadow-xl">
                        <div className="flex items-center gap-2 mb-6 text-gray-300">
                            <Settings size={20} />
                            <h2 className="font-semibold text-lg">{t('scan_config')}</h2>
                        </div>

                        <div className="space-y-5">
                            {/* Volume Cutoff */}
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <label className="text-gray-400">{t('min_volume_spike')}</label>
                                    <span className="font-mono text-blue-400">{config.vol_cutoff}x</span>
                                </div>
                                <input
                                    type="range" min="1.0" max="5.0" step="0.1"
                                    name="vol_cutoff" value={config.vol_cutoff} onChange={handleChange}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                />
                            </div>

                            {/* Market Cap */}
                            <div>
                                <label className="block text-gray-400 text-sm mb-2">{t('min_market_cap')}</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                                    <input
                                        type="text"
                                        value={formatNumber(config.cap_cutoff)}
                                        onChange={handleCapChange}
                                        className="w-full bg-gray-900 border border-gray-700 rounded-lg py-2 pl-7 pr-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all font-mono tracking-wide"
                                    />
                                </div>
                            </div>

                            {/* Drop % */}
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <label className="text-gray-400">{t('max_drop')}</label>
                                    <span className="font-mono text-red-400">{config.drop_cutoff}%</span>
                                </div>
                                <input
                                    type="range" min="-99" max="-10" step="1"
                                    name="drop_cutoff" value={config.drop_cutoff} onChange={handleChange}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                                />
                            </div>

                            {/* Insider Ownership */}
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <label className="text-gray-400">{t('max_insider_ownership')}</label>
                                    <span className="font-mono text-yellow-400">{(config.max_insider * 100).toFixed(0)}%</span>
                                </div>
                                <input
                                    type="range" min="0.0" max="1.0" step="0.05"
                                    name="max_insider" value={config.max_insider} onChange={handleChange}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-500"
                                />
                            </div>

                            {/* Toggles */}
                            <div className="flex justify-between items-center mb-2">
                                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">{t('markets')}</h4>
                                <button
                                    onClick={fetchCachedTickers}
                                    className="text-[10px] bg-gray-700 hover:bg-gray-600 text-gray-300 px-2 py-1 rounded transition-colors flex items-center gap-1"
                                    title={t('check_list')}
                                >
                                    <span>🔍</span> {t('check_list')}
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_us_market" checked={config.use_us_market} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇺🇸 US</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_ca_market" checked={config.use_ca_market} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇨🇦 Canada (TSX)</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_euronext" checked={config.use_euronext} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇪🇺 Euronext</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_lse" checked={config.use_lse} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇬🇧 London (LSE)</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_hkex" checked={config.use_hkex} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇭🇰 Hong Kong</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_china" checked={config.use_china} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇨🇳 China</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_krx" checked={config.use_krx} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇰🇷 Korea</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group hover:bg-gray-800 p-1 rounded transition-colors">
                                    <input type="checkbox" name="use_jpx" checked={config.use_jpx} onChange={handleChange} className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900" />
                                    <span className="text-sm group-hover:text-white transition-colors">🇯🇵 Japan</span>
                                </label>
                            </div>
                        </div>

                        {/* Custom Tickers */}
                        <div className="pt-4 border-t border-gray-700">
                            <label className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                <span>{t('custom_tickers')}</span>
                                <label className="cursor-pointer text-blue-400 hover:text-blue-300 flex items-center gap-1 whitespace-nowrap">
                                    <input type="file" accept=".txt,.csv" className="hidden" onChange={(e) => {
                                        const file = e.target.files[0];
                                        if (!file) return;
                                        const reader = new FileReader();
                                        reader.onload = (event) => {
                                            const text = event.target.result;
                                            // Extract anything that looks like a ticker
                                            // Split by comma, newline, space, tab
                                            const tokens = text.split(/[\s,]+/);
                                            const current = config.custom_tickers ? config.custom_tickers.split(/[\s,]+/) : [];
                                            const combined = [...new Set([...current, ...tokens])]
                                                .filter(t => t.trim().length > 0)
                                                .join(", ");

                                            setConfig(prev => ({ ...prev, custom_tickers: combined }));
                                            alert(`Loaded ${tokens.filter(t => t.trim().length > 0).length} tickers from file!`);
                                        };
                                        reader.readAsText(file);
                                        e.target.value = ''; // Reset input
                                    }} />
                                    <span>📂 {t('import_list')}</span>
                                </label>
                            </label>
                            <textarea
                                name="custom_tickers"
                                value={config.custom_tickers}
                                onChange={handleChange}
                                rows="3"
                                placeholder="AAPL, TSLA, BTC-USD..."
                                className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 transition-colors font-mono"
                            />
                        </div>

                        {/* Action Buttons */}
                        <div className="pt-4 flex gap-3">
                            {!status.is_running ? (
                                <button
                                    onClick={startScan}
                                    disabled={stopping}
                                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 shadow-lg shadow-blue-900/50 transition-all transform hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Play size={18} fill="currentColor" /> {t('start_scan')}
                                </button>
                            ) : (
                                <button
                                    onClick={stopScan}
                                    disabled={stopping}
                                    className={`flex-1 ${stopping ? 'bg-gray-600' : 'bg-red-600 hover:bg-red-500'} text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 shadow-lg shadow-red-900/50 transition-all ${!stopping && 'animate-pulse'}`}
                                >
                                    <Square size={18} fill="currentColor" /> {stopping ? t('stopping') : t('stop_scan')}
                                </button>
                            )}
                        </div>
                    </div>
                    {/* Pattern Legend */}
                    <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6 shadow-xl">
                        <h3 className="text-gray-300 font-bold mb-4 flex items-center gap-2">
                            <span className="text-blue-400">ℹ️</span> {t('pattern_guide')}
                        </h3>
                        <div className="space-y-4">
                            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="bg-red-500/20 text-red-300 border border-red-500/30 px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap">
                                        🔥 {t('fresh_spike')}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-400 leading-relaxed" dangerouslySetInnerHTML={{ __html: t('fresh_spike_desc') }}></p>
                            </div>

                            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap">
                                        🏗️ {t('base_building')}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-400 leading-relaxed" dangerouslySetInnerHTML={{ __html: t('base_building_desc') }}></p>
                            </div>

                            <div className="grid grid-cols-1 gap-2 mt-2">
                                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                                    <h4 className="text-xs text-green-400 font-bold mb-1">{t('volume_ratio')}</h4>
                                    <p className="text-xs text-gray-500">
                                        <Trans i18nKey="volume_ratio_desc" components={[<span className="text-gray-300"></span>]} />
                                    </p>
                                </div>
                                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                                    <h4 className="text-xs text-red-400 font-bold mb-1">{t('drop_percent')}</h4>
                                    <p className="text-xs text-gray-500">
                                        <Trans i18nKey="drop_percent_desc" components={[<span className="text-gray-300"></span>]} />
                                        <br /><span className="text-red-500/80 italic">{t('drop_warning')}</span>
                                    </p>
                                </div>
                                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                                    <h4 className="text-xs text-yellow-400 font-bold mb-1">{t('insider_ownership')}</h4>
                                    <p className="text-xs text-gray-500">
                                        {t('insider_ownership_desc')}
                                        <ul className="list-disc pl-4 mt-1 space-y-1">
                                            <li dangerouslySetInnerHTML={{ __html: t('high_insider') }}></li>
                                            <li dangerouslySetInnerHTML={{ __html: t('low_insider') }}></li>
                                        </ul>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Right Column: Status & Results */}
                <section className="lg:col-span-2 space-y-6">

                    {/* Status Card */}
                    <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6 shadow-xl">
                        <div className="flex justify-between items-center mb-4">
                            <div className="flex items-center gap-2 text-gray-300">
                                <Layers size={20} />
                                <h2 className="font-semibold text-lg">{t('scan_progress')}</h2>
                            </div>
                            <div className="text-right">
                                <span className="text-3xl font-bold font-mono text-white">
                                    {((status.scanned_count / (status.total_tickers || 1)) * 100).toFixed(1)}%
                                </span>
                                <p className="text-xs text-gray-500">
                                    {status.scanned_count} / {status.total_tickers} {t('ticker')}s
                                </p>
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="h-4 bg-gray-700 rounded-full overflow-hidden mb-6">
                            <div
                                className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-300 ease-out"
                                style={{ width: `${status.progress}%` }}
                            />
                        </div>

                        {/* Log Viewer */}
                        <LogViewer logs={status.logs} />
                    </div>

                    {/* Results Table */}
                    <div className="flex items-center gap-2 text-gray-300 mb-4">
                        <Table size={20} />
                        <h2 className="font-semibold text-lg">{t('results_table')}</h2>
                    </div>
                    <ResultsTable
                        results={status.results}
                        onToggleChecked={handleToggleChecked}
                        onImport={(importedResults) => {
                            setStatus(prev => ({
                                ...prev,
                                results: importedResults,
                                scanned_count: importedResults.length,
                                total_tickers: importedResults.length,
                                is_running: false,
                                progress: 100
                            }));
                        }}
                    />

                </section>
            </main>

            <footer className="text-center py-6 text-gray-500 text-sm">
                <p>
                    {t('concept_inspired')} {' '}
                    <a
                        href="https://x.com/IamZeroIka"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 font-bold transition-colors"
                    >
                        @ZeroIka
                    </a>
                </p>
                <p className="mt-2 text-xs text-gray-600 max-w-2xl mx-auto">
                    ⚠️ {t('disclaimer_text')}
                </p>
            </footer>
        </div >
    );
};

export default Dashboard;
