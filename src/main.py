import os
import uuid
import ezdxf
import json
import traceback
import logging
from typing import Dict, List, Tuple, Any, Union, Optional
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import atexit

# Import template engine for Agent Zero integration
try:
    from kitchen_template_engine import KitchenTemplateEngine
except ImportError:
    logger.warning("Template engine not available - Agent Zero features will be disabled")
    KitchenTemplateEngine = None

TMP_DIR = "/tmp"

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Custom Exceptions
class DXFGenerationError(Exception):
    """Base exception for DXF generation errors."""
    pass

class ValidationError(DXFGenerationError):
    """Exception for validation errors."""
    pass

class EntityProcessingError(DXFGenerationError):
    """Exception for entity processing errors."""
    pass

# Processing Summary Data Structures
@dataclass
class EntitySummary:
    """Summary of processed entity."""
    type: str
    layer: str
    success: bool
    message: Optional[str] = None

@dataclass
class ProcessingSummary:
    """Comprehensive processing summary."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_entities: int = 0
    successful_entities: int = 0
    failed_entities: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    entities_by_layer: Dict[str, int] = field(default_factory=dict)
    entity_details: List[EntitySummary] = field(default_factory=list)
    file_info: Dict[str, Any] = field(default_factory=dict)
    
    def finalize(self, file_path: str, file_size: int):
        """Finalize the summary with file information."""
        self.end_time = datetime.now()
        self.file_info = {
            "path": os.path.basename(file_path),
            "size_bytes": file_size,
            "generation_time_ms": int((self.end_time - self.start_time).total_seconds() * 1000)
        }
    
    def add_entity_result(self, entity_type: str, layer: str, success: bool, message: str = None):
        """Add result of entity processing."""
        self.total_entities += 1
        if success:
            self.successful_entities += 1
        else:
            self.failed_entities += 1
            if message:
                self.errors.append(f"{entity_type}: {message}")
        
        # Track by type and layer
        self.entities_by_type[entity_type] = self.entities_by_type.get(entity_type, 0) + 1
        self.entities_by_layer[layer] = self.entities_by_layer.get(layer, 0) + 1
        
        # Add detailed entity summary
        self.entity_details.append(EntitySummary(
            type=entity_type,
            layer=layer,
            success=success,
            message=message
        ))
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary for JSON response."""
        return {
            "processing_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "total_entities": self.total_entities,
                "successful_entities": self.successful_entities,
                "failed_entities": self.failed_entities,
                "success_rate": f"{(self.successful_entities/self.total_entities*100):.1f}%" if self.total_entities > 0 else "0%",
                "entities_by_type": self.entities_by_type,
                "entities_by_layer": self.entities_by_layer,
                "file_info": self.file_info
            },
            "warnings": self.warnings,
            "errors": self.errors,
            "entity_details": [
                {
                    "type": e.type,
                    "layer": e.layer,
                    "success": e.success,
                    "message": e.message
                } for e in self.entity_details
            ] if len(self.entity_details) <= 50 else f"({len(self.entity_details)} entities - details truncated)"
        }

# File Management System
class TempFileManager:
    """Manages temporary files with automatic cleanup."""
    
    def __init__(self):
        self._temp_files = set()
        atexit.register(self.cleanup_all)
    
    def create_temp_file(self, suffix: str = ".dxf") -> str:
        """Create a temporary file and track it for cleanup."""
        fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=TMP_DIR)
        os.close(fd)  # Close the file descriptor, we just need the path
        self._temp_files.add(temp_path)
        logger.debug(f"Created temp file: {temp_path}")
        return temp_path
    
    def cleanup_file(self, file_path: str):
        """Clean up a specific temporary file."""
        if file_path in self._temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
                self._temp_files.discard(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def cleanup_all(self):
        """Clean up all temporary files."""
        for file_path in list(self._temp_files):
            self.cleanup_file(file_path)
        logger.info(f"Cleaned up {len(self._temp_files)} temporary files")

# Global temp file manager
temp_file_manager = TempFileManager()

# Request Validation Middleware
class RequestValidator:
    """Middleware for validating and preprocessing requests."""
    
    @staticmethod
    def validate_request_size(body: Dict[str, Any]) -> Optional[str]:
        """Validate request size and complexity."""
        # Check total entities
        total_entities = 0
        if "figures" in body:
            total_entities += len(body["figures"])
        if "blocks" in body:
            for block in body["blocks"]:
                total_entities += len(block.get("entities", []))
        
        if total_entities > 10000:  # Configurable limit
            return f"Too many entities requested: {total_entities} (max: 10000)"
        
        # Check for potential memory issues
        for figure in body.get("figures", []):
            if figure.get("type") == "mesh":
                vertices = figure.get("vertices", [])
                if len(vertices) > 50000:
                    return f"Mesh too complex: {len(vertices)} vertices (max: 50000)"
        
        return None
    
    @staticmethod
    def validate_layer_references(body: Dict[str, Any]) -> Optional[str]:
        """Validate that all layer references exist."""
        layer_names = {layer["name"] for layer in body.get("layers", [])}
        
        # Check figures
        for figure in body.get("figures", []):
            layer = figure.get("layer", "default")
            if layer != "default" and layer not in layer_names:
                return f"Figure references undefined layer: '{layer}'"
        
        # Check block entities
        for block in body.get("blocks", []):
            for entity in block.get("entities", []):
                layer = entity.get("layer", "default")
                if layer != "default" and layer not in layer_names:
                    return f"Block entity references undefined layer: '{layer}'"
        
        return None
    
    @staticmethod
    def preprocess_request(body: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess and enhance the request."""
        # Add default layer if none provided
        if not body.get("layers"):
            body["layers"] = [{"name": "default", "color": 7}]
        
        # Set default streaming threshold if not provided
        if "streaming_threshold" not in body:
            body["streaming_threshold"] = 1048576  # 1MB
        
        # Add client info logging
        if "client_info" in body:
            client_info = body["client_info"]
            logger.info(f"Request from client: {client_info}")
        
        return body
    
    @classmethod
    def validate_and_preprocess(cls, body: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Run all validation and preprocessing steps."""
        # Size validation
        error = cls.validate_request_size(body)
        if error:
            return error, body
        
        # Layer reference validation
        error = cls.validate_layer_references(body)
        if error:
            return error, body
        
        # Preprocessing
        processed_body = cls.preprocess_request(body)
        
        return None, processed_body

# Pydantic Models for JSON Schema Validation
class LayerModel(BaseModel):
    """Layer definition model."""
    name: str = Field(..., description="Layer name")
    color: Optional[int] = Field(7, description="Layer color (0-255)")

class EntityModel(BaseModel):
    """Base entity model for blocks."""
    type: str = Field(..., description="Entity type (rectangle, circle, text)")
    points: Optional[List[List[float]]] = Field(None, description="List of coordinate points")
    center: Optional[List[float]] = Field(None, description="Center point coordinates")
    radius: Optional[float] = Field(None, description="Radius for circles")
    text: Optional[str] = Field(None, description="Text content")
    height: Optional[float] = Field(250, description="Text height")
    position: Optional[List[float]] = Field(None, description="Text position coordinates")

class BlockModel(BaseModel):
    """Block definition model."""
    name: str = Field(..., description="Block name")
    entities: List[EntityModel] = Field(default_factory=list, description="List of entities in block")

class FigureModel(BaseModel):
    """Figure/entity model for main drawing."""
    type: str = Field(..., description="Figure type")
    layer: Optional[str] = Field("default", description="Layer name")
    color: Optional[int] = Field(7, description="Entity color")
    
    # Basic geometry fields
    points: Optional[List[List[float]]] = Field(None, description="Coordinate points")
    start: Optional[List[float]] = Field(None, description="Start point for lines/dimensions")
    end: Optional[List[float]] = Field(None, description="End point for lines/dimensions")
    center: Optional[List[float]] = Field(None, description="Center point")
    radius: Optional[float] = Field(None, description="Radius")
    text: Optional[str] = Field(None, description="Text content")
    height: Optional[float] = Field(250, description="Text/entity height")
    position: Optional[List[float]] = Field(None, description="Position coordinates")
    start_angle: Optional[float] = Field(None, description="Start angle for arcs")
    end_angle: Optional[float] = Field(None, description="End angle for arcs")
    major_axis: Optional[List[float]] = Field(None, description="Major axis for ellipses")
    ratio: Optional[float] = Field(0.5, description="Ratio for ellipses")
    base: Optional[List[float]] = Field(None, description="Base point for dimensions")
    angle: Optional[float] = Field(0, description="Angle for dimensions")
    name: Optional[str] = Field(None, description="Block name for block references")
    insert_at: Optional[List[float]] = Field(None, description="Insertion point for blocks")
    
    # Phase 3A: Advanced geometry fields
    control_points: Optional[List[List[float]]] = Field(None, description="Control points for splines")
    degree: Optional[int] = Field(3, description="Degree for splines")
    closed: Optional[bool] = Field(False, description="Whether polyline/spline is closed")
    start_param: Optional[float] = Field(0, description="Start parameter for ellipses")
    end_param: Optional[float] = Field(6.283185, description="End parameter for ellipses")
    solid_type: Optional[str] = Field("box", description="Type of solid (box, cylinder, sphere)")
    corner1: Optional[List[float]] = Field(None, description="First corner for box solids")
    corner2: Optional[List[float]] = Field(None, description="Second corner for box solids")
    vertices: Optional[List[List[float]]] = Field(None, description="Vertices for meshes/leaders")
    faces: Optional[List[List[int]]] = Field(None, description="Face indices for meshes")
    
    # Phase 3B: Annotation fields
    dimension_type: Optional[str] = Field("linear", description="Type of dimension")
    dimline_point: Optional[List[float]] = Field(None, description="Dimension line point")
    radius_point: Optional[List[float]] = Field(None, description="Radius point for radial dims")
    text_override: Optional[str] = Field(None, description="Override text for dimensions")
    text_height: Optional[float] = Field(250, description="Text height for leaders/annotations")
    boundary: Optional[List[List[float]]] = Field(None, description="Boundary points for hatch")
    pattern: Optional[str] = Field("SOLID", description="Hatch pattern name")
    pattern_scale: Optional[float] = Field(1.0, description="Hatch pattern scale")
    pattern_angle: Optional[float] = Field(0.0, description="Hatch pattern angle")
    width: Optional[float] = Field(1000, description="Width for MTEXT")
    alignment: Optional[str] = Field("LEFT", description="Text alignment")
    
    # Phase 3C: Professional features fields
    label: Optional[str] = Field(None, description="Label for viewports")
    linetype_name: Optional[str] = Field("CONTINUOUS", description="Linetype name")
    linetype_pattern: Optional[List[float]] = Field(None, description="Linetype pattern")
    layer_name: Optional[str] = Field(None, description="Layer name for state management")
    visible: Optional[bool] = Field(True, description="Layer visibility")
    frozen: Optional[bool] = Field(False, description="Layer frozen state")
    locked: Optional[bool] = Field(False, description="Layer locked state")
    lineweight: Optional[str] = Field("DEFAULT", description="Layer lineweight")
    linetype: Optional[str] = Field("CONTINUOUS", description="Layer linetype")
    attribute_type: Optional[str] = Field("definition", description="Attribute type")
    tag: Optional[str] = Field(None, description="Attribute tag")
    prompt: Optional[str] = Field(None, description="Attribute prompt")
    default_value: Optional[str] = Field("", description="Attribute default value")
    value: Optional[str] = Field(None, description="Attribute value")
    
    # Phase 3D: Coordinate systems & transforms fields
    transform_type: Optional[str] = Field("translate", description="Transform type")
    offset: Optional[List[float]] = Field(None, description="Translation offset")
    base_point: Optional[List[float]] = Field(None, description="Base point for transforms")
    origin: Optional[List[float]] = Field(None, description="UCS origin")
    x_axis: Optional[List[float]] = Field(None, description="UCS X-axis direction")
    y_axis: Optional[List[float]] = Field(None, description="UCS Y-axis direction")

class DXFRequestModel(BaseModel):
    """Main request model for DXF generation."""
    layers: List[LayerModel] = Field(..., description="List of layer definitions")
    blocks: Optional[List[BlockModel]] = Field(default_factory=list, description="List of block definitions")
    figures: List[FigureModel] = Field(..., description="List of figures to draw")
    
    # Step 4: API improvements
    return_summary: Optional[bool] = Field(False, description="Return processing summary instead of DXF file")
    streaming_threshold: Optional[int] = Field(1048576, description="File size threshold for streaming (bytes)")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client information for logging")

class TemplateRequestModel(BaseModel):
    """Request model for template-based kitchen generation."""
    template_name: str = Field(..., description="Kitchen template name")
    customization: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Template customization parameters")
    return_summary: Optional[bool] = Field(False, description="Return processing summary instead of DXF file")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client information for logging")
    
    class Config:
        schema_extra = {
            "example": {
                "template_name": "modern_l_shaped",
                "customization": {
                    "dimensions": [4000, 3000],
                    "style": "modern",
                    "appliances": ["island", "dishwasher"]
                },
                "return_summary": False,
                "client_info": {
                    "application": "Agent Zero",
                    "version": "1.0.0"
                }
            }
        }

class LegacySemanticRequestModel(BaseModel):
    """Legacy request model for backward compatibility with semantic parsing."""
    description: str = Field(..., description="Natural language kitchen description (legacy)")
    return_summary: Optional[bool] = Field(False, description="Return processing summary instead of DXF file")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client information for logging")

# Utility Functions
class GeometryValidator:
    """Validates geometric parameters and constraints."""
    
    @staticmethod
    def validate_point(point: List[float], min_coords: int = 2) -> bool:
        """
        Validate a coordinate point.
        
        Args:
            point: List of coordinate values
            min_coords: Minimum number of coordinates required
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If point is invalid
        """
        if not isinstance(point, (list, tuple)):
            raise ValidationError(f"Point must be a list/tuple, got {type(point)}")
        
        if len(point) < min_coords:
            raise ValidationError(f"Point must have at least {min_coords} coordinates, got {len(point)}")
        
        try:
            [float(coord) for coord in point]
            return True
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid coordinate values in point {point}: {e}")
    
    @staticmethod
    def validate_radius(radius: Union[int, float]) -> bool:
        """
        Validate radius value.
        
        Args:
            radius: Radius value
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If radius is invalid
        """
        try:
            radius_val = float(radius)
            if radius_val <= 0:
                raise ValidationError(f"Radius must be positive, got {radius_val}")
            return True
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid radius value: {e}")
    
    @staticmethod
    def validate_angle(angle: Union[int, float], min_angle: float = -360, max_angle: float = 360) -> bool:
        """
        Validate angle value.
        
        Args:
            angle: Angle in degrees
            min_angle: Minimum allowed angle
            max_angle: Maximum allowed angle
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If angle is invalid
        """
        try:
            angle_val = float(angle)
            if not (min_angle <= angle_val <= max_angle):
                raise ValidationError(f"Angle must be between {min_angle}° and {max_angle}°, got {angle_val}°")
            return True
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid angle value: {e}")

class CoordinateConverter:
    """Handles coordinate conversion and validation."""
    
    @staticmethod
    def safe_tuple_float(lst: List[Union[str, int, float]]) -> Tuple[float, ...]:
        """
        Safely convert a list of values to a tuple of floats.
        
        Args:
            lst: List of values that can be converted to float
            
        Returns:
            Tuple of float values, original values if conversion fails
        """
        try:
            return tuple(map(float, lst))
        except Exception as e:
            logger.warning(f"Error converting coordinates to float: {lst} - {e}")
            return tuple(lst)

# Entity Processors (Factory Pattern)
class EntityProcessor(ABC):
    """Abstract base class for entity processors."""
    
    @abstractmethod
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """
        Process an entity and add it to the target.
        
        Args:
            entity_data: Entity configuration data
            target: Target to add entity to (modelspace or block)
            dxf_attribs: DXF attributes for the entity
            
        Returns:
            bool: True if processing was successful
        """
        pass

class RectangleProcessor(EntityProcessor):
    """Processor for rectangle entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "points" not in entity_data:
                raise EntityProcessingError("Rectangle missing required 'points' field")
            
            points_data = entity_data["points"]
            if len(points_data) < 3:
                raise EntityProcessingError(f"Rectangle needs at least 3 points, got {len(points_data)}")
            
            # Validate each point
            validated_points = []
            for i, point in enumerate(points_data):
                GeometryValidator.validate_point(point)
                validated_points.append(CoordinateConverter.safe_tuple_float(point))
            
            target.add_lwpolyline(validated_points, close=True, dxfattribs=dxf_attribs)
            logger.debug(f"Rectangle processed successfully with {len(validated_points)} points")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in rectangle: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing rectangle: {e}")
            return False

class CircleProcessor(EntityProcessor):
    """Processor for circle entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "center" not in entity_data:
                raise EntityProcessingError("Circle missing required 'center' field")
            if "radius" not in entity_data:
                raise EntityProcessingError("Circle missing required 'radius' field")
            
            # Validate geometry
            GeometryValidator.validate_point(entity_data["center"])
            GeometryValidator.validate_radius(entity_data["radius"])
            
            center = CoordinateConverter.safe_tuple_float(entity_data["center"])
            radius = float(entity_data["radius"])
            
            target.add_circle(center=center, radius=radius, dxfattribs=dxf_attribs)
            logger.debug(f"Circle processed successfully (center: {center}, radius: {radius})")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in circle: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing circle: {e}")
            return False

class LineProcessor(EntityProcessor):
    """Processor for line entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            start = CoordinateConverter.safe_tuple_float(entity_data["start"])
            end = CoordinateConverter.safe_tuple_float(entity_data["end"])
            target.add_line(start, end, dxfattribs=dxf_attribs)
            logger.debug(f"Line processed successfully")
            return True
        except Exception as e:
            logger.error(f"Error processing line: {e}")
            return False

class TextProcessor(EntityProcessor):
    """Processor for text entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            text_content = entity_data["text"]
            height = float(entity_data.get("height", 250))
            position = CoordinateConverter.safe_tuple_float(entity_data["position"])
            
            text = target.add_text(text_content, dxfattribs={"height": height, **dxf_attribs})
            text.dxf.insert = position
            try:
                try:
                    text.set_align("LEFT")
                except AttributeError:
                    # Fallback for older ezdxf versions
                    text.dxf.halign = 0  # LEFT align
            except AttributeError:
                # Fallback for older ezdxf versions
                text.dxf.halign = 0  # LEFT align
            logger.debug(f"Text processed successfully")
            return True
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return False

class ArcProcessor(EntityProcessor):
    """Processor for arc entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            required_fields = ["center", "radius", "start_angle", "end_angle"]
            for field in required_fields:
                if field not in entity_data:
                    raise EntityProcessingError(f"Arc missing required '{field}' field")
            
            # Validate geometry
            GeometryValidator.validate_point(entity_data["center"])
            GeometryValidator.validate_radius(entity_data["radius"])
            GeometryValidator.validate_angle(entity_data["start_angle"])
            GeometryValidator.validate_angle(entity_data["end_angle"])
            
            center = CoordinateConverter.safe_tuple_float(entity_data["center"])
            radius = float(entity_data["radius"])
            start_angle = float(entity_data["start_angle"])
            end_angle = float(entity_data["end_angle"])
            
            target.add_arc(
                center=center,
                radius=radius,
                start_angle=start_angle,
                end_angle=end_angle,
                dxfattribs=dxf_attribs
            )
            logger.debug(f"Arc processed successfully (center: {center}, radius: {radius}, angles: {start_angle}°-{end_angle}°)")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in arc: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing arc: {e}")
            return False

# Phase 3A: Advanced Entity Processors
class SplineProcessor(EntityProcessor):
    """Processor for spline/NURBS entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "control_points" not in entity_data:
                raise EntityProcessingError("Spline missing required 'control_points' field")
            
            control_points = entity_data["control_points"]
            if len(control_points) < 2:
                raise EntityProcessingError(f"Spline needs at least 2 control points, got {len(control_points)}")
            
            # Validate control points
            validated_points = []
            for i, point in enumerate(control_points):
                GeometryValidator.validate_point(point)
                validated_points.append(CoordinateConverter.safe_tuple_float(point))
            
            # Create spline with default parameters
            degree = int(entity_data.get("degree", 3))
            closed = bool(entity_data.get("closed", False))
            
            spline = target.add_spline(dxfattribs=dxf_attribs)
            spline.fit_points = validated_points
            spline.degree = degree
            spline.closed = closed
            
            logger.debug(f"Spline processed successfully with {len(validated_points)} control points")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in spline: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing spline: {e}")
            return False

class PolylineProcessor(EntityProcessor):
    """Processor for 2D/3D polyline entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "points" not in entity_data:
                raise EntityProcessingError("Polyline missing required 'points' field")
            
            points_data = entity_data["points"]
            if len(points_data) < 2:
                raise EntityProcessingError(f"Polyline needs at least 2 points, got {len(points_data)}")
            
            # Validate points
            validated_points = []
            for i, point in enumerate(points_data):
                GeometryValidator.validate_point(point)
                validated_points.append(CoordinateConverter.safe_tuple_float(point))
            
            # Determine if 3D based on first point
            is_3d = len(validated_points[0]) > 2
            closed = bool(entity_data.get("closed", False))
            
            if is_3d:
                polyline = target.add_polyline3d(validated_points, dxfattribs=dxf_attribs)
                if closed:
                    polyline.close(True)
            else:
                polyline = target.add_lwpolyline(validated_points, close=closed, dxfattribs=dxf_attribs)
            
            logger.debug(f"{'3D ' if is_3d else ''}Polyline processed successfully with {len(validated_points)} points")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in polyline: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing polyline: {e}")
            return False

class EllipseProcessor(EntityProcessor):
    """Processor for complete ellipse entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            required_fields = ["center", "major_axis"]
            for field in required_fields:
                if field not in entity_data:
                    raise EntityProcessingError(f"Ellipse missing required '{field}' field")
            
            # Validate geometry
            GeometryValidator.validate_point(entity_data["center"])
            GeometryValidator.validate_point(entity_data["major_axis"])
            
            center = CoordinateConverter.safe_tuple_float(entity_data["center"])
            major_axis = CoordinateConverter.safe_tuple_float(entity_data["major_axis"])
            ratio = float(entity_data.get("ratio", 0.5))
            start_param = float(entity_data.get("start_param", 0))
            end_param = float(entity_data.get("end_param", 6.283185))  # 2*pi
            
            if not (0 < ratio <= 1):
                raise EntityProcessingError(f"Ellipse ratio must be between 0 and 1, got {ratio}")
            
            target.add_ellipse(
                center=center,
                major_axis=major_axis,
                ratio=ratio,
                start_param=start_param,
                end_param=end_param,
                dxfattribs=dxf_attribs
            )
            
            logger.debug(f"Ellipse processed successfully (center: {center}, ratio: {ratio})")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in ellipse: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing ellipse: {e}")
            return False

class SolidProcessor(EntityProcessor):
    """Processor for 3D solid entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            solid_type = entity_data.get("solid_type", "box")
            
            if solid_type == "box":
                return self._process_box(entity_data, target, dxf_attribs)
            elif solid_type == "cylinder":
                return self._process_cylinder(entity_data, target, dxf_attribs)
            elif solid_type == "sphere":
                return self._process_sphere(entity_data, target, dxf_attribs)
            else:
                logger.warning(f"Unsupported solid type: {solid_type}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error processing solid: {e}")
            return False
    
    def _process_box(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process a 3D box solid."""
        required_fields = ["corner1", "corner2"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Box missing required '{field}' field")
        
        # For now, create as 3D face since ezdxf solid support is limited
        corner1 = CoordinateConverter.safe_tuple_float(entity_data["corner1"])
        corner2 = CoordinateConverter.safe_tuple_float(entity_data["corner2"])
        
        # Create 8 vertices of the box
        x1, y1, z1 = corner1[0], corner1[1], corner1[2] if len(corner1) > 2 else 0
        x2, y2, z2 = corner2[0], corner2[1], corner2[2] if len(corner2) > 2 else 0
        
        vertices = [
            (x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1),  # bottom
            (x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2)   # top
        ]
        
        # Create faces (simplified representation)
        target.add_3dface([vertices[0], vertices[1], vertices[2], vertices[3]], dxfattribs=dxf_attribs)  # bottom
        target.add_3dface([vertices[4], vertices[5], vertices[6], vertices[7]], dxfattribs=dxf_attribs)  # top
        
        logger.debug(f"Box solid processed successfully")
        return True
    
    def _process_cylinder(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process a cylinder solid (simplified as circle representation)."""
        required_fields = ["center", "radius", "height"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Cylinder missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["center"])
        GeometryValidator.validate_radius(entity_data["radius"])
        
        center = CoordinateConverter.safe_tuple_float(entity_data["center"])
        radius = float(entity_data["radius"])
        height = float(entity_data["height"])
        
        # Create base and top circles
        base_center = center
        top_center = (center[0], center[1], center[2] + height if len(center) > 2 else height)
        
        target.add_circle(center=base_center, radius=radius, dxfattribs=dxf_attribs)
        target.add_circle(center=top_center, radius=radius, dxfattribs=dxf_attribs)
        
        logger.debug(f"Cylinder solid processed successfully")
        return True
    
    def _process_sphere(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process a sphere solid (simplified as circle representation)."""
        required_fields = ["center", "radius"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Sphere missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["center"])
        GeometryValidator.validate_radius(entity_data["radius"])
        
        center = CoordinateConverter.safe_tuple_float(entity_data["center"])
        radius = float(entity_data["radius"])
        
        # Create sphere as circle (simplified representation)
        target.add_circle(center=center, radius=radius, dxfattribs=dxf_attribs)
        
        logger.debug(f"Sphere solid processed successfully")
        return True

class MeshProcessor(EntityProcessor):
    """Processor for mesh/surface entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "vertices" not in entity_data:
                raise EntityProcessingError("Mesh missing required 'vertices' field")
            if "faces" not in entity_data:
                raise EntityProcessingError("Mesh missing required 'faces' field")
            
            vertices = entity_data["vertices"]
            faces = entity_data["faces"]
            
            if len(vertices) < 3:
                raise EntityProcessingError(f"Mesh needs at least 3 vertices, got {len(vertices)}")
            if len(faces) < 1:
                raise EntityProcessingError(f"Mesh needs at least 1 face, got {len(faces)}")
            
            # Validate vertices
            validated_vertices = []
            for i, vertex in enumerate(vertices):
                GeometryValidator.validate_point(vertex, min_coords=3)
                validated_vertices.append(CoordinateConverter.safe_tuple_float(vertex))
            
            # Create mesh as 3D faces
            for face_indices in faces:
                if len(face_indices) < 3:
                    logger.warning(f"Skipping face with less than 3 vertices: {face_indices}")
                    continue
                
                face_vertices = []
                for idx in face_indices:
                    if 0 <= idx < len(validated_vertices):
                        face_vertices.append(validated_vertices[idx])
                    else:
                        logger.warning(f"Invalid vertex index: {idx}")
                        continue
                
                if len(face_vertices) >= 3:
                    # Pad to 4 vertices for 3DFACE (repeat last vertex if needed)
                    while len(face_vertices) < 4:
                        face_vertices.append(face_vertices[-1])
                    
                    target.add_3dface(face_vertices[:4], dxfattribs=dxf_attribs)
            
            logger.debug(f"Mesh processed successfully with {len(validated_vertices)} vertices and {len(faces)} faces")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in mesh: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing mesh: {e}")
            return False

# Phase 3B: Annotation System Processors
class DimensionProcessor(EntityProcessor):
    """Processor for dimension entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            dim_type = entity_data.get("dimension_type", "linear")
            
            if dim_type == "linear":
                return self._process_linear_dimension(entity_data, target, dxf_attribs)
            elif dim_type == "angular":
                return self._process_angular_dimension(entity_data, target, dxf_attribs)
            elif dim_type == "radial":
                return self._process_radial_dimension(entity_data, target, dxf_attribs)
            elif dim_type == "diameter":
                return self._process_diameter_dimension(entity_data, target, dxf_attribs)
            else:
                logger.warning(f"Unsupported dimension type: {dim_type}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error processing dimension: {e}")
            return False
    
    def _process_linear_dimension(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process linear dimension."""
        required_fields = ["start", "end", "dimline_point"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Linear dimension missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["start"])
        GeometryValidator.validate_point(entity_data["end"])
        GeometryValidator.validate_point(entity_data["dimline_point"])
        
        start = CoordinateConverter.safe_tuple_float(entity_data["start"])
        end = CoordinateConverter.safe_tuple_float(entity_data["end"])
        dimline_point = CoordinateConverter.safe_tuple_float(entity_data["dimline_point"])
        
        angle = float(entity_data.get("angle", 0))
        text_override = entity_data.get("text_override", "")
        
        dim = target.add_linear_dim(
            base=dimline_point,
            p1=start,
            p2=end,
            angle=angle,
            dxfattribs=dxf_attribs
        )
        
        if text_override:
            dim.render()
            dim.dxf.text = text_override
        else:
            dim.render()
        
        logger.debug(f"Linear dimension processed successfully")
        return True
    
    def _process_radial_dimension(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process radial dimension."""
        required_fields = ["center", "radius_point"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Radial dimension missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["center"])
        GeometryValidator.validate_point(entity_data["radius_point"])
        
        center = CoordinateConverter.safe_tuple_float(entity_data["center"])
        radius_point = CoordinateConverter.safe_tuple_float(entity_data["radius_point"])
        
        dim = target.add_radial_dim(
            center=center,
            radius=radius_point,
            dxfattribs=dxf_attribs
        )
        dim.render()
        
        logger.debug(f"Radial dimension processed successfully")
        return True

class LeaderProcessor(EntityProcessor):
    """Processor for leader/multileader entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "vertices" not in entity_data:
                raise EntityProcessingError("Leader missing required 'vertices' field")
            
            vertices = entity_data["vertices"]
            if len(vertices) < 2:
                raise EntityProcessingError(f"Leader needs at least 2 vertices, got {len(vertices)}")
            
            # Validate vertices
            validated_vertices = []
            for vertex in vertices:
                GeometryValidator.validate_point(vertex)
                validated_vertices.append(CoordinateConverter.safe_tuple_float(vertex))
            
            # Create leader as polyline with arrowhead
            leader = target.add_lwpolyline(validated_vertices, dxfattribs=dxf_attribs)
            
            # Add text if provided
            if "text" in entity_data and entity_data["text"]:
                text_content = entity_data["text"]
                text_height = float(entity_data.get("text_height", 250))
                text_position = validated_vertices[-1]  # Position at end of leader
                
                text = target.add_text(
                    text_content,
                    dxfattribs={"height": text_height, **dxf_attribs}
                )
                text.dxf.insert = text_position
                try:
                    text.set_align("LEFT")
                except AttributeError:
                    # Fallback for older ezdxf versions
                    text.dxf.halign = 0  # LEFT align
            
            logger.debug(f"Leader processed successfully with {len(validated_vertices)} vertices")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in leader: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing leader: {e}")
            return False

class HatchProcessor(EntityProcessor):
    """Processor for hatch/fill pattern entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "boundary" not in entity_data:
                raise EntityProcessingError("Hatch missing required 'boundary' field")
            
            boundary = entity_data["boundary"]
            if len(boundary) < 3:
                raise EntityProcessingError(f"Hatch boundary needs at least 3 points, got {len(boundary)}")
            
            # Validate boundary points
            validated_boundary = []
            for point in boundary:
                GeometryValidator.validate_point(point)
                validated_boundary.append(CoordinateConverter.safe_tuple_float(point))
            
            pattern_name = entity_data.get("pattern", "SOLID")
            pattern_scale = float(entity_data.get("pattern_scale", 1.0))
            pattern_angle = float(entity_data.get("pattern_angle", 0.0))
            
            # Create hatch
            hatch = target.add_hatch(dxfattribs=dxf_attribs)
            
            # Set pattern
            if pattern_name == "SOLID":
                hatch.set_solid_fill()
            else:
                hatch.set_pattern_fill(pattern_name, scale=pattern_scale, angle=pattern_angle)
            
            # Add boundary
            hatch.paths.add_polyline_path(validated_boundary, is_closed=True)
            
            logger.debug(f"Hatch processed successfully with pattern '{pattern_name}'")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in hatch: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing hatch: {e}")
            return False

class MTextProcessor(EntityProcessor):
    """Processor for multiline text (MTEXT) entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            if "text" not in entity_data:
                raise EntityProcessingError("MTEXT missing required 'text' field")
            if "position" not in entity_data:
                raise EntityProcessingError("MTEXT missing required 'position' field")
            
            GeometryValidator.validate_point(entity_data["position"])
            
            text_content = entity_data["text"]
            position = CoordinateConverter.safe_tuple_float(entity_data["position"])
            height = float(entity_data.get("height", 250))
            width = float(entity_data.get("width", 1000))
            
            # Create MTEXT
            mtext = target.add_mtext(
                text_content,
                dxfattribs={
                    "char_height": height,
                    "width": width,
                    **dxf_attribs
                }
            )
            mtext.dxf.insert = position
            
            # Set alignment
            alignment = entity_data.get("alignment", "LEFT")
            if alignment == "CENTER":
                mtext.dxf.attachment_point = 5  # Middle center
            elif alignment == "RIGHT":
                mtext.dxf.attachment_point = 6  # Middle right
            else:
                mtext.dxf.attachment_point = 4  # Middle left
            
            logger.debug(f"MTEXT processed successfully")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in MTEXT: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing MTEXT: {e}")
            return False

# Phase 3C: Professional Features Processors
class ViewportProcessor(EntityProcessor):
    """Processor for viewport entities."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Validate required fields
            required_fields = ["center", "width", "height"]
            for field in required_fields:
                if field not in entity_data:
                    raise EntityProcessingError(f"Viewport missing required '{field}' field")
            
            GeometryValidator.validate_point(entity_data["center"])
            
            center = CoordinateConverter.safe_tuple_float(entity_data["center"])
            width = float(entity_data["width"])
            height = float(entity_data["height"])
            
            if width <= 0 or height <= 0:
                raise EntityProcessingError(f"Viewport dimensions must be positive, got width={width}, height={height}")
            
            # Create viewport as rectangle (simplified representation)
            # Calculate corner points
            half_width = width / 2
            half_height = height / 2
            corners = [
                (center[0] - half_width, center[1] - half_height),
                (center[0] + half_width, center[1] - half_height),
                (center[0] + half_width, center[1] + half_height),
                (center[0] - half_width, center[1] + half_height)
            ]
            
            target.add_lwpolyline(corners, close=True, dxfattribs=dxf_attribs)
            
            # Add viewport label if specified
            if "label" in entity_data:
                label_text = target.add_text(
                    entity_data["label"],
                    dxfattribs={"height": 100, **dxf_attribs}
                )
                label_text.dxf.insert = center
                try:
                    label_text.set_align("MIDDLE_CENTER")
                except AttributeError:
                    # Fallback for older ezdxf versions
                    label_text.dxf.halign = 1  # CENTER align
                    label_text.dxf.valign = 1  # MIDDLE align
            
            logger.debug(f"Viewport processed successfully (center: {center}, size: {width}x{height})")
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in viewport: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing viewport: {e}")
            return False

class LinetypeProcessor(EntityProcessor):
    """Processor for custom linetype definitions."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            # Note: This is a simplified implementation
            # In a full implementation, you would create custom linetypes in the document
            
            linetype_name = entity_data.get("linetype_name", "CONTINUOUS")
            pattern = entity_data.get("linetype_pattern", [])
            
            # For now, just log the linetype definition
            logger.debug(f"Linetype '{linetype_name}' defined with pattern: {pattern}")
            
            # Apply linetype to subsequent entities by updating dxf_attribs
            if hasattr(target, 'doc'):  # If we have access to the document
                try:
                    # Check if linetype exists, if not create it
                    if linetype_name not in target.doc.linetypes:
                        if pattern:
                            target.doc.linetypes.new(linetype_name, dxfattribs={'pattern': pattern})
                        logger.debug(f"Custom linetype '{linetype_name}' created")
                except Exception as e:
                    logger.warning(f"Could not create custom linetype: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing linetype: {e}")
            return False

class LayerStateProcessor(EntityProcessor):
    """Processor for layer state management."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            layer_name = entity_data.get("layer_name")
            if not layer_name:
                raise EntityProcessingError("Layer state missing required 'layer_name' field")
            
            # Layer state properties
            visible = bool(entity_data.get("visible", True))
            frozen = bool(entity_data.get("frozen", False))
            locked = bool(entity_data.get("locked", False))
            color = entity_data.get("color", 7)
            lineweight = entity_data.get("lineweight", "DEFAULT")
            linetype = entity_data.get("linetype", "CONTINUOUS")
            
            # Apply layer state (simplified implementation)
            if hasattr(target, 'doc'):  # If we have access to the document
                try:
                    if layer_name in target.doc.layers:
                        layer = target.doc.layers.get(layer_name)
                        layer.dxf.color = color
                        layer.dxf.linetype = linetype
                        if not visible:
                            layer.off()
                        if frozen:
                            layer.freeze()
                        if locked:
                            layer.lock()
                        logger.debug(f"Layer state applied to '{layer_name}'")
                    else:
                        logger.warning(f"Layer '{layer_name}' not found for state management")
                except Exception as e:
                    logger.warning(f"Could not apply layer state: {e}")
            
            return True
            
        except (ValidationError, EntityProcessingError) as e:
            logger.error(f"Validation error in layer state: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing layer state: {e}")
            return False

class AttributeProcessor(EntityProcessor):
    """Processor for attribute definitions and insertions."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            attr_type = entity_data.get("attribute_type", "definition")
            
            if attr_type == "definition":
                return self._process_attribute_definition(entity_data, target, dxf_attribs)
            elif attr_type == "value":
                return self._process_attribute_value(entity_data, target, dxf_attribs)
            else:
                logger.warning(f"Unknown attribute type: {attr_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing attribute: {e}")
            return False
    
    def _process_attribute_definition(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process attribute definition."""
        required_fields = ["tag", "position"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Attribute definition missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["position"])
        
        tag = entity_data["tag"]
        position = CoordinateConverter.safe_tuple_float(entity_data["position"])
        prompt = entity_data.get("prompt", tag)
        default_value = entity_data.get("default_value", "")
        height = float(entity_data.get("height", 250))
        
        # Create attribute definition (simplified as text)
        attr_text = target.add_text(
            f"{tag}: {default_value}",
            dxfattribs={"height": height, **dxf_attribs}
        )
        attr_text.dxf.insert = position
        attr_text.set_align("LEFT")
        
        logger.debug(f"Attribute definition processed: {tag}")
        return True
    
    def _process_attribute_value(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process attribute value insertion."""
        required_fields = ["tag", "value", "position"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"Attribute value missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["position"])
        
        tag = entity_data["tag"]
        value = entity_data["value"]
        position = CoordinateConverter.safe_tuple_float(entity_data["position"])
        height = float(entity_data.get("height", 250))
        
        # Create attribute value as text
        attr_text = target.add_text(
            f"{tag}: {value}",
            dxfattribs={"height": height, **dxf_attribs}
        )
        attr_text.dxf.insert = position
        attr_text.set_align("LEFT")
        
        logger.debug(f"Attribute value processed: {tag}={value}")
        return True

# Phase 3D: Coordinate Systems & Transforms
class CoordinateSystemProcessor(EntityProcessor):
    """Processor for User Coordinate Systems (UCS) and transformations."""
    
    def process(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        try:
            transform_type = entity_data.get("transform_type", "translate")
            
            if transform_type == "translate":
                return self._process_translation(entity_data, target, dxf_attribs)
            elif transform_type == "rotate":
                return self._process_rotation(entity_data, target, dxf_attribs)
            elif transform_type == "scale":
                return self._process_scaling(entity_data, target, dxf_attribs)
            elif transform_type == "ucs":
                return self._process_ucs_definition(entity_data, target, dxf_attribs)
            else:
                logger.warning(f"Unknown transform type: {transform_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing coordinate system: {e}")
            return False
    
    def _process_translation(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process translation transformation."""
        if "offset" not in entity_data:
            raise EntityProcessingError("Translation missing required 'offset' field")
        
        GeometryValidator.validate_point(entity_data["offset"])
        offset = CoordinateConverter.safe_tuple_float(entity_data["offset"])
        
        # Create visual representation of translation (arrow)
        start_point = entity_data.get("base_point", [0, 0])
        GeometryValidator.validate_point(start_point)
        start = CoordinateConverter.safe_tuple_float(start_point)
        end = (start[0] + offset[0], start[1] + offset[1])
        
        # Draw translation vector
        target.add_line(start, end, dxfattribs=dxf_attribs)
        
        # Add arrowhead (simplified)
        arrow_size = 50
        arrow_angle = 0.5  # radians
        import math
        
        dx = offset[0]
        dy = offset[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            angle = math.atan2(dy, dx)
            arrow1 = (
                end[0] - arrow_size * math.cos(angle - arrow_angle),
                end[1] - arrow_size * math.sin(angle - arrow_angle)
            )
            arrow2 = (
                end[0] - arrow_size * math.cos(angle + arrow_angle),
                end[1] - arrow_size * math.sin(angle + arrow_angle)
            )
            
            target.add_line(end, arrow1, dxfattribs=dxf_attribs)
            target.add_line(end, arrow2, dxfattribs=dxf_attribs)
        
        logger.debug(f"Translation processed: offset {offset}")
        return True
    
    def _process_ucs_definition(self, entity_data: Dict[str, Any], target: Any, dxf_attribs: Dict[str, Any]) -> bool:
        """Process UCS definition."""
        required_fields = ["origin", "x_axis", "y_axis"]
        for field in required_fields:
            if field not in entity_data:
                raise EntityProcessingError(f"UCS definition missing required '{field}' field")
        
        GeometryValidator.validate_point(entity_data["origin"])
        GeometryValidator.validate_point(entity_data["x_axis"])
        GeometryValidator.validate_point(entity_data["y_axis"])
        
        origin = CoordinateConverter.safe_tuple_float(entity_data["origin"])
        x_axis = CoordinateConverter.safe_tuple_float(entity_data["x_axis"])
        y_axis = CoordinateConverter.safe_tuple_float(entity_data["y_axis"])
        
        # Draw UCS axes
        axis_length = 100
        x_end = (origin[0] + x_axis[0] * axis_length, origin[1] + x_axis[1] * axis_length)
        y_end = (origin[0] + y_axis[0] * axis_length, origin[1] + y_axis[1] * axis_length)
        
        # X-axis (red)
        x_attribs = {**dxf_attribs, "color": 1}  # Red
        target.add_line(origin, x_end, dxfattribs=x_attribs)
        
        # Y-axis (green)
        y_attribs = {**dxf_attribs, "color": 3}  # Green
        target.add_line(origin, y_end, dxfattribs=y_attribs)
        
        # Add labels
        target.add_text("X", dxfattribs={"height": 50, **x_attribs}).dxf.insert = x_end
        target.add_text("Y", dxfattribs={"height": 50, **y_attribs}).dxf.insert = y_end
        
        logger.debug(f"UCS defined at origin {origin}")
        return True

# Entity Factory
class EntityFactory:
    """Factory for creating entity processors."""
    
    _processors = {
        # Basic geometry (Step 2)
        "rectangle": RectangleProcessor(),
        "circle": CircleProcessor(),
        "line": LineProcessor(),
        "text": TextProcessor(),
        "arc": ArcProcessor(),
        
        # Phase 3A: Advanced geometry
        "spline": SplineProcessor(),
        "polyline": PolylineProcessor(),
        "ellipse": EllipseProcessor(),
        "solid": SolidProcessor(),
        "mesh": MeshProcessor(),
        
        # Phase 3B: Annotations
        "dimension": DimensionProcessor(),
        "leader": LeaderProcessor(),
        "hatch": HatchProcessor(),
        "mtext": MTextProcessor(),
        
        # Phase 3C: Professional features
        "viewport": ViewportProcessor(),
        "linetype": LinetypeProcessor(),
        "layer_state": LayerStateProcessor(),
        "attribute": AttributeProcessor(),
        
        # Phase 3D: Coordinate systems & transforms
        "coordinate_system": CoordinateSystemProcessor(),
    }
    
    @classmethod
    def get_processor(cls, entity_type: str) -> Optional[EntityProcessor]:
        """Get processor for the specified entity type."""
        return cls._processors.get(entity_type)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported entity types."""
        return list(cls._processors.keys())

# Main DXF Generator Class
class DXFGenerator:
    """Main class for generating DXF files from instructions."""
    
    def __init__(self):
        self.doc = None
        self.msp = None
        self.summary = None
        
    def generate_from_instructions(self, data: Dict[str, Any]) -> Tuple[str, ProcessingSummary]:
        """
        Generate a DXF file from structured instructions with detailed summary.
        
        Args:
            data: Dictionary containing DXF generation instructions
            
        Returns:
            Tuple[str, ProcessingSummary]: Path to DXF file and processing summary
            
        Raises:
            DXFGenerationError: If DXF generation fails
        """
        # Initialize processing summary
        self.summary = ProcessingSummary()
        
        try:
            # Use temp file manager for better cleanup
            filepath = temp_file_manager.create_temp_file(".dxf")
            
            logger.info(f"Starting DXF generation: {filepath}")
            
            # Initialize DXF document
            self._initialize_document()
            
            # Process layers, blocks, and figures with summary tracking
            self._process_layers(data.get("layers", []))
            self._process_blocks(data.get("blocks", []))
            self._process_figures(data.get("figures", []))
            
            # Add layout elements
            self._add_layout_elements()
            
            # Save document
            self.doc.saveas(filepath)
            file_size = os.path.getsize(filepath)
            
            # Finalize summary
            self.summary.finalize(filepath, file_size)
            
            logger.info(f"DXF generation completed: {self.summary.successful_entities}/{self.summary.total_entities} entities processed")
            
            return filepath, self.summary
            
        except Exception as e:
            if self.summary:
                self.summary.errors.append(f"Generation failed: {str(e)}")
                self.summary.end_time = datetime.now()
            logger.error(f"DXF generation failed: {e}", exc_info=True)
            raise DXFGenerationError(f"Failed to generate DXF: {e}") from e
    
    def _initialize_document(self):
        """Initialize the DXF document."""
        self.doc = ezdxf.new(dxfversion="R2010")
        self.doc.header['$INSUNITS'] = 4
        self.msp = self.doc.modelspace()
        logger.debug("DXF document initialized")
    
    def _process_layers(self, layers: List[Dict[str, Any]]):
        """Process layer definitions."""
        for layer in layers:
            try:
                self.doc.layers.new(
                    name=layer["name"], 
                    dxfattribs={"color": layer.get("color", 7)}
                )
                logger.debug(f"Layer processed: {layer['name']}")
            except Exception as e:
                logger.error(f"Error processing layer '{layer.get('name', '')}': {e}")
    
    def _process_blocks(self, blocks: List[Dict[str, Any]]):
        """Process block definitions."""
        for block in blocks:
            try:
                block_def = self.doc.blocks.new(name=block["name"])
                logger.debug(f"Processing block: {block['name']}")
                
                for entity in block.get("entities", []):
                    self._process_entity(entity, block_def)
                    
            except Exception as e:
                logger.error(f"Error processing block '{block.get('name', '')}': {e}")
    
    def _process_figures(self, figures: List[Dict[str, Any]]):
        """Process figure definitions."""
        for figure in figures:
            try:
                self._process_entity(figure, self.msp)
            except Exception as e:
                logger.error(f"Error processing figure: {e}")
    
    def _process_entity(self, entity_data: Dict[str, Any], target: Any):
        """Process a single entity using the factory pattern with summary tracking."""
        entity_type = entity_data.get("type")
        layer = entity_data.get("layer", "default")
        
        if not entity_type:
            message = "Entity missing type field"
            logger.warning(message)
            if self.summary:
                self.summary.add_entity_result("unknown", layer, False, message)
            return
        
        processor = EntityFactory.get_processor(entity_type)
        if not processor:
            message = f"Unsupported entity type: {entity_type}"
            logger.warning(message)
            if self.summary:
                self.summary.add_entity_result(entity_type, layer, False, message)
            return
        
        # Prepare DXF attributes
        dxf_attribs = {
            "layer": layer,
            "color": int(entity_data.get("color", 7))
        }
        
        # Process the entity with summary tracking
        try:
            success = processor.process(entity_data, target, dxf_attribs)
            if self.summary:
                if success:
                    self.summary.add_entity_result(entity_type, layer, True)
                else:
                    self.summary.add_entity_result(entity_type, layer, False, "Processing failed")
        except Exception as e:
            error_msg = f"Exception during processing: {str(e)}"
            logger.error(f"Error processing {entity_type}: {e}")
            if self.summary:
                self.summary.add_entity_result(entity_type, layer, False, error_msg)
    
    def _add_layout_elements(self):
        """Add standard layout elements."""
        layout = self.doc.layout()
        layout.add_line((0, 0), (210, 0), dxfattribs={"color": 6})
        layout_text = layout.add_text("Generated Drawing", dxfattribs={"height": 10})
        layout_text.dxf.insert = (10, 20)

# Main function remains the same but uses the new architecture
def handle_template_request(req: Any, res: Any) -> Any:
    """
    Handle template-based kitchen generation for Agent Zero.
    
    Args:
        req: Request object from Appwrite
        res: Response object from Appwrite
        
    Returns:
        Binary DXF file or JSON response
    """
    if KitchenTemplateEngine is None:
        return res.json({"error": "Template engine not available"}, 503)
    
    try:
        body = json.loads(req.body_raw)
        logger.info("Template-based DXF generation request received")
        logger.debug(f"Template request: {json.dumps(body, indent=2)}")
        
        # Validate template request
        try:
            validated_request = TemplateRequestModel(**body)
            logger.info("Template request validation successful")
        except PydanticValidationError as ve:
            logger.warning(f"Template validation failed: {ve.errors()}")
            return res.json({"error": f"Invalid template request format: {ve.errors()}"}, 400)
        
        # Initialize template engine
        engine = KitchenTemplateEngine()
        
        # Get and customize template
        try:
            base_template = engine.get_template(validated_request.template_name)
            customized_template = engine.customize_template(base_template, validated_request.customization)
            
            # Validate the customized template
            validation_result = engine.validate_kitchen_json(customized_template["dxf_template"])
            if not validation_result["valid"]:
                logger.warning(f"Template validation issues: {validation_result['errors']}")
                return res.json({
                    "error": "Template validation failed",
                    "validation_errors": validation_result["errors"]
                }, 400)
            
        except ValueError as e:
            logger.warning(f"Template not found: {e}")
            available_templates = engine.list_templates()
            return res.json({
                "error": str(e),
                "available_templates": available_templates
            }, 400)
        
        # Prepare DXF instructions
        dxf_instructions = customized_template["dxf_template"].copy()
        
        # Add client info if provided
        if validated_request.client_info:
            dxf_instructions["client_info"] = validated_request.client_info
        
        # Generate DXF using existing engine
        generator = DXFGenerator()
        dxf_path, processing_summary = generator.generate_from_instructions(dxf_instructions)
        
        # Add template info to summary
        processing_summary.template_info = {
            "template_name": validated_request.template_name,
            "customization_applied": validated_request.customization,
            "template_description": base_template.get("description", ""),
            "validation_warnings": validation_result.get("warnings", [])
        }
        
        # Check if client wants detailed summary instead of file
        if validated_request.return_summary:
            temp_file_manager.cleanup_file(dxf_path)
            summary_dict = processing_summary.to_dict()
            summary_dict["template_info"] = processing_summary.template_info
            return res.json(summary_dict, 200)
        
        # Return DXF file with template processing info in headers
        file_size = os.path.getsize(dxf_path)
        
        try:
            with open(dxf_path, "rb") as f:
                file_content = f.read()
            
            temp_file_manager.cleanup_file(dxf_path)
            
            headers = {
                "Content-Type": "application/dxf",
                "Content-Disposition": f'attachment; filename="kitchen_{validated_request.template_name}_{uuid.uuid4().hex[:8]}.dxf"',
                "X-Processing-Summary": json.dumps(processing_summary.to_dict()),
                "X-Template-Info": json.dumps(processing_summary.template_info)
            }
            
            logger.info(f"Template DXF generated successfully: {file_size} bytes using '{validated_request.template_name}' template")
            return res.send(file_content, 200, headers)
            
        except Exception as e:
            temp_file_manager.cleanup_file(dxf_path)
            raise e
            
    except Exception as e:
        logger.error(f"Template processing error: {e}", exc_info=True)
        return res.json({"error": f"Template processing failed: {str(e)}"}, 500)

def handle_legacy_semantic_request(req: Any, res: Any) -> Any:
    """
    Handle legacy semantic requests by converting to template-based approach.
    
    Args:
        req: Request object from Appwrite
        res: Response object from Appwrite
        
    Returns:
        Binary DXF file or JSON response
    """
    if KitchenTemplateEngine is None:
        return res.json({"error": "Template engine not available"}, 503)
    
    try:
        body = json.loads(req.body_raw)
        logger.info("Legacy semantic request received - converting to template-based")
        
        # Validate legacy request
        try:
            validated_request = LegacySemanticRequestModel(**body)
        except PydanticValidationError as ve:
            logger.warning(f"Legacy semantic validation failed: {ve.errors()}")
            return res.json({"error": f"Invalid request format: {ve.errors()}"}, 400)
        
        # Initialize template engine
        engine = KitchenTemplateEngine()
        
        # Translate German terms if present
        description = engine.translate_german_terms(validated_request.description)
        
        # Simple rule-based template selection (replaces semantic parsing)
        template_name = "modern_l_shaped"  # Default
        customization = {}
        
        # Extract dimensions using simple pattern matching
        import re
        dim_match = re.search(r'(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)', description.lower())
        if dim_match:
            width = float(dim_match.group(1)) * 1000  # Convert to mm
            height = float(dim_match.group(2)) * 1000
            customization["dimensions"] = [int(width), int(height)]
            
            # Select template based on size
            area = width * height / 1000000  # m²
            if area < 8:
                template_name = "compact_galley"
            elif area > 20:
                template_name = "u_shaped_luxury"
        
        # Extract style
        if "traditional" in description.lower() or "country" in description.lower():
            customization["style"] = "traditional"
            if template_name == "modern_l_shaped":
                template_name = "traditional_country"
        elif "open" in description.lower():
            template_name = "open_plan_modern"
        
        # Extract appliances
        appliances = []
        if "island" in description.lower():
            appliances.append("island")
        if "dishwasher" in description.lower():
            appliances.append("dishwasher")
        if appliances:
            customization["appliances"] = appliances
        
        # Convert to template request
        template_request = {
            "template_name": template_name,
            "customization": customization,
            "return_summary": validated_request.return_summary,
            "client_info": validated_request.client_info or {"legacy_semantic": True}
        }
        
        # Create mock request object for template handler
        class MockRequest:
            def __init__(self, body_data):
                self.body_raw = json.dumps(body_data)
        
        mock_req = MockRequest(template_request)
        
        # Process using template handler
        logger.info(f"Converted legacy semantic to template: {template_name} with customization: {customization}")
        return handle_template_request(mock_req, res)
        
    except Exception as e:
        logger.error(f"Legacy semantic processing error: {e}", exc_info=True)
        return res.json({"error": f"Legacy semantic processing failed: {str(e)}"}, 500)

def main(context: Any) -> Any:
    """
    Main Appwrite function handler supporting multiple generation modes.
    
    Routes:
    - Default: Traditional DXF generation from structured JSON
    - Template-based: Agent Zero kitchen template generation
    - Legacy: Backward compatibility for semantic requests
    
    Args:
        context: Appwrite function context containing request and response objects
        
    Returns:
        Binary DXF file or JSON error response
    """
    req = context.req
    res = context.res

    # Simple routing based on request content
    try:
        body = json.loads(req.body_raw)
        
        # Check for template-based request (has 'template_name' field)
        if "template_name" in body and isinstance(body["template_name"], str):
            logger.info("Routing to template-based generation")
            return handle_template_request(req, res)
        
        # Check for legacy semantic request (has 'description' field)
        elif "description" in body and isinstance(body["description"], str):
            logger.info("Routing to legacy semantic endpoint")
            return handle_legacy_semantic_request(req, res)
        
        # Traditional DXF generation
        else:
            logger.info("Routing to traditional DXF generation")
            return handle_traditional_dxf_request(req, res, body)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {e}")
        return res.json({"error": "Invalid JSON format"}, 400)
    except Exception as e:
        logger.error(f"Unexpected routing error: {e}", exc_info=True)
        return res.json({"error": "Internal server error"}, 500)

def handle_traditional_dxf_request(req: Any, res: Any, body: Dict[str, Any]) -> Any:
    """
    Handle traditional DXF generation from structured JSON.
    
    Args:
        req: Request object
        res: Response object  
        body: Parsed JSON body
        
    Returns:
        Binary DXF file or JSON response
    """
    try:
        logger.info("Traditional DXF generation request received")
        logger.debug(f"Request body: {json.dumps(body, indent=2)}")

        # Step 4: Apply request validation middleware
        validation_error, processed_body = RequestValidator.validate_and_preprocess(body)
        if validation_error:
            logger.warning(f"Request validation failed: {validation_error}")
            return res.json({"error": validation_error}, 400)

        # Validate request using Pydantic model
        try:
            validated_data = DXFRequestModel(**processed_body)
            logger.info("Request validation successful")
        except PydanticValidationError as ve:
            logger.warning(f"Pydantic validation failed: {ve.errors()}")
            return res.json({"error": f"Invalid request format: {ve.errors()}"}, 400)

        # Generate DXF using the enhanced class-based architecture
        generator = DXFGenerator()
        dxf_path, processing_summary = generator.generate_from_instructions(validated_data.dict())

        # Check if client wants detailed summary instead of file
        request_summary = body.get("return_summary", False)
        if request_summary:
            # Return processing summary as JSON
            temp_file_manager.cleanup_file(dxf_path)  # Clean up since we're not returning the file
            return res.json(processing_summary.to_dict(), 200)

        # Check file size for streaming decision
        file_size = os.path.getsize(dxf_path)
        use_streaming = file_size > 1024 * 1024  # Stream files larger than 1MB
        
        try:
            if use_streaming:
                # Implement streaming for large files
                logger.info(f"Streaming large DXF file: {os.path.basename(dxf_path)} ({file_size} bytes)")
                
                def generate_file_chunks():
                    try:
                        with open(dxf_path, "rb") as f:
                            while True:
                                chunk = f.read(8192)  # 8KB chunks
                                if not chunk:
                                    break
                                yield chunk
                    finally:
                        # Cleanup after streaming
                        temp_file_manager.cleanup_file(dxf_path)
                
                # Return streaming response
                headers = {
                    "Content-Type": "application/dxf",
                    "Content-Disposition": f'attachment; filename="{os.path.basename(dxf_path)}"',
                    "Content-Length": str(file_size),
                    "X-Processing-Summary": json.dumps(processing_summary.to_dict())
                }
                return res.send(generate_file_chunks(), 200, headers)
                
            else:
                # Regular response for smaller files
                with open(dxf_path, "rb") as f:
                    file_content = f.read()
                
                # Cleanup temp file
                temp_file_manager.cleanup_file(dxf_path)
                
                headers = {
                    "Content-Type": "application/dxf",
                    "Content-Disposition": f'attachment; filename="{os.path.basename(dxf_path)}"',
                    "X-Processing-Summary": json.dumps(processing_summary.to_dict())
                }
                
                logger.info(f"DXF file returned successfully: {os.path.basename(dxf_path)} ({file_size} bytes)")
                return res.send(file_content, 200, headers)
                
        except Exception as e:
            # Ensure cleanup on error
            temp_file_manager.cleanup_file(dxf_path)
            raise e

    except DXFGenerationError as e:
        logger.error(f"DXF generation error: {e}")
        return res.json({"error": str(e)}, 500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return res.json({"error": "Internal server error"}, 500)

# Backwards compatibility for the test
def generate_dxf_from_instructions(data: Dict[str, Any]) -> str:
    """Backwards compatibility wrapper for tests."""
    generator = DXFGenerator()
    file_path, summary = generator.generate_from_instructions(data)
    return file_path

def safe_tuple_float(lst: List[Union[str, int, float]]) -> Tuple[float, ...]:
    """Backwards compatibility wrapper for tests."""
    return CoordinateConverter.safe_tuple_float(lst)