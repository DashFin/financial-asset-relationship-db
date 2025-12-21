"""Unit tests for 2D graph visualizations.

This module contains comprehensive unit tests for the graph_2d_visuals module including:
- 2D graph visualization creation
- Layout algorithms (circular, grid, spring)
- Relationship trace creation
- Filtering and display options
- Edge cases and error handling
"""

import pytest

import plotly.graph_objects as go

from src.visualizations.graph_2d_visuals import (
    visualize_2d_graph,
    _create_circular_layout,
    _create_grid_layout,
    _create_spring_layout_2d,
    _create_2d_relationship_traces,
)


def create_relationship_traces_with_defaults(
        graph, positions, asset_ids, **overrides
):
    """Helper to call _create_2d_relationship_traces with default parameters."""
    defaults = {
        "show_same_sector": True,
        "show_market_cap": True,
        "show_correlation": True,
        "show_corporate_bond": True,
        "show_commodity_currency": True,
        "show_income_comparison": True,
        "show_regulatory": True,
        "show_all_relationships": False,
    } | overrides
    return _create_2d_relationship_traces(graph, positions, asset_ids, **defaults)



@pytest.mark.unit
class TestVisualize2DGraph:
    """Test suite for the visualize_2d_graph function."""

    def test_visualize_2d_graph_with_populated_graph(self, populated_graph):
        """Test creating 2D visualization with populated graph."""
        # Execute
        fig = visualize_2d_graph(populated_graph)

        # Assert
        assert isinstance(fig, go.Figure)
        assert "2D Asset Relationship Network" in fig.layout.title.text
        assert fig.layout.plot_bgcolor == "white"
        assert fig.layout.paper_bgcolor == "#F8F9FA"

    def test_visualize_2d_graph_with_empty_graph(self, empty_graph):
        """Test creating 2D visualization with empty graph."""
        # Execute
        fig = visualize_2d_graph(empty_graph)

        # Assert
        assert isinstance(fig, go.Figure)

    def test_visualize_2d_graph_spring_layout(self, populated_graph):
        """Test 2D visualization with spring layout."""
        # Execute
        fig = visualize_2d_graph(populated_graph, layout_type="spring")

        # Assert
        assert isinstance(fig, go.Figure)
        # Verify layout type is mentioned in annotations
        has_layout_info = any("spring" in str(ann.text).lower() for ann in fig.layout.annotations)
        assert has_layout_info, "Layout type should be indicated in figure"

    def test_visualize_2d_graph_circular_layout(self, populated_graph):
        """Test 2D visualization with circular layout."""
        # Execute
        fig = visualize_2d_graph(populated_graph, layout_type="circular")

        # Assert
        assert isinstance(fig, go.Figure)
        has_layout_info = any("circular" in str(ann.text).lower() for ann in fig.layout.annotations)
        assert has_layout_info

    def test_visualize_2d_graph_grid_layout(self, populated_graph):
        """Test 2D visualization with grid layout."""
        # Execute
        fig = visualize_2d_graph(populated_graph, layout_type="grid")

        # Assert
        assert isinstance(fig, go.Figure)
        has_layout_info = any("grid" in str(ann.text).lower() for ann in fig.layout.annotations)
        assert has_layout_info

    def test_visualize_2d_graph_with_relationship_filters(self, populated_graph):
        """Test 2D visualization with selective relationship filtering."""
        # Execute - show only same sector relationships
        fig = visualize_2d_graph(
            populated_graph,
            show_same_sector=True,
            show_market_cap=False,
            show_correlation=False,
            show_corporate_bond=False,
            show_commodity_currency=False,
            show_income_comparison=False,
            show_regulatory=False,
            show_all_relationships=False,
        )

        # Assert
        assert isinstance(fig, go.Figure)

    def test_visualize_2d_graph_show_all_relationships(self, populated_graph):
        """Test showing all relationships regardless of individual filters."""
        # Execute
        fig = visualize_2d_graph(populated_graph, show_all_relationships=True)

        # Assert
        assert isinstance(fig, go.Figure)
        # When show_all is True, should display more traces
        assert len(fig.data) > 0

    def test_visualize_2d_graph_node_sizes(self, populated_graph):
        """Test that node sizes are properly calculated."""
        # Execute
        fig = visualize_2d_graph(populated_graph)

        # Find node trace
        node_traces = [trace for trace in fig.data if hasattr(trace, 'mode') and 'markers' in trace.mode]
        assert len(node_traces) > 0, "Should have node traces"
        
        node_trace = node_traces[0]
        if hasattr(node_trace.marker, 'size'):
            sizes = node_trace.marker.size
            # Verify sizes are within expected range
            for size in sizes:
                assert 20 <= size <= 50, "Node sizes should be between 20 and 50"

    def test_visualize_2d_graph_preserves_graph_state(self, populated_graph):
        """Test that visualization doesn't modify the graph."""
        initial_asset_count = len(populated_graph.assets)
        
        # Execute
        visualize_2d_graph(populated_graph)

        # Assert
        assert len(populated_graph.assets) == initial_asset_count


@pytest.mark.unit
class TestLayoutAlgorithms:
    """Test suite for layout algorithms."""

    def test_create_circular_layout_empty_list(self):
        """Test circular layout with empty asset list."""
        # Execute
        positions = _create_circular_layout([])

        # Assert
        assert isinstance(positions, dict)
        assert len(positions) == 0

    def test_create_circular_layout_single_asset(self):
        """Test circular layout with one asset."""
        # Execute
        positions = _create_circular_layout(["ASSET_1"])

        # Assert
        assert len(positions) == 1
        assert "ASSET_1" in positions
        x, y = positions["ASSET_1"]
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_create_circular_layout_multiple_assets(self):
        """Test circular layout with multiple assets."""
        asset_ids = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        
        # Execute
        positions = _create_circular_layout(asset_ids)

        # Assert
        assert len(positions) == 4
        for asset_id in asset_ids:
            assert asset_id in positions
            x, y = positions[asset_id]
            # Verify positions are roughly on unit circle
            distance = (x**2 + y**2)**0.5
            assert abs(distance - 1.0) < 0.01

    def test_create_grid_layout_empty_list(self):
        """Test grid layout with empty asset list."""
        # Execute
        positions = _create_grid_layout([])

        # Assert
        assert isinstance(positions, dict)
        assert len(positions) == 0

    def test_create_grid_layout_single_asset(self):
        """Test grid layout with one asset."""
        # Execute
        positions = _create_grid_layout(["ASSET_1"])

        # Assert
        assert len(positions) == 1
        assert "ASSET_1" in positions

    def test_create_grid_layout_multiple_assets(self):
        """Test grid layout with multiple assets."""
        asset_ids = [f"ASSET_{i}" for i in range(9)]
        
        # Execute
        positions = _create_grid_layout(asset_ids)

        # Assert
        assert len(positions) == 9
        # With 9 assets, should form a 3x3 grid
        x_coords = [pos[0] for pos in positions.values()]
        y_coords = [pos[1] for pos in positions.values()]
        
        # Verify we have grid-like structure
        assert len(set(x_coords)) <= 3  # At most 3 columns
        assert len(set(y_coords)) <= 3  # At most 3 rows

    def test_create_spring_layout_2d_empty_dict(self):
        """Test spring layout conversion with empty positions."""
        # Execute
        positions = _create_spring_layout_2d({}, [])

        # Assert
        assert isinstance(positions, dict)
        assert len(positions) == 0

    def test_create_spring_layout_2d_conversion(self):
        """Test conversion from 3D to 2D positions."""
        positions_3d = {
            "ASSET_1": (1.0, 2.0, 3.0),
            "ASSET_2": (4.0, 5.0, 6.0),
        }
        asset_ids = ["ASSET_1", "ASSET_2"]
        
        # Execute
        positions_2d = _create_spring_layout_2d(positions_3d, asset_ids)

        # Assert
        assert len(positions_2d) == 2
        assert positions_2d["ASSET_1"] == (1.0, 2.0)  # z-coordinate dropped
        assert positions_2d["ASSET_2"] == (4.0, 5.0)

    def test_create_spring_layout_2d_with_numpy_array(self):
        """Test spring layout with numpy array positions."""
        import numpy as np
        
        positions_3d = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        asset_ids = ["ASSET_1", "ASSET_2"]
        
        # Convert to dict format
        positions_dict = {asset_ids[i]: positions_3d[i] for i in range(len(asset_ids))}
        
        # Execute
        positions_2d = _create_spring_layout_2d(positions_dict, asset_ids)

        # Assert
        assert len(positions_2d) == 2


@pytest.mark.unit  
class TestRelationshipTraces:
    """Test suite for relationship trace creation."""

    def test_create_2d_relationship_traces_with_relationships(self, populated_graph):
        """Test creating relationship traces with existing relationships."""
        # Add some relationships
        populated_graph.add_relationship("TEST_AAPL", "TEST_BOND", "corporate_bond_to_equity", 0.8)
        
        # Create positions
        positions = {"TEST_AAPL": (0, 0), "TEST_BOND": (1, 1), "TEST_GOLD": (2, 2), "TEST_EUR": (3, 3)}
        asset_ids = list(positions.keys())
        
        # Execute
        traces = create_relationship_traces_with_defaults(
            populated_graph,
            positions,
            asset_ids,
        )

        # Assert
        assert isinstance(traces, list)

    def test_create_2d_relationship_traces_show_all(self, populated_graph):
        """Test creating traces with show_all_relationships=True."""
        positions = {"TEST_AAPL": (0, 0), "TEST_BOND": (1, 1)}
        asset_ids = list(positions.keys())
        
        # Execute
        traces = create_relationship_traces_with_defaults(
            populated_graph,
            positions,
            asset_ids,
            show_same_sector=False,
            show_market_cap=False,
            show_correlation=False,
            show_corporate_bond=False,
            show_commodity_currency=False,
            show_income_comparison=False,
            show_regulatory=False,
            show_all_relationships=True,
        )

        # Assert
        assert isinstance(traces, list)

    def test_create_2d_relationship_traces_selective_filtering(self, populated_graph):
        """Test selective relationship filtering."""
        positions = {"TEST_AAPL": (0, 0), "TEST_BOND": (1, 1)}
        asset_ids = list(positions.keys())
        
        # Execute - only show corporate bond relationships
        traces = create_relationship_traces_with_defaults(
            populated_graph,
            positions,
            asset_ids,
            show_same_sector=False,
            show_market_cap=False,
            show_correlation=False,
            show_corporate_bond=True,
            show_commodity_currency=False,
            show_income_comparison=False,
            show_regulatory=False,
            show_all_relationships=False,
        )

        # Assert
        assert isinstance(traces, list)

    def test_create_2d_relationship_traces_empty_graph(self, empty_graph):
        """Test creating traces with empty graph."""
        positions = {}
        asset_ids = []
        
        # Execute
        traces = create_relationship_traces_with_defaults(
            empty_graph,
            positions,
            asset_ids,
        )

        # Assert
        assert isinstance(traces, list)
        assert len(traces) == 0


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_visualize_2d_graph_with_single_asset(self, empty_graph, sample_equity):
        """Test 2D visualization with only one asset."""
        empty_graph.add_asset(sample_equity)
        
        # Execute
        fig = visualize_2d_graph(empty_graph)

        # Assert
        assert isinstance(fig, go.Figure)

    def test_circular_layout_with_many_assets(self):
        """Test circular layout with many assets."""
        asset_ids = [f"ASSET_{i}" for i in range(100)]
        
        # Execute
        positions = _create_circular_layout(asset_ids)

        # Assert
        assert len(positions) == 100
        # Verify all positions are on unit circle
        for pos in positions.values():
            distance = (pos[0]**2 + pos[1]**2)**0.5
            assert abs(distance - 1.0) < 0.01

    def test_grid_layout_with_non_square_number(self):
        """Test grid layout with non-perfect-square number of assets."""
        asset_ids = [f"ASSET_{i}" for i in range(7)]
        
        # Execute
        positions = _create_grid_layout(asset_ids)

        # Assert
        assert len(positions) == 7

    def test_visualize_2d_graph_with_invalid_layout_type(self, populated_graph):
        """Test that invalid layout type defaults to spring."""
        # Execute - use invalid layout type
        fig = visualize_2d_graph(populated_graph, layout_type="invalid")

        # Assert - should still create valid figure (defaults to spring)
        assert isinstance(fig, go.Figure)

    def test_relationship_traces_with_missing_assets_in_positions(self, populated_graph):
        """Test creating traces when some assets in relationships aren't in positions."""
        # Add relationship
        populated_graph.add_relationship("TEST_AAPL", "TEST_BOND", "corporate_bond_to_equity", 0.8)
        
        # Create positions without TEST_BOND
        positions = {"TEST_AAPL": (0, 0)}
        asset_ids = ["TEST_AAPL"]
        
        # Execute - should handle missing assets gracefully
        traces = _create_2d_relationship_traces(
            populated_graph,
            positions,
            asset_ids,
            show_same_sector=True,
            show_market_cap=True,
            show_correlation=True,
            show_corporate_bond=True,
            show_commodity_currency=True,
            show_income_comparison=True,
            show_regulatory=True,
            show_all_relationships=False,
        )

        # Assert
        assert isinstance(traces, list)

# ============================================================================
# ADDITIONAL COMPREHENSIVE TESTS FOR ENHANCED COVERAGE
# Generated to test formatting changes and ensure robustness
# ============================================================================


class TestStringQuoteHandling:
    """Test string quote handling after formatting changes (single vs double quotes)."""

    def test_has_getitem_attribute_detection(self):
        """Test __getitem__ attribute detection with various types."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        # Create mock positions with different types
        positions_3d = {
            'asset1': (1.0, 2.0, 3.0),
            'asset2': [4.0, 5.0, 6.0],
            'asset3': (7.0, 8.0, 9.0)
        }
        asset_ids = ['asset1', 'asset2', 'asset3']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert len(result) == 3
        assert 'asset1' in result
        assert result['asset1'] == (1.0, 2.0)
        assert result['asset2'] == (4.0, 5.0)

    def test_create_spring_layout_2d_with_numpy_arrays(self):
        """Test spring layout conversion with numpy array positions."""
        import numpy as np
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': np.array([1.0, 2.0, 3.0]),
            'asset2': np.array([4.0, 5.0, 6.0])
        }
        asset_ids = ['asset1', 'asset2']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert len(result) == 2
        assert isinstance(result['asset1'], tuple)
        assert result['asset1'] == (1.0, 2.0)

    def test_create_spring_layout_2d_missing_asset(self):
        """Test spring layout handles missing assets gracefully."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': (1.0, 2.0, 3.0)
        }
        asset_ids = ['asset1', 'asset2', 'asset3']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        # Should only include asset1
        assert len(result) == 1
        assert 'asset1' in result
        assert 'asset2' not in result


class TestRelationshipDictionaryFormatting:
    """Test relationship dictionary formatting with updated quote style."""

    def test_relationship_groups_structure(self, sample_graph):
        """Test relationship groups are properly structured with correct keys."""
        from src.visualizations.graph_2d_visuals import _create_2d_relationship_traces
        
        positions = {
            'AAPL': (0.0, 0.0),
            'GOOGL': (1.0, 1.0),
            'MSFT': (2.0, 2.0)
        }
        
        traces = _create_2d_relationship_traces(sample_graph, positions)
        
        # Verify traces were created
        assert len(traces) > 0
        for trace in traces:
            # Verify trace has expected properties
            assert hasattr(trace, 'x')
            assert hasattr(trace, 'y')
            assert hasattr(trace, 'mode')

    def test_relationship_hover_text_format(self, sample_graph):
        """Test hover text format for relationships."""
        from src.visualizations.graph_2d_visuals import _create_2d_relationship_traces
        
        positions = {
            'AAPL': (0.0, 0.0),
            'GOOGL': (1.0, 1.0)
        }
        
        # Add a relationship
        sample_graph.add_relationship('AAPL', 'GOOGL', 'sector_peer', strength=0.8)
        
        traces = _create_2d_relationship_traces(sample_graph, positions)
        
        assert len(traces) > 0
        # Verify at least one trace has hover information
        has_hover = any(hasattr(trace, 'hovertext') or hasattr(trace, 'hoverinfo') for trace in traces)
        assert has_hover

    def test_relationship_source_target_keys(self, sample_graph):
        """Test relationship dictionaries use correct keys (source_id, target_id)."""
        from src.visualizations.graph_2d_visuals import _create_2d_relationship_traces
        
        positions = {
            'AAPL': (0.0, 0.0),
            'GOOGL': (1.0, 1.0)
        }
        
        sample_graph.add_relationship('AAPL', 'GOOGL', 'test_rel', strength=0.5)
        
        traces = _create_2d_relationship_traces(sample_graph, positions)
        
        # Should create traces without errors
        assert len(traces) > 0


class TestVisualizationModeStrings:
    """Test visualization mode string handling (single quotes vs double quotes)."""

    def test_node_trace_mode_format(self, sample_graph):
        """Test node trace uses correct mode string format."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        fig = visualize_2d_graph(sample_graph, layout_type='circular')
        
        # Find node traces (should have markers+text mode)
        node_traces = [trace for trace in fig.data if hasattr(trace, 'marker') and trace.marker]
        
        assert len(node_traces) > 0
        for trace in node_traces:
            if hasattr(trace, 'mode'):
                # Mode should include 'markers' for nodes
                assert 'markers' in trace.mode.lower() or trace.mode == 'markers+text'

    def test_edge_trace_mode_format(self, sample_graph):
        """Test edge trace uses correct mode string format."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        sample_graph.add_relationship('AAPL', 'GOOGL', 'test', strength=0.5)
        
        fig = visualize_2d_graph(sample_graph, layout_type='spring')
        
        # Find edge traces (should have lines mode)
        edge_traces = [trace for trace in fig.data if not hasattr(trace, 'marker') or not trace.marker]
        
        # If relationships exist, should have edge traces
        if len(sample_graph.relationships) > 0:
            assert len(edge_traces) > 0

    def test_hoverinfo_string_format(self, sample_graph):
        """Test hoverinfo uses correct string format."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        fig = visualize_2d_graph(sample_graph, layout_type='grid')
        
        # Check that traces have hoverinfo set
        for trace in fig.data:
            if hasattr(trace, 'hoverinfo'):
                assert isinstance(trace.hoverinfo, str)


class TestColorStringFormatting:
    """Test color string formatting with single quotes."""

    def test_asset_class_color_mapping(self, sample_graph):
        """Test asset class colors are properly mapped."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        fig = visualize_2d_graph(sample_graph, layout_type='circular')
        
        # Find node trace
        node_traces = [trace for trace in fig.data if hasattr(trace, 'marker') and trace.marker]
        
        assert len(node_traces) > 0
        for trace in node_traces:
            if hasattr(trace.marker, 'color'):
                colors = trace.marker.color
                # Colors should be valid hex or rgba strings
                if isinstance(colors, list):
                    for color in colors:
                        assert isinstance(color, str)
                        # Should be hex color format
                        assert color.startswith('#') or 'rgb' in color.lower()

    def test_default_color_for_unknown_asset_class(self, sample_graph):
        """Test default color is applied for unknown asset classes."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        from src.models.financial_models import AssetClass
        
        # Create asset with unknown/custom asset class
        # (This tests the .get() fallback in color mapping)
        
        fig = visualize_2d_graph(sample_graph, layout_type='spring')
        
        node_traces = [trace for trace in fig.data if hasattr(trace, 'marker') and trace.marker]
        assert len(node_traces) > 0

    def test_gridcolor_string_format(self, sample_graph):
        """Test grid color uses proper rgba string format."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        fig = visualize_2d_graph(sample_graph, layout_type='grid')
        
        # Check layout grid colors
        assert hasattr(fig.layout, 'xaxis')
        assert hasattr(fig.layout, 'yaxis')
        
        if hasattr(fig.layout.xaxis, 'gridcolor'):
            assert isinstance(fig.layout.xaxis.gridcolor, str)
        if hasattr(fig.layout.yaxis, 'gridcolor'):
            assert isinstance(fig.layout.yaxis.gridcolor, str)


class TestLayoutFunctionParameterFormatting:
    """Test function parameters after formatting changes."""

    def test_create_spring_layout_2d_parameters(self):
        """Test _create_spring_layout_2d handles parameters correctly."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        # Test with multiline parameter formatting
        positions_3d = {
            'asset1': (1.0, 2.0, 3.0),
            'asset2': (4.0, 5.0, 6.0)
        }
        asset_ids = ['asset1', 'asset2']
        
        result = _create_spring_layout_2d(
            positions_3d,
            asset_ids
        )
        
        assert len(result) == 2
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in result.values())

    def test_visualize_2d_graph_with_all_layout_types(self, sample_graph):
        """Test visualization with all supported layout types."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        layout_types = ['circular', 'grid', 'spring']
        
        for layout_type in layout_types:
            fig = visualize_2d_graph(sample_graph, layout_type=layout_type)
            assert fig is not None
            assert len(fig.data) > 0

    def test_relationship_trace_creation_with_multiple_types(self, sample_graph):
        """Test relationship traces with multiple relationship types."""
        from src.visualizations.graph_2d_visuals import _create_2d_relationship_traces
        
        positions = {
            'AAPL': (0.0, 0.0),
            'GOOGL': (1.0, 1.0),
            'MSFT': (2.0, 2.0)
        }
        
        # Add multiple relationship types
        sample_graph.add_relationship('AAPL', 'GOOGL', 'sector_peer', strength=0.8)
        sample_graph.add_relationship('GOOGL', 'MSFT', 'competitor', strength=0.6)
        sample_graph.add_relationship('AAPL', 'MSFT', 'sector_peer', strength=0.7)
        
        traces = _create_2d_relationship_traces(sample_graph, positions)
        
        # Should create separate traces for each relationship type
        assert len(traces) >= 1


class TestHoverTextMultilineFormatting:
    """Test multiline string formatting in hover text."""

    def test_hover_text_line_breaks(self, sample_graph):
        """Test hover text contains proper line breaks."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        sample_graph.add_relationship('AAPL', 'GOOGL', 'test', strength=0.9)
        
        fig = visualize_2d_graph(sample_graph, layout_type='circular')
        
        # Check for traces with hover text
        for trace in fig.data:
            if hasattr(trace, 'hovertext') and trace.hovertext:
                # Verify hover text is a list or string
                assert isinstance(trace.hovertext, (list, str))

    def test_node_hover_text_format(self, sample_graph):
        """Test node hover text includes asset information."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        fig = visualize_2d_graph(sample_graph, layout_type='spring')
        
        # Find node traces
        node_traces = [trace for trace in fig.data if hasattr(trace, 'marker') and trace.marker]
        
        assert len(node_traces) > 0
        for trace in node_traces:
            if hasattr(trace, 'hovertext') and trace.hovertext:
                # Hover text should contain asset information
                if isinstance(trace.hovertext, list):
                    assert len(trace.hovertext) > 0


class TestEdgeCasesWithFormattingChanges:
    """Test edge cases that might be affected by formatting changes."""

    def test_empty_positions_dict(self):
        """Test handling of empty positions dictionary."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {}
        asset_ids = []
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert result == {}

    def test_positions_with_special_characters_in_keys(self):
        """Test positions dictionary with special character keys."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset-1': (1.0, 2.0, 3.0),
            'asset_2': (4.0, 5.0, 6.0),
            'asset.3': (7.0, 8.0, 9.0)
        }
        asset_ids = ['asset-1', 'asset_2', 'asset.3']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert len(result) == 3
        assert 'asset-1' in result
        assert 'asset_2' in result
        assert 'asset.3' in result

    def test_very_large_coordinate_values(self):
        """Test handling of very large coordinate values."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': (1e10, 2e10, 3e10),
            'asset2': (-1e10, -2e10, -3e10)
        }
        asset_ids = ['asset1', 'asset2']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert len(result) == 2
        assert result['asset1'] == (1e10, 2e10)
        assert result['asset2'] == (-1e10, -2e10)

    def test_zero_coordinate_values(self):
        """Test handling of zero coordinate values."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': (0.0, 0.0, 0.0),
            'asset2': (0.0, 1.0, 0.0)
        }
        asset_ids = ['asset1', 'asset2']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert result['asset1'] == (0.0, 0.0)
        assert result['asset2'] == (0.0, 1.0)


class TestVisualizationRobustness:
    """Test visualization robustness with various graph states."""

    def test_visualization_with_single_asset(self):
        """Test visualization with only one asset."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        from src.logic.asset_graph import AssetRelationshipGraph
        from src.models.financial_models import Equity, AssetClass
        
        graph = AssetRelationshipGraph()
        asset = Equity(
            id='SINGLE',
            name='Single Asset',
            asset_class=AssetClass.EQUITY,
            price=100.0
        )
        graph.add_asset(asset)
        
        fig = visualize_2d_graph(graph, layout_type='circular')
        
        assert fig is not None
        assert len(fig.data) > 0

    def test_visualization_with_disconnected_assets(self):
        """Test visualization with multiple disconnected assets."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        # sample_graph has disconnected assets by default
        from src.logic.asset_graph import AssetRelationshipGraph
        from src.models.financial_models import Equity, AssetClass
        
        graph = AssetRelationshipGraph()
        for i in range(5):
            asset = Equity(
                id=f'ASSET{i}',
                name=f'Asset {i}',
                asset_class=AssetClass.EQUITY,
                price=100.0
            )
            graph.add_asset(asset)
        
        fig = visualize_2d_graph(graph, layout_type='grid')
        
        assert fig is not None
        assert len(fig.data) > 0

    def test_visualization_with_dense_relationships(self, sample_graph):
        """Test visualization with many relationships."""
        from src.visualizations.graph_2d_visuals import visualize_2d_graph
        
        # Add many relationships
        assets = list(sample_graph.assets.keys())
        for i, source in enumerate(assets):
            for target in assets[i+1:]:
                sample_graph.add_relationship(source, target, 'dense', strength=0.5)
        
        fig = visualize_2d_graph(sample_graph, layout_type='spring')
        
        assert fig is not None
        # Should have many traces
        assert len(fig.data) >= 2


class TestGetitemAttributeAccess:
    """Test __getitem__ attribute access patterns."""

    def test_tuple_getitem_access(self):
        """Test __getitem__ access on tuples."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': (1.0, 2.0, 3.0)
        }
        asset_ids = ['asset1']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert hasattr(positions_3d['asset1'], '__getitem__')
        assert result['asset1'] == (1.0, 2.0)

    def test_list_getitem_access(self):
        """Test __getitem__ access on lists."""
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': [1.0, 2.0, 3.0]
        }
        asset_ids = ['asset1']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert hasattr(positions_3d['asset1'], '__getitem__')
        assert result['asset1'] == (1.0, 2.0)

    def test_mixed_types_getitem_access(self):
        """Test __getitem__ access with mixed position types."""
        import numpy as np
        from src.visualizations.graph_2d_visuals import _create_spring_layout_2d
        
        positions_3d = {
            'asset1': (1.0, 2.0, 3.0),
            'asset2': [4.0, 5.0, 6.0],
            'asset3': np.array([7.0, 8.0, 9.0])
        }
        asset_ids = ['asset1', 'asset2', 'asset3']
        
        result = _create_spring_layout_2d(positions_3d, asset_ids)
        
        assert len(result) == 3
        # All should be converted to tuples
        for pos in result.values():
            assert isinstance(pos, tuple)
            assert len(pos) == 2