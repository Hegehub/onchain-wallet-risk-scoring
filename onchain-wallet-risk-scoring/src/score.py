import argparse, json, os
import pandas as pd, numpy as np

def load_txs(path):
    df = pd.read_csv(path, parse_dates=['date'])
    df['usd_value'] = df['usd_value'].fillna(0.0)
    return df.sort_values('date')

def factor_low_liquidity(df):
    # proxy: many txs in tokens with small $ value per trade
    small = (df['usd_value'].abs() < 50).mean()
    return small  # 0..1

def factor_fresh_contracts(df):
    # proxy: many unique counterparties used once
    counts = df['counterparty'].value_counts()
    fresh_ratio = (counts==1).mean()
    return fresh_ratio

def factor_direction_entropy(df):
    # alternating in/out can suggest mixing
    dirs = df['direction'].map({'in':1,'out':0}).dropna().values
    if len(dirs)<3: return 0.0
    flips = (dirs[1:]!=dirs[:-1]).mean()
    return flips

def factor_time_bursts(df):
    # multiple txs within 1 minute windows
    ts = df['date'].sort_values().values.astype('datetime64[s]').astype('int64')
    if len(ts)<2: return 0.0
    diffs = np.diff(ts)
    burst = (diffs<=60).mean()
    return burst

def score_wallet(df):
    factors = {
        'low_liquidity': factor_low_liquidity(df),
        'fresh_contracts': factor_fresh_contracts(df),
        'direction_entropy': factor_direction_entropy(df),
        'time_bursts': factor_time_bursts(df),
    }
    weights = {'low_liquidity':0.25,'fresh_contracts':0.25,'direction_entropy':0.25,'time_bursts':0.25}
    raw = sum(factors[k]*weights[k] for k in factors)
    score = int(min(max(raw,0),1)*100)
    label = 'GREEN' if score<33 else ('AMBER' if score<66 else 'RED')
    return score, label, factors

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--out', default='outputs/report.json')
    p.add_argument('--explain', action='store_true')
    args = p.parse_args()

    os.makedirs('outputs', exist_ok=True)
    df = load_txs(args.data)
    score, label, factors = score_wallet(df)

    report = {'overall_score':score, 'label':label, 'factors':factors, 'n_txs':int(len(df))}
    with open(args.out, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    if args.explain:
        # save flagged txs (simple rule: low $ value and bursty timing)
        flagged = df[(df['usd_value'].abs()<50)].copy()
        flagged.to_csv('outputs/flagged.csv', index=False)

    print(json.dumps(report, indent=2))

if __name__=='__main__':
    main()
