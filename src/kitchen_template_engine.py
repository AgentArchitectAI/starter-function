"""
Kitchen Template Engine for Agent Zero Integration

This module provides JSON templates and helper functions for Agent Zero to generate
valid kitchen DXF requests without natural language parsing. Agent Zero collects
client specifications and uses these templates to create structured JSON requests.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class KitchenTemplateEngine:
    """
    Template-based kitchen DXF generation engine for Agent Zero.
    
    Provides JSON templates, customization helpers, and validation functions
    to help Agent Zero generate valid kitchen design requests.
    
    Example usage:
        engine = KitchenTemplateEngine()
        template = engine.get_template("modern_l_shaped")
        customized = engine.customize_template(template, {"dimensions": [4000, 3000]})
        valid_json = engine.validate_kitchen_json(customized)
    """
    
    def __init__(self, vocabulary_path: str = "kitchen_vocabulary.json"):
        """Initialize with kitchen vocabulary for term translation."""
        self.vocabulary_path = vocabulary_path
        self.vocabulary = self._load_vocabulary()
        self.templates = self._load_templates()
        logger.info("Kitchen template engine initialized")
    
    def _load_vocabulary(self) -> Dict[str, Any]:
        """Load kitchen vocabulary mappings from JSON file."""
        try:
            vocab_file = Path(__file__).parent.parent / self.vocabulary_path
            if vocab_file.exists():
                with open(vocab_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Vocabulary file not found: {vocab_file}")
                return self._get_default_vocabulary()
        except Exception as e:
            logger.error(f"Error loading vocabulary: {e}")
            return self._get_default_vocabulary()
    
    def _get_default_vocabulary(self) -> Dict[str, Any]:
        """Fallback vocabulary if file not found."""
        return {
            "german_to_english": {
                "küche": "kitchen",
                "modern": "modern",
                "insel": "island",
                "spüle": "sink", 
                "herd": "stove",
                "kühlschrank": "refrigerator",
                "geschirrspüler": "dishwasher",
                "traditionell": "traditional",
                "klein": "small",
                "groß": "large",
                "meter": "meters"
            },
            "layout_types": ["l_shaped", "galley", "u_shaped", "open_plan", "compact"],
            "styles": ["modern", "traditional", "industrial", "transitional"],
            "appliances": ["island", "sink", "stove", "refrigerator", "dishwasher", "oven", "microwave"]
        }
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined kitchen templates."""
        return {
            "modern_l_shaped": self._get_modern_l_shaped_template(),
            "compact_galley": self._get_compact_galley_template(),
            "u_shaped_luxury": self._get_u_shaped_luxury_template(),
            "open_plan_modern": self._get_open_plan_template(),
            "traditional_country": self._get_traditional_template()
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        Get kitchen template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Dictionary containing the kitchen template
            
        Raises:
            ValueError: If template name is not found
        """
        if template_name not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")
        
        # Return a deep copy to prevent modification of original template
        import copy
        return copy.deepcopy(self.templates[template_name])
    
    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a specific template."""
        template = self.get_template(template_name)
        return {
            "name": template_name,
            "description": template.get("description", ""),
            "recommended_dimensions": template.get("parameters", {}).get("recommended_dimensions", []),
            "min_dimensions": template.get("parameters", {}).get("min_dimensions", []),
            "appliances_included": template.get("appliances_included", []),
            "style": template.get("style", "modern")
        }
    
    def customize_template(self, template: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize template with user parameters.
        
        Args:
            template: Base template dictionary
            params: Customization parameters
            
        Returns:
            Customized template dictionary
        """
        logger.info(f"Customizing template with params: {params}")
        
        customized = template.copy()
        
        # Apply dimensions if provided
        if "dimensions" in params:
            customized = self._apply_dimensions(customized, params["dimensions"])
        
        # Apply style modifications if provided
        if "style" in params:
            customized = self._apply_style(customized, params["style"])
        
        # Add/modify appliances if provided
        if "appliances" in params:
            customized = self._apply_appliances(customized, params["appliances"])
        
        # Apply any custom properties
        if "custom_properties" in params:
            customized = self._apply_custom_properties(customized, params["custom_properties"])
        
        return customized
    
    def validate_kitchen_json(self, kitchen_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Agent Zero generated JSON.
        
        Args:
            kitchen_json: Kitchen JSON to validate
            
        Returns:
            Dictionary with validation results and corrected JSON
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "corrected_json": kitchen_json.copy()
        }
        
        # Check required fields
        required_fields = ["layers", "figures"]
        for field in required_fields:
            if field not in kitchen_json:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Validate layers
        if "layers" in kitchen_json:
            layer_validation = self._validate_layers(kitchen_json["layers"])
            validation_result["errors"].extend(layer_validation["errors"])
            validation_result["warnings"].extend(layer_validation["warnings"])
        
        # Validate figures
        if "figures" in kitchen_json:
            figures_validation = self._validate_figures(kitchen_json["figures"])
            validation_result["errors"].extend(figures_validation["errors"])
            validation_result["warnings"].extend(figures_validation["warnings"])
        
        # Check for geometric issues
        geometry_validation = self._validate_geometry(kitchen_json)
        validation_result["warnings"].extend(geometry_validation["warnings"])
        
        return validation_result
    
    def suggest_templates(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest templates based on requirements.
        
        Args:
            requirements: Dictionary with client requirements
            
        Returns:
            List of suggested templates with scores
        """
        suggestions = []
        
        # Extract key requirements
        dimensions = requirements.get("dimensions", [])
        style = requirements.get("style", "").lower()
        appliances = requirements.get("appliances", [])
        budget = requirements.get("budget", "medium").lower()
        
        # Score each template
        for template_name, template in self.templates.items():
            score = self._score_template(template, dimensions, style, appliances, budget)
            suggestions.append({
                "template_name": template_name,
                "score": score,
                "description": template.get("description", ""),
                "reasons": self._get_suggestion_reasons(template, requirements)
            })
        
        # Sort by score (highest first)
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        
        return suggestions
    
    def translate_german_terms(self, text: str) -> str:
        """
        Translate German kitchen terms to English.
        
        Args:
            text: Text containing German terms
            
        Returns:
            Text with German terms translated to English
        """
        german_to_english = self.vocabulary.get("german_to_english", {})
        
        translated = text.lower()
        for german, english in german_to_english.items():
            translated = translated.replace(german, english)
        
        return translated
    
    def _apply_dimensions(self, template: Dict[str, Any], dimensions: List[int]) -> Dict[str, Any]:
        """Apply dimensional scaling to template."""
        if len(dimensions) < 2:
            logger.warning("Dimensions must have at least width and height")
            return template
        
        width, height = dimensions[0], dimensions[1]
        
        # Scale all figures to new dimensions
        if "dxf_template" in template and "figures" in template["dxf_template"]:
            for figure in template["dxf_template"]["figures"]:
                if figure.get("type") == "rectangle" and "points" in figure:
                    # Scale room perimeter
                    if len(figure["points"]) == 4:
                        figure["points"] = [
                            [0, 0], [width, 0], [width, height], [0, height]
                        ]
                
                # Scale other elements proportionally (simplified)
                # In a full implementation, this would be more sophisticated
        
        return template
    
    def _apply_style(self, template: Dict[str, Any], style: str) -> Dict[str, Any]:
        """Apply style modifications to template."""
        style_colors = {
            "modern": {"cabinets": 3, "appliances": 5, "accent": 1},
            "traditional": {"cabinets": 6, "appliances": 4, "accent": 2},
            "industrial": {"cabinets": 8, "appliances": 9, "accent": 7}
        }
        
        if style in style_colors and "dxf_template" in template:
            colors = style_colors[style]
            
            # Apply color scheme to layers
            if "layers" in template["dxf_template"]:
                for layer in template["dxf_template"]["layers"]:
                    if layer["name"] == "Cabinets":
                        layer["color"] = colors["cabinets"]
                    elif layer["name"] == "Appliances":
                        layer["color"] = colors["appliances"]
        
        return template
    
    def _apply_appliances(self, template: Dict[str, Any], appliances: List[str]) -> Dict[str, Any]:
        """Add or modify appliances in template."""
        # This would add appliance entities to the figures list
        # Simplified implementation for now
        if "appliances_included" not in template:
            template["appliances_included"] = []
        
        template["appliances_included"].extend(appliances)
        template["appliances_included"] = list(set(template["appliances_included"]))  # Remove duplicates
        
        return template
    
    def _apply_custom_properties(self, template: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom properties to template."""
        template.update(properties)
        return template
    
    def _validate_layers(self, layers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Validate layer definitions."""
        result = {"errors": [], "warnings": []}
        
        if not layers:
            result["errors"].append("No layers defined")
            return result
        
        layer_names = set()
        for layer in layers:
            if "name" not in layer:
                result["errors"].append("Layer missing name field")
            else:
                name = layer["name"]
                if name in layer_names:
                    result["warnings"].append(f"Duplicate layer name: {name}")
                layer_names.add(name)
            
            if "color" not in layer:
                result["warnings"].append(f"Layer '{layer.get('name', 'unnamed')}' missing color")
        
        return result
    
    def _validate_figures(self, figures: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Validate figure definitions."""
        result = {"errors": [], "warnings": []}
        
        if not figures:
            result["warnings"].append("No figures defined")
            return result
        
        for i, figure in enumerate(figures):
            if "type" not in figure:
                result["errors"].append(f"Figure {i} missing type field")
            
            figure_type = figure.get("type")
            if figure_type == "rectangle" and "points" not in figure:
                result["errors"].append(f"Rectangle figure {i} missing points")
            elif figure_type == "circle" and ("center" not in figure or "radius" not in figure):
                result["errors"].append(f"Circle figure {i} missing center or radius")
        
        return result
    
    def _validate_geometry(self, kitchen_json: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate geometric consistency."""
        result = {"warnings": []}
        
        # Check for overlapping appliances, minimum clearances, etc.
        # Simplified implementation
        figures = kitchen_json.get("figures", [])
        appliance_count = len([f for f in figures if f.get("layer") == "Appliances"])
        
        if appliance_count == 0:
            result["warnings"].append("No appliances found in kitchen design")
        elif appliance_count > 20:
            result["warnings"].append("Very high number of appliances - check for duplicates")
        
        return result
    
    def _score_template(self, template: Dict[str, Any], dimensions: List[int], 
                       style: str, appliances: List[str], budget: str) -> float:
        """Score template based on requirements."""
        score = 0.0
        
        # Dimension scoring
        if dimensions:
            rec_dims = template.get("parameters", {}).get("recommended_dimensions", [])
            if rec_dims and len(dimensions) >= 2 and len(rec_dims) >= 2:
                width_diff = abs(dimensions[0] - rec_dims[0]) / rec_dims[0]
                height_diff = abs(dimensions[1] - rec_dims[1]) / rec_dims[1]
                dimension_score = max(0, 1 - (width_diff + height_diff) / 2)
                score += dimension_score * 0.4
        
        # Style scoring
        template_style = template.get("style", "").lower()
        if style and template_style == style:
            score += 0.3
        elif style and style in template_style:
            score += 0.15
        
        # Appliance scoring
        template_appliances = set(template.get("appliances_included", []))
        requested_appliances = set(appliances)
        if requested_appliances:
            overlap = len(template_appliances & requested_appliances)
            total_requested = len(requested_appliances)
            appliance_score = overlap / total_requested if total_requested > 0 else 0
            score += appliance_score * 0.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_suggestion_reasons(self, template: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
        """Get reasons why a template was suggested."""
        reasons = []
        
        dimensions = requirements.get("dimensions", [])
        style = requirements.get("style", "").lower()
        
        # Check dimension match
        rec_dims = template.get("parameters", {}).get("recommended_dimensions", [])
        if dimensions and rec_dims:
            if abs(dimensions[0] - rec_dims[0]) < rec_dims[0] * 0.2:
                reasons.append("Good dimension match")
        
        # Check style match
        template_style = template.get("style", "").lower()
        if style and template_style == style:
            reasons.append(f"Perfect {style} style match")
        
        return reasons
    
    def _get_modern_l_shaped_template(self) -> Dict[str, Any]:
        """Get modern L-shaped kitchen template."""
        return {
            "description": "Modern L-shaped kitchen with optional island",
            "style": "modern",
            "parameters": {
                "min_dimensions": [3000, 2500],
                "recommended_dimensions": [4000, 3000]
            },
            "appliances_included": ["refrigerator", "stove", "sink", "dishwasher"],
            "dxf_template": {
                "layers": [
                    {"name": "Walls", "color": 7},
                    {"name": "Cabinets", "color": 3},
                    {"name": "Appliances", "color": 5},
                    {"name": "Dimensions", "color": 2},
                    {"name": "Text", "color": 1}
                ],
                "figures": [
                    {
                        "type": "rectangle",
                        "points": [[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
                        "layer": "Walls"
                    },
                    {
                        "type": "rectangle",
                        "points": [[100, 100], [3900, 100], [3900, 700], [100, 700]],
                        "layer": "Cabinets"
                    },
                    {
                        "type": "rectangle",
                        "points": [[100, 700], [700, 700], [700, 2900], [100, 2900]],
                        "layer": "Cabinets"
                    }
                ]
            }
        }
    
    def _get_compact_galley_template(self) -> Dict[str, Any]:
        """Get compact galley kitchen template."""
        return {
            "description": "Compact galley kitchen for small spaces",
            "style": "modern",
            "parameters": {
                "min_dimensions": [1800, 2400],
                "recommended_dimensions": [2400, 3600]
            },
            "appliances_included": ["refrigerator", "stove", "sink"],
            "dxf_template": {
                "layers": [
                    {"name": "Walls", "color": 7},
                    {"name": "Cabinets", "color": 3},
                    {"name": "Appliances", "color": 5}
                ],
                "figures": [
                    {
                        "type": "rectangle",
                        "points": [[0, 0], [2400, 0], [2400, 3600], [0, 3600]],
                        "layer": "Walls"
                    },
                    {
                        "type": "rectangle",
                        "points": [[100, 100], [2300, 100], [2300, 700], [100, 700]],
                        "layer": "Cabinets"
                    },
                    {
                        "type": "rectangle",
                        "points": [[100, 2900], [2300, 2900], [2300, 3500], [100, 3500]],
                        "layer": "Cabinets"
                    }
                ]
            }
        }
    
    def _get_u_shaped_luxury_template(self) -> Dict[str, Any]:
        """Get U-shaped luxury kitchen template."""
        return {
            "description": "Luxury U-shaped kitchen with premium appliances",
            "style": "modern",
            "parameters": {
                "min_dimensions": [4000, 3500],
                "recommended_dimensions": [5000, 4000]
            },
            "appliances_included": ["refrigerator", "stove", "sink", "dishwasher", "oven", "microwave"],
            "dxf_template": {
                "layers": [
                    {"name": "Walls", "color": 7},
                    {"name": "Cabinets", "color": 3},
                    {"name": "Appliances", "color": 5},
                    {"name": "Luxury", "color": 1}
                ],
                "figures": [
                    {
                        "type": "rectangle",
                        "points": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]],
                        "layer": "Walls"
                    }
                ]
            }
        }
    
    def _get_open_plan_template(self) -> Dict[str, Any]:
        """Get open plan modern kitchen template."""
        return {
            "description": "Open plan modern kitchen with dining integration",
            "style": "modern",
            "parameters": {
                "min_dimensions": [5000, 4000],
                "recommended_dimensions": [6000, 4500]
            },
            "appliances_included": ["island", "refrigerator", "stove", "sink", "dishwasher"],
            "dxf_template": {
                "layers": [
                    {"name": "Walls", "color": 7},
                    {"name": "Cabinets", "color": 3},
                    {"name": "Appliances", "color": 5},
                    {"name": "Dining", "color": 4}
                ],
                "figures": [
                    {
                        "type": "rectangle",
                        "points": [[0, 0], [6000, 0], [6000, 4500], [0, 4500]],
                        "layer": "Walls"
                    }
                ]
            }
        }
    
    def _get_traditional_template(self) -> Dict[str, Any]:
        """Get traditional country kitchen template."""
        return {
            "description": "Traditional country-style kitchen with farmhouse elements",
            "style": "traditional",
            "parameters": {
                "min_dimensions": [3500, 3000],
                "recommended_dimensions": [4500, 3500]
            },
            "appliances_included": ["refrigerator", "stove", "sink", "pantry"],
            "dxf_template": {
                "layers": [
                    {"name": "Walls", "color": 7},
                    {"name": "Cabinets", "color": 6},
                    {"name": "Appliances", "color": 4},
                    {"name": "Traditional", "color": 2}
                ],
                "figures": [
                    {
                        "type": "rectangle",
                        "points": [[0, 0], [4500, 0], [4500, 3500], [0, 3500]],
                        "layer": "Walls"
                    }
                ]
            }
        }