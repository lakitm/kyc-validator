"""
validate.py — KYC data validation: screen a customer file, flag exceptions.

Reads data/customers.csv, runs validation checks, writes
outputs/exceptions.csv (one row per violation, with reason codes) and
prints a summary by violation type.

Run:  python src/validate.py

Reason codes (real AML/KYC systems speak in codes — keep them stable):
  R01_MISSING_FIELD        required field is empty
  R02_MALFORMED_EMAIL      email fails format check
  R03_IMPOSSIBLE_DOB       birth date in future or age > 120
  R04_DUPLICATE_ID         customer_id appears more than once
  R05_WATCHLIST_MATCH      normalized name matches watchlist name or alias
"""

import re
import pandas as pd

CUSTOMERS_PATH = "data/customers.csv"
WATCHLIST_PATH = "data/watchlist.csv"
EXCEPTIONS_PATH = "outputs/exceptions.csv"

REQUIRED_FIELDS = ["customer_id", "full_name", "birth_date", "email"]

exceptions = []


def flag(row, code, detail):
    """Record one violation."""
    exceptions.append({
        "customer_id": row.get("customer_id"),
        "full_name": row.get("full_name"),
        "reason_code": code,
        "detail": detail,
    })


def check_required_fields(df):
    for col in REQUIRED_FIELDS:
        for _, row in df[df[col].isna()].iterrows():
            flag(row, "R01_MISSING_FIELD", f"{col} is empty")


EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")


def check_email_format(df):
    for _, row in df[df.email.notna()].iterrows():
        if not EMAIL_RE.match(str(row.email)):
            flag(row, "R02_MALFORMED_EMAIL", f"email '{row.email}' fails format check")


def check_birth_dates(df):
    today = pd.Timestamp.today()
    for _, row in df[df.birth_date.notna()].iterrows():
        parsed = pd.to_datetime(row.birth_date, errors="coerce")
        if pd.isna(parsed):
            flag(row, "R03_IMPOSSIBLE_DOB", f"birth_date '{row.birth_date}' is unparseable")
        elif parsed > today:
            flag(row, "R03_IMPOSSIBLE_DOB", f"birth_date {parsed.date()} is in the future")
        elif (today - parsed).days / 365.25 > 120:
            flag(row, "R03_IMPOSSIBLE_DOB", f"birth_date {parsed.date()} implies age over 120")


def check_duplicate_ids(df):
    dupes = df[df.duplicated(subset="customer_id", keep=False)]
    for _, group in dupes.groupby("customer_id"):
        names = group.full_name.tolist()
        for _, row in group.iterrows():
            others = [n for n in names if n != row.full_name]
            flag(row, "R04_DUPLICATE_ID",
                 f"customer_id used {len(group)} times, name here is {row.full_name!r}, "
                 f"elsewhere {others!r}")


def normalize(name):
    return re.sub(r"\s+", " ", str(name).strip().lower())


def check_watchlist(df, watchlist):
    exact = {}
    initials = {}
    for _, w in watchlist.iterrows():
        for candidate in [w["name"], w["alias"]]:
            if pd.isna(candidate):
                continue
            norm = normalize(candidate)
            exact[norm] = (w["name"], w["listed_reason"])
            parts = norm.split()
            if len(parts) >= 2:
                initials[(parts[0][0], parts[-1])] = (w["name"], w["listed_reason"])

    for _, row in df[df.full_name.notna()].iterrows():
        norm = normalize(row.full_name)
        if norm in exact:
            watch_name, reason = exact[norm]
            flag(row, "R05_WATCHLIST_MATCH", f"exact match to '{watch_name}' ({reason})")
            continue
        parts = norm.split()
        if len(parts) >= 2:
            key = (parts[0][0], parts[-1])
            if key in initials:
                watch_name, reason = initials[key]
                flag(row, "R05_WATCHLIST_MATCH",
                     f"initial-style match to '{watch_name}' ({reason}), confirm before acting")


def main():
    df = pd.read_csv(CUSTOMERS_PATH)
    watchlist = pd.read_csv(WATCHLIST_PATH)
    print(f"loaded {len(df)} customer records, {len(watchlist)} watchlist entries\n")

    check_required_fields(df)
    check_email_format(df)
    check_birth_dates(df)
    check_duplicate_ids(df)
    check_watchlist(df, watchlist)

    exc = pd.DataFrame(exceptions)
    if exc.empty:
        print("no exceptions found — either the data is clean or the checks aren't.")
        return

    exc.to_csv(EXCEPTIONS_PATH, index=False)

    print("=== KYC VALIDATION SUMMARY ===")
    print(f"records screened : {len(df)}")
    print(f"exceptions raised: {len(exc)}")
    print(f"records affected : {exc.customer_id.nunique()}\n")
    print(exc.reason_code.value_counts().to_string())
    print(f"\nfull report: {EXCEPTIONS_PATH}")


if __name__ == "__main__":
    main()
