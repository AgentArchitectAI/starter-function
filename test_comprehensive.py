#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Professional DXF Generation System
Tests all 19 entity types, error handling, validation, and API features
"""

import pytest
import json
import os
import sys
import tempfile
from unittest.mock import Mock, patch

sys.path.append('src')

from main import (
    DXFGenerator, EntityFactory, RequestValidator, ProcessingSummary,
    TempFileManager, GeometryValidator, CoordinateConverter,
    ValidationError, EntityProcessingError, DXFGenerationError
)

class TestGeometryValidator:
    """Test geometric parameter validation."""
    
    def test_valid_point_2d(self):
        """Test valid 2D point validation."""
        assert GeometryValidator.validate_point([0, 0])
        assert GeometryValidator.validate_point([100.5, -50.25])
    
    def test_valid_point_3d(self):
        """Test valid 3D point validation."""
        assert GeometryValidator.validate_point([0, 0, 0], min_coords=3)
        assert GeometryValidator.validate_point([100, 200, 300], min_coords=3)
    
    def test_invalid_point_format(self):
        """Test invalid point format validation."""
        with pytest.raises(ValidationError):
            GeometryValidator.validate_point("not a list")
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_point([])
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_point([1])  # Too few coordinates
    
    def test_invalid_point_values(self):
        """Test invalid point coordinate values."""
        with pytest.raises(ValidationError):
            GeometryValidator.validate_point([1, "invalid"])
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_point([None, 0])
    
    def test_valid_radius(self):
        """Test valid radius validation."""
        assert GeometryValidator.validate_radius(10)
        assert GeometryValidator.validate_radius(0.5)
        assert GeometryValidator.validate_radius(100.0)
    
    def test_invalid_radius(self):
        """Test invalid radius validation."""
        with pytest.raises(ValidationError):
            GeometryValidator.validate_radius(0)
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_radius(-5)
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_radius("invalid")
    
    def test_valid_angle(self):
        """Test valid angle validation."""
        assert GeometryValidator.validate_angle(0)
        assert GeometryValidator.validate_angle(45)
        assert GeometryValidator.validate_angle(-90)
        assert GeometryValidator.validate_angle(360)
    
    def test_invalid_angle(self):
        """Test invalid angle validation."""
        with pytest.raises(ValidationError):
            GeometryValidator.validate_angle(400)  # Too large
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_angle(-400)  # Too small
        
        with pytest.raises(ValidationError):
            GeometryValidator.validate_angle("invalid")


class TestCoordinateConverter:
    """Test coordinate conversion utilities."""
    
    def test_safe_tuple_float_valid(self):
        """Test valid coordinate conversion."""
        result = CoordinateConverter.safe_tuple_float([1, 2, 3])
        assert result == (1.0, 2.0, 3.0)
        
        result = CoordinateConverter.safe_tuple_float(["1.5", "2.7"])
        assert result == (1.5, 2.7)
    
    def test_safe_tuple_float_invalid(self):
        """Test invalid coordinate conversion fallback."""
        result = CoordinateConverter.safe_tuple_float([1, "invalid", 3])
        assert result == (1, "invalid", 3)  # Returns original on error


class TestRequestValidator:
    """Test request validation middleware."""
    
    def test_valid_request_size(self):
        """Test valid request size validation."""
        small_request = {
            "figures": [{"type": "circle"} for _ in range(100)]
        }
        error = RequestValidator.validate_request_size(small_request)
        assert error is None
    
    def test_oversized_request(self):
        """Test oversized request validation."""
        large_request = {
            "figures": [{"type": "circle"} for _ in range(15000)]
        }
        error = RequestValidator.validate_request_size(large_request)
        assert error is not None
        assert "Too many entities" in error
    
    def test_valid_layer_references(self):
        """Test valid layer reference validation."""
        valid_request = {
            "layers": [{"name": "Layer1"}],
            "figures": [{"type": "circle", "layer": "Layer1"}]
        }
        error = RequestValidator.validate_layer_references(valid_request)
        assert error is None
    
    def test_invalid_layer_references(self):
        """Test invalid layer reference validation."""
        invalid_request = {
            "layers": [{"name": "Layer1"}],
            "figures": [{"type": "circle", "layer": "NonExistentLayer"}]
        }
        error = RequestValidator.validate_layer_references(invalid_request)
        assert error is not None
        assert "undefined layer" in error
    
    def test_request_preprocessing(self):
        """Test request preprocessing."""
        minimal_request = {"figures": [{"type": "circle"}]}
        processed = RequestValidator.preprocess_request(minimal_request)
        
        assert "layers" in processed
        assert processed["layers"][0]["name"] == "default"
        assert "streaming_threshold" in processed


class TestTempFileManager:
    """Test temporary file management."""
    
    def test_create_temp_file(self):
        """Test temporary file creation."""
        manager = TempFileManager()
        temp_path = manager.create_temp_file(".test")
        
        assert os.path.exists(temp_path)
        assert temp_path.endswith(".test")
        
        manager.cleanup_file(temp_path)
        assert not os.path.exists(temp_path)
    
    def test_cleanup_all(self):
        """Test bulk cleanup."""
        manager = TempFileManager()
        temp_files = [
            manager.create_temp_file(f".test{i}") for i in range(3)
        ]
        
        for temp_file in temp_files:
            assert os.path.exists(temp_file)
        
        manager.cleanup_all()
        
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


class TestProcessingSummary:
    """Test processing summary functionality."""
    
    def test_processing_summary_initialization(self):
        """Test summary initialization."""
        summary = ProcessingSummary()
        assert summary.total_entities == 0
        assert summary.successful_entities == 0
        assert summary.failed_entities == 0
        assert len(summary.warnings) == 0
        assert len(summary.errors) == 0
    
    def test_add_entity_result_success(self):
        """Test adding successful entity result."""
        summary = ProcessingSummary()
        summary.add_entity_result("circle", "layer1", True)
        
        assert summary.total_entities == 1
        assert summary.successful_entities == 1
        assert summary.failed_entities == 0
        assert summary.entities_by_type["circle"] == 1
        assert summary.entities_by_layer["layer1"] == 1
    
    def test_add_entity_result_failure(self):
        """Test adding failed entity result."""
        summary = ProcessingSummary()
        summary.add_entity_result("invalid", "layer1", False, "Test error")
        
        assert summary.total_entities == 1
        assert summary.successful_entities == 0
        assert summary.failed_entities == 1
        assert "invalid: Test error" in summary.errors
    
    def test_summary_to_dict(self):
        """Test summary dictionary conversion."""
        summary = ProcessingSummary()
        summary.add_entity_result("circle", "layer1", True)
        summary.add_entity_result("line", "layer1", False, "Error")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            summary.finalize(tmp_path, 1000)
            summary_dict = summary.to_dict()
            
            assert "processing_summary" in summary_dict
            assert "warnings" in summary_dict
            assert "errors" in summary_dict
            assert "entity_details" in summary_dict
            
            proc_summary = summary_dict["processing_summary"]
            assert proc_summary["total_entities"] == 2
            assert proc_summary["successful_entities"] == 1
            assert proc_summary["failed_entities"] == 1
            assert proc_summary["success_rate"] == "50.0%"
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestEntityFactory:
    """Test entity factory pattern."""
    
    def test_get_supported_types(self):
        """Test getting supported entity types."""
        supported = EntityFactory.get_supported_types()
        
        # Verify all 19 entity types are supported
        expected_types = [
            "rectangle", "circle", "line", "text", "arc",  # Basic (5)
            "spline", "polyline", "ellipse", "solid", "mesh",  # Advanced (5)
            "dimension", "leader", "hatch", "mtext",  # Annotations (4)
            "viewport", "linetype", "layer_state", "attribute",  # Professional (4)
            "coordinate_system"  # Coordinate systems (1)
        ]
        
        for entity_type in expected_types:
            assert entity_type in supported
        
        assert len(supported) >= 19
    
    def test_get_processor_valid(self):
        """Test getting valid processors."""
        processor = EntityFactory.get_processor("circle")
        assert processor is not None
        
        processor = EntityFactory.get_processor("rectangle")
        assert processor is not None
    
    def test_get_processor_invalid(self):
        """Test getting invalid processors."""
        processor = EntityFactory.get_processor("nonexistent")
        assert processor is None


class TestDXFGenerator:
    """Test main DXF generator functionality."""
    
    def test_simple_generation(self):
        """Test simple DXF generation."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "figures": [
                {"type": "circle", "center": [0, 0], "radius": 10, "layer": "TestLayer"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.total_entities == 1
            assert summary.successful_entities == 1
            assert summary.failed_entities == 0
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def test_complex_generation(self):
        """Test complex DXF generation with multiple entity types."""
        generator = DXFGenerator()
        data = {
            "layers": [
                {"name": "Geometry", "color": 7},
                {"name": "Dimensions", "color": 2}
            ],
            "figures": [
                {"type": "rectangle", "points": [[0, 0], [100, 0], [100, 50], [0, 50]], "layer": "Geometry"},
                {"type": "circle", "center": [150, 25], "radius": 20, "layer": "Geometry"},
                {"type": "dimension", "dimension_type": "linear", "start": [0, 0], "end": [100, 0], "dimline_point": [50, -15], "layer": "Dimensions"},
                {"type": "text", "text": "Test Drawing", "position": [200, 25], "layer": "Geometry"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.total_entities == 4
            assert summary.successful_entities >= 3  # At least 3 should succeed
            
            # Check entity breakdown
            assert "rectangle" in summary.entities_by_type
            assert "circle" in summary.entities_by_type
            assert "Geometry" in summary.entities_by_layer
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def test_error_handling(self):
        """Test error handling in DXF generation."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "figures": [
                {"type": "invalid_type", "layer": "TestLayer"},
                {"type": "circle", "center": [0, 0], "radius": 10, "layer": "TestLayer"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.total_entities == 2
            assert summary.successful_entities == 1
            assert summary.failed_entities == 1
            assert len(summary.errors) > 0
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def test_blocks_processing(self):
        """Test block processing functionality."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "blocks": [
                {
                    "name": "TestBlock",
                    "entities": [
                        {"type": "circle", "center": [0, 0], "radius": 5},
                        {"type": "text", "text": "Block Text", "position": [10, 0]}
                    ]
                }
            ],
            "figures": [
                {"type": "circle", "center": [50, 50], "radius": 20, "layer": "TestLayer"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            # Should process figures and block entities
            assert summary.total_entities >= 1
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)


class TestAdvancedEntities:
    """Test advanced entity processing."""
    
    def test_spline_processing(self):
        """Test spline entity processing."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "figures": [
                {
                    "type": "spline",
                    "control_points": [[0, 0], [50, 100], [100, 50], [150, 150]],
                    "degree": 3,
                    "closed": False,
                    "layer": "TestLayer"
                }
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.successful_entities >= 1
            assert "spline" in summary.entities_by_type
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def test_dimension_processing(self):
        """Test dimension entity processing."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "figures": [
                {
                    "type": "dimension",
                    "dimension_type": "linear",
                    "start": [0, 0],
                    "end": [100, 0],
                    "dimline_point": [50, 30],
                    "layer": "TestLayer"
                },
                {
                    "type": "dimension",
                    "dimension_type": "radial",
                    "center": [200, 100],
                    "radius_point": [250, 100],
                    "layer": "TestLayer"
                }
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.total_entities == 2
            assert "dimension" in summary.entities_by_type
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def test_hatch_processing(self):
        """Test hatch entity processing."""
        generator = DXFGenerator()
        data = {
            "layers": [{"name": "TestLayer", "color": 7}],
            "figures": [
                {
                    "type": "hatch",
                    "boundary": [[0, 0], [100, 0], [100, 100], [0, 100]],
                    "pattern": "ANSI31",
                    "pattern_scale": 1.5,
                    "pattern_angle": 45,
                    "layer": "TestLayer"
                }
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(data)
        
        try:
            assert os.path.exists(dxf_path)
            assert summary.successful_entities >= 1
            assert "hatch" in summary.entities_by_type
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)


class TestIntegration:
    """Integration tests with real DXF files."""
    
    def test_kitchen_layout_generation(self):
        """Test kitchen layout DXF generation."""
        generator = DXFGenerator()
        
        # Kitchen layout with cabinets, appliances, and dimensions
        kitchen_data = {
            "layers": [
                {"name": "Walls", "color": 7},
                {"name": "Cabinets", "color": 3},
                {"name": "Appliances", "color": 5},
                {"name": "Dimensions", "color": 2},
                {"name": "Text", "color": 4}
            ],
            "figures": [
                # Kitchen perimeter walls
                {"type": "rectangle", "points": [[0, 0], [4000, 0], [4000, 3000], [0, 3000]], "layer": "Walls"},
                
                # Base cabinets
                {"type": "rectangle", "points": [[100, 100], [1500, 100], [1500, 700], [100, 700]], "layer": "Cabinets"},
                {"type": "rectangle", "points": [[1600, 100], [3900, 100], [3900, 700], [1600, 700]], "layer": "Cabinets"},
                {"type": "rectangle", "points": [[100, 700], [700, 700], [700, 2400], [100, 2400]], "layer": "Cabinets"},
                
                # Appliances
                {"type": "rectangle", "points": [[1500, 100], [1600, 100], [1600, 700], [1500, 700]], "layer": "Appliances"},  # Dishwasher
                {"type": "rectangle", "points": [[700, 700], [1300, 700], [1300, 1300], [700, 1300]], "layer": "Appliances"},  # Refrigerator
                
                # Island
                {"type": "rectangle", "points": [[1800, 1500], [3200, 1500], [3200, 2200], [1800, 2200]], "layer": "Cabinets"},
                
                # Dimensions
                {"type": "dimension", "dimension_type": "linear", "start": [0, 0], "end": [4000, 0], "dimline_point": [2000, -200], "layer": "Dimensions"},
                {"type": "dimension", "dimension_type": "linear", "start": [0, 0], "end": [0, 3000], "dimline_point": [-200, 1500], "layer": "Dimensions"},
                
                # Labels
                {"type": "text", "text": "KITCHEN LAYOUT", "position": [2000, 2800], "height": 200, "layer": "Text"},
                {"type": "text", "text": "ISLAND", "position": [2500, 1850], "height": 100, "layer": "Text"},
                {"type": "text", "text": "REF", "position": [1000, 1000], "height": 80, "layer": "Text"},
                
                # Hatching for island
                {"type": "hatch", "boundary": [[1800, 1500], [3200, 1500], [3200, 2200], [1800, 2200]], "pattern": "ANSI31", "layer": "Cabinets"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(kitchen_data)
        
        try:
            assert os.path.exists(dxf_path)
            file_size = os.path.getsize(dxf_path)
            assert file_size > 10000  # Should be a substantial file
            
            # Verify comprehensive processing
            assert summary.total_entities == len(kitchen_data["figures"])
            assert summary.successful_entities >= 10  # Most entities should succeed
            
            # Verify entity type diversity
            assert len(summary.entities_by_type) >= 4  # Multiple entity types
            assert len(summary.entities_by_layer) == 5  # All layers used
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)


# Pytest configuration and test runner
if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])