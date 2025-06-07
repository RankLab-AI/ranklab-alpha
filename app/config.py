## Tailwind-like theme configuration for RankLab

# Color palette
COLORS = {
    "persian-rose": "#F61067",
    "sunflower-yellow": "#FFE033",
    "pigment-green": "#00E05E",
    "space-cadet": "#392D62",
    "dark-space-cadet": "#322854",
    "darker-space-cadet": "#2a2346",
    "darkest-space-cadet": "#1e1a31",
    "off-white": "#FCFCFF",
}

# Theme definitions
THEMES = {
    "light": {
        "background": COLORS["off-white"],
        "primary": COLORS["persian-rose"],
        "text": COLORS["darker-space-cadet"],  # default dark text on light background
        "logo_file": "logo-rose.png",
        "sidebar_bg": COLORS["off-white"],
        "sidebar_text": COLORS["darker-space-cadet"],
        "sidebar_border": COLORS["pigment-green"],
        "sidebar_hover": COLORS["space-cadet"],
    },
    "dark": {
        "background": COLORS["darkest-space-cadet"],
        "primary": COLORS["space-cadet"],
        "text": COLORS["off-white"],  # light text on dark background
        "logo_file": "logo-white.png",
        "sidebar_bg": COLORS["space-cadet"],
        "sidebar_text": COLORS["off-white"],
        "sidebar_border": COLORS["darker-space-cadet"],
        "sidebar_hover": COLORS["sunflower-yellow"],
    },
}

# Example usage in Jinja template:
# <body style="background-color: {{ THEMES[theme]['background'] }}; color: {{ THEMES[theme]['text'] }};">
# <button style="background-color: {{ THEMES[theme]['primary'] }};">Primary Action</button>
