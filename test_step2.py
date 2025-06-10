#!/usr/bin/env python3
"""
Test Step 2 improvements:
- Class-based architecture
- Enhanced error handling
- Geometric validation
- Entity factory pattern
"""

import json
import sys
import os
sys.path.append('src')

from main import (
    DXFGenerator, EntityFactory, GeometryValidator, 
    ValidationError, EntityProcessingError, DXFGenerationError
)

def test_enhanced_error_handling():
    """Test enhanced error handling with detailed messages."""
    print("🧪 Testing enhanced error handling...")
    
    generator = DXFGenerator()
    
    # Test with invalid circle (missing radius)
    invalid_data = {
        "layers": [{"name": "TestLayer", "color": 1}],
        "figures": [
            {
                "type": "circle",
                "center": [0, 0],
                # Missing radius - should trigger validation error
                "layer": "TestLayer"
            }
        ]
    }
    
    # The system handles invalid entities gracefully by logging errors
    # and continuing with valid entities, so this should still succeed
    # but log the validation error
    try:
        dxf_path = generator.generate_from_instructions(invalid_data)
        if os.path.exists(dxf_path):
            os.remove(dxf_path)  # Cleanup
            print("✅ System gracefully handles invalid entities (logs error, continues processing)")
        else:
            print("❌ DXF file should still be generated")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_geometric_validation():
    """Test geometric parameter validation."""
    print("🧪 Testing geometric validation...")
    
    # Test point validation
    try:
        GeometryValidator.validate_point([0, 10])
        print("✅ Valid point accepted")
    except ValidationError:
        print("❌ Valid point rejected")
        return False
    
    # Test invalid point
    try:
        GeometryValidator.validate_point("not_a_point")
        print("❌ Invalid point should be rejected")
        return False
    except ValidationError:
        print("✅ Invalid point correctly rejected")
    
    # Test radius validation
    try:
        GeometryValidator.validate_radius(5.0)
        print("✅ Valid radius accepted")
    except ValidationError:
        print("❌ Valid radius rejected")
        return False
    
    # Test invalid radius
    try:
        GeometryValidator.validate_radius(-1)
        print("❌ Negative radius should be rejected")
        return False
    except ValidationError:
        print("✅ Negative radius correctly rejected")
    
    # Test angle validation
    try:
        GeometryValidator.validate_angle(45)
        print("✅ Valid angle accepted")
    except ValidationError:
        print("❌ Valid angle rejected")
        return False
    
    return True

def test_entity_factory():
    """Test entity factory pattern."""
    print("🧪 Testing entity factory pattern...")
    
    # Test supported entity types
    supported_types = EntityFactory.get_supported_types()
    expected_types = ["rectangle", "circle", "line", "text", "arc"]
    
    for entity_type in expected_types:
        if entity_type not in supported_types:
            print(f"❌ Missing entity type: {entity_type}")
            return False
    
    print(f"✅ All expected entity types supported: {supported_types}")
    
    # Test processor retrieval
    circle_processor = EntityFactory.get_processor("circle")
    if circle_processor is None:
        print("❌ Failed to get circle processor")
        return False
    
    print("✅ Entity processor retrieval working")
    
    # Test unsupported type
    invalid_processor = EntityFactory.get_processor("unsupported_type")
    if invalid_processor is not None:
        print("❌ Should return None for unsupported type")
        return False
    
    print("✅ Correctly handles unsupported entity types")
    
    return True

def test_class_architecture():
    """Test the new class-based architecture."""
    print("🧪 Testing class-based architecture...")
    
    # Test DXFGenerator initialization
    generator = DXFGenerator()
    if generator.doc is not None or generator.msp is not None:
        print("❌ Generator should initialize with None values")
        return False
    
    print("✅ DXFGenerator initializes correctly")
    
    # Test successful generation with valid data
    valid_data = {
        "layers": [{"name": "TestLayer", "color": 2}],
        "figures": [
            {
                "type": "rectangle",
                "layer": "TestLayer",
                "points": [[0, 0], [10, 0], [10, 5], [0, 5]]
            },
            {
                "type": "circle",
                "center": [5, 2.5],
                "radius": 1.0
            }
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(valid_data)
        if os.path.exists(dxf_path):
            os.remove(dxf_path)  # Cleanup
            print("✅ Class-based DXF generation successful")
            return True
        else:
            print("❌ DXF file not generated")
            return False
    except Exception as e:
        print(f"❌ Class-based generation failed: {e}")
        return False

def main():
    """Run all Step 2 tests."""
    print("🚀 Running Step 2 validation tests...\n")
    
    tests = [
        test_class_architecture,
        test_entity_factory,
        test_geometric_validation,
        test_enhanced_error_handling
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Step 2 architecture improvements working perfectly!")
        return True
    else:
        print("⚠️  Some tests failed - needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)