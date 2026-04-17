import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    p = argparse.ArgumentParser(description="Train an AutoGluon router model (text->application_type).")
    p.add_argument("--train", required=True, help="Training CSV path (must have query_text, application_type).")
    p.add_argument("--out-dir", required=True, help="Model output directory.")
    p.add_argument("--time-limit", type=int, default=600, help="Training time limit seconds.")
    args = p.parse_args()

    train_path = Path(args.train)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(train_path)
    if "query_text" not in df.columns or "application_type" not in df.columns:
        raise SystemExit("Training CSV must contain columns: query_text, application_type")

    # Use AutoGluon Tabular + text n-grams (lighter than downloading Transformers).
    from autogluon.tabular import TabularPredictor
    from autogluon.features.generators import AutoMLPipelineFeatureGenerator

    feature_generator = AutoMLPipelineFeatureGenerator(
        enable_text_ngram_features=True,
        enable_text_special_features=True,
    )

    predictor = TabularPredictor(
        label="application_type",
        problem_type="multiclass",
        path=str(out_dir),
        verbosity=2,
    )
    predictor.fit(
        train_data=df[["query_text", "application_type"]],
        time_limit=max(60, int(args.time_limit)),
        presets="medium_quality_faster_train",
        feature_generator=feature_generator,
    )

    # Save a quick leaderboard if available
    try:
        lb = predictor.leaderboard(df[["query_text", "application_type"]], silent=True)
        lb.to_csv(out_dir / "leaderboard.csv", index=False)
    except Exception:
        pass

    print(f"Saved model to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

