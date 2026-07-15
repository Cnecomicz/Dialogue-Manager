BORDER_WIDTH = "1px"
COLOR_CLOSE_BG = "#333"
COLOR_CLOSE_BORDER = "#555"
COLOR_DANGER_BG = "#7f1d1d"
COLOR_DANGER_BORDER = "#c53030"
COLOR_DANGER_DISABLED_BG = "#4b1c1c"
COLOR_DARK_BG = "#111827"
COLOR_DELETE_HIGHLIGHT = "#ef4444"
COLOR_DISABLED_BG = "#374151"
COLOR_HEADER_BUTTON_BG = "#374151"
COLOR_INPUT_BG = "#ffffff"
COLOR_INPUT_BORDER = "#9ca3af"
COLOR_INPUT_TEXT = "#111827"
COLOR_LOG_ROW_BORDER = "#1f2a37"
COLOR_PANEL_ALT_BG = "#252d35"
COLOR_PANEL_BG = "#1f252b"
COLOR_PANEL_BORDER = "#444"
COLOR_PICK_BG = "#5a6370"
COLOR_PICK_BORDER = "#777"
COLOR_PRIMARY_BG = "#4b5563"
COLOR_PRIMARY_BORDER = "#666"
COLOR_ROW_BORDER = "#333"
COLOR_SELECT_HIGHLIGHT = "#fbbf24"
COLOR_TEXT = "#e6e6e6"
COLOR_TEXT_DISABLED = "#6b7280"
COLOR_TEXT_DOCUMENT = "#d1d5db"
COLOR_TEXT_LIGHT = "#e5e7eb"
COLOR_TEXT_MUTED = "#9ca3af"
FONT_SIZE_BASE = "14px"
FONT_SIZE_H1 = "24px"
FONT_SIZE_H2 = "20px"
FONT_SIZE_LG = "16px"
FONT_SIZE_SM = "13px"
FONT_SIZE_TITLE = "18px"
FONT_SIZE_XS = "12px"
PADDING_BUTTON = "8px 14px"
PADDING_INPUT = "6px 8px"
PADDING_PANEL_BUTTON = "10px"
PADDING_PICK_BUTTON = "6px 10px"
PANEL_WIDTH = "320px"
RADIUS = "4px"
RADIUS_LG = "8px"
SERVER_SHUTDOWN_DELAY_SECONDS = 0.1
SERVER_URL = "http://localhost:8050"

def get_close_button_style() -> dict[str, str]:
    """Build a fresh style dict for a close/cancel button.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "padding": PADDING_BUTTON,
        "backgroundColor": COLOR_CLOSE_BG,
        "color": COLOR_TEXT,
        "border": thin_border(COLOR_CLOSE_BORDER),
        "borderRadius": RADIUS,
        "cursor": "pointer"
    }

def get_danger_button_style() -> dict[str, str]:
    """Build a fresh style dict for a destruction action button.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "padding": PADDING_BUTTON,
        "backgroundColor": COLOR_DANGER_BG,
        "color": COLOR_TEXT,
        "border": thin_border(COLOR_DANGER_BORDER),
        "borderRadius": RADIUS,
        "cursor": "pointer"
    }

def get_input_style() -> dict[str, str | int]:
    """Return consistent styling for text input fields.

    Returns:
        dict[str, str | int]: Inline style for inputs.
    """
    return {
        "width": "100%",
        "backgroundColor": COLOR_INPUT_BG,
        "color": COLOR_INPUT_TEXT,
        "caretColor": COLOR_INPUT_TEXT,
        "border": thin_border(COLOR_INPUT_BORDER),
        "fontSize": FONT_SIZE_BASE,
        "padding": PADDING_INPUT,
        "boxSizing": "border-box"
    }

def get_key_badge_style() -> dict[str, str]:
    """Return styling for a keyboard key badge in the shortcuts overlay.

    Returns:
        dict[str, str]: Inline style for key badges.
    """
    return {
        "backgroundColor": COLOR_DARK_BG,
        "color": COLOR_TEXT_LIGHT,
        "border": thin_border(COLOR_PRIMARY_BG),
        "borderRadius": RADIUS,
        "padding": "2px 8px",
        "fontFamily": "monospace",
        "fontSize": FONT_SIZE_SM,
        "whiteSpace": "nowrap"
    }

def get_label_style() -> dict[str, str | int]:
    """Return consistent styling for form labels.

    Returns:
        dict[str, str | int]: Inline style for labels.
    """
    return {
        "fontWeight": "bold",
        "marginBottom": "4px",
        "marginTop": "12px",
        "color": COLOR_TEXT_LIGHT,
        "fontSize": FONT_SIZE_BASE
    }

def get_panel_button_base_style() -> dict[str, str]:
    """Build a fresh base style dict for side panel buttons.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "width": "100%",
        "padding": PADDING_PANEL_BUTTON,
        "marginBottom": "8px",
        "border": thin_border(COLOR_PRIMARY_BORDER),
        "borderRadius": RADIUS
    }

def get_panel_button_danger_base_style() -> dict[str, str]:
    """Build a fresh base style dict for danger panel buttons.

    Returns:
        dict[str, str]: A new inline style mapping (no border).
    """
    return {
        "width": "100%",
        "padding": PADDING_PANEL_BUTTON,
        "marginBottom": "8px",
        "borderRadius": RADIUS
    }

def get_panel_button_danger_disabled_style() -> dict[str, str | float]:
    """Build the style for a disabled danger side-panel button.

    Returns:
        dict[str, str | float]: A new inline style mapping.
    """
    return {
        **get_panel_button_danger_base_style(),
        "backgroundColor": COLOR_DANGER_DISABLED_BG,
        "color": COLOR_TEXT_DISABLED,
        "border": thin_border(COLOR_DANGER_BG),
        "cursor": "not-allowed",
        "opacity": 0.5
    }

def get_panel_button_danger_style() -> dict[str, str | float]:
    """Build the style for an enabled danger side panel button.

    Returns:
        dict[str, str | float]: A new inline style mapping.
    """
    return {
        **get_panel_button_danger_base_style(),
        "backgroundColor": COLOR_DANGER_BG,
        "color": COLOR_TEXT,
        "border": thin_border(COLOR_DANGER_BORDER),
        "cursor": "pointer"
    }

def get_panel_button_disabled_style() -> dict[str, str | float]:
    """Build the style for a disabled primary side panel button.

    Returns:
        dict[str, str | float]: A new inline style mapping.
    """
    return {
        **get_panel_button_base_style(),
        "backgroundColor": COLOR_DISABLED_BG,
        "color": COLOR_TEXT_DISABLED,
        "cursor": "not-allowed",
        "opacity": 0.5
    }

def get_panel_button_enabled_style() -> dict[str, str | float]:
    """Build the style for an enabled primary side panel button.

    Returns:
        dict[str, str | float]: A new inline style mapping.
    """
    return {
        **get_panel_button_base_style(),
        "backgroundColor": COLOR_PRIMARY_BG,
        "color": COLOR_TEXT,
        "cursor": "pointer"
    }

def get_pick_button_style() -> dict[str, str]:
    """Build the style for a pick button.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "padding": PADDING_PICK_BUTTON,
        "backgroundColor": COLOR_PICK_BG,
        "color": COLOR_TEXT,
        "border": thin_border(COLOR_PICK_BORDER),
        "borderRadius": RADIUS,
        "cursor": "pointer",
        "fontSize": FONT_SIZE_XS,
        "marginLeft": "8px"
    }

def get_primary_button_style() -> dict[str, str]:
    """Build a fresh style dict for a primary/save action button.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "padding": PADDING_BUTTON,
        "backgroundColor": COLOR_PRIMARY_BG,
        "color": COLOR_TEXT,
        "border": thin_border(COLOR_PRIMARY_BORDER),
        "borderRadius": RADIUS,
        "cursor": "pointer"
    }

def get_textarea_style(height: str = "auto") -> dict[str, str | int]:
    """Return consistent styling for textarea fields.

    Args:
        height (str): Height of textarea (default "auto").

    Returns:
        dict[str, str | int]: Inline style for textareas.
    """
    return {
        "width": "100%",
        "height": height,
        "backgroundColor": COLOR_INPUT_BG,
        "color": COLOR_INPUT_TEXT,
        "caretColor": COLOR_INPUT_TEXT,
        "border": thin_border(COLOR_INPUT_BORDER),
        "fontSize": FONT_SIZE_BASE,
        "padding": PADDING_INPUT,
        "resize": "none",
        "overflowY": "auto",
        "boxSizing": "border-box"
    }

def get_toolbar_button_disabled_style() -> dict[str, str]:
    """Build the style for a disabled header/toolbar action button.

    Returns:
        dict[str, str]: Anew inline style mapping for a disabled button.
    """
    return {
        **get_toolbar_button_style(),
        "color": COLOR_TEXT_MUTED,
        "cursor": "not-allowed",
        "opacity": "0.5"
    }

def get_toolbar_button_style() -> dict[str, str]:
    """Build the style for a header/toolbar action button.

    Returns:
        dict[str, str]: A new inline style mapping.
    """
    return {
        "padding": PADDING_BUTTON,
        "fontSize": FONT_SIZE_LG,
        "backgroundColor": COLOR_HEADER_BUTTON_BG,
        "color": COLOR_TEXT_LIGHT,
        "border": thin_border(COLOR_PRIMARY_BG),
        "borderRadius": RADIUS,
        "cursor": "pointer"
    }

def thin_border(color: str) -> str:
    """Build a standard thin solid CSS border declaration.

    Args:
        color (str): CSS color for the border.

    Returns:
        str: A CSS border shorthand value such as "1px solid #666".
    """
    return f"{BORDER_WIDTH} solid {color}"