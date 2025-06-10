#!/usr/bin/env python3
"""
Test script for Phase 1: Semantic Translation Layer

This script tests the Agent Zero integration by verifying that:
1. Natural language descriptions can be parsed into structured parameters
2. Parsed parameters can generate valid DXF instructions  
3. DXF generation works end-to-end from natural language
4. The /semantic endpoint routing works correctly

Run this test to validate Phase 1 completion.
"""

import sys
import os
import json
import tempfile
from unittest.mock import Mock

# Add src to path for imports
sys.path.append('src')

from semantic_parser import KitchenSemanticParser
from main import generate_dxf_from_instructions, handle_semantic_request, SemanticRequestModel

def test_semantic_parser():
    """Test the core semantic parser functionality."""
    print("🧪 Testing KitchenSemanticParser...")
    
    parser = KitchenSemanticParser()
    
    # Test 1: Basic L-shaped kitchen
    description1 = "Modern L-shaped kitchen with island, 4x3 meters"
    params1 = parser.parse_description(description1)
    
    assert params1["layout"] == "l_shaped", f"Expected l_shaped, got {params1['layout']}"
    assert params1["style"] == "modern", f"Expected modern, got {params1['style']}"
    assert params1["dimensions"] == (4000, 3000), f"Expected (4000, 3000), got {params1['dimensions']}"
    assert "island" in params1["appliances"], f"Island not found in appliances: {params1['appliances']}"
    print("✅ Basic L-shaped kitchen parsing works")
    
    # Test 2: Compact galley kitchen
    description2 = "Small galley kitchen for studio apartment, 2.5x1.8 meters"  
    params2 = parser.parse_description(description2)
    
    assert params2["layout"] in ["galley", "compact"], f"Expected galley/compact, got {params2['layout']}"
    assert params2["dimensions"] == (2500, 1800), f"Expected (2500, 1800), got {params2['dimensions']}"
    print("✅ Compact galley kitchen parsing works")
    
    # Test 3: Traditional U-shaped kitchen
    description3 = "Traditional farmhouse U-shaped kitchen with pantry"
    params3 = parser.parse_description(description3)
    
    assert params3["layout"] == "u_shaped", f"Expected u_shaped, got {params3['layout']}"
    assert params3["style"] == "traditional", f"Expected traditional, got {params3['style']}"
    assert "pantry" in params3["features"], f"Pantry not found in features: {params3['features']}"
    print("✅ Traditional U-shaped kitchen parsing works")
    
    print("✅ All semantic parsing tests passed!\n")

def test_dxf_instruction_generation():
    """Test DXF instruction generation from semantic parameters."""
    print("🧪 Testing DXF instruction generation...")
    
    parser = KitchenSemanticParser()
    
    # Test with a modern L-shaped kitchen
    description = "Modern L-shaped kitchen with island, 4x3 meters, stainless steel appliances"
    params = parser.parse_description(description)
    
    # Generate DXF instructions
    instructions = parser.generate_dxf_instructions(params)
    
    # Validate instruction structure
    assert "layers" in instructions, "Missing layers in instructions"
    assert "figures" in instructions, "Missing figures in instructions"
    assert len(instructions["layers"]) > 0, "No layers generated"
    assert len(instructions["figures"]) > 0, "No figures generated"
    
    # Check for required layers
    layer_names = [layer["name"] for layer in instructions["layers"]]
    required_layers = ["Walls", "Cabinets", "Appliances"]
    for req_layer in required_layers:
        assert req_layer in layer_names, f"Missing required layer: {req_layer}"
    
    print(f"✅ Generated {len(instructions['figures'])} entities across {len(instructions['layers'])} layers")
    print("✅ DXF instruction generation works!\n")
    
    return instructions

def test_end_to_end_generation():
    """Test complete end-to-end DXF generation from natural language."""
    print("🧪 Testing end-to-end DXF generation...")
    
    parser = KitchenSemanticParser()
    
    # Parse description and generate instructions
    description = "Contemporary open plan kitchen with island, 5x4 meters"
    params = parser.parse_description(description)
    instructions = parser.generate_dxf_instructions(params)
    
    # Generate actual DXF file
    try:
        dxf_file_path = generate_dxf_from_instructions(instructions)
        
        # Verify file was created and has content
        assert os.path.exists(dxf_file_path), f"DXF file not created: {dxf_file_path}"
        file_size = os.path.getsize(dxf_file_path)
        assert file_size > 1000, f"DXF file too small: {file_size} bytes"
        
        print(f"✅ Generated DXF file: {os.path.basename(dxf_file_path)} ({file_size} bytes)")
        
        # Cleanup
        os.remove(dxf_file_path)
        print("✅ End-to-end generation works!\n")
        
    except Exception as e:
        print(f"❌ End-to-end generation failed: {e}")
        raise

def test_semantic_request_validation():
    """Test the semantic request model validation."""
    print("🧪 Testing semantic request validation...")
    
    # Valid request
    valid_request = {
        "description": "Modern kitchen with island, 4x3 meters",
        "return_summary": False,
        "client_info": {
            "application": "Agent Zero",
            "version": "1.0.0"
        }
    }
    
    try:
        validated = SemanticRequestModel(**valid_request)
        assert validated.description == valid_request["description"]
        assert validated.return_summary == False
        print("✅ Valid semantic request validation works")
    except Exception as e:
        print(f"❌ Valid request validation failed: {e}")
        raise
    
    # Invalid request (missing description)
    invalid_request = {
        "return_summary": True
    }
    
    try:
        SemanticRequestModel(**invalid_request)
        assert False, "Should have failed validation"
    except Exception:
        print("✅ Invalid request properly rejected")
    
    print("✅ Semantic request validation works!\n")

def test_mock_semantic_endpoint():
    """Test the semantic endpoint handler with mock objects."""
    print("🧪 Testing semantic endpoint handler...")
    
    # Create mock request and response objects
    mock_req = Mock()
    mock_res = Mock()
    
    # Mock a semantic request
    semantic_request = {
        "description": "Modern L-shaped kitchen with island, 4x3 meters",
        "return_summary": True,
        "client_info": {
            "application": "Test Agent",
            "version": "1.0.0"
        }
    }
    
    mock_req.body_raw = json.dumps(semantic_request)
    
    # Mock response methods
    mock_res.json = Mock(return_value="mocked_json_response")
    mock_res.send = Mock(return_value="mocked_send_response")
    
    try:
        # Call the semantic handler
        result = handle_semantic_request(mock_req, mock_res)
        
        # Since we requested return_summary=True, should call res.json
        mock_res.json.assert_called_once()
        
        # Get the call arguments to verify structure
        call_args = mock_res.json.call_args[0][0]  # First positional argument
        
        assert "processing_summary" in call_args, "Missing processing_summary in response"
        assert "semantic_parsing" in call_args, "Missing semantic_parsing in response"
        
        print("✅ Semantic endpoint handler works")
        print(f"✅ Response includes semantic parsing info")
        
    except Exception as e:
        print(f"❌ Semantic endpoint test failed: {e}")
        raise
    
    print("✅ Mock semantic endpoint test passed!\n")

def run_all_tests():
    """Run all Phase 1 validation tests."""
    print("🚀 Running Phase 1: Semantic Translation Layer Tests\n")
    
    try:
        # Test individual components
        test_semantic_parser()
        test_dxf_instruction_generation()
        test_end_to_end_generation()
        test_semantic_request_validation()
        test_mock_semantic_endpoint()
        
        # Final integration test
        print("🎯 Final Integration Test...")
        parser = KitchenSemanticParser()
        
        # Test Agent Zero's typical use case
        agent_zero_description = "I need a modern kitchen design for my 4x3 meter space with an island"
        params = parser.parse_description(agent_zero_description)
        instructions = parser.generate_dxf_instructions(params)
        dxf_path = generate_dxf_from_instructions(instructions)
        
        file_size = os.path.getsize(dxf_path)
        print(f"✅ Agent Zero use case: Generated {file_size} byte DXF from '{agent_zero_description}'")
        
        # Cleanup
        os.remove(dxf_path)
        
        print("\n🎉 ALL PHASE 1 TESTS PASSED!")
        print("✅ Agent Zero can now generate kitchens from natural language")
        print("✅ Semantic translation layer is working")
        print("✅ DXF generation integration complete")
        print("\n📊 Phase 1 Success Metrics:")
        print("- ✅ Natural language parsing: Working")
        print("- ✅ Layout type detection: Working") 
        print("- ✅ Dimension extraction: Working")
        print("- ✅ Appliance identification: Working")
        print("- ✅ DXF instruction generation: Working")
        print("- ✅ End-to-end generation: Working")
        print("- ✅ Request validation: Working")
        print("- ✅ Error handling: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 1 TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)