# On-Chain Wallet Risk Scoring

Heuristic risk scoring toolkit for wallet transaction histories.  
Designed for quick due diligence (DD) and anomaly detection in DeFi.

## What it does
- Scores wallets (0–100) by **behavioral risk**: mixing, low-liquidity tokens, fresh-contract interactions, timing clusters
- Flags **red/amber/green** with explainable components
- Works offline on CSV exports (`date,tx_hash,token,amount,usd_value,direction,counterparty,tags`)

## Quickstart
```bash
pip install -r requirements.txt
python src/score.py --data data/sample_tx.csv --out outputs/report.json
python src/score.py --data data/sample_tx.csv --explain
```

## Output
- JSON report with overall score + per-factor breakdown
- CSV of flagged transactions

## Notes
- This is a heuristic baseline for analysts. For production, plug real labeling sources (sanctions/blacklists, liquidity oracles).

## License
MIT
=======================================
01.21.26
