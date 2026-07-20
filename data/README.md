# Data — fully synthetic, by design

**No real customer data exists anywhere in this project.** KYC records are
personally identifiable information; publishing real ones would violate both
data-privacy law and the first principle of compliance work. Instead:

- `customers.csv` is **generated** by `src/generate_data.py` (seeded, so
  results reproduce exactly). It is git-ignored; run the generator to create it.
- `watchlist.csv` is a small, entirely fictional screening list (committed —
  it contains no real names by intent).

The generator injects known defects and prints the ground-truth counts,
so the validator's catch rate can be verified against what was planted.
