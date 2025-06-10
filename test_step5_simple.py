#!/usr/bin/env python3
"""
Step 5: Simple Testing & Validation
Run core tests without pytest dependency for validation
"""

import json
import os
import sys
import tempfile

sys.path.append('src')

from main import (
    DXFGenerator, EntityFactory, RequestValidator, ProcessingSummary,
    TempFileManager, GeometryValidator, CoordinateConverter
)

def test_geometry_validator():
    """Test geometric parameter validation."""
    print("🧪 Testing Geometry Validator...")
    
    try:
        # Test valid points
        assert GeometryValidator.validate_point([0, 0])
        assert GeometryValidator.validate_point([100.5, -50.25])
        
        # Test valid radius
        assert GeometryValidator.validate_radius(10)
        assert GeometryValidator.validate_radius(0.5)
        
        # Test valid angles
        assert GeometryValidator.validate_angle(0)
        assert GeometryValidator.validate_angle(45)
        assert GeometryValidator.validate_angle(-90)
        
        print("✅ Geometry validator working correctly")
        return True
    except Exception as e:
        print(f"❌ Geometry validator test failed: {e}")
        return False

def test_coordinate_converter():
    """Test coordinate conversion utilities."""
    print("🧪 Testing Coordinate Converter...")
    
    try:
        result = CoordinateConverter.safe_tuple_float([1, 2, 3])
        assert result == (1.0, 2.0, 3.0)
        
        result = CoordinateConverter.safe_tuple_float(["1.5", "2.7"])
        assert result == (1.5, 2.7)
        
        print("✅ Coordinate converter working correctly")
        return True
    except Exception as e:
        print(f"❌ Coordinate converter test failed: {e}")
        return False

def test_request_validator():
    """Test request validation middleware."""
    print("🧪 Testing Request Validator...")
    
    try:
        # Test valid request
        small_request = {
            "figures": [{"type": "circle"} for _ in range(100)]
        }
        error = RequestValidator.validate_request_size(small_request)
        assert error is None
        
        # Test oversized request
        large_request = {
            "figures": [{"type": "circle"} for _ in range(15000)]
        }
        error = RequestValidator.validate_request_size(large_request)
        assert error is not None
        assert "Too many entities" in error
        
        # Test layer validation
        valid_request = {
            "layers": [{"name": "Layer1"}],
            "figures": [{"type": "circle", "layer": "Layer1"}]
        }
        error = RequestValidator.validate_layer_references(valid_request)
        assert error is None
        
        # Test preprocessing
        minimal_request = {"figures": [{"type": "circle"}]}
        processed = RequestValidator.preprocess_request(minimal_request)
        assert "layers" in processed
        
        print("✅ Request validator working correctly")
        return True
    except Exception as e:
        print(f"❌ Request validator test failed: {e}")
        return False

def test_temp_file_manager():
    """Test temporary file management."""
    print("🧪 Testing Temp File Manager...")
    
    try:
        manager = TempFileManager()
        temp_path = manager.create_temp_file(".test")
        
        assert os.path.exists(temp_path)
        assert temp_path.endswith(".test")
        
        manager.cleanup_file(temp_path)
        assert not os.path.exists(temp_path)
        
        print("✅ Temp file manager working correctly")
        return True
    except Exception as e:
        print(f"❌ Temp file manager test failed: {e}")
        return False

def test_processing_summary():
    """Test processing summary functionality."""
    print("🧪 Testing Processing Summary...")
    
    try:
        summary = ProcessingSummary()
        assert summary.total_entities == 0
        assert summary.successful_entities == 0
        
        # Add entity results
        summary.add_entity_result("circle", "layer1", True)
        summary.add_entity_result("invalid", "layer1", False, "Test error")
        
        assert summary.total_entities == 2
        assert summary.successful_entities == 1
        assert summary.failed_entities == 1
        assert "invalid: Test error" in summary.errors
        
        # Test dictionary conversion
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            summary.finalize(tmp_path, 1000)
            summary_dict = summary.to_dict()
            
            assert "processing_summary" in summary_dict
            assert "warnings" in summary_dict
            assert "errors" in summary_dict
            
            proc_summary = summary_dict["processing_summary"]
            assert proc_summary["total_entities"] == 2
            assert proc_summary["success_rate"] == "50.0%"
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        print("✅ Processing summary working correctly")
        return True
    except Exception as e:
        print(f"❌ Processing summary test failed: {e}")
        return False

def test_entity_factory():
    """Test entity factory pattern."""
    print("🧪 Testing Entity Factory...")
    
    try:
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
        
        # Test processors
        processor = EntityFactory.get_processor("circle")
        assert processor is not None
        
        processor = EntityFactory.get_processor("nonexistent")
        assert processor is None
        
        print(f"✅ Entity factory working correctly ({len(supported)} types supported)")
        return True
    except Exception as e:
        print(f"❌ Entity factory test failed: {e}")
        return False

def test_simple_dxf_generation():
    """Test simple DXF generation."""
    print("🧪 Testing Simple DXF Generation...")
    
    try:
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
            
            file_size = os.path.getsize(dxf_path)
            assert file_size > 1000  # Should be substantial file
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
        
        print("✅ Simple DXF generation working correctly")
        return True
    except Exception as e:
        print(f"❌ Simple DXF generation test failed: {e}")
        return False

def test_complex_dxf_generation():
    """Test complex DXF generation with multiple entity types."""
    print("🧪 Testing Complex DXF Generation...")
    
    try:
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
            
            file_size = os.path.getsize(dxf_path)
            assert file_size > 5000  # Should be substantial file
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
        
        print("✅ Complex DXF generation working correctly")
        return True
    except Exception as e:
        print(f"❌ Complex DXF generation test failed: {e}")
        return False

def test_kitchen_layout_integration():
    """Test kitchen layout integration."""
    print("🧪 Testing Kitchen Layout Integration...")
    
    try:
        generator = DXFGenerator()
        
        # Kitchen layout from examples document
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
                
                # Appliances
                {"type": "rectangle", "points": [[1500, 100], [1600, 100], [1600, 700], [1500, 700]], "layer": "Appliances"},
                {"type": "rectangle", "points": [[700, 700], [1300, 700], [1300, 1300], [700, 1300]], "layer": "Appliances"},
                
                # Island
                {"type": "rectangle", "points": [[1800, 1500], [3200, 1500], [3200, 2200], [1800, 2200]], "layer": "Cabinets"},
                
                # Dimensions
                {"type": "dimension", "dimension_type": "linear", "start": [0, 0], "end": [4000, 0], "dimline_point": [2000, -200], "layer": "Dimensions"},
                
                # Labels
                {"type": "text", "text": "KITCHEN LAYOUT", "position": [2000, 2800], "height": 200, "layer": "Text"},
                {"type": "text", "text": "ISLAND", "position": [2500, 1850], "height": 100, "layer": "Text"},
                
                # Hatching
                {"type": "hatch", "boundary": [[1800, 1500], [3200, 1500], [3200, 2200], [1800, 2200]], "pattern": "ANSI31", "layer": "Cabinets"}
            ]
        }
        
        dxf_path, summary = generator.generate_from_instructions(kitchen_data)
        
        try:
            assert os.path.exists(dxf_path)
            file_size = os.path.getsize(dxf_path)
            assert file_size > 10000  # Should be substantial file
            
            # Verify comprehensive processing
            assert summary.total_entities == len(kitchen_data["figures"])
            assert summary.successful_entities >= 8  # Most entities should succeed
            
            # Verify entity type diversity
            assert len(summary.entities_by_type) >= 4  # Multiple entity types
            assert len(summary.entities_by_layer) == 5  # All layers used
            
        finally:
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
        
        print("✅ Kitchen layout integration working correctly")
        return True
    except Exception as e:
        print(f"❌ Kitchen layout integration test failed: {e}")
        return False

def main():
    """Run all Step 5 tests."""
    print("🚀 Running Step 5: Testing & Documentation Validation...\n")
    
    tests = [
        test_geometry_validator,
        test_coordinate_converter,
        test_request_validator,
        test_temp_file_manager,
        test_processing_summary,
        test_entity_factory,
        test_simple_dxf_generation,
        test_complex_dxf_generation,
        test_kitchen_layout_integration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Step 5: Testing & Documentation completed successfully!")
        print("🏆 All core functionality validated!")
        print("📚 Documentation and examples ready for production!")
        return True
    else:
        print("⚠️  Some tests failed - needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)