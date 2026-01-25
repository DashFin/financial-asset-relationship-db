from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Any, Final, Optional, TypedDict, cast

import gradio as gr
import plotly.graph_objects as go

from src.analysis.formulaic_analysis import FormulaicdAnalyzer
from src.data.real_data_fetcher import create_real_database
from src.logic.asset_graph import AssetRelationshipGraph
from src.models.financial_models import Asset
from src.reports.schema_report import generate_schema_report
from src.visualizations.formulaic_visuals import FormulaicVisualizer
from src.visualizations.graph_2d_visuals import visualize_2d_graph
from src.visualizations.graph_visuals import (
    visualize_3d_graph,
    visualize_3d_graph_with_filters,
)
from src.visualizations.metric_visuals import visualize_metrics


LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


# -------- Typed structures --------


class RelationshipMetrics(TypedDict):
    total_assets: int
    total_relationships: int
    average_relationship_strength: float
    relationship_density: float
    regulatory_event_count: int
    asset_class_distribution: dict[str, int]
    top_relationships: list[tuple[str, str, str, float]]


class AssetRelationshipView(TypedDict):
    outgoing: dict[str, dict[str, Any]]
    incoming: dict[str, dict[str, Any]]


GradioUpdate = Any  # gr.update has no public typing


class AppConstants:
    TITLE: Final[str] = "Financial Asset Relationship Database Visualization"
    ERROR_LABEL: Final[str] = "Error"

    INITIAL_GRAPH_ERROR: Final[str] = "Failed to create sample database"
    REFRESH_OUTPUTS_ERROR: Final[str] = "Error refreshing outputs"

    APP_START_INFO: Final[str] = "Starting Financial Asset Relationship Database application"
    APP_LAUNCH_INFO: Final[str] = "Launching Gradio interface"
    APP_START_ERROR: Final[str] = "Failed to start application"

    NETWORK_STATISTICS_TEXT: Final[str] = (
        "Network Statistics:\n\n"
        "Total Assets: {total_assets}\n"
        "Total Relationships: {total_relationships}\n"
        "Average Relationship Strength: {average_relationship_strength:.3f}\n"
        "Relationship Density: {relationship_density:.2f}%\n"
        "Regulatory Events: {regulatory_event_count}\n\n"
        "Asset Class Distribution:\n{asset_class_distribution}\n\n"
        "Top Relationships:\n"
    )


class FinancialAssetApp:
    def __init__(self) -> None:
        self.graph: Optional[AssetRelationshipGraph] = None
        self._initialize_graph()

    def _initialize_graph(self) -> None:
        try:
            LOGGER.info("Initializing real financial dataset")
            self.graph = create_real_database()
            LOGGER.info("Initialized graph with %d assets", len(self.graph.assets))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("%s: %s", AppConstants.INITIAL_GRAPH_ERROR, exc)
            raise

    def ensure_graph(self) -> AssetRelationshipGraph:
        if self.graph is None:
            LOGGER.warning("Graph missing, reinitializing")
            self._initialize_graph()

        assert self.graph is not None  # for mypy
        return self.graph

    @staticmethod
    def _update_metrics_text(graph: AssetRelationshipGraph) -> str:
        raw_metrics = cast(RelationshipMetrics, graph.calculate_metrics())

        text = AppConstants.NETWORK_STATISTICS_TEXT.format(
            total_assets=raw_metrics["total_assets"],
            total_relationships=raw_metrics["total_relationships"],
            average_relationship_strength=raw_metrics[
                "average_relationship_strength"
            ],
            relationship_density=raw_metrics["relationship_density"],
            regulatory_event_count=raw_metrics["regulatory_event_count"],
            asset_class_distribution=json.dumps(
                raw_metrics["asset_class_distribution"], indent=2
            ),
        )

        for idx, (src, tgt, rel, strength) in enumerate(
            raw_metrics["top_relationships"], start=1
        ):
            text += f"{idx}. {src} → {tgt} ({rel}): {strength:.1%}\n"

        return text

    def update_all_metrics_outputs(
        self,
        graph: AssetRelationshipGraph,
    ) -> tuple[go.Figure, go.Figure, go.Figure, str]:
        fig1, fig2, fig3 = visualize_metrics(graph)
        return fig1, fig2, fig3, self._update_metrics_text(graph)

    @staticmethod
    def update_asset_info(
        selected_asset: Optional[str],
        graph: AssetRelationshipGraph,
    ) -> tuple[dict[str, Any], AssetRelationshipView]:
        if not selected_asset or selected_asset not in graph.assets:
            return {}, {"outgoing": {}, "incoming": {}}

        asset: Asset = graph.assets[selected_asset]
        asset_dict: dict[str, Any] = asdict(asset)
        asset_dict["asset_class"] = asset.asset_class.value

        outgoing = {
            target: {"relationship_type": rel, "strength": strength}
            for target, rel, strength in graph.relationships.get(selected_asset, [])
        }

        incoming = {
            source: {"relationship_type": rel, "strength": strength}
            for source, rel, strength in graph.incoming_relationships.get(
                selected_asset, []
            )
        }

        return asset_dict, {"outgoing": outgoing, "incoming": incoming}

    def refresh_all_outputs(
        self,
        graph_state: AssetRelationshipGraph,
    ) -> tuple[
        go.Figure,
        go.Figure,
        go.Figure,
        go.Figure,
        str,
        str,
        GradioUpdate,
        GradioUpdate,
    ]:
        try:
            graph = self.ensure_graph()

            fig_3d = visualize_3d_graph(graph)
            fig1, fig2, fig3, metrics_txt = self.update_all_metrics_outputs(graph)
            schema = generate_schema_report(graph)
            assets = list(graph.assets.keys())

            return (
                fig_3d,
                fig1,
                fig2,
                fig3,
                metrics_txt,
                schema,
                gr.update(choices=assets, value=None),
                gr.update(value="", visible=False),
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("%s: %s", AppConstants.REFRESH_OUTPUTS_ERROR, exc)
            return (
                go.Figure(),
                go.Figure(),
                go.Figure(),
                go.Figure(),
                "",
                "",
                gr.update(choices=[], value=None),
                gr.update(value=str(exc), visible=True),
            )

    def generate_formulaic_analysis(
        self,
        graph_state: AssetRelationshipGraph,
    ) -> tuple[
        go.Figure,
        go.Figure,
        go.Figure,
        GradioUpdate,
        str,
        GradioUpdate,
    ]:
        try:
            graph = self.ensure_graph()

            analyzer = FormulaicdAnalyzer()
            visualizer = FormulaicVisualizer()

            results: dict[str, Any] = analyzer.analyze_graph(graph)

            dashboard = visualizer.create_formula_dashboard(results)
            correlation = visualizer.create_correlation_network(
                results.get("empirical_relationships", {})
            )
            comparison = visualizer.create_metric_comparison_chart(results)

            formulas = results.get("formulas", [])
            choices = [f.name for f in formulas if hasattr(f, "name")]

            summary = self._format_formula_summary(
                results.get("summary", {}),
                results,
            )

            return (
                dashboard,
                correlation,
                comparison,
                gr.update(choices=choices, value=choices[0] if choices else None),
                summary,
                gr.update(visible=False),
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Formulaic analysis failure: %s", exc)
            empty = go.Figure()
            return (
                empty,
                empty,
                empty,
                gr.update(choices=[], value=None),
                str(exc),
                gr.update(value=str(exc), visible=True),
            )

    @staticmethod
    def _format_formula_summary(
        summary: dict[str, Any],
        results: dict[str, Any],
    ) -> str:
        formulas = results.get("formulas", [])
        return "\n".join(
            [
                "Formulaic Analysis Summary",
                f"Total formulas: {len(formulas)}",
                f"Average R²: {summary.get('avg_r_squared', 0):.3f}",
                f"Empirical points: {summary.get('empirical_data_points', 0)}",
            ]
        )
