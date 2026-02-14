"""Ingest NSE symbol lists from workspace files and write normalized list for the fetcher.

Usage:
  python -m backend.scripts.ingest_symbols --source <path> --out backend/database/symbols.txt
  python -m backend.scripts.ingest_symbols  # auto-detect sources
"""
from pathlib import Path
import argparse
import sys


def normalize_symbol(sym: str) -> str:
    s = sym.strip()
    if not s:
        return ""
    # keep existing dot-suffixed symbols as-is (e.g. AIRTELPP.E1)
    if s.upper().endswith('.NS'):
        return s.upper()
    if '.' in s:
        return s.upper()
    # for plain tickers assume NSE and append .NS
    return s.upper() + '.NS'


def load_from_file(p: Path):
    out = []
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            out.append(line)
    return out


def find_candidates(root: Path):
    candidates = list(root.rglob('nse_scanner_symbols.txt'))
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, help='Path to source symbols file')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'database' / 'symbols.txt')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    sources = []
    if args.source:
        if not args.source.exists():
            print('Source file not found:', args.source)
            sys.exit(1)
        sources = [args.source]
    else:
        candidates = find_candidates(repo_root)
        if candidates:
            print('Found candidate symbol files:')
            for c in candidates:
                print(' -', c)
            sources = candidates
        else:
            print('No candidate symbol files found under', repo_root)
            sys.exit(1)

    raw = []
    for s in sources:
        raw.extend(load_from_file(s))

    normalized = []
    for r in raw:
        n = normalize_symbol(r)
        if n:
            normalized.append(n)

    # unique and stable order
    uniq = sorted(set(normalized))

    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(f'Would write {len(uniq)} symbols to {out_path}')
        for u in uniq[:200]:
            print(u)
        return

    with out_path.open('w', encoding='utf-8') as f:
        for u in uniq:
            f.write(u + '\n')

    print(f'Wrote {len(uniq)} symbols to {out_path}')


if __name__ == '__main__':
    main()
