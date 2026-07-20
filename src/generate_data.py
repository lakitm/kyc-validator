"""
generate_data.py — create a synthetic customer file with deliberate defects.

Real KYC data is PII and cannot be published. This script generates ~1,000
fake customers, then injects the kinds of defects a compliance analyst
screens for daily. Every defect count is printed so the validator's catch
rate can be checked against ground truth.

Run:  python src/generate_data.py
Output: data/customers.csv
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 1000

FIRST = ["Maria", "Jose", "Juan", "Ana", "Antonio", "Rosa", "Pedro", "Carmen",
         "Ricardo", "Luz", "Miguel", "Teresa", "Andres", "Josefa", "Ramon",
         "Elena", "Francisco", "Isabel", "Manuel", "Sofia", "Diego", "Angela"]
LAST = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza",
        "Torres", "Flores", "Villanueva", "Ramos", "Aquino", "Navarro",
        "Salazar", "Domingo", "Castillo", "Mercado", "Aguilar", "Rivera"]

def make_clean(n):
    first = RNG.choice(FIRST, n)
    last = RNG.choice(LAST, n)
    names = [f"{f} {l}" for f, l in zip(first, last)]
    birth_years = RNG.integers(1950, 2005, n)
    births = [f"{y}-{RNG.integers(1,13):02d}-{RNG.integers(1,29):02d}" for y in birth_years]
    ids = [f"PSN-{RNG.integers(10_000_000, 99_999_999)}" for _ in range(n)]
    emails = [f"{f.lower()}.{l.lower()}{RNG.integers(1,99)}@example.com"
              for f, l in zip(first, last)]
    mobiles = [f"+639{RNG.integers(100_000_000, 999_999_999)}" for _ in range(n)]
    signups = [f"20{RNG.integers(19,26):02d}-{RNG.integers(1,13):02d}-{RNG.integers(1,29):02d}"
               for _ in range(n)]
    return pd.DataFrame({
        "customer_id": ids, "full_name": names, "birth_date": births,
        "email": emails, "mobile": mobiles, "signup_date": signups,
    })

df = make_clean(N)
report = {}

for col, k in [("full_name", 10), ("birth_date", 12), ("email", 8)]:
    idx = RNG.choice(df.index, k, replace=False)
    df.loc[idx, col] = np.nan
    report[f"missing_{col}"] = k

bad_emails = ["not-an-email", "maria@@example.com", "jose.example.com",
              "ana@", "@example.com"]
idx = RNG.choice(df.index[df.email.notna()], 20, replace=False)
df.loc[idx, "email"] = RNG.choice(bad_emails, 20)
report["malformed_email"] = 20

idx = RNG.choice(df.index[df.birth_date.notna()], 10, replace=False)
future = [f"20{RNG.integers(27,35)}-01-15" for _ in range(5)]
ancient = [f"18{RNG.integers(10,90)}-06-01" for _ in range(5)]
df.loc[idx, "birth_date"] = future + ancient
report["impossible_birth_date"] = 10

dup_src = RNG.choice(df.index, 15, replace=False)
dup_rows = df.loc[dup_src].copy()
variations = []
for name in dup_rows.full_name.fillna("Unknown Person"):
    parts = str(name).split()
    style = RNG.integers(0, 3)
    if style == 0:
        variations.append(f"  {name.upper()} ")
    elif style == 1 and len(parts) >= 2:
        variations.append(f"{parts[0][0]}. {' '.join(parts[1:])}")
    else:
        variations.append(f"{name} ")
dup_rows["full_name"] = variations
df = pd.concat([df, dup_rows], ignore_index=True)
report["duplicate_customer_id"] = 15

watch_names = ["Ernesto Malvar", "Corazon Dizon", "Feliciano Roque",
               "Marites Buenaventura", "Rodrigo Salcedo"]
idx = RNG.choice(df.index, 5, replace=False)
styled = [n if i % 2 == 0 else n.upper() + " " for i, n in enumerate(watch_names)]
df.loc[idx, "full_name"] = styled
report["watchlist_name_planted"] = 5

df = df.sample(frac=1, random_state=7).reset_index(drop=True)
df.to_csv("data/customers.csv", index=False)

print(f"wrote data/customers.csv — {len(df)} rows")
print("\nground truth (validator should catch at least these):")
for k, v in report.items():
    print(f"  {k:28s} {v}")
