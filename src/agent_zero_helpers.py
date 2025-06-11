# src/agent_zero_helpers.py
"""
Agent Zero Helper Functions

This module provides helper functions specifically designed for Agent Zero integration.
It includes template selection logic, German term translation, and JSON validation
utilities to support Agent Zero in generating kitchen DXF requests.

Phase 2 Day 5 deliverable for IMPLEMENTATION_PLAN.md
"""

import json
import logging
import re
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentZeroHelpers:
    """
    Helper functions for Agent Zero kitchen design integration.
    
    Provides template selection, language translation, and validation
    utilities to support Agent Zero in generating kitchen designs.
    """
    
    def __init__(self, vocabulary_path: str = "kitchen_vocabulary.json", 
                 templates_dir: str = "agent_zero_templates/kitchen_templates"):
        """
        Initialize Agent Zero helpers.
        
        Args:
            vocabulary_path: Path to kitchen vocabulary JSON file
            templates_dir: Directory containing kitchen template files
        """
        self.vocabulary_path = vocabulary_path
        self.templates_dir = Path(templates_dir)
        self.vocabulary = self._load_vocabulary()
        self.available_templates = self._load_available_templates()
        logger.info("Agent Zero helpers initialized")
    
    def select_best_template(self, requirements: Dict[str, Any]) -> str:
        """
        Select optimal template based on requirements.
        
        Args:
            requirements: Dictionary with client requirements including:
                - dimensions: [width, height] in millimeters
                - style: style preference
                - appliances: list of required appliances
                - layout_preference: preferred layout type
                - budget: budget category
                
        Returns:
            Name of the best matching template
        """
        logger.info(f"Selecting template for requirements: {requirements}")
        
        # Extract key requirements
        dimensions = requirements.get("dimensions", [4000, 3000])
        style = requirements.get("style", "modern").lower()
        appliances = requirements.get("appliances", [])
        layout_pref = requirements.get("layout_preference", "").lower()
        budget = requirements.get("budget", "mid_range").lower()
        
        # Calculate room area
        room_area = dimensions[0] * dimensions[1] if len(dimensions) >= 2 else 12000000  # Default 4x3m
        
        # Score each available template
        template_scores = {}
        for template_name in self.available_templates:
            score = self._score_template_match(template_name, dimensions, room_area, 
                                             style, appliances, layout_pref, budget)
            template_scores[template_name] = score
            logger.debug(f"Template {template_name} scored: {score:.2f}")
        
        # Select best match
        best_template = max(template_scores, key=template_scores.get)
        best_score = template_scores[best_template]
        
        logger.info(f"Selected template: {best_template} (score: {best_score:.2f})")
        
        return best_template
    
    def translate_german_terms(self, text: str) -> str:
        """
        Translate German kitchen terms to English.
        
        Args:
            text: Text potentially containing German kitchen terms
            
        Returns:
            Text with German terms translated to English
        """
        logger.info(f"Translating German terms in: {text}")
        
        if not text:
            return text
        
        translated_text = text.lower()
        
        # Get German to English mappings from vocabulary
        german_mappings = self.vocabulary.get("german_to_english", {})
        
        # Apply direct translations
        for german_term, english_term in german_mappings.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(german_term) + r'\b'
            translated_text = re.sub(pattern, english_term, translated_text, flags=re.IGNORECASE)
        
        # Handle common German kitchen phrases
        phrase_mappings = {
            "küche mit insel": "kitchen with island",
            "moderne küche": "modern kitchen", 
            "kleine küche": "small kitchen",
            "große küche": "large kitchen",
            "offene küche": "open kitchen",
            "l-förmige küche": "l-shaped kitchen",
            "u-förmige küche": "u-shaped kitchen"
        }
        
        for german_phrase, english_phrase in phrase_mappings.items():
            translated_text = translated_text.replace(german_phrase, english_phrase)
        
        # Handle dimension translations
        translated_text = re.sub(r'(\d+)\s*x\s*(\d+)\s*meter', r'\1x\2 meters', translated_text)
        translated_text = re.sub(r'(\d+)\s*meter', r'\1 meters', translated_text)
        
        logger.info(f"Translation result: {translated_text}")
        return translated_text
    
    def validate_generated_json(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate Agent Zero generated JSON.
        
        Args:
            json_data: JSON data generated by Agent Zero
            
        Returns:
            Tuple of (is_valid, error_list, suggestions)
        """
        logger.info("Validating Agent Zero generated JSON")
        
        errors = []
        suggestions = {}
        
        # Check required top-level fields
        required_fields = ["template_name", "customization", "client_info"]
        for field in required_fields:
            if field not in json_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate template_name
        if "template_name" in json_data:
            template_name = json_data["template_name"]
            if template_name not in self.available_templates:
                errors.append(f"Unknown template: {template_name}")
                suggestions["template_name"] = f"Available templates: {list(self.available_templates)}"
        
        # Validate customization section
        if "customization" in json_data:
            customization_errors = self._validate_customization(json_data["customization"])
            errors.extend(customization_errors)
        
        # Validate client_info
        if "client_info" in json_data:
            client_errors = self._validate_client_info(json_data["client_info"])
            errors.extend(client_errors)
        
        # Check for common Agent Zero mistakes
        common_errors = self._check_common_mistakes(json_data)
        errors.extend(common_errors)
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation result: {'Valid' if is_valid else 'Invalid'} ({len(errors)} errors)")
        
        return is_valid, errors, suggestions
    
    def extract_requirements_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract structured requirements from natural language text.
        
        Args:
            text: Natural language description of kitchen requirements
            
        Returns:
            Dictionary with extracted requirements
        """
        logger.info(f"Extracting requirements from: {text}")
        
        # Translate German terms first
        translated_text = self.translate_german_terms(text)
        
        requirements = {
            "dimensions": self._extract_dimensions(translated_text),
            "style": self._extract_style(translated_text),
            "appliances": self._extract_appliances(translated_text),
            "layout_preference": self._extract_layout(translated_text),
            "budget": self._extract_budget(translated_text),
            "special_requirements": self._extract_special_requirements(translated_text)
        }
        
        logger.info(f"Extracted requirements: {requirements}")
        return requirements
    
    def suggest_template_alternatives(self, template_name: str, 
                                    requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest alternative templates based on requirements.
        
        Args:
            template_name: Current template selection
            requirements: Client requirements
            
        Returns:
            List of alternative templates with reasons
        """
        logger.info(f"Finding alternatives to template: {template_name}")
        
        alternatives = []
        
        for alt_template in self.available_templates:
            if alt_template == template_name:
                continue
            
            # Load template info
            template_info = self._get_template_info(alt_template)
            if not template_info:
                continue
            
            # Calculate match score
            score = self._score_template_match(alt_template, 
                                             requirements.get("dimensions", [4000, 3000]),
                                             12000000,  # Default area
                                             requirements.get("style", "modern"),
                                             requirements.get("appliances", []),
                                             requirements.get("layout_preference", ""),
                                             requirements.get("budget", "mid_range"))
            
            # Generate recommendation reason
            reason = self._generate_alternative_reason(template_info, requirements)
            
            alternatives.append({
                "template_name": alt_template,
                "match_score": score,
                "reason": reason,
                "description": template_info.get("description", ""),
                "dimensions": template_info.get("parameters", {}).get("recommended_dimensions", [])
            })
        
        # Sort by match score
        alternatives.sort(key=lambda x: x["match_score"], reverse=True)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def _load_vocabulary(self) -> Dict[str, Any]:
        """Load kitchen vocabulary from JSON file."""
        try:
            vocab_file = Path(self.vocabulary_path)
            if vocab_file.exists():
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Vocabulary file not found: {vocab_file}")
                return self._get_default_vocabulary()
        except Exception as e:
            logger.error(f"Error loading vocabulary: {e}")
            return self._get_default_vocabulary()
    
    def _load_available_templates(self) -> List[str]:
        """Load list of available template names."""
        templates = []
        if self.templates_dir.exists():
            for json_file in self.templates_dir.glob("*.json"):
                templates.append(json_file.stem)
        
        if not templates:
            logger.warning("No templates found, using defaults")
            templates = ["modern_l_shaped", "compact_galley", "u_shaped_luxury", 
                        "open_plan_modern", "traditional_country"]
        
        logger.info(f"Available templates: {templates}")
        return templates
    
    def _score_template_match(self, template_name: str, dimensions: List[int], 
                            room_area: int, style: str, appliances: List[str],
                            layout_pref: str, budget: str) -> float:
        """Calculate match score for a template."""
        score = 0.0
        
        # Load template for scoring
        template_info = self._get_template_info(template_name)
        if not template_info:
            return 0.0
        
        # Dimension scoring (40% weight)
        if dimensions and len(dimensions) >= 2:
            template_dims = template_info.get("parameters", {}).get("recommended_dimensions", [4000, 3000])
            if template_dims:
                # Calculate how well dimensions match
                width_ratio = min(dimensions[0], template_dims[0]) / max(dimensions[0], template_dims[0])
                height_ratio = min(dimensions[1], template_dims[1]) / max(dimensions[1], template_dims[1])
                dimension_score = (width_ratio + height_ratio) / 2
                score += dimension_score * 0.4
        
        # Layout preference scoring (25% weight)
        template_layout = template_info.get("parameters", {}).get("layout_type", "")
        if layout_pref and template_layout:
            if layout_pref in template_layout or template_layout in layout_pref:
                score += 0.25
        
        # Style preference scoring (20% weight) 
        template_style = template_info.get("parameters", {}).get("style", "modern")
        if style and template_style:
            if style.lower() == template_style.lower():
                score += 0.2
            elif any(s in template_style.lower() for s in [style.lower()]):
                score += 0.1
        
        # Appliance requirements scoring (15% weight)
        template_appliances = set(template_info.get("appliances_included", []))
        required_appliances = set(appliances)
        if required_appliances:
            appliance_match = len(required_appliances.intersection(template_appliances)) / len(required_appliances)
            score += appliance_match * 0.15
        
        return score
    
    def _get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Load template info from JSON file."""
        try:
            template_file = self.templates_dir / f"{template_name}.json"
            if template_file.exists():
                with open(template_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
        return None
    
    def _extract_dimensions(self, text: str) -> Optional[List[int]]:
        """Extract dimensions from text."""
        # Look for patterns like "4x3 meters", "4000x3000", "4 by 3"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*m(?:eters?)?',
            r'(\d+)\s*by\s*(\d+)\s*m(?:eters?)?',
            r'(\d{4,})\s*x\s*(\d{4,})'  # For mm values
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                width, height = float(match.group(1)), float(match.group(2))
                # Convert to mm if needed
                if width < 100:  # Assume meters
                    width *= 1000
                    height *= 1000
                return [int(width), int(height)]
        
        return None
    
    def _extract_style(self, text: str) -> str:
        """Extract style preference from text."""
        styles = self.vocabulary.get("styles", {})
        for style_name, keywords in styles.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    return style_name
        return "modern"  # Default
    
    def _extract_appliances(self, text: str) -> List[str]:
        """Extract appliance requirements from text."""
        found_appliances = []
        appliances = self.vocabulary.get("appliances", {})
        
        for appliance_name, keywords in appliances.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if appliance_name not in found_appliances:
                        found_appliances.append(appliance_name)
        
        return found_appliances
    
    def _extract_layout(self, text: str) -> str:
        """Extract layout preference from text."""
        layouts = self.vocabulary.get("layouts", {})
        for layout_name, keywords in layouts.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    return layout_name
        return ""
    
    def _extract_budget(self, text: str) -> str:
        """Extract budget category from text."""
        budget_indicators = self.vocabulary.get("budget_indicators", {})
        for budget_category, keywords in budget_indicators.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    return budget_category
        return "mid_range"  # Default
    
    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special requirements from text."""
        special_reqs = []
        
        # Common special requirements
        if any(word in text.lower() for word in ["accessible", "wheelchair", "disability"]):
            special_reqs.append("accessibility_compliant")
        
        if any(word in text.lower() for word in ["professional", "chef", "commercial"]):
            special_reqs.append("professional_grade")
        
        if any(word in text.lower() for word in ["entertaining", "party", "guests"]):
            special_reqs.append("entertainment_focused")
        
        return special_reqs
    
    def _validate_customization(self, customization: Dict[str, Any]) -> List[str]:
        """Validate customization parameters."""
        errors = []
        
        # Check dimensions format
        if "dimensions" in customization:
            dims = customization["dimensions"]
            if not isinstance(dims, list) or len(dims) != 2:
                errors.append("Dimensions must be a list of [width, height]")
            elif not all(isinstance(d, (int, float)) and d > 0 for d in dims):
                errors.append("Dimensions must be positive numbers")
        
        # Check appliances format
        if "appliances" in customization:
            appliances = customization["appliances"]
            if not isinstance(appliances, list):
                errors.append("Appliances must be a list")
        
        return errors
    
    def _validate_client_info(self, client_info: Dict[str, Any]) -> List[str]:
        """Validate client information."""
        errors = []
        
        # Check for required client fields
        if "project_name" not in client_info:
            errors.append("Missing project_name in client_info")
        
        return errors
    
    def _check_common_mistakes(self, json_data: Dict[str, Any]) -> List[str]:
        """Check for common Agent Zero mistakes."""
        errors = []
        
        # Check for mixing units (common mistake)
        if "customization" in json_data and "dimensions" in json_data["customization"]:
            dims = json_data["customization"]["dimensions"] 
            if isinstance(dims, list) and len(dims) == 2:
                if dims[0] < 100 and dims[1] > 1000:  # Mixed units
                    errors.append("Inconsistent units detected - use millimeters for all dimensions")
        
        return errors
    
    def _generate_alternative_reason(self, template_info: Dict[str, Any], 
                                   requirements: Dict[str, Any]) -> str:
        """Generate reason for alternative template suggestion."""
        reasons = []
        
        # Check dimension advantages
        template_dims = template_info.get("parameters", {}).get("recommended_dimensions", [])
        required_dims = requirements.get("dimensions", [])
        if template_dims and required_dims:
            if template_dims[0] * template_dims[1] > required_dims[0] * required_dims[1]:
                reasons.append("better suited for larger spaces")
            else:
                reasons.append("optimized for compact spaces")
        
        # Check style advantages
        template_style = template_info.get("parameters", {}).get("style", "")
        if template_style:
            reasons.append(f"designed in {template_style} style")
        
        return ", ".join(reasons) if reasons else "alternative design approach"
    
    def _get_default_vocabulary(self) -> Dict[str, Any]:
        """Fallback vocabulary if file not found."""
        return {
            "german_to_english": {
                "küche": "kitchen",
                "modern": "modern", 
                "insel": "island",
                "spüle": "sink",
                "herd": "stove"
            },
            "styles": {
                "modern": ["modern", "contemporary"],
                "traditional": ["traditional", "classic"]
            },
            "appliances": {
                "island": ["island"],
                "sink": ["sink"]
            }
        } 