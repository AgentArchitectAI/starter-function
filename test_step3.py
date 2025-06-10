#!/usr/bin/env python3
"""
Test Enhanced Step 3: Professional DXF Entity System
- Phase 3A: Advanced geometry (splines, polylines, ellipses, 3D solids, meshes)
- Phase 3B: Annotation system (dimensions, leaders, hatching, MTEXT)
- Phase 3C: Professional features (viewports, linetypes, attributes)
- Phase 3D: Coordinate systems & transforms
"""

import json
import sys
import os
sys.path.append('src')

from main import DXFGenerator, EntityFactory

def test_advanced_geometry():
    """Test Phase 3A: Advanced geometry entities."""
    print("🧪 Testing Phase 3A: Advanced Geometry...")
    
    generator = DXFGenerator()
    
    advanced_data = {
        "layers": [{"name": "AdvancedLayer", "color": 5}],
        "figures": [
            # Test spline
            {
                "type": "spline",
                "control_points": [[0, 0], [50, 100], [100, 50], [150, 150]],
                "degree": 3,
                "closed": False,
                "layer": "AdvancedLayer"
            },
            # Test polyline
            {
                "type": "polyline",
                "points": [[200, 0], [250, 50], [300, 0], [350, 50]],
                "closed": False,
                "layer": "AdvancedLayer"
            },
            # Test ellipse
            {
                "type": "ellipse",
                "center": [100, 200],
                "major_axis": [50, 0],
                "ratio": 0.6,
                "layer": "AdvancedLayer"
            },
            # Test 3D solid (box)
            {
                "type": "solid",
                "solid_type": "box",
                "corner1": [0, 300, 0],
                "corner2": [50, 350, 50],
                "layer": "AdvancedLayer"
            },
            # Test mesh
            {
                "type": "mesh",
                "vertices": [[0, 400, 0], [50, 400, 0], [25, 450, 25], [25, 400, 50]],
                "faces": [[0, 1, 2], [0, 2, 3], [1, 2, 3]],
                "layer": "AdvancedLayer"
            }
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(advanced_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            os.remove(dxf_path)  # Cleanup
            print(f"✅ Advanced geometry entities generated successfully ({file_size} bytes)")
            return True
        else:
            print("❌ Advanced geometry DXF file not created")
            return False
    except Exception as e:
        print(f"❌ Advanced geometry test failed: {e}")
        return False

def test_annotation_system():
    """Test Phase 3B: Annotation system."""
    print("🧪 Testing Phase 3B: Annotation System...")
    
    generator = DXFGenerator()
    
    annotation_data = {
        "layers": [{"name": "Annotations", "color": 2}],
        "figures": [
            # Test linear dimension
            {
                "type": "dimension",
                "dimension_type": "linear",
                "start": [0, 0],
                "end": [100, 0],
                "dimline_point": [50, 30],
                "layer": "Annotations"
            },
            # Test radial dimension
            {
                "type": "dimension",
                "dimension_type": "radial",
                "center": [200, 100],
                "radius_point": [250, 100],
                "layer": "Annotations"
            },
            # Test leader
            {
                "type": "leader",
                "vertices": [[50, 150], [100, 200], [150, 200]],
                "text": "Important Note",
                "text_height": 150,
                "layer": "Annotations"
            },
            # Test hatch
            {
                "type": "hatch",
                "boundary": [[300, 50], [400, 50], [400, 150], [300, 150]],
                "pattern": "ANSI31",
                "pattern_scale": 1.5,
                "pattern_angle": 45,
                "layer": "Annotations"
            },
            # Test MTEXT
            {
                "type": "mtext",
                "text": "This is multi-line text\\Pwith line breaks\\Pand formatting",
                "position": [500, 100],
                "height": 120,
                "width": 2000,
                "alignment": "CENTER",
                "layer": "Annotations"
            }
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(annotation_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            os.remove(dxf_path)  # Cleanup
            print(f"✅ Annotation system generated successfully ({file_size} bytes)")
            return True
        else:
            print("❌ Annotation system DXF file not created")
            return False
    except Exception as e:
        print(f"❌ Annotation system test failed: {e}")
        return False

def test_professional_features():
    """Test Phase 3C: Professional features."""
    print("🧪 Testing Phase 3C: Professional Features...")
    
    generator = DXFGenerator()
    
    professional_data = {
        "layers": [{"name": "Professional", "color": 4}],
        "figures": [
            # Test viewport
            {
                "type": "viewport",
                "center": [100, 100],
                "width": 200,
                "height": 150,
                "label": "VIEW A",
                "layer": "Professional"
            },
            # Test linetype definition
            {
                "type": "linetype",
                "linetype_name": "CUSTOM_DASH",
                "linetype_pattern": [12.7, -6.35, 3.175, -6.35],
                "layer": "Professional"
            },
            # Test attribute definition
            {
                "type": "attribute",
                "attribute_type": "definition",
                "tag": "PART_NUMBER",
                "position": [300, 100],
                "prompt": "Enter part number:",
                "default_value": "PN-001",
                "layer": "Professional"
            },
            # Test attribute value
            {
                "type": "attribute",
                "attribute_type": "value",
                "tag": "MATERIAL",
                "value": "Steel",
                "position": [300, 150],
                "layer": "Professional"
            }
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(professional_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            os.remove(dxf_path)  # Cleanup
            print(f"✅ Professional features generated successfully ({file_size} bytes)")
            return True
        else:
            print("❌ Professional features DXF file not created")
            return False
    except Exception as e:
        print(f"❌ Professional features test failed: {e}")
        return False

def test_coordinate_systems():
    """Test Phase 3D: Coordinate systems & transforms."""
    print("🧪 Testing Phase 3D: Coordinate Systems & Transforms...")
    
    generator = DXFGenerator()
    
    coordinate_data = {
        "layers": [{"name": "Coordinates", "color": 6}],
        "figures": [
            # Test translation
            {
                "type": "coordinate_system",
                "transform_type": "translate",
                "base_point": [0, 0],
                "offset": [100, 50],
                "layer": "Coordinates"
            },
            # Test UCS definition
            {
                "type": "coordinate_system",
                "transform_type": "ucs",
                "origin": [200, 200],
                "x_axis": [1, 0],
                "y_axis": [0, 1],
                "layer": "Coordinates"
            }
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(coordinate_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            os.remove(dxf_path)  # Cleanup
            print(f"✅ Coordinate systems generated successfully ({file_size} bytes)")
            return True
        else:
            print("❌ Coordinate systems DXF file not created")
            return False
    except Exception as e:
        print(f"❌ Coordinate systems test failed: {e}")
        return False

def test_entity_factory_coverage():
    """Test entity factory coverage for all new types."""
    print("🧪 Testing Entity Factory Coverage...")
    
    expected_types = [
        # Step 2 basic types
        "rectangle", "circle", "line", "text", "arc",
        # Phase 3A
        "spline", "polyline", "ellipse", "solid", "mesh",
        # Phase 3B
        "dimension", "leader", "hatch", "mtext",
        # Phase 3C
        "viewport", "linetype", "layer_state", "attribute",
        # Phase 3D
        "coordinate_system"
    ]
    
    supported_types = EntityFactory.get_supported_types()
    
    missing_types = []
    for entity_type in expected_types:
        if entity_type not in supported_types:
            missing_types.append(entity_type)
    
    if missing_types:
        print(f"❌ Missing entity types: {missing_types}")
        return False
    
    print(f"✅ All {len(expected_types)} entity types supported in factory")
    print(f"📊 Entity coverage: {supported_types}")
    return True

def test_comprehensive_drawing():
    """Test comprehensive drawing with all entity types."""
    print("🧪 Testing Comprehensive Professional Drawing...")
    
    generator = DXFGenerator()
    
    comprehensive_data = {
        "layers": [
            {"name": "Geometry", "color": 7},
            {"name": "Dimensions", "color": 2},
            {"name": "Text", "color": 3},
            {"name": "Professional", "color": 4}
        ],
        "blocks": [
            {
                "name": "TitleBlock",
                "entities": [
                    {"type": "rectangle", "points": [[0, 0], [200, 0], [200, 50], [0, 50]]},
                    {"type": "text", "text": "Professional Drawing", "position": [100, 25], "height": 120}
                ]
            }
        ],
        "figures": [
            # Basic geometry
            {"type": "rectangle", "points": [[0, 0], [100, 0], [100, 100], [0, 100]], "layer": "Geometry"},
            {"type": "circle", "center": [200, 50], "radius": 30, "layer": "Geometry"},
            
            # Advanced geometry
            {"type": "spline", "control_points": [[300, 0], [350, 50], [400, 0]], "layer": "Geometry"},
            {"type": "ellipse", "center": [500, 50], "major_axis": [40, 0], "ratio": 0.7, "layer": "Geometry"},
            
            # Annotations
            {"type": "dimension", "dimension_type": "linear", "start": [0, 0], "end": [100, 0], "dimline_point": [50, -30], "layer": "Dimensions"},
            {"type": "leader", "vertices": [[200, 80], [250, 120]], "text": "Ø60", "layer": "Dimensions"},
            {"type": "hatch", "boundary": [[50, 50], [75, 50], [75, 75], [50, 75]], "pattern": "SOLID", "layer": "Geometry"},
            
            # Professional features
            {"type": "viewport", "center": [600, 300], "width": 200, "height": 150, "label": "SECTION A-A", "layer": "Professional"},
            {"type": "attribute", "attribute_type": "value", "tag": "DRAWING_NO", "value": "DWG-001", "position": [50, 400], "layer": "Text"},
            
            # Coordinate system
            {"type": "coordinate_system", "transform_type": "ucs", "origin": [0, 0], "x_axis": [1, 0], "y_axis": [0, 1], "layer": "Professional"}
        ]
    }
    
    try:
        dxf_path = generator.generate_from_instructions(comprehensive_data)
        if os.path.exists(dxf_path):
            file_size = os.path.getsize(dxf_path)
            os.remove(dxf_path)  # Cleanup
            print(f"✅ Comprehensive professional drawing generated successfully ({file_size} bytes)")
            print(f"📐 Drawing includes {len(comprehensive_data['figures'])} entities across {len(comprehensive_data['layers'])} layers")
            return True
        else:
            print("❌ Comprehensive drawing DXF file not created")
            return False
    except Exception as e:
        print(f"❌ Comprehensive drawing test failed: {e}")
        return False

def main():
    """Run all Enhanced Step 3 tests."""
    print("🚀 Running Enhanced Step 3 Professional DXF System Tests...\n")
    
    tests = [
        test_entity_factory_coverage,
        test_advanced_geometry,
        test_annotation_system,
        test_professional_features,
        test_coordinate_systems,
        test_comprehensive_drawing
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Enhanced Step 3: Professional DXF Entity System working perfectly!")
        print("🏆 This tool can now generate professional-grade DXF files!")
        return True
    else:
        print("⚠️  Some tests failed - needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)