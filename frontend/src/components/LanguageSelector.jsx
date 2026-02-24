import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown } from 'lucide-react';
import 'flag-icons/css/flag-icons.min.css';

const LANGUAGES = [
    { code: 'en', label: 'EN', flag: 'fi-gb' },
    { code: 'es', label: 'ES', flag: 'fi-es' },
    { code: 'fr', label: 'FR', flag: 'fi-fr' },
    { code: 'it', label: 'IT', flag: 'fi-it' },
    { code: 'zh', label: 'ZH', flag: 'fi-cn' },
    { code: 'th', label: 'TH', flag: 'fi-th' },
];

const LanguageSelector = () => {
    const { i18n } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const currentLang = LANGUAGES.find(l => l.code === i18n.language) || LANGUAGES[0];

    const changeLanguage = (code) => {
        i18n.changeLanguage(code);
        setIsOpen(false);
    };

    // Click outside handler
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 bg-gray-800 border border-gray-600 hover:bg-gray-700 text-white px-3 py-1.5 rounded-full transition-all text-sm shadow-md"
            >
                <span className={`fi ${currentLang.flag} rounded-sm`}></span>
                <span className="font-semibold">{currentLang.label}</span>
                <ChevronDown size={14} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-32 bg-gray-800 border border-gray-600 rounded-lg shadow-xl overflow-hidden z-50 animate-fade-in-down">
                    {LANGUAGES.map((lang) => (
                        <button
                            key={lang.code}
                            onClick={() => changeLanguage(lang.code)}
                            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-3 hover:bg-gray-700 transition-colors
                                ${currentLang.code === lang.code ? 'bg-gray-700 font-bold text-white' : 'text-gray-300'}
                            `}
                        >
                            <span className={`fi ${lang.flag} rounded-sm`}></span>
                            {lang.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default LanguageSelector;
