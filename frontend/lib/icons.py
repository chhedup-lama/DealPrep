"""A single, self-contained monochrome icon set built in Phosphor Icons'
visual language (bold, geometric, one color via currentColor), used
everywhere in the app instead of emoji.

There's no React runtime here to install @phosphor-icons/react into — this
is a Streamlit/Python app — so icons are hand-authored inline SVGs using
only primitive shapes (circle/rect/line/polygon) and straight-line/simple-
arc path commands (no bezier curves, to keep every glyph easy to verify by
inspection). "Weight" is stroke-width on the same shape, not a second path
set: BOLD = 2.4, REGULAR = 1.5 — matching Phosphor's own bold/regular
distinction without doubling the amount of hand-authored geometry.

Two render paths, same shape data, so an icon looks identical everywhere:
- `svg()` — inline <svg> for content we fully control via st.markdown.
- `mask_data_uri()` — a CSS mask-image source for native Streamlit widgets
  (st.button, st.page_link) whose label can't hold raw HTML.
"""

from __future__ import annotations

import base64

BOLD = 2.4
REGULAR = 1.5
WEIGHTS = {"bold": BOLD, "regular": REGULAR}

# viewBox 0 0 24 24. Primitives and straight-line/simple-arc paths only.
_SHAPES: dict[str, str] = {
    "house": (
        '<polyline points="4,11 12,4 20,11"/>'
        '<rect x="6" y="10" width="12" height="10" rx="1"/>'
        '<rect x="10" y="15" width="4" height="6"/>'
    ),
    "buildings": (
        '<rect x="4" y="7" width="7" height="14" rx="1"/>'
        '<rect x="13" y="10" width="7" height="11" rx="1"/>'
        '<line x1="3" y1="21" x2="21" y2="21"/>'
    ),
    "briefcase": (
        '<rect x="3" y="8" width="18" height="12" rx="2"/>'
        '<path d="M9 8V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" fill="none"/>'
        '<line x1="3" y1="13" x2="21" y2="13"/>'
    ),
    "users": (
        '<circle cx="9" cy="8" r="3.2"/>'
        '<path d="M3.3 20a5.7 6 0 0 1 11.4 0" fill="none"/>'
        '<circle cx="17.2" cy="9.2" r="2.3"/>'
        '<path d="M14.8 20a4.4 4.9 0 0 1 6.8-4.2" fill="none"/>'
    ),
    "ticket": (
        '<rect x="3" y="7" width="18" height="10" rx="2"/>'
        '<line x1="14" y1="7" x2="14" y2="17" stroke-dasharray="2,2"/>'
    ),
    "map": (
        '<polygon points="9,4 4,6 4,20 9,18 15,20 20,18 20,4 15,6"/>'
        '<line x1="9" y1="4" x2="9" y2="18"/>'
        '<line x1="15" y1="6" x2="15" y2="20"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="9"/>'
        '<line x1="12" y1="12" x2="12" y2="7"/>'
        '<line x1="12" y1="12" x2="15.3" y2="14"/>'
    ),
    "thumbs-up": (
        '<rect x="3" y="11" width="4" height="10" rx="1" fill="currentColor" stroke="none"/>'
        '<path d="M9 21h7.6a2 2 0 0 0 1.9-1.4l1.6-6A2 2 0 0 0 18.2 11H13V6.2a1.5 1.5 0 0 0-3 0V10L9 11z" '
        'fill="currentColor" stroke="none"/>'
    ),
    "arrow-up": (
        '<line x1="12" y1="19" x2="12" y2="6"/>'
        '<polyline points="7,11 12,6 17,11"/>'
    ),
    "check": ('<polyline points="4,13 9,18 20,6"/>'),
    "warning": (
        '<path d="M12 4L3 20h18L12 4z" fill="none"/>'
        '<line x1="12" y1="10" x2="12" y2="15"/>'
        '<circle cx="12" cy="17.7" r="0.9" fill="currentColor" stroke="none"/>'
    ),
    "pencil": (
        '<path d="M4 20l1-5L16 4l4 4L9 19l-5 1z" fill="none"/>'
        '<line x1="13" y1="6.5" x2="17.5" y2="11"/>'
    ),
    "phone": (
        '<rect x="7" y="2" width="10" height="20" rx="2"/>'
        '<circle cx="12" cy="18" r="0.9" fill="currentColor" stroke="none"/>'
    ),
    "shield": ('<polygon points="12,3 18,5.5 18,11 12,20 6,11 6,5.5"/>'),
    "eye": (
        '<path d="M2 12 A10 6 0 0 1 22 12 A10 6 0 0 1 2 12 Z" fill="none"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
}


def svg(name: str, weight: str = "bold", size: int = 18, color: str = "currentColor") -> str:
    """Inline <svg> markup for embedding directly in a st.markdown block."""
    shape = _SHAPES[name]
    stroke_width = WEIGHTS[weight]
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:block;flex-shrink:0;">{shape}</svg>'
    )


def mask_data_uri(name: str, weight: str = "bold") -> str:
    """The same icon as a data: URI for CSS mask-image, so it can be
    attached to native Streamlit widgets (buttons, page links) whose label
    can't hold raw HTML. The mask "ink" color doesn't matter — only its
    alpha shape does; visible color comes entirely from the
    `background-color: currentColor` wherever the mask is applied."""
    shape = _SHAPES[name]
    stroke_width = WEIGHTS[weight]
    markup = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="black" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{shape}</svg>'
    )
    encoded = base64.b64encode(markup.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def image_data_uri(name: str, weight: str = "bold", size: int = 24, color: str = "currentColor") -> str:
    """A single-color SVG data URI for embedding via Markdown image syntax
    (e.g. `st.tabs` labels, which render GitHub-flavored Markdown images
    like icons but can't hold raw HTML/CSS masks). Unlike mask_data_uri(),
    the color is baked directly into the glyph since an <img> src has no
    CSS currentColor to inherit through."""
    shape = _SHAPES[name]
    stroke_width = WEIGHTS[weight]
    markup = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{shape}</svg>'
    )
    encoded = base64.b64encode(markup.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
