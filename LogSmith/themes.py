# LogSmith/themes.py

from typing import Dict

from .levels import LevelStyle
from .colors import CPrint


LIGHT_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = CPrint.FG.DIM_GREY, intensity=CPrint.Intensity.DIM),
    10: LevelStyle(fg = CPrint.FG.SKY_BLUE, intensity=CPrint.Intensity.DIM),
    20: LevelStyle(fg = CPrint.FG.GREEN),
    30: LevelStyle(fg = CPrint.FG.ORANGE, intensity=CPrint.Intensity.BOLD),
    40: LevelStyle(fg = CPrint.FG.BRIGHT_RED, intensity=CPrint.Intensity.BOLD),
    50: LevelStyle(fg = CPrint.FG.BRIGHT_YELLOW, bg = CPrint.BG.RED, intensity = CPrint.Intensity.BOLD,
                   styles    = (CPrint.Style.UNDERLINE,)
    )
}

DARK_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = CPrint.FG.BRIGHT_BLACK),
    10: LevelStyle(fg = CPrint.FG.BLUE),
    20: LevelStyle(fg = CPrint.FG.GREEN),
    30: LevelStyle(fg = CPrint.FG.ORANGE),
    40: LevelStyle(fg = CPrint.FG.RED),
    50: LevelStyle(fg = CPrint.FG.YELLOW, bg = CPrint.BG.RED,
                   styles = (CPrint.Style.UNDERLINE,)
    )
}

NEON_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = "38;5;51"),
    10: LevelStyle(fg = "38;5;201"),
    20: LevelStyle(fg = "38;5;46"),
    30: LevelStyle(fg = "38;5;226"),
    40: LevelStyle(fg = "38;5;196"),
    50: LevelStyle(fg = "38;5;15", bg = "48;5;196"),
}

PASTEL_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = "38;5;153", intensity = CPrint.Intensity.DIM),     # pastel lavender
    10: LevelStyle(fg = "38;5;159", intensity = CPrint.Intensity.NORMAL),  # pastel sky blue
    20: LevelStyle(fg = "38;5;151", intensity = CPrint.Intensity.NORMAL),  # pastel mint
    30: LevelStyle(fg = "38;5;223", intensity = CPrint.Intensity.BOLD),    # pastel peach
    40: LevelStyle(fg = "38;5;217", intensity = CPrint.Intensity.BOLD),    # pastel pink
    50: LevelStyle(fg = "38;5;231",
                   bg = "48;5;217",
                   intensity = CPrint.Intensity.BOLD,
                   styles = (CPrint.Style.UNDERLINE,),
    ),
}

FIRE_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = "38;5;130", intensity = CPrint.Intensity.DIM),       # dim ember orange
    10: LevelStyle(fg = "38;5;166", intensity = CPrint.Intensity.NORMAL),    # warm orange
    20: LevelStyle(fg = "38;5;208", intensity = CPrint.Intensity.NORMAL),    # bright orange
    30: LevelStyle(fg = "38;5;214", intensity = CPrint.Intensity.BOLD),      # amber
    40: LevelStyle(fg = "38;5;196", intensity = CPrint.Intensity.BOLD),      # red
    50: LevelStyle(
            fg = "38;5;226",                                              # bright yellow
            bg = "48;5;196",                                              # red background
            intensity = CPrint.Intensity.BOLD,
            styles = (CPrint.Style.UNDERLINE,)
        ),
}

OCEAN_THEME: Dict[int, LevelStyle] = {
    5:  LevelStyle(fg = "38;5;24", intensity = CPrint.Intensity.DIM),        # deep navy
    10: LevelStyle(fg = "38;5;31", intensity = CPrint.Intensity.NORMAL),     # muted blue
    20: LevelStyle(fg = "38;5;37", intensity = CPrint.Intensity.NORMAL),     # teal
    30: LevelStyle(fg = "38;5;43", intensity = CPrint.Intensity.BOLD),       # aqua
    40: LevelStyle(fg = "38;5;81", intensity = CPrint.Intensity.BOLD),       # bright cyan
    50: LevelStyle(
            fg = CPrint.FG.WHITE,
            bg = "48;5;24",                                               # deep navy background
            intensity = CPrint.Intensity.BOLD,
            styles = (CPrint.Style.UNDERLINE,)
        ),
}
