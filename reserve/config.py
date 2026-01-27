"""
Configuration Constants for Reserve Audio Analyzer
Colors, fonts, layout settings, and display parameters
"""

# ════════════════════════════════════════════════════════════════
# COLOR PALETTE - Oscilloscope Theme
# ════════════════════════════════════════════════════════════════

class Colors:
    """Color constants for UI theming"""
    # Backgrounds
    BLACK = '#000000'
    DARK_GRAY = '#0a0a0a'

    # Green palette (primary)
    GREEN_BRIGHT = '#00ff41'    # Primary text, highlights
    GREEN_MEDIUM = '#00aa00'    # Secondary text
    GREEN_DARK = '#003300'      # Button backgrounds
    GREEN_BORDER = '#001a00'    # Borders, grid lines

    # Accent colors
    YELLOW = '#ffff00'          # Warnings, reverse button
    RED = '#ff0000'             # Errors, stop button

    # Aliases for semantic use
    PRIMARY = GREEN_BRIGHT
    SECONDARY = GREEN_MEDIUM
    BACKGROUND = BLACK
    SURFACE = DARK_GRAY
    BORDER = GREEN_BORDER
    WARNING = YELLOW
    ERROR = RED


# ════════════════════════════════════════════════════════════════
# TYPOGRAPHY
# ════════════════════════════════════════════════════════════════

class Fonts:
    """Font settings"""
    TITLE_FAMILY = 'Arial'
    MONO_FAMILY = 'Courier New'

    # Font sizes (scaled 1.7x)
    TITLE_SIZE = 61
    SUBTITLE_SIZE = 20
    SECTION_SIZE = 20
    LABEL_SIZE = 17
    VALUE_SIZE = 27
    BUTTON_SIZE = 24


# ════════════════════════════════════════════════════════════════
# LAYOUT DIMENSIONS
# ════════════════════════════════════════════════════════════════

class Layout:
    """Layout dimensions and spacing"""
    # Window (scaled 1.7x from original 960x570)
    WINDOW_WIDTH = 1632
    WINDOW_HEIGHT = 969
    WINDOW_X = 100
    WINDOW_Y = 50

    # Margins and spacing
    MAIN_MARGIN = 10
    MAIN_SPACING = 10

    # Panel sizes
    CONTROL_PANEL_WIDTH = 425
    HEADER_HEIGHT = 77
    STATUS_BAR_HEIGHT = 44

    # Button heights
    BUTTON_HEIGHT = 48
    BUTTON_HEIGHT_SMALL = 41

    # Section title
    SECTION_TITLE_WIDTH = 408
    SECTION_TITLE_HEIGHT = 34

    # Canvas dimensions
    CANVAS_WIDTH = 12.75
    CANVAS_HEIGHT = 4.08
    CANVAS_DPI = 100


# ════════════════════════════════════════════════════════════════
# DISPLAY SETTINGS
# ════════════════════════════════════════════════════════════════

# Waveform display
DISPLAY_SAMPLES = 4000          # Number of samples for waveform display
WINDOW_SIZE_MS = 2000           # Animation window size (2 seconds)

# Animation settings
ANIMATION_INTERVAL_MS = 100     # Animation update interval (10fps)
PLAYBACK_STEP_MS = 100          # Playback position increment per update

# FFT settings
FFT_SIZE = 16384                # FFT computation size
SAVGOL_WINDOW = 51              # Savitzky-Golay filter window size


# ════════════════════════════════════════════════════════════════
# STYLESHEET
# ════════════════════════════════════════════════════════════════

def get_stylesheet():
    """Generate QSS stylesheet from color constants"""
    return f"""
    QMainWindow {{
        background-color: {Colors.BLACK};
    }}

    #header {{
        background-color: {Colors.BLACK};
        border: 2px solid {Colors.BORDER};
    }}

    #title {{
        color: {Colors.GREEN_BRIGHT};
    }}

    #subtitle {{
        color: {Colors.GREEN_MEDIUM};
    }}

    #controlPanel {{
        background-color: {Colors.DARK_GRAY};
        border: 2px solid {Colors.BORDER};
    }}

    #displayPanel {{
        background-color: {Colors.BLACK};
        border: 2px solid {Colors.BORDER};
    }}

    #section {{
        background-color: {Colors.DARK_GRAY};
        border: 3px solid {Colors.BORDER};
        border-radius: 9px;
    }}

    #sectionTitle {{
        color: {Colors.GREEN_BRIGHT};
    }}

    #fileLabel, #reverseStatus {{
        color: {Colors.GREEN_MEDIUM};
    }}

    QPushButton {{
        background-color: {Colors.GREEN_DARK};
        color: {Colors.GREEN_BRIGHT};
        border: 3px solid {Colors.GREEN_BRIGHT};
        border-radius: 9px;
        padding: 14px;
    }}

    QPushButton:hover {{
        background-color: {Colors.GREEN_BRIGHT};
        color: {Colors.BLACK};
    }}

    #reverseButton {{
        border-color: {Colors.YELLOW};
        color: {Colors.YELLOW};
    }}

    #reverseButton:hover {{
        background-color: {Colors.YELLOW};
    }}

    #stopButton {{
        border-color: {Colors.RED};
        color: {Colors.RED};
    }}

    #stopButton:hover {{
        background-color: {Colors.RED};
    }}

    #parameterBox {{
        background-color: {Colors.BLACK};
        border: 3px solid {Colors.BORDER};
        border-radius: 5px;
    }}

    #paramLabel {{
        color: {Colors.GREEN_MEDIUM};
    }}

    #paramValue {{
        color: {Colors.GREEN_BRIGHT};
    }}

    #channelLabel {{
        color: {Colors.GREEN_BRIGHT};
    }}

    #statusBar {{
        background-color: {Colors.DARK_GRAY};
        border: 2px solid {Colors.BORDER};
    }}

    #statusLabel, #timeLabel {{
        color: {Colors.GREEN_BRIGHT};
    }}
    """
