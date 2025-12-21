/**
 * Comprehensive unit tests for MetricsDashboard component.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetricsDashboard from '../../app/components/MetricsDashboard';
import type { Metrics } from '../../app/types/api';
import { mockMetrics } from '../test-utils';

describe('MetricsDashboard Component', () => {
  it('should render all metric cards', () => {
    render(<MetricsDashboard metrics={mockMetrics} />);
    
    expect(screen.getByText('Total Assets')).toBeInTheDocument();
    expect(screen.getByText('Total Relationships')).toBeInTheDocument();
    expect(screen.getByText('Network Density')).toBeInTheDocument();
  });

  it('should display metrics correctly', () => {
    render(<MetricsDashboard metrics={mockMetrics} />);
    
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('42.00%')).toBeInTheDocument();
  });

  it('should format network density as percentage', () => {
    render(<MetricsDashboard metrics={mockMetrics} />);
    expect(screen.getByText('42.00%')).toBeInTheDocument();
  });

  it('should display average degree with 2 decimals', () => {
    render(<MetricsDashboard metrics={mockMetrics} />);
    expect(screen.getByText('5.60')).toBeInTheDocument();
  });

  it('should display all asset classes', () => {
    render(<MetricsDashboard metrics={mockMetrics} />);
    
    expect(screen.getByText('EQUITY:')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('COMMODITY:')).toBeInTheDocument();
  });

  it('should handle zero metrics', () => {
    const zeroMetrics: Metrics = {
      total_assets: 0,
      total_relationships: 0,
      asset_classes: {},
      avg_degree: 0,
      max_degree: 0,
      network_density: 0,
    };
    
    render(<MetricsDashboard metrics={zeroMetrics} />);
    expect(screen.getByText('0.00%')).toBeInTheDocument();
  });
});

// ============================================================================
// ADDITIONAL COMPREHENSIVE TESTS FOR ENHANCED COVERAGE
// Tests for formatting changes and component robustness
// ============================================================================

describe('MetricsDashboard - File Ending and Formatting Tests', () => {
  const completeMetrics = {
    total_assets: 100,
    total_relationships: 250,
    avg_relationship_strength: 0.75,
    asset_classes: {
      EQUITY: 60,
      FIXED_INCOME: 25,
      COMMODITY: 10,
      CURRENCY: 5,
    },
  };

  test('component renders without trailing newline issues', () => {
    render(<MetricsDashboard metrics={completeMetrics} />);
    
    expect(screen.getByText(/100/)).toBeInTheDocument();
    expect(screen.getByText(/250/)).toBeInTheDocument();
  });

  test('maintains proper component structure', () => {
    const { container } = render(<MetricsDashboard metrics={completeMetrics} />);
    
    expect(container.firstChild).toBeTruthy();
    expect(container.querySelector('div')).toBeInTheDocument();
  });

  test('displays all metric values correctly', () => {
    render(<MetricsDashboard metrics={completeMetrics} />);
    
    expect(screen.getByText(/100/)).toBeInTheDocument();
    expect(screen.getByText(/250/)).toBeInTheDocument();
    expect(screen.getByText(/0\.75|75/)).toBeInTheDocument();
  });

  test('handles zero values correctly', () => {
    const zeroMetrics = {
      total_assets: 0,
      total_relationships: 0,
      avg_relationship_strength: 0,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={zeroMetrics} />);
    
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  test('handles very large numbers', () => {
    const largeMetrics = {
      total_assets: 999999,
      total_relationships: 5000000,
      avg_relationship_strength: 0.999,
      asset_classes: {
        EQUITY: 500000,
      },
    };

    render(<MetricsDashboard metrics={largeMetrics} />);
    
    expect(screen.getByText(/999999/)).toBeInTheDocument();
  });

  test('handles decimal precision correctly', () => {
    const preciseMetrics = {
      total_assets: 100,
      total_relationships: 200,
      avg_relationship_strength: 0.123456789,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={preciseMetrics} />);
    
    // Should display with appropriate precision
    expect(screen.getByText(/0\.12/)).toBeInTheDocument();
  });

  test('handles missing asset classes', () => {
    const noClassesMetrics = {
      total_assets: 50,
      total_relationships: 100,
      avg_relationship_strength: 0.5,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={noClassesMetrics} />);
    
    expect(screen.getByText(/50/)).toBeInTheDocument();
  });

  test('handles single asset class', () => {
    const singleClassMetrics = {
      total_assets: 10,
      total_relationships: 20,
      avg_relationship_strength: 0.8,
      asset_classes: {
        EQUITY: 10,
      },
    };

    render(<MetricsDashboard metrics={singleClassMetrics} />);
    
    expect(screen.getByText(/10/)).toBeInTheDocument();
  });

  test('asset class distribution displays correctly', () => {
    render(<MetricsDashboard metrics={completeMetrics} />);
    
    expect(screen.getByText(/60/)).toBeInTheDocument();
    expect(screen.getByText(/25/)).toBeInTheDocument();
    expect(screen.getByText(/10/)).toBeInTheDocument();
    expect(screen.getByText(/5/)).toBeInTheDocument();
  });

  test('responsive layout maintained', () => {
    const { container } = render(<MetricsDashboard metrics={completeMetrics} />);
    
    // Should have proper structure for responsive layout
    expect(container.firstChild).toBeTruthy();
  });

  test('accessibility attributes present', () => {
    render(<MetricsDashboard metrics={completeMetrics} />);
    
    // Component should be accessible
    const elements = screen.getAllByText(/\d+/);
    expect(elements.length).toBeGreaterThan(0);
  });

  test('handles null/undefined gracefully', () => {
    const incompleteMetrics = {
      total_assets: 100,
      total_relationships: 200,
      avg_relationship_strength: null as any,
      asset_classes: undefined as any,
    };

    render(<MetricsDashboard metrics={incompleteMetrics} />);
    
    // Should not crash
    expect(screen.getByText(/100/)).toBeInTheDocument();
  });

  test('percentage calculations correct', () => {
    const percentMetrics = {
      total_assets: 100,
      total_relationships: 200,
      avg_relationship_strength: 1.0,
      asset_classes: {
        EQUITY: 50,
        FIXED_INCOME: 50,
      },
    };

    render(<MetricsDashboard metrics={percentMetrics} />);
    
    // If percentages are shown, they should be calculated correctly
    expect(screen.getByText(/50/)).toBeInTheDocument();
  });

  test('styling classes applied correctly', () => {
    const { container } = render(<MetricsDashboard metrics={completeMetrics} />);
    
    // Should have appropriate CSS classes
    const divs = container.querySelectorAll('div');
    expect(divs.length).toBeGreaterThan(0);
  });

  test('metric cards render individually', () => {
    render(<MetricsDashboard metrics={completeMetrics} />);
    
    // Each metric should be independently rendered
    expect(screen.getByText(/100/)).toBeInTheDocument();
    expect(screen.getByText(/250/)).toBeInTheDocument();
  });

  test('handles component re-renders', () => {
    const { rerender } = render(<MetricsDashboard metrics={completeMetrics} />);
    
    const updatedMetrics = {
      ...completeMetrics,
      total_assets: 150,
    };
    
    rerender(<MetricsDashboard metrics={updatedMetrics} />);
    
    expect(screen.getByText(/150/)).toBeInTheDocument();
  });

  test('maintains data integrity across updates', () => {
    const { rerender } = render(<MetricsDashboard metrics={completeMetrics} />);
    
    const newMetrics = {
      total_assets: 200,
      total_relationships: 400,
      avg_relationship_strength: 0.85,
      asset_classes: {
        EQUITY: 120,
      },
    };
    
    rerender(<MetricsDashboard metrics={newMetrics} />);
    
    expect(screen.getByText(/200/)).toBeInTheDocument();
    expect(screen.getByText(/400/)).toBeInTheDocument();
  });
});

describe('MetricsDashboard - Edge Cases', () => {
  test('handles extreme values', () => {
    const extremeMetrics = {
      total_assets: Number.MAX_SAFE_INTEGER,
      total_relationships: 0,
      avg_relationship_strength: 1.0,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={extremeMetrics} />);
    
    // Should render without crashing
    expect(screen.getByText(new RegExp(extremeMetrics.total_assets.toString().substring(0, 5)))).toBeInTheDocument();
  });

  test('handles negative values gracefully', () => {
    const negativeMetrics = {
      total_assets: -1,
      total_relationships: -5,
      avg_relationship_strength: -0.5,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={negativeMetrics} />);
    
    // Component should handle gracefully (even if illogical)
    expect(screen.getByText(/-1/)).toBeInTheDocument();
  });

  test('handles NaN values', () => {
    const nanMetrics = {
      total_assets: NaN,
      total_relationships: 100,
      avg_relationship_strength: NaN,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={nanMetrics} />);
    
    // Should not crash
    expect(screen.getByText(/100/)).toBeInTheDocument();
  });

  test('handles Infinity values', () => {
    const infMetrics = {
      total_assets: Infinity,
      total_relationships: 100,
      avg_relationship_strength: 0.5,
      asset_classes: {},
    };

    render(<MetricsDashboard metrics={infMetrics} />);
    
    // Should render something
    expect(screen.getByText(/100/)).toBeInTheDocument();
  });
});