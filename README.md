# KYC Data Validator

A compliance analyst's first daily task, built as a standalone Python tool. It
screens a customer file for the defects that actually make KYC data
untrustworthy: missing required fields, malformed contact info, impossible
birth dates, duplicate identities, and names that match a screening
watchlist. Every violation gets written to an exceptions report with a
stable reason code, the same way real AML/KYC systems communicate results.

Second project in my risk & compliance analyst portfolio series (first:
[loan-eda](https://github.com/lakitm/loan-eda)). 

## Why the data is synthetic

Real KYC records are PII, so none of this can be real customer data.
`src/generate_data.py` builds about 1,000 fictional customers and
deliberately plants known defects into them, then prints exactly what it
planted. That's what makes the validator's catch rate checkable instead of
just claimed. I know exactly what should get caught, so I know exactly what
got missed.

## Results

Full run, 1,015 records screened, all 5 checks active:

| Reason code | Caught | Planted | Match |
|---|---|---|---|
| `R01_MISSING_FIELD` | 31 | 30 | 30 planted + 1 explained below |
| `R02_MALFORMED_EMAIL` | 20 | 20 | exact |
| `R03_IMPOSSIBLE_DOB` | 10 | 10 | exact |
| `R04_DUPLICATE_ID` | 30 | 30 (15 pairs) | exact |
| `R05_WATCHLIST_MATCH` | 5 | 5 | exact |

The one number that didn't match exactly was R01, one higher than planted, and at first that looked like a bug. Traced it down: one row was missing a birth date, and that same row got picked for the duplicate-injection step, so its duplicate copy inherited the missing field too. Both rows are legitimately bad, the generator's own count just didn't anticipate a planted defect riding along into a second row. Good reminder to check a surprise before assuming it's a mistake.

There are three decisions I want to own here:

- The email check uses a pragmatic regex, not the full spec. I only need to catch garbage, missing `@`, missing domain, double `@`, not validate every legal address. Anything stricter would end up flagging real customers, not just real problems.
- An unparseable birth date gets treated as `R03_IMPOSSIBLE_DOB`, not `R01_MISSING_FIELD`. A garbled value isn't the same as an empty one, and blurring those together would make R01 mean two different things. This dataset never actually plants a date like that, so this decision exists for data I haven't seen yet, not for anything I caught here.
- The watchlist check normalizes case and whitespace first, then adds a looser pass that matches on last name plus first initial, so "E. Malvar" still catches "Ernesto Malvar." That second pass trades precision for recall on purpose: a shared surname and a matching initial isn't proof of identity, so those hits get marked "confirm before acting" instead of treated the same as an exact match. It didn't misfire once on this dataset, but that's a small, surname-diverse population, not a promise it stays clean at scale.

## Reason codes

| Code | Meaning |
|------|---------|
| R01_MISSING_FIELD | Required field is empty |
| R02_MALFORMED_EMAIL | Email fails format check |
| R03_IMPOSSIBLE_DOB | Birth date in future or age > 120 |
| R04_DUPLICATE_ID | customer_id appears more than once |
| R05_WATCHLIST_MATCH | Normalized name matches watchlist name or alias |

## Running it

```bash
git clone https://github.com/lakitm/kyc-validator.git
cd kyc-validator
python -m venv venv && source venv/Scripts/activate  
pip install -r requirements.txt
python src/generate_data.py   
python src/validate.py        
```

## Structure

```
kyc-validator/
├── README.md
├── requirements.txt
├── data/
│   ├── README.md          ← why synthetic, how to regenerate
│   └── watchlist.csv      ← fictional screening list (committed)
├── src/
│   ├── generate_data.py   ← seeded generator with defect injection
│   └── validate.py        ← the validator: 5 checks, reason-coded output
└── outputs/               ← exceptions report lands here (git-ignored)
```

## Author

**Tamira Laki**, BS Mathematics (CS specialization).
Portfolio hub: [github.com/lakitm/Portfolio](https://github.com/lakitm/Portfolio)