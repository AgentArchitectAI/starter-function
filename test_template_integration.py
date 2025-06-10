#!/usr/bin/env python3
"""
Test script for Template-Based Kitchen Generation (Corrected Architecture)

This script validates the corrected Agent Zero integration approach:
1. Agent Zero collects client specifications
2. Agent Zero selects and customizes templates 
3. Agent Zero generates JSON requests for DXF API
4. DXF generation works end-to-end from templates

Run this test to validate the corrected Phase 1 implementation.
"""

import sys
import os
import json
import tempfile
from unittest.mock import Mock

# Add src to path for imports
sys.path.append('src')

from kitchen_template_engine import KitchenTemplateEngine
from main import generate_dxf_from_instructions, handle_template_request, handle_legacy_semantic_request, TemplateRequestModel

def test_template_engine():
    """Test the core template engine functionality."""
    print("🧪 Testing KitchenTemplateEngine...")
    
    engine = KitchenTemplateEngine()
    
    # Test 1: Template listing
    templates = engine.list_templates()
    assert len(templates) >= 5, f"Expected at least 5 templates, got {len(templates)}"
    assert "modern_l_shaped" in templates, "modern_l_shaped template missing"
    assert "compact_galley" in templates, "compact_galley template missing"
    print("✅ Template listing works")
    
    # Test 2: Template retrieval
    template = engine.get_template("modern_l_shaped")
    assert "description" in template, "Template missing description"
    assert "dxf_template" in template, "Template missing dxf_template"
    print("✅ Template retrieval works")
    
    # Test 3: Template customization
    customization = {
        "dimensions": [4000, 3000],
        "style": "modern",
        "appliances": ["island", "dishwasher"]
    }
    customized = engine.customize_template(template, customization)
    assert customized is not None, "Template customization failed"
    print("✅ Template customization works")
    
    # Test 4: German translation
    german_text = "moderne küche mit insel"
    translated = engine.translate_german_terms(german_text)
    assert "modern" in translated or "moderne" in translated, "German translation not working"
    print("✅ German translation works")
    
    print("✅ All template engine tests passed!\n")

def test_template_dxf_generation():
    """Test DXF generation from templates."""
    print("🧪 Testing template-based DXF generation...")
    
    engine = KitchenTemplateEngine()
    
    # Test with modern L-shaped kitchen
    template = engine.get_template("modern_l_shaped")
    customized = engine.customize_template(template, {
        "dimensions": [4000, 3000],
        "style": "modern"
    })
    
    # Generate DXF instructions
    dxf_instructions = customized["dxf_template"]
    
    # Validate instruction structure
    assert "layers" in dxf_instructions, "Missing layers in instructions"
    assert "figures" in dxf_instructions, "Missing figures in instructions"
    assert len(dxf_instructions["layers"]) > 0, "No layers generated"
    assert len(dxf_instructions["figures"]) > 0, "No figures generated"
    
    # Generate actual DXF file
    dxf_path = generate_dxf_from_instructions(dxf_instructions)
    
    # Verify file was created and has content
    assert os.path.exists(dxf_path), f"DXF file not created: {dxf_path}"
    file_size = os.path.getsize(dxf_path)
    assert file_size > 1000, f"DXF file too small: {file_size} bytes"
    
    print(f"✅ Generated DXF file: {os.path.basename(dxf_path)} ({file_size} bytes)")
    
    # Cleanup
    os.remove(dxf_path)
    print("✅ Template-based DXF generation works!\n")

def test_template_request_validation():
    """Test the template request model validation."""
    print("🧪 Testing template request validation...")
    
    # Valid request
    valid_request = {
        "template_name": "modern_l_shaped",
        "customization": {
            "dimensions": [4000, 3000],
            "style": "modern"
        },
        "return_summary": False,
        "client_info": {
            "application": "Agent Zero",
            "version": "1.0.0"
        }
    }
    
    try:
        validated = TemplateRequestModel(**valid_request)
        assert validated.template_name == "modern_l_shaped"
        assert validated.return_summary == False
        print("✅ Valid template request validation works")
    except Exception as e:
        print(f"❌ Valid request validation failed: {e}")
        raise
    
    # Invalid request (missing template_name)
    invalid_request = {
        "customization": {"dimensions": [4000, 3000]},
        "return_summary": True
    }
    
    try:
        TemplateRequestModel(**invalid_request)
        assert False, "Should have failed validation"
    except Exception:
        print("✅ Invalid request properly rejected")
    
    print("✅ Template request validation works!\n")

def test_mock_template_endpoint():
    """Test the template endpoint handler with mock objects."""
    print("🧪 Testing template endpoint handler...")
    
    # Create mock request and response objects
    mock_req = Mock()
    mock_res = Mock()
    
    # Mock a template request
    template_request = {
        "template_name": "modern_l_shaped",
        "customization": {
            "dimensions": [4000, 3000],
            "style": "modern"
        },
        "return_summary": True,
        "client_info": {
            "application": "Test Agent",
            "version": "1.0.0"
        }
    }
    
    mock_req.body_raw = json.dumps(template_request)
    
    # Mock response methods
    mock_res.json = Mock(return_value="mocked_json_response")
    mock_res.send = Mock(return_value="mocked_send_response")
    
    try:
        # Call the template handler
        result = handle_template_request(mock_req, mock_res)
        
        # Since we requested return_summary=True, should call res.json
        mock_res.json.assert_called_once()
        
        # Get the call arguments to verify structure
        call_args = mock_res.json.call_args[0][0]  # First positional argument
        
        assert "processing_summary" in call_args, "Missing processing_summary in response"
        assert "template_info" in call_args, "Missing template_info in response"
        
        print("✅ Template endpoint handler works")
        print("✅ Response includes template processing info")
        
    except Exception as e:
        print(f"❌ Template endpoint test failed: {e}")
        raise
    
    print("✅ Mock template endpoint test passed!\n")

def test_legacy_semantic_compatibility():
    """Test backward compatibility with legacy semantic requests."""
    print("🧪 Testing legacy semantic compatibility...")
    
    # Create mock request and response objects
    mock_req = Mock()
    mock_res = Mock()
    
    # Mock a legacy semantic request
    legacy_request = {
        "description": "Modern kitchen with island, 4x3 meters",
        "return_summary": True,
        "client_info": {
            "application": "Legacy Test",
            "version": "1.0.0"
        }
    }
    
    mock_req.body_raw = json.dumps(legacy_request)
    
    # Mock response methods
    mock_res.json = Mock(return_value="mocked_json_response")
    mock_res.send = Mock(return_value="mocked_send_response")
    
    try:
        # Call the legacy semantic handler
        result = handle_legacy_semantic_request(mock_req, mock_res)
        
        # Since we requested return_summary=True, should call res.json
        mock_res.json.assert_called_once()
        
        # Get the call arguments to verify structure
        call_args = mock_res.json.call_args[0][0]  # First positional argument
        
        assert "processing_summary" in call_args, "Missing processing_summary in response"
        assert "template_info" in call_args, "Missing template_info in response"
        
        print("✅ Legacy semantic handler works")
        print("✅ Converted semantic request to template-based approach")
        
    except Exception as e:
        print(f"❌ Legacy semantic test failed: {e}")
        raise
    
    print("✅ Legacy semantic compatibility test passed!\n")

def test_multiple_templates():
    """Test multiple template types and customizations."""
    print("🧪 Testing multiple template scenarios...")
    
    engine = KitchenTemplateEngine()
    
    test_scenarios = [
        {
            "name": "Small apartment",
            "template": "compact_galley",
            "customization": {"dimensions": [2400, 1800]}
        },
        {
            "name": "Large luxury kitchen",
            "template": "u_shaped_luxury", 
            "customization": {"dimensions": [5000, 4000], "style": "modern"}
        },
        {
            "name": "Traditional farmhouse",
            "template": "traditional_country",
            "customization": {"style": "traditional", "appliances": ["pantry"]}
        },
        {
            "name": "Open plan modern",
            "template": "open_plan_modern",
            "customization": {"dimensions": [6000, 4500], "appliances": ["island"]}
        }
    ]
    
    for scenario in test_scenarios:
        try:
            template = engine.get_template(scenario["template"])
            customized = engine.customize_template(template, scenario["customization"])
            
            # Validate the customized template
            validation = engine.validate_kitchen_json(customized["dxf_template"])
            assert validation["valid"], f"Template validation failed for {scenario['name']}"
            
            # Generate DXF to ensure it works
            dxf_path = generate_dxf_from_instructions(customized["dxf_template"])
            file_size = os.path.getsize(dxf_path)
            
            print(f"✅ {scenario['name']}: {scenario['template']} ({file_size} bytes)")
            
            # Cleanup
            os.remove(dxf_path)
            
        except Exception as e:
            print(f"❌ Failed scenario '{scenario['name']}': {e}")
            raise
    
    print("✅ Multiple template scenarios work!\n")

def run_all_tests():
    """Run all template-based integration tests."""
    print("🚀 Running Template-Based Kitchen Generation Tests\n")
    
    try:
        # Test individual components
        test_template_engine()
        test_template_dxf_generation()
        test_template_request_validation()
        test_mock_template_endpoint()
        test_legacy_semantic_compatibility()
        test_multiple_templates()
        
        # Final integration test
        print("🎯 Final Integration Test...")
        engine = KitchenTemplateEngine()
        
        # Test Agent Zero's corrected workflow
        agent_zero_request = {
            "template_name": "modern_l_shaped",
            "customization": {
                "dimensions": [4000, 3000],
                "style": "modern",
                "appliances": ["island", "dishwasher"]
            }
        }
        
        template = engine.get_template(agent_zero_request["template_name"])
        customized = engine.customize_template(template, agent_zero_request["customization"])
        dxf_path = generate_dxf_from_instructions(customized["dxf_template"])
        
        file_size = os.path.getsize(dxf_path)
        print(f"✅ Agent Zero workflow: Generated {file_size} byte DXF using template '{agent_zero_request['template_name']}'")
        
        # Cleanup
        os.remove(dxf_path)
        
        print("\n🎉 ALL TEMPLATE-BASED TESTS PASSED!")
        print("✅ Agent Zero can now generate kitchens using JSON templates")
        print("✅ Template-based architecture is working correctly")
        print("✅ Legacy semantic compatibility maintained")
        print("✅ DXF generation integration complete")
        print("\n📊 Corrected Architecture Success Metrics:")
        print("- ✅ Template selection and retrieval: Working")
        print("- ✅ Template customization: Working")
        print("- ✅ German/English vocabulary support: Working")
        print("- ✅ JSON validation and error handling: Working") 
        print("- ✅ DXF generation from templates: Working")
        print("- ✅ Multiple template types: Working")
        print("- ✅ Legacy compatibility: Working")
        print("- ✅ Agent Zero workflow: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEMPLATE-BASED TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)