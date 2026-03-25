# HotBunk YouTube Shorts -- Visual Rendering Specs

Programmatic rendering via PIL/Pillow. Each short = sequence of PNG frames composited into video.

---

## Global Constants

```python
# Canvas
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Colors
BG_PRIMARY = "#0a0e14"         # deep ocean black
BG_GRID = "#0f1a24"            # sonar grid line color (faint)
CYAN = "#00d4ff"               # headers, accents, highlights
WHITE = "#ffffff"              # body text
GREEN = "#00ff88"              # good states, confirmations
RED = "#ff4444"                # alerts, warnings, cost
AMBER = "#ffaa00"              # caution, transitions
DIM_CYAN = "#005577"           # subtle accents, watermark
GRID_LINE = "#0d1820"          # very faint grid lines
SONAR_RING = "#00d4ff"         # sonar ping rings (with alpha fade)

# Typography (all monospace)
FONT_FAMILY = "JetBrainsMono-Regular.ttf"
FONT_BOLD = "JetBrainsMono-Bold.ttf"
FONT_HERO = 160                # huge numbers ($200, 150x)
FONT_LARGE = 96                # section headers
FONT_MEDIUM = 56               # subheaders, labels
FONT_BODY = 40                 # body text, descriptions
FONT_SMALL = 32                # captions, fine print
FONT_CODE = 36                 # terminal/code text
FONT_TINY = 24                 # watermark, metadata

# Layout
MARGIN_X = 80                  # horizontal padding from edges
CENTER_X = 540                 # horizontal center
CENTER_Y = 960                 # vertical center
SAFE_TOP = 200                 # below status bar cutoff
SAFE_BOTTOM = 1720             # above home indicator cutoff

# Sonar Grid
GRID_SPACING = 120             # pixels between grid lines
GRID_LINE_WIDTH = 1            # 1px thin lines
GRID_OPACITY = 0.08            # very subtle

# Watermark
WATERMARK_OPACITY = 0.06       # barely visible
WATERMARK_Y = 1800             # near bottom
```

---

## Shared Background Renderer

Every frame starts with this base layer. Build once, composite on top.

```
Layer 1: Solid fill BG_PRIMARY (#0a0e14)
Layer 2: Vertical grid lines every GRID_SPACING px, color GRID_LINE, width 1px, opacity 0.08
Layer 3: Horizontal grid lines every GRID_SPACING px, same specs
Layer 4: Radial gradient vignette -- edges darken to pure black, center stays BG_PRIMARY
         Ellipse centered at (540, 960), radiusX=700, radiusY=1200, falloff from 0% to 30% darker
Layer 5: Submarine silhouette watermark, bottom-right corner
         Position: (820, 1780), max size 200x80px
         Color: DIM_CYAN at WATERMARK_OPACITY
```

### Sonar Ping Effect (reusable)

Concentric expanding rings emanating from a point. Used as transition/accent.

```
Parameters: center=(x, y), num_rings=4, max_radius=400, ring_width=2
Each ring:
  - radius = max_radius * (i / num_rings)
  - color = SONAR_RING with alpha = 1.0 - (i / num_rings)  # outer rings fade
  - stroke width = ring_width
Duration: rings expand over 0.8s (24 frames at 30fps)
  - Frame N: each ring radius = target_radius * ease_out(N/24)
  - ease_out(t) = 1 - (1-t)^3  # cubic ease out
```

### Depth Gauge Bar (reusable)

Vertical bar with fill level, used to show capacity/percentage.

```
Parameters: x, y, width=40, height=600, fill_pct=0.0-1.0, fill_color=GREEN
Outer rect: (x, y, x+width, y+height), stroke CYAN 2px, fill none
Inner rect: (x+2, y+height*(1-fill_pct)+2, x+width-2, y+height-2), fill fill_color
Tick marks: every 20% on left side, 8px wide, color DIM_CYAN
```

### Glow Effect (reusable)

Text glow for emphasis. Render text multiple times at increasing sizes with decreasing opacity.

```
Parameters: text, position, font_size, color
Pass 1: Draw text at 2x blur, color at 15% opacity (outer glow)
Pass 2: Draw text at 1x blur, color at 30% opacity (inner glow)
Pass 3: Draw text sharp, color at 100% opacity (core)
Implementation: use PIL ImageFilter.GaussianBlur on text layer, composite
```

---

## Short 1: "The Math"

**Duration:** 18 seconds total
**Music note:** low synth pulse, sonar pings on transitions

---

### Frame 1.1 -- Hook: The Price

**Duration:** 3.0 seconds (frames 1-90)

```
Background: shared base

Element: "$200"
  Font: FONT_BOLD at 160px
  Color: CYAN with glow effect
  Position: centered horizontally (CENTER_X), y=720 (baseline)
  Anchor: center
  Glow: 3-pass, blur radii 12px/6px/0px

Element: "per month"
  Font: FONT_FAMILY at 48px
  Color: WHITE at 60% opacity
  Position: centered horizontally, y=820
  Anchor: center

Element: sonar ping
  Center: (CENTER_X, 720)
  Triggers at frame 15 (0.5s in)
  4 rings expanding to max_radius=500 over 24 frames

Animation:
  - Frames 1-15: "$200" fades in (opacity 0% to 100%, ease_in)
  - Frame 15: sonar ping triggers from text center
  - Frames 15-30: "per month" fades in
  - Frames 30-90: hold static
```

---

### Frame 1.2 -- The Real Cost

**Duration:** 3.0 seconds (frames 91-180)

```
Background: shared base

Element: "$200" (carried forward)
  Font: FONT_BOLD at 80px (shrunk from 160)
  Color: CYAN at 40% opacity (dimmed)
  Position: x=CENTER_X, y=500
  Anchor: center

Element: arrow
  Shape: horizontal line with arrowhead
  Start: (300, 700), End: (780, 700)
  Color: RED
  Line width: 4px
  Arrowhead: 20px equilateral triangle at end point
  Animation: draws left-to-right over frames 91-115 (0.8s)

Element: "$30,000"
  Font: FONT_BOLD at 140px
  Color: RED with glow effect (red glow)
  Position: centered horizontally, y=960
  Anchor: center
  Glow: blur radii 10px/5px/0px, color RED

Element: "equivalent API tokens"
  Font: FONT_FAMILY at 40px
  Color: WHITE at 70% opacity
  Position: centered horizontally, y=1080
  Anchor: center

Animation:
  - Frames 91-105: "$200" shrinks and moves up (interpolate size 160->80, y 720->500)
  - Frames 91-115: arrow draws in left to right
  - Frames 115-130: "$30,000" scales up from 0% to 100% (bounce ease)
  - Frames 130-145: subtitle fades in
  - Frames 145-180: hold
```

---

### Frame 1.3 -- The Multiplier

**Duration:** 3.0 seconds (frames 181-270)

```
Background: shared base

Element: "150x"
  Font: FONT_BOLD at 200px
  Color: CYAN
  Position: centered, y=860
  Anchor: center
  Glow: pulsing -- oscillates between blur 8px and 16px
    Pulse cycle: 1.5s (45 frames), sinusoidal
    Alpha of outer glow oscillates 10%-25%

Element: "That's the arbitrage."
  Font: FONT_FAMILY at 48px
  Color: WHITE
  Position: centered, y=1060
  Anchor: center

Element: horizontal rule
  Shape: line from (200, 1000) to (880, 1000)
  Color: CYAN at 30% opacity
  Width: 1px

Animation:
  - Frames 181-200: "150x" zooms in from 50% scale to 100% (ease_out cubic)
  - Frames 181-270: glow pulses continuously
  - Frames 200-215: horizontal rule fades in
  - Frames 215-230: subtitle types in character by character (typewriter effect, 2 frames per char)
  - Frames 230-270: hold with pulsing glow
```

---

### Frame 1.4 -- Idle Capacity

**Duration:** 3.0 seconds (frames 271-360)

```
Background: shared base

Element: clock icon
  Shape: circle (radius 50px) with two hands (hour at 10, minute at 2)
  Position: (CENTER_X, 550), center of circle
  Color: CYAN, stroke 3px
  Hands: CYAN, 3px stroke, lengths 30px (hour) and 40px (minute)

Element: "8 hours of sleep."
  Font: FONT_BOLD at 64px
  Color: WHITE
  Position: centered, y=700
  Anchor: center

Element: capacity meter bar (horizontal variant)
  Position: x=140, y=900, width=800, height=60
  Outer rect: stroke CYAN 2px
  Fill: left 33% = GREEN ("active"), right 67% = DIM_CYAN ("idle")
  Labels above bar:
    "ACTIVE" at x=140, y=860, font FONT_SMALL, color GREEN
    "IDLE" at x=600, y=860, font FONT_SMALL, color DIM_CYAN

Element: "Your subscription sleeps. HotBunk doesn't."
  Font: FONT_FAMILY at 36px
  Color: WHITE at 70% opacity
  Position: centered, y=1060
  Anchor: center
  Max width: 900px (line wrap if needed)

Animation:
  - Frames 271-285: clock fades in
  - Frames 285-300: text fades in
  - Frames 300-330: meter bar fills left-to-right (first green section, then dim section)
  - Frames 330-345: bottom text fades in
  - Frames 345-360: hold
```

---

### Frame 1.5 -- The Product

**Duration:** 3.0 seconds (frames 361-450)

```
Background: shared base

Element: HotBunk logo text
  Text: "HOTBUNK"
  Font: FONT_BOLD at 96px
  Color: CYAN with glow
  Position: centered, y=500
  Letter spacing: +8px (tracked out)

Element: "Pool your accounts."
  Font: FONT_FAMILY at 48px
  Color: WHITE
  Position: centered, y=620

Element: terminal block
  Background rect: (100, 740, 980, 1100)
  Fill: #0d1117 (dark terminal bg)
  Border: CYAN at 1px, rounded corners 8px (approximate with rect)
  Top bar: (100, 740, 980, 780), fill #161b22
    Three dots: circles at (125, 760), (150, 760), (175, 760), radii 6px
    Colors: RED, AMBER, GREEN respectively

  Terminal content (starting y=810, x=130, line height 44px):
    Line 1: "$ hotbunk status"
      "$" in GREEN, rest in WHITE, font FONT_CODE
    Line 2: ""  (blank, 22px gap)
    Line 3: "ACCOUNT    STATE       IDLE"
      Color: DIM_CYAN, font FONT_CODE
    Line 4: "drew       SLEEPING    4h 22m"
      "drew" in CYAN, "SLEEPING" in GREEN, "4h 22m" in WHITE
      Font: FONT_CODE
    Line 5: "amelia     INTERACTIVE  --"
      "amelia" in CYAN, "INTERACTIVE" in AMBER, "--" in DIM_CYAN
      Font: FONT_CODE
    Line 6: "owen       IDLE        1h 05m"
      "owen" in CYAN, "IDLE" in GREEN, "1h 05m" in WHITE
      Font: FONT_CODE

Animation:
  - Frames 361-375: logo fades in with glow
  - Frames 375-390: subtitle fades in
  - Frames 390-400: terminal block slides up from y+50 to final position (ease_out)
  - Frames 400-450: terminal lines type in one by one (typewriter), 8 frames per line
```

---

### Frame 1.6 -- CTA

**Duration:** 3.0 seconds (frames 451-540)

```
Background: shared base

Element: GitHub icon (simplified)
  Shape: circle with octocat silhouette (or just a circle with "GH" text)
  Position: (CENTER_X, 600), radius 50px
  Color: WHITE

Element: "github.com/drewbeyersdorf/hotbunk"
  Font: FONT_CODE at 32px
  Color: CYAN
  Position: centered, y=720
  Anchor: center

Element: install command box
  Background rect: (180, 820, 900, 900)
  Fill: #0d1117
  Border: GREEN 2px

  Text: "pip install hotbunk"
  Font: FONT_CODE at 40px
  Color: GREEN
  Position: centered within box, y=870
  Anchor: center

Element: "Your compute. Your rules."
  Font: FONT_BOLD at 48px
  Color: WHITE
  Position: centered, y=1050

Element: HotBunk wordmark
  Text: "HOTBUNK"
  Font: FONT_BOLD at 72px
  Color: CYAN with glow
  Position: centered, y=1250

Animation:
  - Frames 451-465: GitHub icon fades in
  - Frames 465-480: URL types in (typewriter, 1 frame per char)
  - Frames 480-500: install box fades in
  - Frames 500-515: tagline fades in
  - Frames 515-540: logo pulses with glow, hold
```

---

## Short 2: "The Bunk"

**Duration:** 21 seconds total
**Music note:** mechanical hum, shift-change klaxon sound effect

---

### Frame 2.1 -- Submarine Cross-Section

**Duration:** 4.0 seconds (frames 1-120)

```
Background: shared base

Element: ASCII submarine art (rendered as monospace text block)
  Font: FONT_CODE at 28px
  Color: CYAN
  Position: x=100, y=400 (top-left of text block)
  Line height: 34px

  ASCII content (each line rendered individually):
  ```
       ___________________________
      /                           \
     /  +-------+  +-------+      \
    |   | BUNK  |  | BUNK  |  OPS  |
    |   |  (A)  |  |  (B)  |  CTR  |
    |   +-------+  +-------+       |
    |   CREW QUARTERS    |  CONN   |
     \___________________| ______/
      \________________________/
  ```

  Bunk labels "(A)" and "(B)" rendered in different colors:
    "(A)" sections: GREEN
    "(B)" sections: AMBER
    Rest: CYAN

Element: "Hot bunking."
  Font: FONT_BOLD at 64px
  Color: WHITE
  Position: centered, y=1050

Element: "One bunk. Two sailors. Never empty."
  Font: FONT_FAMILY at 40px
  Color: WHITE at 60% opacity
  Position: centered, y=1140

Animation:
  - Frames 1-60: submarine draws in line by line (top to bottom), each line takes 6 frames
  - Frames 60-80: labels fade in
  - Frames 80-95: bottom text fades in
  - Frames 95-120: hold
```

---

### Frame 2.2 -- Sailor A on Watch

**Duration:** 3.0 seconds (frames 121-210)

```
Background: shared base

Element: submarine cross-section (simplified, smaller)
  Same ASCII art but at FONT_CODE 22px
  Position: x=100, y=200
  Color: DIM_CYAN (dimmed, background element)

Element: Bunk A highlight box
  Rect around Bunk A area in the ASCII: approximate (180, 340, 380, 460)
  Border: GREEN 3px, pulsing glow
  Fill: GREEN at 5% opacity

Element: Bunk B highlight box
  Rect around Bunk B area: approximate (420, 340, 620, 460)
  Border: AMBER 2px, no glow
  Fill: AMBER at 3% opacity

Element: status labels (below submarine)
  "SAILOR A" at x=280, y=550
    Font: FONT_BOLD at 44px, color GREEN
  "ON WATCH" below at x=280, y=600
    Font: FONT_FAMILY at 36px, color GREEN

  "SAILOR B" at x=800, y=550
    Font: FONT_BOLD at 44px, color AMBER
  "SLEEPING" below at x=800, y=600
    Font: FONT_FAMILY at 36px, color AMBER

Element: activity indicator for A
  Small pulsing circle at (280, 500), radius 8px, GREEN
  Pulses: radius oscillates 6-10px over 30 frames

Element: sleep indicator for B
  Three "z" characters stacked: "z Z z" near (800, 480)
  Font: FONT_BODY at 36px, color AMBER at 40% opacity
  Float animation: y oscillates +/- 5px over 60 frames

Animation:
  - Frames 121-135: highlight boxes fade in
  - Frames 135-150: status labels type in
  - Frames 150-210: indicators pulse/animate, hold
```

---

### Frame 2.3 -- Shift Change

**Duration:** 3.5 seconds (frames 211-315)

```
Background: shared base

Element: submarine (same dimmed background)

Element: "SHIFT CHANGE" banner
  Text: ">> SHIFT CHANGE <<"
  Font: FONT_BOLD at 56px
  Color: AMBER, flashing (alternates full opacity / 40% opacity every 15 frames)
  Position: centered, y=550

Element: swap animation
  Two arrows forming an X pattern:
    Arrow 1: from (280, 700) to (800, 700), curving up through y=620
    Arrow 2: from (800, 750) to (280, 750), curving down through y=830
  Color: CYAN, stroke 3px
  Arrowheads: 15px

  Label on left path: "A" in GREEN circle (radius 25px) at left start
  Label on right path: "B" in AMBER circle (radius 25px) at right start

Element: Sailor A label (moving right)
  Starts: x=200, y=700
  Ends: x=820, y=700
  "A" inside GREEN circle, font FONT_BOLD 36px

Element: Sailor B label (moving left)
  Starts: x=820, y=750
  Ends: x=200, y=750
  "B" inside AMBER circle, font FONT_BOLD 36px

Animation:
  - Frames 211-225: "SHIFT CHANGE" flashes in
  - Frames 225-280: swap arrows draw, A and B circles travel along paths
    A moves right: x interpolates 200->820 with ease_in_out over 55 frames
    B moves left: x interpolates 820->200 with ease_in_out over 55 frames
  - Frames 280-315: labels settle, flash stops, hold
```

---

### Frame 2.4 -- Map to Claude

**Duration:** 3.5 seconds (frames 316-420)

```
Background: shared base

Element: header
  Text: "Now map it."
  Font: FONT_BOLD at 64px
  Color: CYAN
  Position: centered, y=400

Element: horizontal divider
  Line from (200, 460) to (880, 460), CYAN at 30%, 1px

Element: left column -- submarine
  Header: "SUBMARINE" at x=300, y=530, font FONT_MEDIUM, color DIM_CYAN, centered
  Item 1: "Sailor A = on watch" at x=300, y=610, font FONT_BODY, color GREEN, centered
  Item 2: "Sailor B = sleeping" at x=300, y=670, font FONT_BODY, color AMBER, centered

Element: vertical divider
  Line from (540, 500) to (540, 800), CYAN at 20%, 1px

Element: right column -- hotbunk
  Header: "HOTBUNK" at x=780, y=530, font FONT_MEDIUM, color CYAN, centered
  Item 1: "Account A = interactive" at x=780, y=610, font FONT_BODY, color GREEN, centered
  Item 2: "Account B = running agents" at x=780, y=670, font FONT_BODY, color AMBER, centered

Element: mapping arrows
  Dashed arrows from left items to right items:
  Arrow 1: (440, 610) -> (600, 610), dashed, GREEN, 2px
  Arrow 2: (440, 670) -> (600, 670), dashed, AMBER, 2px

Element: bottom text
  "Same capacity. Fully utilized."
  Font: FONT_FAMILY at 40px
  Color: WHITE
  Position: centered, y=900

Animation:
  - Frames 316-330: header types in
  - Frames 330-345: left column fades in top to bottom
  - Frames 345-360: right column fades in top to bottom
  - Frames 360-380: mapping arrows draw in (dashed, left to right)
  - Frames 380-400: bottom text fades in
  - Frames 400-420: hold
```

---

### Frame 2.5 -- The Swap

**Duration:** 3.5 seconds (frames 421-525)

```
Background: shared base

Element: two account cards

  Card A (left side):
    Rect: (80, 400, 500, 750)
    Fill: #0d1117
    Border: initially GREEN 2px, transitions to DIM_CYAN
    Header bar: (80, 400, 500, 450), fill GREEN at 15%
    Header text: "ACCOUNT A" at (290, 430), FONT_BOLD 36px, GREEN
    Status line 1: "State: IDLE" at (130, 500), FONT_CODE 32px
      "IDLE" in DIM_CYAN (was GREEN, now changed)
    Status line 2: "Since: 2m ago" at (130, 545), FONT_CODE 28px, DIM_CYAN
    Status line 3: "Jobs: 0" at (130, 585), FONT_CODE 28px, DIM_CYAN

  Card B (right side):
    Rect: (580, 400, 1000, 750)
    Fill: #0d1117
    Border: initially AMBER 2px, transitions to GREEN
    Header bar: (580, 400, 1000, 450), fill GREEN at 15% (was AMBER)
    Header text: "ACCOUNT B" at (790, 430), FONT_BOLD 36px, GREEN (was AMBER)
    Status line 1: "State: INTERACTIVE" at (630, 500), FONT_CODE 32px
      "INTERACTIVE" in GREEN
    Status line 2: "Priority: OWNER" at (630, 545), FONT_CODE 28px, GREEN
    Status line 3: "Agents: migrated" at (630, 585), FONT_CODE 28px, CYAN

Element: swap indicator
  Two curved arrows between cards (same pattern as frame 2.3 but smaller)
  Center y=580, spanning x=500 to x=580
  Color: CYAN, 2px

Element: "Agents migrate. Owner takes over."
  Font: FONT_FAMILY at 40px
  Color: WHITE
  Position: centered, y=880

Animation:
  - Frames 421-440: both cards visible in initial state (A=active/GREEN, B=agents/AMBER)
  - Frames 440-475: swap animation
    Card A border transitions GREEN -> DIM_CYAN (fade over 35 frames)
    Card B border transitions AMBER -> GREEN (fade over 35 frames)
    Status text updates at frame 458 (midpoint)
  - Frames 475-500: bottom text fades in
  - Frames 500-525: hold
```

---

### Frame 2.6 -- Tagline

**Duration:** 3.5 seconds (frames 526-630)

```
Background: shared base

Element: "The capacity is always hot."
  Font: FONT_BOLD at 56px
  Color: CYAN with glow
  Position: centered, y=750
  Max width: 900px
  Glow: standard 3-pass, pulsing

Element: sonar ping
  Center: (CENTER_X, 750)
  Triggers at frame 540
  6 rings, max_radius=600

Element: HotBunk logo
  Text: "HOTBUNK"
  Font: FONT_BOLD at 80px
  Color: CYAN
  Position: centered, y=1100
  Letter spacing: +6px

Element: subtitle
  Text: "cooperative compute for Claude Code"
  Font: FONT_FAMILY at 32px
  Color: WHITE at 50%
  Position: centered, y=1180

Animation:
  - Frames 526-545: tagline fades in with glow
  - Frame 540: sonar ping triggers
  - Frames 545-570: sonar rings expand
  - Frames 570-590: logo fades in
  - Frames 590-605: subtitle fades in
  - Frames 605-630: hold, glow pulses
```

---

## Short 3: "The Consent"

**Duration:** 18 seconds total
**Music note:** encrypted radio chatter, lock mechanism clicks

---

### Frame 3.1 -- The Lock

**Duration:** 3.0 seconds (frames 1-90)

```
Background: shared base

Element: lock icon (drawn with primitives)
  Position: centered at (CENTER_X, 650)
  Shackle: arc from (500, 600) to (580, 600), curving up to y=520
    Stroke: CYAN, 6px, round caps
  Body: rounded rect (480, 600, 600, 720)
    Fill: CYAN at 15%
    Stroke: CYAN, 4px
  Keyhole: circle at (540, 650) radius 12px, fill BG_PRIMARY
    Plus small rect (534, 650, 546, 690), fill BG_PRIMARY

Element: "Your account."
  Font: FONT_BOLD at 72px
  Color: WHITE
  Position: centered, y=850

Element: "Your rules."
  Font: FONT_BOLD at 72px
  Color: CYAN with glow
  Position: centered, y=950

Animation:
  - Frames 1-20: lock icon draws in (shackle first, then body, then keyhole)
  - Frames 20-40: "Your account." fades in
  - Frames 40-60: "Your rules." fades in with glow
  - Frame 45: sonar ping from lock center, 3 rings, max_radius=300
  - Frames 60-90: hold
```

---

### Frame 3.2 -- Policy File

**Duration:** 4.0 seconds (frames 91-210)

```
Background: shared base

Element: file header
  Text: "policy.yaml"
  Font: FONT_CODE at 36px
  Color: DIM_CYAN
  Position: x=130, y=300

Element: terminal/code block
  Background rect: (80, 340, 1000, 1100)
  Fill: #0d1117
  Border: CYAN at 1px

  YAML content (syntax highlighted, font FONT_CODE at 30px, line height 38px):
  Starting at x=110, y=380:

  Line 1:  "# drew's consent policy"          color: DIM_CYAN (comment)
  Line 2:  "account: drew"                     "account:" CYAN, "drew" WHITE
  Line 3:  ""
  Line 4:  "availability:"                     CYAN
  Line 5:  "  sleep_window:"                   CYAN
  Line 6:  "    start: \"23:00\""              "start:" CYAN, value GREEN
  Line 7:  "    end: \"07:00\""                "end:" CYAN, value GREEN
  Line 8:  "  idle_timeout: 300"               "idle_timeout:" CYAN, "300" AMBER
  Line 9:  ""
  Line 10: "allowed_jobs:"                     CYAN
  Line 11: "  - agents"                        GREEN
  Line 12: "  - training"                      GREEN
  Line 13: "  - ci"                            GREEN
  Line 14: ""
  Line 15: "limits:"                           CYAN
  Line 16: "  max_concurrent: 2"               "max_concurrent:" CYAN, "2" AMBER
  Line 17: "  yield_on_interactive: true"      "yield_on_interactive:" CYAN, "true" GREEN
  Line 18: ""
  Line 19: "# owner ALWAYS has priority"       DIM_CYAN (comment)

Element: "Every account has one."
  Font: FONT_FAMILY at 40px
  Color: WHITE at 70%
  Position: centered, y=1200

Animation:
  - Frames 91-100: file header fades in
  - Frames 100-115: code block background fades in
  - Frames 115-195: YAML lines type in one at a time (typewriter effect)
    Each line: 4 frames to type, 1 frame pause between lines
    Total: 19 lines * 5 frames = 95 frames (fits in window)
  - Frames 195-210: bottom text fades in, hold
```

---

### Frame 3.3 -- State Machine

**Duration:** 4.0 seconds (frames 211-330)

```
Background: shared base

Element: header
  Text: "State Machine"
  Font: FONT_BOLD at 56px
  Color: CYAN
  Position: centered, y=320

Element: state diagram (3 nodes in vertical layout)

  Node: INTERACTIVE
    Position: (CENTER_X, 550)
    Shape: rounded rect (350, 510, 730, 590), corners ~10px
    Fill: GREEN at 15%
    Border: GREEN 3px
    Text: "INTERACTIVE" centered in rect, FONT_BOLD 36px, GREEN

  Node: IDLE
    Position: (CENTER_X, 800)
    Shape: rounded rect (350, 760, 730, 840)
    Fill: AMBER at 15%
    Border: AMBER 3px
    Text: "IDLE" centered, FONT_BOLD 36px, AMBER

  Node: SLEEPING
    Position: (CENTER_X, 1050)
    Shape: rounded rect (350, 1010, 730, 1090)
    Fill: CYAN at 15%
    Border: CYAN 3px
    Text: "SLEEPING" centered, FONT_BOLD 36px, CYAN

  Arrow: INTERACTIVE -> IDLE
    Line from (CENTER_X, 590) to (CENTER_X, 760)
    Color: WHITE at 60%, 2px, arrowhead 12px
    Label: "5 min idle" at (620, 675), FONT_SMALL, DIM_CYAN

  Arrow: IDLE -> SLEEPING
    Line from (CENTER_X, 840) to (CENTER_X, 1010)
    Color: WHITE at 60%, 2px, arrowhead 12px
    Label: "sleep window" at (620, 925), FONT_SMALL, DIM_CYAN

  Arrow: SLEEPING -> INTERACTIVE (curved, right side)
    Path: from (730, 1050) curve right to x=800 then up to (730, 550)
    Color: GREEN, 2px, arrowhead 12px
    Label: "owner returns" at (830, 800), FONT_SMALL, GREEN

  Arrow: IDLE -> INTERACTIVE (curved, left side)
    Path: from (350, 800) curve left to x=280 then up to (350, 550)
    Color: GREEN, 2px, arrowhead 12px
    Label: "activity" at (200, 675), FONT_SMALL, GREEN

Element: status text
  "Automation only runs in IDLE and SLEEPING."
  Font: FONT_FAMILY at 36px
  Color: WHITE at 70%
  Position: centered, y=1250
  Max width: 900px

Animation:
  - Frames 211-225: header fades in
  - Frames 225-245: INTERACTIVE node fades in (border draws, fill appears, text fades)
  - Frames 245-265: IDLE node fades in
  - Frames 265-285: SLEEPING node fades in
  - Frames 285-305: arrows draw in one at a time (5 frames each)
  - Frames 305-315: status text fades in
  - Frames 315-330: hold

  Optional highlight animation (frames 315-330):
    A "pulse" travels the state path: GREEN dot moves INTERACTIVE->IDLE->SLEEPING->INTERACTIVE
    Dot: radius 6px, GREEN, travels along arrow paths
```

---

### Frame 3.4 -- Owner Priority

**Duration:** 3.5 seconds (frames 331-435)

```
Background: shared base

Element: "You come back."
  Font: FONT_BOLD at 64px
  Color: WHITE
  Position: centered, y=450

Element: "Automation yields."
  Font: FONT_BOLD at 64px
  Color: GREEN with glow
  Position: centered, y=560

Element: priority animation (two horizontal bars)

  Bar: "AUTOMATION" (top bar, gets pushed down)
    Initial rect: (140, 750, 940, 830)
    Fill: AMBER at 20%
    Border: AMBER 2px
    Text: "AUTOMATION" + running indicator (3 dots cycling), centered
    Font: FONT_BOLD 36px, AMBER

  Bar: "INTERACTIVE" (slides in from top, pushes automation down)
    Rect: (140, 650, 940, 730)
    Fill: GREEN at 20%
    Border: GREEN 3px
    Text: ">> INTERACTIVE <<" centered
    Font: FONT_BOLD 36px, GREEN

  Priority arrow
    Vertical arrow on left side, pointing up, from (110, 830) to (110, 650)
    Label rotated 90 degrees: "PRIORITY" at (90, 740)
    Color: CYAN, 2px

Element: "Zero config. It just works."
  Font: FONT_FAMILY at 40px
  Color: WHITE at 70%
  Position: centered, y=1000

Animation:
  - Frames 331-350: "You come back." fades in
  - Frames 350-365: "Automation yields." fades in with glow
  - Frames 365-380: automation bar is shown at y=700 position (centered)
  - Frames 380-410: INTERACTIVE bar slides in from y=600 to y=650
    Simultaneously, AUTOMATION bar slides down from y=700 to y=800
    Automation bar border changes AMBER -> DIM_CYAN (deprioritized)
    Automation text changes to "AUTOMATION (yielded)" and dims
  - Frames 410-420: priority arrow and label fade in
  - Frames 420-435: bottom text fades in, hold
```

---

### Frame 3.5 -- Open Source

**Duration:** 3.5 seconds (frames 436-540)

```
Background: shared base

Element: "Open source."
  Font: FONT_BOLD at 80px
  Color: WHITE
  Position: centered, y=550

Element: "MIT License."
  Font: FONT_BOLD at 80px
  Color: GREEN with glow
  Position: centered, y=670

Element: horizontal rule
  Line from (300, 740) to (780, 740), CYAN at 30%, 1px

Element: HotBunk logo
  Text: "HOTBUNK"
  Font: FONT_BOLD at 96px
  Color: CYAN with glow
  Position: centered, y=900
  Letter spacing: +8px

Element: GitHub URL
  Text: "github.com/drewbeyersdorf/hotbunk"
  Font: FONT_CODE at 30px
  Color: CYAN at 70%
  Position: centered, y=1020

Element: install command
  Text: "pip install hotbunk"
  Font: FONT_CODE at 40px
  Color: GREEN
  Position: centered, y=1120
  Background rect: (240, 1090, 840, 1160), fill #0d1117, border GREEN 1px

Element: sonar ping (final flourish)
  Center: (CENTER_X, 900)
  Triggers at frame 480
  5 rings, max_radius=700

Animation:
  - Frames 436-455: "Open source." fades in
  - Frames 455-475: "MIT License." fades in with glow
  - Frames 475-485: horizontal rule fades in
  - Frame 480: sonar ping triggers
  - Frames 485-500: logo fades in
  - Frames 500-515: URL types in
  - Frames 515-525: install command fades in
  - Frames 525-540: hold, glow pulses
```

---

## Rendering Implementation Notes

### File Output

Each frame renders to PNG. FFmpeg composites into MP4.

```
output/
  short1_the_math/
    frame_0001.png ... frame_0540.png
    the_math.mp4
  short2_the_bunk/
    frame_0001.png ... frame_0630.png
    the_bunk.mp4
  short3_the_consent/
    frame_0001.png ... frame_0540.png
    the_consent.mp4
```

### FFmpeg Command

```bash
ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 output.mp4
```

### Font Loading

```python
from PIL import ImageFont

# Try JetBrains Mono first, fall back to system monospace
FONT_PATHS = [
    "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf",
    "/usr/share/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
    "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
]

def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    suffix = "Bold" if bold else "Regular"
    for base in FONT_PATHS:
        path = base.replace("Regular", suffix)
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()
```

### Animation Easing Functions

```python
import math

def ease_in(t: float) -> float:
    """Accelerating from zero velocity."""
    return t * t

def ease_out(t: float) -> float:
    """Decelerating to zero velocity."""
    return 1 - (1 - t) ** 3

def ease_in_out(t: float) -> float:
    """Acceleration then deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2

def pulse(t: float, frequency: float = 1.0) -> float:
    """Sinusoidal pulse 0..1..0."""
    return (math.sin(2 * math.pi * frequency * t - math.pi / 2) + 1) / 2

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t
```

### Glow Renderer

```python
from PIL import Image, ImageDraw, ImageFilter

def render_glow_text(
    canvas: Image.Image,
    text: str,
    position: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color: str,
    blur_passes: list[tuple[int, float]] = [(12, 0.15), (6, 0.30)],
) -> None:
    """Render text with multi-pass glow effect."""
    for blur_radius, alpha in blur_passes:
        glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow_layer)
        draw.text(position, text, font=font, fill=color, anchor="mm")
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
        # Reduce alpha
        r, g, b, a = glow_layer.split()
        a = a.point(lambda x: int(x * alpha))
        glow_layer = Image.merge("RGBA", (r, g, b, a))
        canvas = Image.alpha_composite(canvas, glow_layer)
    # Sharp pass
    draw = ImageDraw.Draw(canvas)
    draw.text(position, text, font=font, fill=color, anchor="mm")
    return canvas
```

### Typewriter Effect

```python
def typewriter_frame(
    full_text: str,
    frame_in_sequence: int,
    frames_per_char: int = 2,
) -> str:
    """Return the substring visible at this frame."""
    chars_visible = frame_in_sequence // frames_per_char
    return full_text[:chars_visible]
```

### Background Grid Renderer

```python
def render_grid(canvas: Image.Image) -> Image.Image:
    """Draw sonar-style grid on canvas."""
    grid = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    w, h = canvas.size
    grid_color = (13, 24, 32, int(255 * 0.08))  # GRID_LINE at 8% opacity

    for x in range(0, w, 120):
        draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y in range(0, h, 120):
        draw.line([(0, y), (w, y)], fill=grid_color, width=1)

    return Image.alpha_composite(canvas, grid)
```

---

## Frame Duration Summary

| Short | Frame | Description | Seconds | Frame Range |
|-------|-------|-------------|---------|-------------|
| 1 | 1.1 | Hook: $200 | 3.0 | 1-90 |
| 1 | 1.2 | Real cost: $30K | 3.0 | 91-180 |
| 1 | 1.3 | 150x multiplier | 3.0 | 181-270 |
| 1 | 1.4 | Idle capacity | 3.0 | 271-360 |
| 1 | 1.5 | Product reveal | 3.0 | 361-450 |
| 1 | 1.6 | CTA | 3.0 | 451-540 |
| **1 total** | | | **18.0** | **540 frames** |
| 2 | 2.1 | Submarine cross-section | 4.0 | 1-120 |
| 2 | 2.2 | Sailor A on watch | 3.0 | 121-210 |
| 2 | 2.3 | Shift change | 3.5 | 211-315 |
| 2 | 2.4 | Map to Claude | 3.5 | 316-420 |
| 2 | 2.5 | The swap | 3.5 | 421-525 |
| 2 | 2.6 | Tagline | 3.5 | 526-630 |
| **2 total** | | | **21.0** | **630 frames** |
| 3 | 3.1 | Lock icon | 3.0 | 1-90 |
| 3 | 3.2 | Policy YAML | 4.0 | 91-210 |
| 3 | 3.3 | State machine | 4.0 | 211-330 |
| 3 | 3.4 | Owner priority | 3.5 | 331-435 |
| 3 | 3.5 | Open source CTA | 3.5 | 436-540 |
| **3 total** | | | **18.0** | **540 frames** |
