# src/template_customizer.py
"""
Template Customization Engine for Agent Zero Integration

This module provides template customization capabilities for Agent Zero.
It handles scaling templates to specified dimensions, adding appliances,
and applying style modifications to kitchen templates.

Phase 2 Day 3-4 deliverable for IMPLEMENTATION_PLAN.md
"""

import json
import logging
import copy
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateCustomizer:
    """
    Template customization engine for Agent Zero kitchen templates.
    
    Handles scaling, appliance modifications, and style changes for
    kitchen templates based on Agent Zero requirements.
    """
    
    def __init__(self):
        """Initialize the template customizer."""
        logger.info("Template customizer initialized")
    
    def apply_dimensions(self, template: Dict[str, Any], width: int, height: int) -> Dict[str, Any]:
        """
        Scale template to specified dimensions.
        
        Args:
            template: Base kitchen template dictionary
            width: Target room width in millimeters
            height: Target room height in millimeters
            
        Returns:
            Scaled template with adjusted coordinates
        """
        logger.info(f"Scaling template to dimensions: {width}x{height}mm")
        
        # Create deep copy to avoid modifying original
        scaled_template = copy.deepcopy(template)
        
        # Get original dimensions from template
        original_dims = template.get("parameters", {}).get("recommended_dimensions", [4000, 3000])
        original_width, original_height = original_dims[0], original_dims[1]
        
        # Calculate scaling factors
        width_scale = width / original_width
        height_scale = height / original_height
        
        logger.info(f"Scaling factors: width={width_scale:.2f}, height={height_scale:.2f}")
        
        # Update template dimensions
        scaled_template["parameters"]["applied_dimensions"] = [width, height]
        scaled_template["parameters"]["scaling_factors"] = [width_scale, height_scale]
        
        # Scale all scalable figures
        if "figures" in scaled_template.get("dxf_template", {}):
            for figure in scaled_template["dxf_template"]["figures"]:
                if figure.get("scale_with_dimensions", False):
                    figure = self._scale_figure_coordinates(figure, width_scale, height_scale)
        
        # Update workflow zones
        if "workflow_zones" in scaled_template:
            for zone_name, zone_data in scaled_template["workflow_zones"].items():
                if "center" in zone_data:
                    zone_data["center"] = [
                        int(zone_data["center"][0] * width_scale),
                        int(zone_data["center"][1] * height_scale)
                    ]
                if "radius" in zone_data:
                    zone_data["radius"] = int(zone_data["radius"] * min(width_scale, height_scale))
        
        return scaled_template
    
    def add_appliances(self, template: Dict[str, Any], appliances: List[str]) -> Dict[str, Any]:
        """
        Add requested appliances to template.
        
        Args:
            template: Kitchen template dictionary
            appliances: List of appliance names to add
            
        Returns:
            Template with additional appliances added
        """
        logger.info(f"Adding appliances: {appliances}")
        
        modified_template = copy.deepcopy(template)
        
        # Get current appliances in template
        current_appliances = set(modified_template.get("appliances_included", []))
        new_appliances = [app for app in appliances if app not in current_appliances]
        
        if not new_appliances:
            logger.info("No new appliances to add")
            return modified_template
        
        # Add new appliances to the list
        modified_template["appliances_included"].extend(new_appliances)
        
        # Get template dimensions for positioning
        dims = modified_template.get("parameters", {}).get("applied_dimensions", 
                                   modified_template.get("parameters", {}).get("recommended_dimensions", [4000, 3000]))
        
        # Add appliances to DXF figures
        for appliance in new_appliances:
            new_figure = self._create_appliance_figure(appliance, dims, modified_template)
            if new_figure:
                modified_template["dxf_template"]["figures"].append(new_figure)
        
        return modified_template
    
    def apply_style_modifications(self, template: Dict[str, Any], style: str) -> Dict[str, Any]:
        """
        Apply style-specific changes to template.
        
        Args:
            template: Kitchen template dictionary  
            style: Style name (modern, traditional, industrial, etc.)
            
        Returns:
            Template with style modifications applied
        """
        logger.info(f"Applying style modifications: {style}")
        
        styled_template = copy.deepcopy(template)
        
        # Update template style parameter
        styled_template["parameters"]["style"] = style
        
        # Apply style-specific modifications
        style_config = self._get_style_configuration(style)
        
        # Update colors based on style
        if "dxf_template" in styled_template and "layers" in styled_template["dxf_template"]:
            for layer in styled_template["dxf_template"]["layers"]:
                layer_name = layer["name"]
                if layer_name in style_config.get("layer_colors", {}):
                    layer["color"] = style_config["layer_colors"][layer_name]
        
        # Update customization options if available
        if "customization_options" in styled_template:
            for option_name, style_values in style_config.get("customization_defaults", {}).items():
                if option_name in styled_template["customization_options"]:
                    styled_template["customization_options"][f"{option_name}_recommended"] = style_values
        
        return styled_template
    
    def combine_customizations(self, template: Dict[str, Any], 
                             dimensions: Optional[List[int]] = None,
                             appliances: Optional[List[str]] = None,
                             style: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply multiple customizations in optimal order.
        
        Args:
            template: Base kitchen template
            dimensions: [width, height] in millimeters
            appliances: List of appliances to add
            style: Style name to apply
            
        Returns:
            Fully customized template
        """
        logger.info("Applying combined customizations")
        
        customized = copy.deepcopy(template)
        
        # Apply customizations in optimal order
        # 1. Style first (affects colors and defaults)
        if style:
            customized = self.apply_style_modifications(customized, style)
        
        # 2. Dimensions (scales coordinates)
        if dimensions and len(dimensions) >= 2:
            customized = self.apply_dimensions(customized, dimensions[0], dimensions[1])
        
        # 3. Appliances last (uses final dimensions for positioning)
        if appliances:
            customized = self.add_appliances(customized, appliances)
        
        # Add customization metadata
        customized["customization_applied"] = {
            "dimensions": dimensions,
            "appliances_added": appliances,
            "style": style,
            "timestamp": self._get_timestamp()
        }
        
        return customized
    
    def _scale_figure_coordinates(self, figure: Dict[str, Any], 
                                width_scale: float, height_scale: float) -> Dict[str, Any]:
        """Scale individual figure coordinates."""
        if "coordinates" in figure:
            coords = figure["coordinates"]
            
            if figure["type"] == "rectangle" and isinstance(coords, list) and len(coords) == 2:
                # Rectangle: [[x1, y1], [x2, y2]]
                figure["coordinates"] = [
                    [int(coords[0][0] * width_scale), int(coords[0][1] * height_scale)],
                    [int(coords[1][0] * width_scale), int(coords[1][1] * height_scale)]
                ]
            elif figure["type"] == "circle" and isinstance(coords, list) and len(coords) == 2:
                # Circle: [x, y] + radius
                figure["coordinates"] = [
                    int(coords[0] * width_scale),
                    int(coords[1] * height_scale)
                ]
                if "radius" in figure:
                    figure["radius"] = int(figure["radius"] * min(width_scale, height_scale))
            elif figure["type"] == "text" and isinstance(coords, list) and len(coords) == 2:
                # Text: [x, y]
                figure["coordinates"] = [
                    int(coords[0] * width_scale),
                    int(coords[1] * height_scale)
                ]
                if "height" in figure:
                    figure["height"] = int(figure["height"] * min(width_scale, height_scale))
        
        return figure
    
    def _create_appliance_figure(self, appliance: str, dimensions: List[int], 
                               template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create DXF figure for new appliance."""
        appliance_configs = {
            "microwave": {
                "type": "rectangle",
                "layer": "Appliances", 
                "size": [600, 400],
                "position_factor": [0.7, 0.2]  # Relative position in room
            },
            "oven": {
                "type": "rectangle",
                "layer": "Appliances",
                "size": [600, 600], 
                "position_factor": [0.3, 0.2]
            },
            "pantry": {
                "type": "rectangle",
                "layer": "Cabinets",
                "size": [800, 600],
                "position_factor": [0.9, 0.8]
            },
            "wine_cooler": {
                "type": "rectangle", 
                "layer": "Appliances",
                "size": [400, 600],
                "position_factor": [0.1, 0.8]
            }
        }
        
        if appliance not in appliance_configs:
            logger.warning(f"Unknown appliance type: {appliance}")
            return None
        
        config = appliance_configs[appliance]
        width, height = dimensions[0], dimensions[1]
        
        # Calculate position
        x = int(width * config["position_factor"][0] - config["size"][0] / 2)
        y = int(height * config["position_factor"][1] - config["size"][1] / 2)
        
        return {
            "type": config["type"],
            "layer": config["layer"],
            "coordinates": [[x, y], [x + config["size"][0], y + config["size"][1]]],
            "description": appliance.replace("_", " ").title(),
            "appliance_type": appliance,
            "customizable": True,
            "added_by_customizer": True
        }
    
    def _get_style_configuration(self, style: str) -> Dict[str, Any]:
        """Get style-specific configuration."""
        style_configs = {
            "modern": {
                "layer_colors": {
                    "Cabinets": 3,  # Green
                    "Appliances": 5,  # Blue
                    "Island": 6,  # Magenta
                    "Text": 1  # Red
                },
                "customization_defaults": {
                    "cabinet_style": ["flat_panel"],
                    "color_scheme": ["white", "gray"],
                    "counter_material": ["quartz", "granite"]
                }
            },
            "traditional": {
                "layer_colors": {
                    "Cabinets": 30,  # Brown
                    "Appliances": 5,  # Blue
                    "Island": 32,  # Dark brown
                    "Text": 1  # Red
                },
                "customization_defaults": {
                    "cabinet_style": ["shaker", "raised_panel"],
                    "color_scheme": ["wood_tone", "cream"],
                    "counter_material": ["granite", "marble"]
                }
            },
            "industrial": {
                "layer_colors": {
                    "Cabinets": 8,  # Dark gray
                    "Appliances": 251,  # Light gray
                    "Island": 9,  # Gray
                    "Text": 7  # White
                },
                "customization_defaults": {
                    "cabinet_style": ["flat_panel"],
                    "color_scheme": ["gray", "black"], 
                    "counter_material": ["stainless_steel", "concrete"]
                }
            }
        }
        
        return style_configs.get(style, style_configs["modern"])
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat() 