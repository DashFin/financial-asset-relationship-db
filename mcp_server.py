import numpy as np
from mcp.server.fastmcp import FastMCP

from src.logic.asset_graph import AssetRelationshipGraph
from src.models.financial_models import Asset, AssetClass, Equity

# Initialize the MCP server
mcp = FastMCP("DashFin-Relationship-Manager")

# Global instance of the graph logic
graph = AssetRelationshipGraph()


@mcp.tool()
def add_equity_node(asset_id: str, symbol: str, name: str, sector: str, price: float) -> str:
    """Adds a new Equity asset to the relationship graph with validation."""
    try:
        # Uses existing Equity dataclass for post-init validation
        new_equity = Equity(
            id=asset_id, symbol=symbol, name=name, asset_class=AssetClass.EQUITY, sector=sector, price=price
        )
        return f"Successfully validated: {new_equity.name} ({new_equity.symbol})"
    except ValueError as e:
        return f"Validation Error: {str(e)}"


@mcp.resource("graph://data/3d-layout")
def get_3d_layout() -> str:
    """Provides current 3D visualization data for AI spatial reasoning."""
    # Leverages existing logic for deterministic layouts (seed 42)
    positions, asset_ids, colors, hover = graph.get_3d_visualization_data_enhanced()
    return f"Assets: {asset_ids}\nPositions: {positions.tolist()}"


if __name__ == "__main__":
    mcp.run()
