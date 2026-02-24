import global_tickers
import logging

# Mock config
config = {
    'use_euronext': True,
    'use_jpx': True,
    'use_lse': True,
    'use_hkex': True,
    'use_china': True, # Placeholder
    'use_krx': True    # Placeholder
}

print("Testing Global Fetchers...")

euronext = global_tickers.get_cached_or_fetch('euronext', global_tickers.fetch_euronext)
print(f"Euronext: {len(euronext)}")

jpx = global_tickers.get_cached_or_fetch('jpx', global_tickers.fetch_jpx)
print(f"JPX: {len(jpx)}")

lse = global_tickers.get_cached_or_fetch('lse', global_tickers.fetch_lse_wiki)
print(f"LSE: {len(lse)}")

hkex = global_tickers.get_cached_or_fetch('hkex', global_tickers.fetch_hkex_wiki)
print(f"HKEX: {len(hkex)}")

china = global_tickers.get_cached_or_fetch('china', global_tickers.fetch_china_mojing)
print(f"China: {len(china)}")

krx = global_tickers.get_cached_or_fetch('krx', global_tickers.fetch_korea_finance_data)
print(f"KRX: {len(krx)}")

print("Done.")
