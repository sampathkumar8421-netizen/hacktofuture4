import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    p = argparse.ArgumentParser(description="Predict application_type for a user query using trained router model.")
    p.add_argument("--model-dir", required=True)
    p.add_argument("--text", required=True)
    args = p.parse_args()

    from autogluon.tabular import TabularPredictor

    predictor = TabularPredictor.load(Path(args.model_dir))
    df = pd.DataFrame([{"query_text": args.text}])
    pred = predictor.predict(df)
    proba = predictor.predict_proba(df)

    print(f"predicted_application_type: {pred.iloc[0]}")
    # show top-5 probabilities
    p_series = proba.iloc[0].sort_values(ascending=False).head(5)
    print("top5:")
    for k, v in p_series.items():
        print(f"  {k}\t{float(v):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

