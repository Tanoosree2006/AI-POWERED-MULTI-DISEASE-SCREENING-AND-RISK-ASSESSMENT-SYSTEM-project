"""Exports the dataset to ml/data/wdbc.csv (for inspection) and writes two example
input JSON files built from real held-out test records."""
import json

from config import DATA_DIR, EXAMPLES_DIR, ensure_dirs
from data import load_data, split_data


def main():
    ensure_dirs()
    X, y = load_data()
    X.assign(malignant=y).to_csv(DATA_DIR / "wdbc.csv", index=False)
    *_, X_test, _, _, y_test = split_data(X, y)
    for label, v in (("malignant", 1), ("benign", 0)):
        idx = y_test[y_test == v].index[0]
        (EXAMPLES_DIR / f"sample_{label}.json").write_text(json.dumps(X.loc[idx].to_dict(), indent=2))
    print(f"Wrote {DATA_DIR / 'wdbc.csv'} ({len(X)} rows) and example JSON files in {EXAMPLES_DIR}")


if __name__ == "__main__":
    main()
