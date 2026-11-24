"""
Standard Classification of Transported Goods (SCTG) Reference Data Dictionary.
Provides official definitions, codes, and human-readable descriptions for all 2-digit SCTG commodity classes
used in the Freight Analysis Framework (FAF6).
"""

from typing import Dict, Optional
import textwrap

# Official SCTG 2-digit commodity code descriptions (2022 FAF6 / Commodity Flow Survey benchmark)
SCTG_DESCRIPTIONS: Dict[int, str] = {
    1: "Live animals and live fish",
    2: "Cereal grains (includes seed)",
    3: "Other agricultural products",
    4: "Animal feed, eggs, honey, and other products of animal origin",
    5: "Meat, poultry, fish, seafood, and their preparations",
    6: "Milled grain products and preparations, and bakery products",
    7: "Other prepared foodstuffs, fats and oils",
    8: "Alcoholic beverages and denatured alcohol",
    9: "Tobacco products",
    10: "Monumental or building stone",
    11: "Natural sands",
    12: "Gravel and crushed stone",
    13: "Other non-metallic minerals, not elsewhere classified",
    14: "Metallic ores and concentrates",
    15: "Coal",
    16: "Crude petroleum",
    17: "Gasoline and aviation turbine fuel",
    18: "Fuel oils",
    19: "Other coal and petroleum products, not elsewhere classified",
    20: "Basic chemicals",
    21: "Pharmaceutical products",
    22: "Fertilizers",
    23: "Other chemical products and preparations",
    24: "Plastics and rubber",
    25: "Logs and other wood in the rough",
    26: "Wood products",
    27: "Pulp, newsprint, paper, and paperboard",
    28: "Paper or paperboard articles",
    29: "Printed products",
    30: "Textiles, leather, and articles of textiles or leather",
    31: "Non-metallic mineral products",
    32: "Base metal in primary or semi-finished forms",
    33: "Articles of base metal",
    34: "Machinery",
    35: "Electronic and other electrical equipment and components",
    36: "Motorized and other vehicles (including parts)",
    37: "Transportation equipment, not elsewhere classified",
    38: "Precision instruments and apparatus",
    39: "Furniture, mattresses, lamps, and lighting fittings",
    40: "Miscellaneous manufactured products",
    41: "Waste and scrap",
    43: "Mixed freight"
}

# Standard explanatory note for charts and public displays
SCTG_EXPLANATORY_NOTE: str = (
    "Commodities are classified using the Standard Classification of Transported Goods (SCTG), "
    "a standardized system used in freight transportation statistics. "
    "Tonnage represents the estimated weight of goods transported."
)

def get_sctg_description(code: int) -> str:
    """Return the official commodity description for an SCTG code."""
    try:
        int_code = int(code)
    except (ValueError, TypeError):
        return f"Commodity SCTG {code}"
    return SCTG_DESCRIPTIONS.get(int_code, f"Commodity SCTG {int_code:02d}")

def get_sctg_code_str(code: int) -> str:
    """Format SCTG code as standard padded string (e.g., 'SCTG 02')."""
    try:
        int_code = int(code)
        return f"SCTG {int_code:02d}"
    except (ValueError, TypeError):
        return f"SCTG {code}"

def get_sctg_display_label(code: int, max_line_width: int = 30) -> str:
    """
    Format a multi-line category label for charts with full commodity name
    and smaller SCTG code notation below.
    """
    desc = get_sctg_description(code)
    code_str = get_sctg_code_str(code)
    wrapped = "<br>".join(textwrap.wrap(desc, width=max_line_width))
    return f"{wrapped}<br><sub>{code_str}</sub>"
