import React, { useState, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, Upload, ChevronUp, ChevronDown } from 'lucide-react';

const ResultsTable = ({ results, onImport, onToggleChecked }) => {
    const { t } = useTranslation();
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'descending' });
    const fileInputRef = useRef(null);

    const handleExport = () => {
        const headers = ["Ticker", "Pattern", "Volume Ratio", "Drop %", "Market Cap", "Insider Own %", "Market", "Checked"];
        const csvRows = [headers.join(",")];

        for (const r of results) {
            csvRows.push([
                r.ticker,
                r.pattern,
                r.volume_ratio,
                r.drop_pct,
                r.market_cap,
                r.insider_own,
                r.market || "Unknown",
                r.checked || false
            ].join(","));
        }

        const csvContent = csvRows.join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "scan_results.csv";
        link.click();
        URL.revokeObjectURL(url);
    };

    const handleImportClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const text = e.target.result;
                const lines = text.split('\n');
                // Basic CSV parsing (assuming standard format with headers)
                // Remove header row
                const dataLines = lines.slice(1).filter(line => line.trim() !== '');

                const parsedResults = dataLines.map(line => {
                    const cols = line.split(',').map(c => c.trim());
                    if (cols.length < 6) return null;

                    const ticker = cols[0];
                    const pattern = cols[1];
                    const volume_ratio = parseFloat(cols[2]);
                    const drop_pct = parseFloat(cols[3]);
                    const market_cap = cols[4];
                    const insider_own = cols[5];
                    const market = cols[6] || "Unknown";
                    const checked = cols[7] === "true" || cols[7] === "Checked";

                    // Reconstruct raw values for sorting
                    let market_cap_raw = 0;
                    if (market_cap.endsWith('B')) {
                        market_cap_raw = parseFloat(market_cap.replace('$', '').replace('B', '')) * 1_000_000_000;
                    } else if (market_cap.endsWith('M')) {
                        market_cap_raw = parseFloat(market_cap.replace('$', '').replace('M', '')) * 1_000_000;
                    }

                    return {
                        ticker,
                        pattern,
                        volume_ratio,
                        drop_pct,
                        market_cap,
                        insider_own,
                        market,
                        checked,
                        market_cap_raw,
                        insider_own_raw: insider_own.endsWith('%') ? parseFloat(insider_own.replace('%', '')) / 100 : 0
                    };
                }).filter(r => r !== null);

                if (onImport) onImport(parsedResults);

                // Reset input
                event.target.value = '';
                alert(t('import_success', { count: parsedResults.length }));

            } catch (error) {
                console.error("Import error:", error);
                alert(t('import_error'));
            }
        };
        reader.readAsText(file);
    };

    const sortedResults = useMemo(() => {
        let sortableItems = [...results];
        if (sortConfig.key !== null) {
            sortableItems.sort((a, b) => {
                let aKey = a[sortConfig.key];
                let bKey = b[sortConfig.key];

                // Handle raw values for formatting columns
                if (sortConfig.key === 'market_cap') {
                    aKey = a['market_cap_raw'] || 0;
                    bKey = b['market_cap_raw'] || 0;
                }
                if (sortConfig.key === 'insider_own') {
                    aKey = a['insider_own_raw'] || 0;
                    bKey = b['insider_own_raw'] || 0;
                }

                if (aKey < bKey) {
                    return sortConfig.direction === 'ascending' ? -1 : 1;
                }
                if (aKey > bKey) {
                    return sortConfig.direction === 'ascending' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [results, sortConfig]);

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const getClassNamesFor = (name) => {
        if (!sortConfig) {
            return;
        }
        return sortConfig.key === name ? sortConfig.direction : undefined;
    };

    const renderSortIcon = (name) => {
        if (sortConfig.key !== name) return <div className="w-4 h-4" />; // spacer
        return sortConfig.direction === 'ascending' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
    };

    if (!results || results.length === 0) {
        return (
            <div className="mt-8 text-center text-gray-500 py-12 border-2 border-dashed border-gray-700 rounded-xl">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".csv"
                    className="hidden"
                />
                <div className="flex flex-col items-center gap-4">
                    <p>{t('no_results')}</p>
                    <button
                        onClick={handleImportClick}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg transition-all font-medium text-sm"
                    >
                        <Upload size={16} />
                        {t('import_results')}
                    </button>
                </div>
            </div>
        );
    }

    const HeaderCell = ({ label, sortKey, align = "left" }) => (
        <th
            className={`py-3 px-1 font-semibold cursor-pointer hover:bg-gray-800 transition-colors select-none whitespace-nowrap ${align === "right" ? "text-right" : "text-left"}`}
            onClick={() => requestSort(sortKey)}
        >
            <div className={`flex items-center gap-1 ${align === "right" ? "justify-end" : "justify-start"}`}>
                {label}
                <span className="text-gray-500">{renderSortIcon(sortKey)}</span>
            </div>
        </th>
    );

    return (
        <div className="mt-8 bg-gray-800 rounded-xl border border-gray-700 shadow-xl overflow-hidden">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".csv"
                className="hidden"
            />
            <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800/50 backdrop-blur">
                <h2 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    {t('scan_results')} ({results.length})
                </h2>
                <div className="flex gap-2">
                    <button
                        onClick={handleImportClick}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all font-medium text-sm shadow-lg shadow-blue-900/30"
                    >
                        <Upload size={16} />
                        {t('import_results')}
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-all font-medium text-sm shadow-lg shadow-green-900/30"
                    >
                        <Download size={16} />
                        {t('export_csv')}
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-900/50 text-gray-400 text-xs uppercase tracking-wider">
                            <th className="py-3 px-1 w-8">
                                <div className="flex items-center justify-center">
                                    <span className="text-[10px] text-gray-500 uppercase">{t('table_checked')}</span>
                                </div>
                            </th>
                            <HeaderCell label={t('table_ticker')} sortKey="ticker" />
                            <HeaderCell label={t('table_market')} sortKey="market" />
                            <HeaderCell label={t('table_pattern')} sortKey="pattern" />
                            <HeaderCell label={t('table_volume_ratio')} sortKey="volume_ratio" align="right" />
                            <HeaderCell label={t('table_drop_pct')} sortKey="drop_pct" align="right" />
                            <HeaderCell label={t('table_market_cap')} sortKey="market_cap" align="right" />
                            <HeaderCell label={t('table_insider_pct')} sortKey="insider_own" align="right" />
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {sortedResults.map((r, i) => (
                            <tr key={`${r.ticker}-${i}`} className={`hover:bg-gray-700/50 transition-colors group ${r.checked ? 'opacity-40' : ''}`}>
                                <td className="py-3 px-1 text-center">
                                    <input
                                        type="checkbox"
                                        checked={r.checked || false}
                                        onChange={(e) => onToggleChecked && onToggleChecked(r.ticker, e.target.checked)}
                                        className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-offset-gray-900 cursor-pointer"
                                    />
                                </td>
                                <td className="py-3 px-1 font-bold text-white text-sm">
                                    <a
                                        href={`https://finance.yahoo.com/quote/${r.ticker}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="hover:underline text-blue-400 flex items-center gap-1"
                                    >
                                        {r.ticker}
                                    </a>
                                </td>
                                <td className="py-3 px-1 text-xs text-gray-400">
                                    <span className="bg-gray-900/50 px-1 py-0.5 rounded border border-gray-700/50">
                                        {r.market || "US"}
                                    </span>
                                </td>
                                <td className="py-3 px-1">
                                    <span className={`px-1 py-0.5 rounded text-[10px] font-bold whitespace-nowrap ${r.pattern.includes("FRESH")
                                        ? "bg-red-500/20 text-red-300 border border-red-500/30"
                                        : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                                        }`}>
                                        {r.pattern.replace("FRESH SPIKE", t('fresh_spike')).replace("BASE BUILDING", t('base_building'))}
                                    </span>
                                </td>
                                <td className="py-3 px-1 text-right font-mono text-green-400 text-xs">{r.volume_ratio}x</td>
                                <td className="py-3 px-1 text-right font-mono text-red-400 text-xs">{r.drop_pct}%</td>
                                <td className="py-3 px-1 text-right text-gray-300 font-mono text-xs">{r.market_cap}</td>
                                <td className="py-3 px-1 text-right text-yellow-500 font-mono text-xs">{r.insider_own}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ResultsTable;
