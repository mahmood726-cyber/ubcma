from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


def _split_csv_arg(value: str | Sequence[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _require_columns(df: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing {label} column(s): {', '.join(missing)}")


def _require_finite(name: str, values: np.ndarray) -> None:
    if values.size and not np.all(np.isfinite(values)):
        raise ValueError(f"{name} contains NaN or infinite values.")


@dataclass
class MetaAnalysisDataset:
    y: np.ndarray
    se: np.ndarray
    quality: np.ndarray
    quality_score: np.ndarray
    moderators: np.ndarray
    moderator_reference_values: np.ndarray
    design: np.ndarray
    study_ids: list[str]
    quality_names: list[str]
    moderator_names: list[str]
    design_names: list[str]
    raw: pd.DataFrame

    @property
    def n_studies(self) -> int:
        return int(self.y.shape[0])

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        effect_col: str = "yi",
        se_col: str = "sei",
        quality_cols: Sequence[str] | str | None = None,
        moderator_cols: Sequence[str] | str | None = None,
        design_col: str | None = None,
        design_reference: str | None = None,
        study_id_col: str | None = None,
    ) -> "MetaAnalysisDataset":
        df = pd.read_csv(path).copy()
        return cls.from_dataframe(
            df,
            effect_col=effect_col,
            se_col=se_col,
            quality_cols=quality_cols,
            moderator_cols=moderator_cols,
            design_col=design_col,
            design_reference=design_reference,
            study_id_col=study_id_col,
        )

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        effect_col: str = "yi",
        se_col: str = "sei",
        quality_cols: Sequence[str] | str | None = None,
        moderator_cols: Sequence[str] | str | None = None,
        design_col: str | None = None,
        design_reference: str | None = None,
        study_id_col: str | None = None,
    ) -> "MetaAnalysisDataset":
        df = df.copy()
        if effect_col not in df or se_col not in df:
            raise ValueError(
                f"CSV must contain '{effect_col}' and '{se_col}' columns."
            )

        y = df[effect_col].astype(float).to_numpy()
        se = df[se_col].astype(float).to_numpy()
        if np.any(se <= 0):
            raise ValueError("Standard errors must be strictly positive.")
        _require_finite(effect_col, y)
        _require_finite(se_col, se)

        quality_names = _split_csv_arg(quality_cols)
        if quality_names:
            _require_columns(df, quality_names, "quality")
        else:
            quality_names = [
                col
                for col in df.columns
                if col.lower().startswith("rob_") or col.lower().startswith("bias_")
            ]

        summary_quality_name = next(
            (
                col
                for col in df.columns
                if col.lower() in {"quality_score", "bias_score", "risk_of_bias", "rob"}
            ),
            None,
        )

        quality = (
            df[quality_names].astype(float).to_numpy()
            if quality_names
            else np.zeros((len(df), 0), dtype=float)
        )
        _require_finite("quality", quality)
        if quality.shape[1]:
            quality_score = quality.mean(axis=1)
        elif summary_quality_name is not None:
            quality_score = df[summary_quality_name].astype(float).to_numpy()
        else:
            quality_score = np.zeros(len(df), dtype=float)
        _require_finite("quality_score", quality_score)

        moderator_names = _split_csv_arg(moderator_cols)
        if moderator_names:
            _require_columns(df, moderator_names, "moderator")
        moderators = (
            df[moderator_names].astype(float).to_numpy()
            if moderator_names
            else np.zeros((len(df), 0), dtype=float)
        )
        _require_finite("moderators", moderators)
        moderator_reference_values = (
            moderators.mean(axis=0)
            if moderators.shape[1]
            else np.zeros(0, dtype=float)
        )
        if moderators.shape[1]:
            moderators = moderators - moderator_reference_values

        design_names: list[str] = []
        if design_col:
            if design_col not in df.columns:
                raise ValueError(f"Missing design column: {design_col}")
            design_series = df[design_col].astype(str)
            categories = list(pd.unique(design_series))
            if design_reference is None and len(categories) > 1:
                raise ValueError(
                    "design_reference is required when the design column has multiple levels."
                )
            if design_reference is not None:
                if design_reference not in categories:
                    raise ValueError(
                        f"design_reference '{design_reference}' was not found in column '{design_col}'."
                    )
                ordered = [design_reference] + [
                    category for category in categories if category != design_reference
                ]
                design_series = pd.Categorical(
                    design_series,
                    categories=ordered,
                    ordered=True,
                )
            design_df = pd.get_dummies(
                design_series,
                prefix=design_col,
                drop_first=True,
                dtype=float,
            )
            design = design_df.to_numpy()
            design_names = design_df.columns.tolist()
        else:
            design = np.zeros((len(df), 0), dtype=float)
        _require_finite("design", design)

        if study_id_col:
            if study_id_col not in df.columns:
                raise ValueError(f"Missing study-id column: {study_id_col}")
            study_ids = df[study_id_col].astype(str).tolist()
        elif "study_id" in df:
            study_ids = df["study_id"].astype(str).tolist()
        else:
            study_ids = [f"study_{i + 1}" for i in range(len(df))]

        return cls(
            y=y,
            se=se,
            quality=quality,
            quality_score=quality_score,
            moderators=moderators,
            moderator_reference_values=moderator_reference_values,
            design=design,
            study_ids=study_ids,
            quality_names=quality_names,
            moderator_names=moderator_names,
            design_names=design_names,
            raw=df,
        )
