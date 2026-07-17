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
