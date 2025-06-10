"""
Semantic parsing module for converting natural language kitchen descriptions 
into structured parameters for DXF generation.

This module enables Agent Zero to describe kitchens in natural language
and have them converted to precise technical specifications.
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class KitchenSemanticParser:
    """
    Converts natural language kitchen descriptions into structured parameters
    for the DXF generation system.
    
    Example usage:
        parser = KitchenSemanticParser()
        params = parser.parse_description("Modern L-shaped kitchen with island, 4x3 meters")
        # Returns: {'layout': 'l_shaped', 'style': 'modern', 'dimensions': (4000, 3000), ...}
    """
    
    def __init__(self, vocabulary_path: str = "kitchen_vocabulary.json"):
        """Initialize with kitchen vocabulary for term mapping."""
        self.vocabulary_path = vocabulary_path
        self.vocabulary = self._load_vocabulary()
        logger.info("Kitchen semantic parser initialized")
    
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
            "layouts": {
                "l_shaped": ["l-shaped", "corner kitchen", "angular layout", "l shape"],
                "galley": ["galley", "corridor", "two-wall kitchen", "narrow"],
                "u_shaped": ["u-shaped", "horseshoe", "three-wall", "u shape"],
                "open_plan": ["open plan", "open concept", "great room"],
                "compact": ["compact", "small", "tiny", "studio"]
            },
            "styles": {
                "modern": ["modern", "contemporary", "minimalist", "sleek", "current"],
                "traditional": ["traditional", "classic", "farmhouse", "country", "rustic"],
                "industrial": ["industrial", "urban", "loft", "metal", "concrete"],
                "transitional": ["transitional", "mixed", "blend", "fusion"]
            },
            "appliances": {
                "island": ["island", "central counter", "kitchen island", "center island"],
                "peninsula": ["peninsula", "breakfast bar", "extended counter"],
                "refrigerator": ["refrigerator", "fridge", "cooling"],
                "stove": ["stove", "range", "cooktop", "cooking"],
                "sink": ["sink", "basin", "washing"],
                "dishwasher": ["dishwasher", "dish washing", "cleaning"],
                "oven": ["oven", "baking", "roasting"],
                "microwave": ["microwave", "micro"]
            },
            "features": {
                "pantry": ["pantry", "storage room", "food storage"],
                "breakfast_nook": ["breakfast nook", "eating area", "dining"],
                "bar_seating": ["bar seating", "counter seating", "stools"]
            }
        }
    
    def parse_description(self, description: str) -> Dict[str, Any]:
        """
        Main parsing function: converts natural language to structured parameters.
        
        Args:
            description: Natural language kitchen description
            
        Returns:
            Dict with parsed parameters: layout, style, dimensions, appliances, etc.
        """
        logger.info(f"Parsing description: {description}")
        
        # Normalize text
        normalized_text = description.lower().strip()
        
        # Extract key components
        result = {
            "layout": self.extract_layout_type(normalized_text),
            "style": self.extract_style(normalized_text),
            "dimensions": self.extract_dimensions(normalized_text),
            "appliances": self.extract_appliances(normalized_text),
            "features": self.extract_features(normalized_text),
            "original_description": description
        }
        
        # Apply smart defaults for missing information
        result = self._apply_smart_defaults(result)
        
        logger.info(f"Parsed result: {result}")
        return result
    
    def extract_layout_type(self, text: str) -> str:
        """
        Identify kitchen layout type from description.
        
        Args:
            text: Normalized description text
            
        Returns:
            Layout type string (l_shaped, galley, u_shaped, open_plan, compact)
        """
        for layout_type, keywords in self.vocabulary["layouts"].items():
            for keyword in keywords:
                if keyword in text:
                    logger.debug(f"Found layout: {layout_type} (keyword: {keyword})")
                    return layout_type
        
        # Default based on common patterns
        if any(word in text for word in ["small", "tiny", "studio"]):
            return "compact"
        elif any(word in text for word in ["open", "great room"]):
            return "open_plan"
        else:
            return "l_shaped"  # Most common default
    
    def extract_style(self, text: str) -> str:
        """
        Identify kitchen style from description.
        
        Args:
            text: Normalized description text
            
        Returns:
            Style string (modern, traditional, industrial, transitional)
        """
        for style_type, keywords in self.vocabulary["styles"].items():
            for keyword in keywords:
                if keyword in text:
                    logger.debug(f"Found style: {style_type} (keyword: {keyword})")
                    return style_type
        
        return "modern"  # Default to modern
    
    def extract_dimensions(self, text: str) -> Tuple[int, int]:
        """
        Parse room dimensions from description.
        
        Args:
            text: Description text
            
        Returns:
            Tuple of (width, length) in millimeters
        """
        # Pattern for dimensions like "4x3 meters", "12x10 feet", "4 by 3 m"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:meters?|m\b)',
            r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:feet|ft\b)',
            r'(\d+(?:\.\d+)?)\s*by\s*(\d+(?:\.\d+)?)\s*(?:meters?|m\b)',
            r'(\d+(?:\.\d+)?)\s*by\s*(\d+(?:\.\d+)?)\s*(?:feet|ft\b)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                width = float(match.group(1))
                length = float(match.group(2))
                
                # Convert feet to meters if needed
                if 'feet' in pattern or 'ft' in pattern:
                    width *= 0.3048
                    length *= 0.3048
                
                # Convert to millimeters
                width_mm = int(width * 1000)
                length_mm = int(length * 1000)
                
                logger.debug(f"Found dimensions: {width_mm}x{length_mm}mm")
                return (width_mm, length_mm)
        
        # Default dimensions based on layout type if not specified
        layout = self.extract_layout_type(text)
        defaults = {
            "compact": (2400, 1800),
            "galley": (3600, 2400),
            "l_shaped": (4000, 3000),
            "u_shaped": (4800, 3600),
            "open_plan": (6000, 4200)
        }
        
        default_dims = defaults.get(layout, (4000, 3000))
        logger.debug(f"Using default dimensions for {layout}: {default_dims}")
        return default_dims
    
    def extract_appliances(self, text: str) -> List[str]:
        """
        Identify required appliances from description.
        
        Args:
            text: Description text
            
        Returns:
            List of appliance identifiers
        """
        found_appliances = []
        
        for appliance, keywords in self.vocabulary["appliances"].items():
            for keyword in keywords:
                if keyword in text:
                    found_appliances.append(appliance)
                    logger.debug(f"Found appliance: {appliance} (keyword: {keyword})")
                    break
        
        # Always include basic appliances if not specified
        basics = ["refrigerator", "stove", "sink"]
        for basic in basics:
            if basic not in found_appliances:
                found_appliances.append(basic)
        
        return list(set(found_appliances))  # Remove duplicates
    
    def extract_features(self, text: str) -> List[str]:
        """
        Identify special features from description.
        
        Args:
            text: Description text
            
        Returns:
            List of feature identifiers
        """
        found_features = []
        
        for feature, keywords in self.vocabulary["features"].items():
            for keyword in keywords:
                if keyword in text:
                    found_features.append(feature)
                    logger.debug(f"Found feature: {feature} (keyword: {keyword})")
                    break
        
        return found_features
    
    def _apply_smart_defaults(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply intelligent defaults based on parsed parameters.
        
        Args:
            params: Parsed parameters dictionary
            
        Returns:
            Enhanced parameters with smart defaults
        """
        # Ensure minimum appliances for functionality
        if "island" in params["appliances"] and "sink" not in params["appliances"]:
            params["appliances"].append("sink")
        
        # Add dishwasher near sink for modern kitchens
        if params["style"] == "modern" and "dishwasher" not in params["appliances"]:
            params["appliances"].append("dishwasher")
        
        # Ensure reasonable dimensions
        width, length = params["dimensions"]
        if width < 1800 or length < 1200:  # Too small
            params["dimensions"] = (2400, 1800)
            logger.warning("Adjusted dimensions to minimum viable size")
        
        # Add default features based on layout
        if params["layout"] in ["l_shaped", "u_shaped"] and not params["features"]:
            if "island" in params["appliances"]:
                params["features"].append("bar_seating")
        
        return params
    
    def generate_dxf_instructions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed parameters to DXF generation instructions.
        
        Args:
            params: Parsed semantic parameters
            
        Returns:
            DXF instruction dictionary ready for generation
        """
        logger.info("Generating DXF instructions from semantic parameters")
        
        # Get layout generator based on type
        layout_generator = self._get_layout_generator(params["layout"])
        
        # Generate base layout
        instructions = layout_generator(params)
        
        # Apply style-specific modifications
        instructions = self._apply_style_modifications(instructions, params["style"])
        
        logger.info(f"Generated DXF instructions with {len(instructions.get('figures', []))} entities")
        return instructions
    
    def _get_layout_generator(self, layout_type: str):
        """Get the appropriate layout generator function."""
        generators = {
            "l_shaped": self._generate_l_shaped_layout,
            "galley": self._generate_galley_layout,
            "u_shaped": self._generate_u_shaped_layout,
            "open_plan": self._generate_open_plan_layout,
            "compact": self._generate_compact_layout
        }
        return generators.get(layout_type, self._generate_l_shaped_layout)
    
    def _generate_l_shaped_layout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate L-shaped kitchen layout."""
        width, length = params["dimensions"]
        
        # Define basic layers
        layers = [
            {"name": "Walls", "color": 7},
            {"name": "Cabinets", "color": 3},
            {"name": "Appliances", "color": 5},
            {"name": "Dimensions", "color": 2},
            {"name": "Text", "color": 1}
        ]
        
        figures = []
        
        # Room perimeter
        figures.append({
            "type": "rectangle",
            "points": [[0, 0], [width, 0], [width, length], [0, length]],
            "layer": "Walls"
        })
        
        # L-shaped cabinet layout
        cabinet_depth = 600
        
        # Bottom wall cabinets
        figures.append({
            "type": "rectangle", 
            "points": [[100, 100], [width-100, 100], [width-100, 100+cabinet_depth], [100, 100+cabinet_depth]],
            "layer": "Cabinets"
        })
        
        # Side wall cabinets
        figures.append({
            "type": "rectangle",
            "points": [[100, 100+cabinet_depth], [100+cabinet_depth, 100+cabinet_depth], 
                       [100+cabinet_depth, length-100], [100, length-100]],
            "layer": "Cabinets"
        })
        
        # Add appliances
        appliance_positions = self._calculate_appliance_positions(params, "l_shaped")
        for appliance, position in appliance_positions.items():
            if appliance in params["appliances"]:
                figures.extend(self._create_appliance_entities(appliance, position))
        
        # Add island if specified
        if "island" in params["appliances"]:
            island_width = min(1200, width // 3)
            island_length = min(2400, length // 2)
            island_x = (width - island_width) // 2
            island_y = (length - island_length) // 2
            
            figures.append({
                "type": "rectangle",
                "points": [[island_x, island_y], [island_x + island_width, island_y],
                          [island_x + island_width, island_y + island_length], [island_x, island_y + island_length]],
                "layer": "Cabinets"
            })
        
        # Add room dimensions
        figures.append({
            "type": "dimension",
            "dimension_type": "linear",
            "start": [0, 0],
            "end": [width, 0],
            "dimline_point": [width//2, -300],
            "layer": "Dimensions"
        })
        
        figures.append({
            "type": "dimension", 
            "dimension_type": "linear",
            "start": [0, 0],
            "end": [0, length],
            "dimline_point": [-300, length//2],
            "layer": "Dimensions"
        })
        
        # Add title
        figures.append({
            "type": "text",
            "text": f"{params['style'].title()} {params['layout'].replace('_', '-').title()} Kitchen",
            "position": [width//2, length + 500],
            "height": 200,
            "layer": "Text"
        })
        
        return {
            "layers": layers,
            "figures": figures
        }
    
    def _generate_galley_layout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate galley kitchen layout."""
        # Simplified galley implementation
        width, length = params["dimensions"]
        
        layers = [
            {"name": "Walls", "color": 7},
            {"name": "Cabinets", "color": 3}, 
            {"name": "Appliances", "color": 5}
        ]
        
        figures = [
            # Room perimeter
            {
                "type": "rectangle",
                "points": [[0, 0], [width, 0], [width, length], [0, length]],
                "layer": "Walls"
            },
            # Two parallel cabinet runs
            {
                "type": "rectangle",
                "points": [[100, 100], [width-100, 100], [width-100, 700], [100, 700]],
                "layer": "Cabinets"
            },
            {
                "type": "rectangle", 
                "points": [[100, length-700], [width-100, length-700], [width-100, length-100], [100, length-100]],
                "layer": "Cabinets"
            }
        ]
        
        return {"layers": layers, "figures": figures}
    
    def _generate_u_shaped_layout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate U-shaped kitchen layout."""
        # Use L-shaped as base and add third wall
        layout = self._generate_l_shaped_layout(params)
        width, length = params["dimensions"]
        
        # Add third wall of cabinets
        layout["figures"].append({
            "type": "rectangle",
            "points": [[width-700, 100], [width-100, 100], [width-100, length-100], [width-700, length-100]],
            "layer": "Cabinets"
        })
        
        return layout
    
    def _generate_open_plan_layout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate open plan kitchen layout."""
        return self._generate_l_shaped_layout(params)  # Simplified
    
    def _generate_compact_layout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compact kitchen layout."""
        return self._generate_galley_layout(params)  # Simplified
    
    def _calculate_appliance_positions(self, params: Dict[str, Any], layout_type: str) -> Dict[str, Tuple[int, int]]:
        """Calculate optimal appliance positions based on layout."""
        # Simplified positioning logic
        return {
            "refrigerator": (200, 200),
            "stove": (1000, 200),
            "sink": (1800, 200),
            "dishwasher": (2000, 200)
        }
    
    def _create_appliance_entities(self, appliance: str, position: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Create DXF entities for appliances."""
        x, y = position
        appliance_sizes = {
            "refrigerator": (700, 700),
            "stove": (600, 600),
            "sink": (600, 500),
            "dishwasher": (600, 600)
        }
        
        if appliance not in appliance_sizes:
            return []
        
        w, h = appliance_sizes[appliance]
        
        return [{
            "type": "rectangle",
            "points": [[x, y], [x+w, y], [x+w, y+h], [x, y+h]],
            "layer": "Appliances"
        }]
    
    def _apply_style_modifications(self, instructions: Dict[str, Any], style: str) -> Dict[str, Any]:
        """Apply style-specific modifications to layout."""
        # Style modifications could include:
        # - Different line weights
        # - Different hatch patterns  
        # - Style-specific annotations
        
        if style == "industrial":
            # Add industrial elements
            pass
        elif style == "traditional":
            # Add traditional elements
            pass
        
        return instructions