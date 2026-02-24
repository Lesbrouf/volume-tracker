import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

const LogViewer = ({ logs }) => {
    const { t } = useTranslation();
    // We ref the CONTAINER, not the end element
    const containerRef = useRef(null);

    useEffect(() => {
        // Scroll the CONTAINER to the bottom, not the page
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div
            ref={containerRef}
            className="bg-gray-900 border border-gray-700 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm shadow-inner scroll-smooth"
        >
            <div className="sticky top-0 bg-gray-900/90 backdrop-blur z-10 pb-2 border-b border-gray-800 mb-2">
                <h3 className="text-gray-400 text-xs font-bold">{t('system_logs')}</h3>
            </div>

            {logs.length === 0 && <span className="text-gray-600 italic">{t('no_logs')}</span>}
            {logs.map((log, index) => {
                let content = <span className="text-gray-300">{log.message}</span>;

                if (log.message.includes("FOUND:")) {
                    const parts = log.message.split(" - ");
                    const tickerPart = parts[0].replace("FOUND:", "").trim();
                    const patternPart = parts[1] ? parts[1].trim() : "";

                    let translatedPattern = patternPart;
                    if (patternPart.includes("FRESH SPIKE")) translatedPattern = `🔥 ${t('fresh_spike')}`;
                    if (patternPart.includes("BASE BUILDING")) translatedPattern = `🏗️ ${t('base_building')}`;

                    content = (
                        <span>
                            <span className="text-green-400 font-bold">{t('tickers_found_log')}: {tickerPart}</span>
                            <span className="text-gray-300"> - {translatedPattern}</span>
                        </span>
                    );
                } else if (log.message.startsWith("Processed")) {
                    // Extract numbers
                    const match = log.message.match(/Processed (.*)\.\.\./);
                    if (match) {
                        content = <span className="text-gray-400">{t('log_processed', { count: match[1] })}</span>;
                    }
                } else if (log.message === "Scan Complete.") {
                    content = <span className="text-blue-400 font-bold">{t('log_complete')}</span>;
                }

                return (
                    <div key={index} className="mb-1">
                        <span className="text-gray-500 mr-2">[{log.time}]</span>
                        {content}
                    </div>
                );
            })}
        </div>
    );
};

export default LogViewer;
