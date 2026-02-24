import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Copy, Check, Coffee, Heart } from 'lucide-react';

// Icons matching the reference (Outline Style)
const cryptoIcons = {
    BTC: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-800">
            <path d="M8 6h5.5a3.5 3.5 0 1 1 0 7H8V6z" />
            <path d="M8 13h6.5a3.5 3.5 0 1 1 0 7H8v-7z" />
            <line x1="10" y1="4" x2="10" y2="6" />
            <line x1="14" y1="4" x2="14" y2="6" />
            <line x1="10" y1="20" x2="10" y2="22" />
            <line x1="14" y1="20" x2="14" y2="22" />
        </svg>
    ),
    ETH: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-800">
            <path d="M12 2L5 13l7 4 7-4-7-11z" />
            <path d="M12 22l-7-9" />
            <path d="M12 22l7-9" />
            <path d="M5 13l7-4 7 4" />
        </svg>
    ),
    SOL: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-800">
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="4" />
        </svg>
    )
};

const CryptoRow = ({ label, address, type, onCopy, isCopied }) => (
    <div className="bg-[#FAF9F5] p-4 rounded-xl border border-[#E5E5E5] flex items-center justify-between group hover:border-gray-400 transition-colors shadow-sm">
        <div className="flex items-center gap-4 overflow-hidden">
            {/* Minimal Icon Container */}
            <div className="w-6 h-6 flex items-center justify-center">
                {cryptoIcons[type]}
            </div>

            <div className="flex flex-col min-w-0 gap-0.5">
                <span className="text-sm font-medium text-gray-800">{label}</span>
                <span className="text-xs text-gray-500 truncate font-mono max-w-[150px] sm:max-w-[200px]">
                    {address}
                </span>
            </div>
        </div>
        <button
            onClick={() => onCopy(address, type)}
            className="p-2 hover:bg-white rounded-lg transition-colors text-gray-500 hover:text-blue-600 focus:outline-none"
            title="Copy Address"
        >
            {isCopied ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
        </button>
    </div>
);

const SupportModal = ({ isOpen, onClose }) => {
    const { t } = useTranslation();
    const [copied, setCopied] = useState(null);

    // Always call hooks before conditional return

    if (!isOpen) return null;

    const handleCopy = (text, type) => {
        navigator.clipboard.writeText(text);
        setCopied(type);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 transform transition-all scale-100 animate-in fade-in zoom-in duration-200">

                {/* Header */}
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🚀</span>
                        <h2 className="text-xl font-bold text-gray-800">{t('support_modal_title')}</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded-full text-gray-500 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <p className="text-gray-600 text-sm mb-6 leading-relaxed">
                    {t('support_msg')}
                </p>

                {/* Buttons */}
                <div className="space-y-3 mb-8">
                    <a
                        href="https://buymeacoffee.com/goldenlog"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full bg-[#FFDD00] hover:bg-[#FFEA00] text-gray-900 font-bold py-3 rounded-full text-center shadow-md transform hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
                    >
                        <Coffee size={20} className="text-gray-800" />
                        {t('buy_coffee')}
                    </a>

                    <a
                        href="https://ko-fi.com/goldenlog"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full bg-[#FF5E5B] hover:bg-[#FF4542] text-white font-bold py-3 rounded-full text-center shadow-md transform hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
                    >
                        <Heart size={20} fill="currentColor" />
                        {t('support_kofi')}
                    </a>
                </div>

                {/* Crypto Section */}
                <div>
                    <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
                        {t('crypto_donations')}
                    </h3>
                    <div className="space-y-2">
                        <CryptoRow
                            label="Bitcoin (BTC)"
                            type="BTC"
                            address="bc1q7hynfjgws6kyax0uq2faayhvf64f7avs5v854t"
                            onCopy={handleCopy}
                            isCopied={copied === 'BTC'}
                        />
                        <CryptoRow
                            label="Ethereum (ETH)"
                            type="ETH"
                            address="0xe4BcDe9cA927e3f8A6F26fE4e16B67C76fecdF14"
                            onCopy={handleCopy}
                            isCopied={copied === 'ETH'}
                        />
                        <CryptoRow
                            label="Solana (SOL)"
                            type="SOL"
                            address="GoXhF56h1hwHDE7LiRdCikFpoMzHuhXMNQcByHKxkKYP"
                            onCopy={handleCopy}
                            isCopied={copied === 'SOL'}
                        />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SupportModal;
