# 🍳 Kitchen Layout DXF Generation Examples

This document contains highly detailed examples for generating kitchen layouts using the Professional DXF Generation API. These examples serve as prompts for LLMs to generate the appropriate JSON requests.

## 📋 Instructions for LLM Usage

When using these examples with an LLM, provide the following prompt structure:

```
Using the Professional DXF Generation API, generate a JSON request for [KITCHEN_TYPE] based on the following requirements: [REQUIREMENTS]

The output must be valid JSON that can be sent directly to the DXF generation API. Include all necessary layers, precise measurements in millimeters, and appropriate entity types.

Reference the kitchen examples below for proper formatting and entity usage.
```

---

## 🏠 Example 1: Modern L-Shaped Kitchen

**Use Case**: Contemporary 3.6m × 3.0m L-shaped kitchen with island
**Target Audience**: Residential architects, kitchen designers
**Key Features**: Integrated appliances, quartz countertops, modern cabinetry

### LLM Prompt:
```
Create a modern L-shaped kitchen layout (3600mm × 3000mm) with:
- L-shaped base cabinets along two walls
- Central island (2000mm × 1000mm)
- Integrated refrigerator, dishwasher, and cooktop
- Quartz countertops with 40mm thickness
- Proper dimensions and professional annotations
- Hatching to show material differences

Output: Complete JSON for DXF generation API
```

### Expected JSON Output:
```json
{
  "layers": [
    {"name": "Walls", "color": 7},
    {"name": "Cabinets", "color": 3},
    {"name": "Countertops", "color": 6},
    {"name": "Appliances", "color": 5},
    {"name": "Dimensions", "color": 2},
    {"name": "Text", "color": 4},
    {"name": "Hatching", "color": 8}
  ],
  "figures": [
    {
      "type": "rectangle",
      "points": [[0, 0], [3600, 0], [3600, 3000], [0, 3000]],
      "layer": "Walls",
      "color": 7
    },
    {
      "type": "polyline",
      "points": [[150, 150], [1800, 150], [1800, 750], [3450, 750], [3450, 2850], [150, 2850]],
      "closed": true,
      "layer": "Cabinets"
    },
    {
      "type": "polyline",
      "points": [[150, 150], [1800, 150], [1800, 790], [3450, 790], [3450, 2850], [150, 2850]],
      "closed": true,
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[1300, 1200], [3300, 1200], [3300, 2200], [1300, 2200]],
      "layer": "Cabinets"
    },
    {
      "type": "rectangle",
      "points": [[1300, 1200], [3300, 1200], [3300, 2240], [1300, 2240]],
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[600, 150], [800, 150], [800, 750], [600, 750]],
      "layer": "Appliances"
    },
    {
      "type": "circle",
      "center": [2200, 790],
      "radius": 300,
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[150, 1400], [750, 1400], [750, 2000], [150, 2000]],
      "layer": "Appliances"
    },
    {
      "type": "hatch",
      "boundary": [[1300, 1200], [3300, 1200], [3300, 2240], [1300, 2240]],
      "pattern": "ANSI31",
      "pattern_scale": 2.0,
      "pattern_angle": 45,
      "layer": "Hatching"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [3600, 0],
      "dimline_point": [1800, -300],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [0, 3000],
      "dimline_point": [-300, 1500],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [1300, 1200],
      "end": [3300, 1200],
      "dimline_point": [2300, 1000],
      "layer": "Dimensions"
    },
    {
      "type": "text",
      "text": "MODERN L-SHAPED KITCHEN",
      "position": [1800, 2700],
      "height": 150,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "ISLAND",
      "position": [2300, 1700],
      "height": 100,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "REF",
      "position": [450, 1700],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "COOKTOP",
      "position": [2200, 500],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "DW",
      "position": [700, 450],
      "height": 60,
      "layer": "Text"
    },
    {
      "type": "leader",
      "vertices": [[2200, 790], [2500, 500], [2800, 500]],
      "text": "INDUCTION COOKTOP",
      "text_height": 80,
      "layer": "Dimensions"
    }
  ]
}
```

---

## 🏢 Example 2: Commercial Galley Kitchen

**Use Case**: Restaurant/commercial galley kitchen 6.0m × 2.4m
**Target Audience**: Restaurant designers, commercial architects
**Key Features**: Stainless steel equipment, prep stations, dishwashing area

### LLM Prompt:
```
Design a commercial galley kitchen (6000mm × 2400mm) with:
- Parallel work stations on both sides
- Commercial-grade stainless steel equipment
- Prep stations with cutting boards
- Dishwashing area with commercial dishwasher
- Storage areas and cold storage
- Proper clearances and safety zones
- Health department compliant layout

Output: Complete JSON for DXF generation API
```

### Expected JSON Output:
```json
{
  "layers": [
    {"name": "Structure", "color": 7},
    {"name": "Equipment", "color": 5},
    {"name": "Prep_Areas", "color": 3},
    {"name": "Storage", "color": 6},
    {"name": "Safety_Zones", "color": 1},
    {"name": "Dimensions", "color": 2},
    {"name": "Labels", "color": 4}
  ],
  "figures": [
    {
      "type": "rectangle",
      "points": [[0, 0], [6000, 0], [6000, 2400], [0, 2400]],
      "layer": "Structure"
    },
    {
      "type": "rectangle",
      "points": [[100, 100], [2800, 100], [2800, 700], [100, 700]],
      "layer": "Equipment"
    },
    {
      "type": "rectangle",
      "points": [[100, 1700], [2800, 1700], [2800, 2300], [100, 2300]],
      "layer": "Equipment"
    },
    {
      "type": "rectangle",
      "points": [[3000, 100], [5900, 100], [5900, 700], [3000, 700]],
      "layer": "Prep_Areas"
    },
    {
      "type": "rectangle",
      "points": [[3000, 1700], [5900, 1700], [5900, 2300], [3000, 2300]],
      "layer": "Storage"
    },
    {
      "type": "rectangle",
      "points": [[500, 100], [1000, 100], [1000, 700], [500, 700]],
      "layer": "Equipment"
    },
    {
      "type": "rectangle",
      "points": [[1200, 100], [1800, 100], [1800, 700], [1200, 700]],
      "layer": "Equipment"
    },
    {
      "type": "rectangle",
      "points": [[2000, 100], [2600, 100], [2600, 700], [2000, 700]],
      "layer": "Equipment"
    },
    {
      "type": "rectangle",
      "points": [[100, 1700], [800, 1700], [800, 2300], [100, 2300]],
      "layer": "Equipment"
    },
    {
      "type": "circle",
      "center": [3000, 1200],
      "radius": 600,
      "layer": "Safety_Zones"
    },
    {
      "type": "hatch",
      "boundary": [[500, 100], [1000, 100], [1000, 700], [500, 700]],
      "pattern": "ANSI32",
      "pattern_scale": 1.0,
      "layer": "Equipment"
    },
    {
      "type": "hatch",
      "boundary": [[1200, 100], [1800, 100], [1800, 700], [1200, 700]],
      "pattern": "ANSI33",
      "pattern_scale": 1.0,
      "layer": "Equipment"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [6000, 0],
      "dimline_point": [3000, -300],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [0, 2400],
      "dimline_point": [-300, 1200],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [100, 700],
      "end": [100, 1700],
      "dimline_point": [-100, 1200],
      "text_override": "1000 CLR",
      "layer": "Dimensions"
    },
    {
      "type": "text",
      "text": "COMMERCIAL GALLEY KITCHEN",
      "position": [3000, 50],
      "height": 120,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "GRILL",
      "position": [750, 400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "FRYER",
      "position": [1500, 400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "RANGE",
      "position": [2300, 400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "DISH",
      "position": [450, 2000],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "PREP STATION",
      "position": [4450, 400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "COLD STORAGE",
      "position": [4450, 2000],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "mtext",
      "text": "SAFETY ZONE\\P1200mm MIN\\PCLEARANCE",
      "position": [3000, 1800],
      "width": 1000,
      "height": 60,
      "alignment": "CENTER",
      "layer": "Labels"
    }
  ]
}
```

---

## 🏡 Example 3: Compact Studio Apartment Kitchen

**Use Case**: Small studio apartment kitchen 2.4m × 1.8m
**Target Audience**: Interior designers, small space specialists
**Key Features**: Space-saving design, multi-functional elements, European appliances

### LLM Prompt:
```
Create a compact studio kitchen (2400mm × 1800mm) with:
- Single-wall layout with upper and lower cabinets
- Compact European appliances (slim dishwasher, combo oven/microwave)
- Fold-down table/breakfast bar
- Maximum storage efficiency
- Apartment-size refrigerator
- Under-cabinet lighting zones
- Modern minimalist design

Output: Complete JSON for DXF generation API
```

### Expected JSON Output:
```json
{
  "layers": [
    {"name": "Walls", "color": 7},
    {"name": "Base_Cabinets", "color": 3},
    {"name": "Upper_Cabinets", "color": 6},
    {"name": "Appliances", "color": 5},
    {"name": "Countertop", "color": 8},
    {"name": "Dimensions", "color": 2},
    {"name": "Text", "color": 4},
    {"name": "Features", "color": 1}
  ],
  "figures": [
    {
      "type": "rectangle",
      "points": [[0, 0], [2400, 0], [2400, 1800], [0, 1800]],
      "layer": "Walls"
    },
    {
      "type": "rectangle",
      "points": [[100, 100], [2300, 100], [2300, 650], [100, 650]],
      "layer": "Base_Cabinets"
    },
    {
      "type": "rectangle",
      "points": [[100, 100], [2300, 100], [2300, 690], [100, 690]],
      "layer": "Countertop"
    },
    {
      "type": "rectangle",
      "points": [[100, 1200], [2300, 1200], [2300, 1700], [100, 1700]],
      "layer": "Upper_Cabinets"
    },
    {
      "type": "rectangle",
      "points": [[100, 100], [700, 100], [700, 650], [100, 650]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[800, 100], [1200, 100], [1200, 650], [800, 650]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1300, 100], [1700, 100], [1700, 650], [1300, 650]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1800, 100], [2300, 100], [2300, 650], [1800, 650]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1300, 1200], [1700, 1200], [1700, 1700], [1300, 1700]],
      "layer": "Appliances"
    },
    {
      "type": "polyline",
      "points": [[2300, 690], [2800, 690], [2800, 890], [2300, 890]],
      "closed": false,
      "layer": "Features"
    },
    {
      "type": "line",
      "start": [2300, 790],
      "end": [2800, 790],
      "layer": "Features"
    },
    {
      "type": "line",
      "start": [100, 1150],
      "end": [2300, 1150],
      "layer": "Features"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [2400, 0],
      "dimline_point": [1200, -200],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [0, 1800],
      "dimline_point": [-200, 900],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [100, 100],
      "end": [2300, 100],
      "dimline_point": [1200, 800],
      "layer": "Dimensions"
    },
    {
      "type": "text",
      "text": "COMPACT STUDIO KITCHEN",
      "position": [1200, 1650],
      "height": 100,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "REF",
      "position": [400, 375],
      "height": 60,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "SINK",
      "position": [1000, 375],
      "height": 60,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "COOKTOP",
      "position": [1500, 375],
      "height": 60,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "DW",
      "position": [2050, 375],
      "height": 50,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "MICRO/OVEN",
      "position": [1500, 1450],
      "height": 50,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "FOLD-DOWN TABLE",
      "position": [2900, 790],
      "height": 60,
      "layer": "Text"
    },
    {
      "type": "leader",
      "vertices": [[2150, 1150], [2150, 1000], [2500, 1000]],
      "text": "UNDER-CABINET LED",
      "text_height": 50,
      "layer": "Features"
    }
  ]
}
```

---

## 🏰 Example 4: Traditional Farmhouse Kitchen

**Use Case**: Large traditional farmhouse kitchen 4.8m × 3.6m
**Target Audience**: Custom home builders, traditional style specialists
**Key Features**: Farmhouse sink, large island, traditional cabinetry, pantry

### LLM Prompt:
```
Design a traditional farmhouse kitchen (4800mm × 3600mm) with:
- Large central island with seating area
- Farmhouse apron-front sink
- Traditional raised-panel cabinetry
- Walk-in pantry corner
- Professional-grade range with hood
- Built-in breakfast nook
- Traditional proportions and details
- Warm wood tones and classic hardware

Output: Complete JSON for DXF generation API
```

### Expected JSON Output:
```json
{
  "layers": [
    {"name": "Walls", "color": 7},
    {"name": "Cabinets", "color": 3},
    {"name": "Island", "color": 6},
    {"name": "Appliances", "color": 5},
    {"name": "Countertops", "color": 8},
    {"name": "Pantry", "color": 4},
    {"name": "Seating", "color": 2},
    {"name": "Dimensions", "color": 2},
    {"name": "Text", "color": 4}
  ],
  "figures": [
    {
      "type": "rectangle",
      "points": [[0, 0], [4800, 0], [4800, 3600], [0, 3600]],
      "layer": "Walls"
    },
    {
      "type": "polyline",
      "points": [[150, 150], [3000, 150], [3000, 750], [4650, 750], [4650, 3450], [150, 3450]],
      "closed": true,
      "layer": "Cabinets"
    },
    {
      "type": "polyline",
      "points": [[150, 150], [3000, 150], [3000, 790], [4650, 790], [4650, 3450], [150, 3450]],
      "closed": true,
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[1600, 1800], [3400, 1800], [3400, 2800], [1600, 2800]],
      "layer": "Island"
    },
    {
      "type": "rectangle",
      "points": [[1600, 1800], [3400, 1800], [3400, 2840], [1600, 2840]],
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[3000, 150], [4650, 150], [4650, 750], [3000, 750]],
      "layer": "Pantry"
    },
    {
      "type": "rectangle",
      "points": [[1800, 150], [2400, 150], [2400, 750], [1800, 750]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1000, 150], [1600, 150], [1600, 750], [1000, 750]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[150, 2400], [750, 2400], [750, 3000], [150, 3000]],
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1600, 2840], [3400, 2840], [3400, 3240], [1600, 3240]],
      "layer": "Seating"
    },
    {
      "type": "circle",
      "center": [2100, 790],
      "radius": 400,
      "layer": "Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1800, 0], [2400, 0], [2400, 150], [1800, 150]],
      "layer": "Appliances"
    },
    {
      "type": "polyline",
      "points": [[1600, 3240], [1600, 3500], [3400, 3500], [3400, 3240]],
      "closed": false,
      "layer": "Seating"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [4800, 0],
      "dimline_point": [2400, -300],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [0, 3600],
      "dimline_point": [-300, 1800],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [1600, 1800],
      "end": [3400, 1800],
      "dimline_point": [2500, 1600],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [1600, 1800],
      "end": [1600, 2800],
      "dimline_point": [1400, 2300],
      "layer": "Dimensions"
    },
    {
      "type": "text",
      "text": "TRADITIONAL FARMHOUSE KITCHEN",
      "position": [2400, 3300],
      "height": 150,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "LARGE ISLAND",
      "position": [2500, 2300],
      "height": 100,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "PANTRY",
      "position": [3825, 450],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "FARMHOUSE SINK",
      "position": [1300, 450],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "PROFESSIONAL RANGE",
      "position": [2100, 450],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "REF",
      "position": [450, 2700],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "text",
      "text": "BREAKFAST NOOK",
      "position": [2500, 3400],
      "height": 80,
      "layer": "Text"
    },
    {
      "type": "leader",
      "vertices": [[2100, 790], [2600, 1200], [3000, 1200]],
      "text": "Ø800 COOKTOP",
      "text_height": 70,
      "layer": "Dimensions"
    },
    {
      "type": "leader",
      "vertices": [[2100, 150], [2600, 600], [3000, 600]],
      "text": "RANGE HOOD",
      "text_height": 70,
      "layer": "Dimensions"
    }
  ]
}
```

---

## 🎯 Example 5: Professional Chef's Kitchen

**Use Case**: High-end residential chef's kitchen 5.4m × 4.2m
**Target Audience**: Luxury home designers, culinary enthusiasts
**Key Features**: Dual islands, professional appliances, multiple prep zones

### LLM Prompt:
```
Create a professional chef's kitchen (5400mm × 4200mm) with:
- Dual islands (main prep island and secondary baking island)
- Professional-grade appliances (dual ovens, 48" range, built-in refrigeration)
- Multiple prep zones with specialized sinks
- Walk-in pantry and wine storage
- Butler's pantry connection
- Pot filler and multiple electrical outlets
- Commercial-grade ventilation

Output: Complete JSON for DXF generation API
```

### Expected JSON Output:
```json
{
  "layers": [
    {"name": "Structure", "color": 7},
    {"name": "Perimeter_Cabinets", "color": 3},
    {"name": "Main_Island", "color": 6},
    {"name": "Baking_Island", "color": 8},
    {"name": "Pro_Appliances", "color": 5},
    {"name": "Countertops", "color": 4},
    {"name": "Storage", "color": 2},
    {"name": "Dimensions", "color": 2},
    {"name": "Labels", "color": 1}
  ],
  "figures": [
    {
      "type": "rectangle",
      "points": [[0, 0], [5400, 0], [5400, 4200], [0, 4200]],
      "layer": "Structure"
    },
    {
      "type": "polyline",
      "points": [[150, 150], [3600, 150], [3600, 750], [5250, 750], [5250, 4050], [150, 4050]],
      "closed": true,
      "layer": "Perimeter_Cabinets"
    },
    {
      "type": "polyline",
      "points": [[150, 150], [3600, 150], [3600, 790], [5250, 790], [5250, 4050], [150, 4050]],
      "closed": true,
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[1200, 1800], [3600, 1800], [3600, 3000], [1200, 3000]],
      "layer": "Main_Island"
    },
    {
      "type": "rectangle",
      "points": [[1200, 1800], [3600, 1800], [3600, 3040], [1200, 3040]],
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[4200, 1500], [5100, 1500], [5100, 2400], [4200, 2400]],
      "layer": "Baking_Island"
    },
    {
      "type": "rectangle",
      "points": [[4200, 1500], [5100, 1500], [5100, 2440], [4200, 2440]],
      "layer": "Countertops"
    },
    {
      "type": "rectangle",
      "points": [[3600, 150], [5250, 150], [5250, 750], [3600, 750]],
      "layer": "Storage"
    },
    {
      "type": "rectangle",
      "points": [[1800, 150], [3000, 150], [3000, 750], [1800, 750]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[150, 150], [900, 150], [900, 750], [150, 750]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1000, 150], [1600, 150], [1600, 750], [1000, 750]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[150, 2400], [750, 2400], [750, 3000], [150, 3000]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[150, 3200], [750, 3200], [750, 3800], [150, 3800]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[4650, 750], [5250, 750], [5250, 1350], [4650, 1350]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "circle",
      "center": [2400, 790],
      "radius": 600,
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1800, 0], [3000, 0], [3000, 150], [1800, 150]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[1500, 1800], [2100, 1800], [2100, 3000], [1500, 3000]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[2700, 1800], [3300, 1800], [3300, 3000], [2700, 3000]],
      "layer": "Pro_Appliances"
    },
    {
      "type": "circle",
      "center": [4650, 1950],
      "radius": 300,
      "layer": "Pro_Appliances"
    },
    {
      "type": "rectangle",
      "points": [[0, 1800], [150, 1800], [150, 2400], [0, 2400]],
      "layer": "Structure"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [5400, 0],
      "dimline_point": [2700, -300],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [0, 0],
      "end": [0, 4200],
      "dimline_point": [-300, 2100],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [1200, 1800],
      "end": [3600, 1800],
      "dimline_point": [2400, 1600],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [1200, 1800],
      "end": [1200, 3000],
      "dimline_point": [1000, 2400],
      "layer": "Dimensions"
    },
    {
      "type": "dimension",
      "dimension_type": "linear",
      "start": [4200, 1500],
      "end": [5100, 1500],
      "dimline_point": [4650, 1300],
      "layer": "Dimensions"
    },
    {
      "type": "text",
      "text": "PROFESSIONAL CHEF'S KITCHEN",
      "position": [2700, 3900],
      "height": 150,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "MAIN PREP ISLAND",
      "position": [2400, 2400],
      "height": 100,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "BAKING ISLAND",
      "position": [4650, 1950],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "WALK-IN PANTRY",
      "position": [4425, 450],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "48\" RANGE",
      "position": [2400, 450],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "DUAL OVENS",
      "position": [525, 450],
      "height": 70,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "PREP SINK",
      "position": [1300, 450],
      "height": 70,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "WINE FRIDGE",
      "position": [450, 2700],
      "height": 70,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "FREEZER",
      "position": [450, 3500],
      "height": 70,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "BUILT-IN REF",
      "position": [4950, 1050],
      "height": 70,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "MAIN SINK",
      "position": [1800, 2400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "BAR SINK",
      "position": [3000, 2400],
      "height": 80,
      "layer": "Labels"
    },
    {
      "type": "text",
      "text": "BUTLER'S PANTRY",
      "position": [75, 2100],
      "height": 60,
      "layer": "Labels"
    },
    {
      "type": "leader",
      "vertices": [[2400, 790], [3000, 1200], [3600, 1200]],
      "text": "Ø1200 COOKTOP WITH GRILL",
      "text_height": 70,
      "layer": "Dimensions"
    },
    {
      "type": "leader",
      "vertices": [[2400, 150], [3000, 600], [3600, 600]],
      "text": "COMMERCIAL HOOD",
      "text_height": 70,
      "layer": "Dimensions"
    },
    {
      "type": "leader",
      "vertices": [[4650, 1950], [5200, 1950], [5400, 1950]],
      "text": "MIXER LIFT",
      "text_height": 60,
      "layer": "Dimensions"
    }
  ]
}
```

---

## 📚 Usage Guidelines for LLMs

### Input Format Requirements:
1. **Measurements**: Always use millimeters (mm) as the unit
2. **Coordinates**: Use [x, y] format for 2D points, [x, y, z] for 3D
3. **Layers**: Create logical layer organization (Walls, Cabinets, Appliances, etc.)
4. **Colors**: Use AutoCAD color codes (1-255, with 7 as default white)

### Entity Selection Guide:
- **Walls/Structure**: Use `rectangle` or `polyline`
- **Cabinets**: Use `rectangle` for simple boxes, `polyline` for complex shapes
- **Appliances**: Use `rectangle` for most, `circle` for cooktops/sinks
- **Countertops**: Use `polyline` to follow cabinet outlines with thickness
- **Dimensions**: Use `dimension` entity with appropriate type
- **Labels**: Use `text` for simple labels, `mtext` for multi-line descriptions
- **Material indication**: Use `hatch` with appropriate patterns
- **Callouts**: Use `leader` entities for detailed annotations

### Standard Kitchen Dimensions (mm):
- **Base cabinets**: 600-700 depth, 850-900 height
- **Wall cabinets**: 300-400 depth, 700-900 height
- **Countertops**: 25-40 thickness beyond cabinet face
- **Islands**: Minimum 1000x2000, typically 1200x2400
- **Walkways**: Minimum 900, preferred 1200
- **Work triangle**: 4000-8000 total perimeter

### Professional Standards:
- Include proper clearances and safety zones
- Add comprehensive dimensions
- Use industry-standard symbols and abbreviations
- Provide clear labeling and annotations
- Include material indications through hatching
- Follow accessibility guidelines where applicable

---

## 🔧 Testing Your Generated JSON

To test your generated JSON:

1. **Validate JSON syntax** using online validators
2. **Check required fields** against the API schema
3. **Verify measurements** are logical and proportional
4. **Test with API** using the provided endpoints
5. **Review DXF output** in CAD software for accuracy

## 📞 Support and Documentation

- **API Documentation**: See `openapi.yaml` for complete API reference
- **Entity Reference**: Check `DXF_CAPABILITIES.md` for supported entity types
- **Test Examples**: Use `test_comprehensive.py` for validation examples