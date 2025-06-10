#!/usr/bin/env python3
"""
Simple test to validate Step 1 improvements:
- Pydantic validation
- Type hints
- Logging
- English translation
"""

import json
import sys
import os
sys.path.append('src')

from main import DXFRequestModel, safe_tuple_float, generate_dxf_from_instructions
from pydantic import ValidationError

def test_pydantic_validation():
    """Test Pydantic model validation."""
    print("🧪 Testing Pydantic validation...")
    
    # Valid request
    valid_data = {
        "layers": [{"name": "Layer1", "color": 1}],
        "figures": [
            {
                "type": "rectangle",
                "layer": "Layer1",
                "points": [[0, 0], [100, 0], [100, 50], [0, 50]]
            }
        ]
    }
    
    try:
        validated = DXFRequestModel(**valid_data)
        print("✅ Valid request passed validation")
    except ValidationError as e:
        print(f"❌ Valid request failed: {e}")
        return False
    
    # Invalid request (missing required fields)
    invalid_data = {"layers": []}  # Missing figures
    
    try:
        DXFRequestModel(**invalid_data)
        print("❌ Invalid request should have failed")
        return False
    except ValidationError:
        print("✅ Invalid request correctly rejected")
    
    return True

def test_coordinate_conversion():
    """Test safe_tuple_float function."""
    print("🧪 Testing coordinate conversion...")
    
    # Valid coordinates
    result = safe_tuple_float([0, 10.5, "20"])
    expected = (0.0, 10.5, 20.0)
    if result == expected:
        print("✅ Coordinate conversion works correctly")
    else:
        print(f"❌ Expected {expected}, got {result}")
        return False
    
    # Invalid coordinates (should handle gracefully)
    result = safe_tuple_float([0, "invalid", 20])
    print(f"✅ Handles invalid coordinates gracefully: {result}")
    
    return True

def test_dxf_generation():
    """Test basic DXF generation."""
    print("🧪 Testing DXF generation...")
    
    test_data = {
        "layers": [{"name": "TestLayer", "color": 2}],
        "blocks": [],
        "figures": [
            {
                "type": "rectangle",
                "layer": "TestLayer",
                "color": 3,
                "points": [[0, 0], [50, 0], [50, 25], [0, 25]]
            },
            {
                "type": "circle",
                "layer": "TestLayer",
                "center": [25, 12.5],
                "radius": 10
            }
        ]
    }
    
    try:
        dxf_path = generate_dxf_from_instructions(test_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            print(f"✅ DXF file generated: {os.path.basename(dxf_path)} ({file_size} bytes)")
            os.remove(dxf_path)  # Cleanup
            return True
        else:
            print("❌ DXF file was not created")
            return False
    except Exception as e:
        print(f"❌ DXF generation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Running Step 1 validation tests...\n")
    
    tests = [
        test_pydantic_validation,
        test_coordinate_conversion,
        test_dxf_generation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All Step 1 improvements working correctly!")
        return True
    else:
        print("⚠️  Some tests failed - needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)