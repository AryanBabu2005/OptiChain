"""
FAF6 Geographic Reference and Network Distance Calculations.
Contains verified coordinates (lat, lon) for all 134 domestic FAF6 zones,
representing CFS metropolitan anchor cities and remainder-of-state centroids.
"""

import math
from typing import Dict, Tuple, Optional
from src.data.sctg_codes import SCTG_DESCRIPTIONS, get_sctg_description, SCTG_EXPLANATORY_NOTE

# Complete mapping of 134 FAF6 Domestic Zones
# Numeric Label -> (Short Description, State FIPS, Latitude, Longitude)
FAF6_DOMESTIC_ZONES: Dict[int, Dict[str, any]] = {
    11: {"name": "Birmingham AL", "state": "AL", "state_fips": 1, "lat": 33.5186, "lon": -86.8104},
    12: {"name": "Mobile AL", "state": "AL", "state_fips": 1, "lat": 30.6954, "lon": -88.0399},
    19: {"name": "Rest of AL", "state": "AL", "state_fips": 1, "lat": 32.3668, "lon": -86.2999},
    20: {"name": "Alaska", "state": "AK", "state_fips": 2, "lat": 61.2181, "lon": -149.9003},
    41: {"name": "Phoenix AZ", "state": "AZ", "state_fips": 4, "lat": 33.4484, "lon": -112.0740},
    42: {"name": "Tucson AZ", "state": "AZ", "state_fips": 4, "lat": 32.2226, "lon": -110.9747},
    49: {"name": "Rest of AZ", "state": "AZ", "state_fips": 4, "lat": 34.5000, "lon": -111.5000},
    50: {"name": "Arkansas", "state": "AR", "state_fips": 5, "lat": 34.7465, "lon": -92.2896},
    61: {"name": "Los Angeles CA", "state": "CA", "state_fips": 6, "lat": 34.0522, "lon": -118.2437},
    62: {"name": "Sacramento CA", "state": "CA", "state_fips": 6, "lat": 38.5816, "lon": -121.4944},
    63: {"name": "San Diego CA", "state": "CA", "state_fips": 6, "lat": 32.7157, "lon": -117.1611},
    64: {"name": "San Francisco CA", "state": "CA", "state_fips": 6, "lat": 37.7749, "lon": -122.4194},
    65: {"name": "Fresno CA", "state": "CA", "state_fips": 6, "lat": 36.7468, "lon": -119.7726},
    69: {"name": "Rest of CA", "state": "CA", "state_fips": 6, "lat": 36.5000, "lon": -119.5000},
    81: {"name": "Denver CO", "state": "CO", "state_fips": 8, "lat": 39.7392, "lon": -104.9903},
    89: {"name": "Rest of CO", "state": "CO", "state_fips": 8, "lat": 39.0000, "lon": -105.5000},
    91: {"name": "Hartford CT", "state": "CT", "state_fips": 9, "lat": 41.7658, "lon": -72.6734},
    92: {"name": "New York NY-NJ-CT-PA (CT Part)", "state": "CT", "state_fips": 9, "lat": 41.1792, "lon": -73.1894},
    99: {"name": "Rest of CT", "state": "CT", "state_fips": 9, "lat": 41.6032, "lon": -72.8877},
    101: {"name": "Philadelphia PA-NJ-DE-MD (DE Part)", "state": "DE", "state_fips": 10, "lat": 39.7447, "lon": -75.5484},
    109: {"name": "Rest of DE", "state": "DE", "state_fips": 10, "lat": 39.1582, "lon": -75.5244},
    111: {"name": "Washington DC-VA-MD-WV (DC Part)", "state": "DC", "state_fips": 11, "lat": 38.9072, "lon": -77.0369},
    121: {"name": "Jacksonville FL-GA (FL Part)", "state": "FL", "state_fips": 12, "lat": 30.3322, "lon": -81.6557},
    122: {"name": "Miami FL", "state": "FL", "state_fips": 12, "lat": 25.7617, "lon": -80.1918},
    123: {"name": "Orlando FL", "state": "FL", "state_fips": 12, "lat": 28.5383, "lon": -81.3792},
    124: {"name": "Tampa FL", "state": "FL", "state_fips": 12, "lat": 27.9506, "lon": -82.4572},
    129: {"name": "Rest of FL", "state": "FL", "state_fips": 12, "lat": 29.6516, "lon": -82.3248},
    131: {"name": "Atlanta GA", "state": "GA", "state_fips": 13, "lat": 33.7490, "lon": -84.3880},
    132: {"name": "Savannah GA", "state": "GA", "state_fips": 13, "lat": 32.0809, "lon": -81.0912},
    139: {"name": "Rest of GA", "state": "GA", "state_fips": 13, "lat": 32.8407, "lon": -83.6324},
    151: {"name": "Honolulu HI", "state": "HI", "state_fips": 15, "lat": 21.3069, "lon": -157.8583},
    159: {"name": "Rest of HI", "state": "HI", "state_fips": 15, "lat": 20.7984, "lon": -156.3319},
    160: {"name": "Idaho", "state": "ID", "state_fips": 16, "lat": 43.6150, "lon": -116.2023},
    171: {"name": "Chicago IL-IN-WI (IL Part)", "state": "IL", "state_fips": 17, "lat": 41.8781, "lon": -87.6298},
    172: {"name": "St. Louis MO-IL (IL Part)", "state": "IL", "state_fips": 17, "lat": 38.6270, "lon": -90.1500},
    179: {"name": "Rest of IL", "state": "IL", "state_fips": 17, "lat": 40.6936, "lon": -89.5890},
    181: {"name": "Chicago IL-IN-WI (IN Part)", "state": "IN", "state_fips": 18, "lat": 41.6020, "lon": -87.3371},
    182: {"name": "Indianapolis IN", "state": "IN", "state_fips": 18, "lat": 39.7684, "lon": -86.1581},
    183: {"name": "Fort Wayne IN", "state": "IN", "state_fips": 18, "lat": 41.0793, "lon": -85.1394},
    189: {"name": "Rest of IN", "state": "IN", "state_fips": 18, "lat": 40.4173, "lon": -86.8753},
    191: {"name": "Des Moines IA", "state": "IA", "state_fips": 19, "lat": 41.5868, "lon": -93.6250},
    199: {"name": "Rest of IA", "state": "IA", "state_fips": 19, "lat": 42.0308, "lon": -93.6319},
    201: {"name": "Kansas City MO-KS (KS Part)", "state": "KS", "state_fips": 20, "lat": 39.1155, "lon": -94.6268},
    202: {"name": "Wichita KS", "state": "KS", "state_fips": 20, "lat": 37.6872, "lon": -97.3301},
    209: {"name": "Rest of KS", "state": "KS", "state_fips": 20, "lat": 38.5000, "lon": -98.0000},
    211: {"name": "Cincinnati OH-KY-IN (KY Part)", "state": "KY", "state_fips": 21, "lat": 39.0837, "lon": -84.5086},
    212: {"name": "Louisville KY-IN (KY Part)", "state": "KY", "state_fips": 21, "lat": 38.2527, "lon": -85.7585},
    219: {"name": "Rest of KY", "state": "KY", "state_fips": 21, "lat": 37.8393, "lon": -84.2700},
    221: {"name": "Baton Rouge LA", "state": "LA", "state_fips": 22, "lat": 30.4515, "lon": -91.1871},
    222: {"name": "Lake Charles-Jennings LA", "state": "LA", "state_fips": 22, "lat": 30.2266, "lon": -93.2174},
    223: {"name": "New Orleans LA-MS (LA Part)", "state": "LA", "state_fips": 22, "lat": 29.9511, "lon": -90.0715},
    229: {"name": "Rest of LA", "state": "LA", "state_fips": 22, "lat": 31.3113, "lon": -92.4451},
    230: {"name": "Maine", "state": "ME", "state_fips": 23, "lat": 43.6591, "lon": -70.2568},
    241: {"name": "Baltimore MD", "state": "MD", "state_fips": 24, "lat": 39.2904, "lon": -76.6122},
    242: {"name": "Washington DC-VA-MD-WV (MD Part)", "state": "MD", "state_fips": 24, "lat": 39.0000, "lon": -77.1000},
    249: {"name": "Rest of MD", "state": "MD", "state_fips": 24, "lat": 39.0458, "lon": -76.6413},
    251: {"name": "Boston MA-RI-NH-CT (MA Part)", "state": "MA", "state_fips": 25, "lat": 42.3601, "lon": -71.0589},
    259: {"name": "Rest of MA", "state": "MA", "state_fips": 25, "lat": 42.2700, "lon": -71.8000},
    261: {"name": "Detroit MI", "state": "MI", "state_fips": 26, "lat": 42.3314, "lon": -83.0458},
    262: {"name": "Grand Rapids MI", "state": "MI", "state_fips": 26, "lat": 42.9634, "lon": -85.6681},
    269: {"name": "Rest of MI", "state": "MI", "state_fips": 26, "lat": 43.5000, "lon": -84.5000},
    271: {"name": "Minneapolis-St. Paul MN-WI (MN Part)", "state": "MN", "state_fips": 27, "lat": 44.9778, "lon": -93.2650},
    279: {"name": "Rest of MN", "state": "MN", "state_fips": 27, "lat": 46.5000, "lon": -94.5000},
    280: {"name": "Mississippi", "state": "MS", "state_fips": 28, "lat": 32.2988, "lon": -90.1848},
    291: {"name": "Kansas City MO-KS (MO Part)", "state": "MO", "state_fips": 29, "lat": 39.0997, "lon": -94.5786},
    292: {"name": "St. Louis MO-IL (MO Part)", "state": "MO", "state_fips": 29, "lat": 38.6270, "lon": -90.1994},
    299: {"name": "Rest of MO", "state": "MO", "state_fips": 29, "lat": 38.0000, "lon": -92.5000},
    300: {"name": "Montana", "state": "MT", "state_fips": 30, "lat": 45.7833, "lon": -108.5007},
    311: {"name": "Omaha NE-IA (NE Part)", "state": "NE", "state_fips": 31, "lat": 41.2565, "lon": -95.9345},
    319: {"name": "Rest of NE", "state": "NE", "state_fips": 31, "lat": 41.5000, "lon": -99.5000},
    321: {"name": "Las Vegas NV", "state": "NV", "state_fips": 32, "lat": 36.1699, "lon": -115.1398},
    329: {"name": "Rest of NV", "state": "NV", "state_fips": 32, "lat": 39.5296, "lon": -119.8138},
    331: {"name": "Boston MA-RI-NH-CT (NH Part)", "state": "NH", "state_fips": 33, "lat": 42.9956, "lon": -71.4548},
    339: {"name": "Rest of NH", "state": "NH", "state_fips": 33, "lat": 43.5000, "lon": -71.5000},
    341: {"name": "New York NY-NJ-CT-PA (NJ Part)", "state": "NJ", "state_fips": 34, "lat": 40.7357, "lon": -74.1724},
    342: {"name": "Philadelphia PA-NJ-DE-MD (NJ Part)", "state": "NJ", "state_fips": 34, "lat": 39.9259, "lon": -75.1196},
    350: {"name": "New Mexico", "state": "NM", "state_fips": 35, "lat": 35.0844, "lon": -106.6504},
    361: {"name": "Albany NY", "state": "NY", "state_fips": 36, "lat": 42.6526, "lon": -73.7562},
    362: {"name": "Buffalo NY", "state": "NY", "state_fips": 36, "lat": 42.8864, "lon": -78.8784},
    363: {"name": "New York NY-NJ-CT-PA (NY Part)", "state": "NY", "state_fips": 36, "lat": 40.7128, "lon": -74.0060},
    364: {"name": "Rochester NY", "state": "NY", "state_fips": 36, "lat": 43.1566, "lon": -77.6088},
    369: {"name": "Rest of NY", "state": "NY", "state_fips": 36, "lat": 43.0481, "lon": -76.1474},
    371: {"name": "Charlotte NC-SC (NC Part)", "state": "NC", "state_fips": 37, "lat": 35.2271, "lon": -80.8431},
    372: {"name": "Greensboro NC", "state": "NC", "state_fips": 37, "lat": 36.0726, "lon": -79.7920},
    373: {"name": "Raleigh-Durham NC", "state": "NC", "state_fips": 37, "lat": 35.7796, "lon": -78.6382},
    379: {"name": "Rest of NC", "state": "NC", "state_fips": 37, "lat": 35.5000, "lon": -80.0000},
    380: {"name": "North Dakota", "state": "ND", "state_fips": 38, "lat": 46.8083, "lon": -100.7837},
    391: {"name": "Cincinnati OH-KY-IN (OH Part)", "state": "OH", "state_fips": 39, "lat": 39.1031, "lon": -84.5120},
    392: {"name": "Cleveland OH", "state": "OH", "state_fips": 39, "lat": 41.4993, "lon": -81.6944},
    393: {"name": "Columbus OH", "state": "OH", "state_fips": 39, "lat": 39.9612, "lon": -82.9988},
    394: {"name": "Dayton OH", "state": "OH", "state_fips": 39, "lat": 39.7589, "lon": -84.1916},
    395: {"name": "Toledo OH", "state": "OH", "state_fips": 39, "lat": 41.6528, "lon": -83.5379},
    399: {"name": "Rest of OH", "state": "OH", "state_fips": 39, "lat": 40.5000, "lon": -82.5000},
    401: {"name": "Oklahoma City OK", "state": "OK", "state_fips": 40, "lat": 35.4676, "lon": -97.5164},
    402: {"name": "Tulsa OK", "state": "OK", "state_fips": 40, "lat": 36.1540, "lon": -95.9928},
    409: {"name": "Rest of OK", "state": "OK", "state_fips": 40, "lat": 35.5000, "lon": -97.5000},
    411: {"name": "Portland OR-WA (OR Part)", "state": "OR", "state_fips": 41, "lat": 45.5152, "lon": -122.6784},
    419: {"name": "Rest of OR", "state": "OR", "state_fips": 41, "lat": 44.0000, "lon": -121.0000},
    421: {"name": "Philadelphia PA-NJ-DE-MD (PA Part)", "state": "PA", "state_fips": 42, "lat": 39.9526, "lon": -75.1652},
    422: {"name": "Pittsburgh PA-OH-WV (PA Part)", "state": "PA", "state_fips": 42, "lat": 40.4406, "lon": -79.9959},
    423: {"name": "Allentown PA-NJ (PA Part)", "state": "PA", "state_fips": 42, "lat": 40.6084, "lon": -75.4902},
    429: {"name": "Rest of PA", "state": "PA", "state_fips": 42, "lat": 40.8000, "lon": -77.5000},
    441: {"name": "Boston MA-RI-NH-CT (RI Part)", "state": "RI", "state_fips": 44, "lat": 41.8240, "lon": -71.4128},
    451: {"name": "Charleston SC", "state": "SC", "state_fips": 45, "lat": 32.7765, "lon": -79.9311},
    452: {"name": "Greenville SC", "state": "SC", "state_fips": 45, "lat": 34.8526, "lon": -82.3940},
    459: {"name": "Rest of SC", "state": "SC", "state_fips": 45, "lat": 34.0000, "lon": -81.0000},
    460: {"name": "South Dakota", "state": "SD", "state_fips": 46, "lat": 43.5460, "lon": -96.7313},
    471: {"name": "Memphis TN-MS-AR (TN Part)", "state": "TN", "state_fips": 47, "lat": 35.1495, "lon": -90.0490},
    472: {"name": "Nashville TN", "state": "TN", "state_fips": 47, "lat": 36.1627, "lon": -86.7816},
    473: {"name": "Knoxville TN", "state": "TN", "state_fips": 47, "lat": 35.9606, "lon": -83.9207},
    479: {"name": "Rest of TN", "state": "TN", "state_fips": 47, "lat": 35.8000, "lon": -86.0000},
    481: {"name": "Austin TX", "state": "TX", "state_fips": 48, "lat": 30.2672, "lon": -97.7431},
    482: {"name": "Beaumont TX", "state": "TX", "state_fips": 48, "lat": 30.0802, "lon": -94.1266},
    483: {"name": "Corpus Christi TX", "state": "TX", "state_fips": 48, "lat": 27.8006, "lon": -97.3964},
    484: {"name": "Dallas-Fort Worth TX-OK (TX Part)", "state": "TX", "state_fips": 48, "lat": 32.7767, "lon": -96.7970},
    485: {"name": "El Paso TX-NM (TX Part)", "state": "TX", "state_fips": 48, "lat": 31.7619, "lon": -106.4850},
    486: {"name": "Houston TX", "state": "TX", "state_fips": 48, "lat": 29.7604, "lon": -95.3698},
    487: {"name": "Laredo TX", "state": "TX", "state_fips": 48, "lat": 27.5036, "lon": -99.5076},
    488: {"name": "San Antonio TX", "state": "TX", "state_fips": 48, "lat": 29.4241, "lon": -98.4936},
    489: {"name": "Rest of TX", "state": "TX", "state_fips": 48, "lat": 31.5000, "lon": -99.0000},
    491: {"name": "Salt Lake City UT", "state": "UT", "state_fips": 49, "lat": 40.7608, "lon": -111.8910},
    499: {"name": "Rest of UT", "state": "UT", "state_fips": 49, "lat": 39.5000, "lon": -111.5000},
    500: {"name": "Vermont", "state": "VT", "state_fips": 50, "lat": 44.4759, "lon": -73.2121},
    511: {"name": "Richmond VA", "state": "VA", "state_fips": 51, "lat": 37.5407, "lon": -77.4360},
    512: {"name": "Virginia Beach-Norfolk VA-NC (VA Part)", "state": "VA", "state_fips": 51, "lat": 36.8529, "lon": -75.9780},
    513: {"name": "Washington DC-VA-MD-WV (VA Part)", "state": "VA", "state_fips": 51, "lat": 38.8816, "lon": -77.0910},
    519: {"name": "Rest of VA", "state": "VA", "state_fips": 51, "lat": 37.5000, "lon": -79.0000},
    531: {"name": "Seattle WA", "state": "WA", "state_fips": 53, "lat": 47.6062, "lon": -122.3321},
    532: {"name": "Portland OR-WA (WA Part)", "state": "WA", "state_fips": 53, "lat": 45.6387, "lon": -122.6615},
    539: {"name": "Rest of WA", "state": "WA", "state_fips": 53, "lat": 47.5000, "lon": -120.5000},
    540: {"name": "West Virginia", "state": "WV", "state_fips": 54, "lat": 38.3498, "lon": -81.6326},
    551: {"name": "Milwaukee WI", "state": "WI", "state_fips": 55, "lat": 43.0389, "lon": -87.9065},
    559: {"name": "Rest of WI", "state": "WI", "state_fips": 55, "lat": 44.5000, "lon": -89.5000},
    560: {"name": "Wyoming", "state": "WY", "state_fips": 56, "lat": 41.1399, "lon": -104.8202},
}

# Mode Definitions from Official Metadata
FAF6_MODES: Dict[int, str] = {
    1: "Truck",
    2: "Rail",
    3: "Water",
    4: "Air (include truck-air)",
    5: "Multiple modes & mail",
    6: "Pipeline",
    7: "Other and unknown",
    8: "No domestic mode"
}

# Trade Type Definitions
FAF6_TRADE_TYPES: Dict[int, str] = {
    1: "Domestic flows",
    2: "Import flows",
    3: "Export flows"
}

# Mode circuity factor relative to great circle distance
# Sourced from US BTS / FHWA Circuity Studies
CIRCUITY_FACTORS: Dict[int, float] = {
    1: 1.17,  # Highway truck network
    2: 1.25,  # Rail network
    3: 1.45,  # Inland waterway / coastal routing
    4: 1.05,  # Air direct flight path
    5: 1.20,  # Multimodal intermodal
    6: 1.10,  # Pipeline right of way
    7: 1.20,  # Other
    8: 1.00   # None
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great circle distance in statute miles between two points.
    """
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def get_corridor_distance(orig_zone: int, dest_zone: int, mode: int = 1) -> float:
    """
    Get estimated network route distance in miles between two FAF zones.
    If orig == dest (intra-regional), an intra-regional average radius of 25 miles is applied.
    """
    if orig_zone == dest_zone:
        return 25.0

    z_orig = FAF6_DOMESTIC_ZONES.get(orig_zone)
    z_dest = FAF6_DOMESTIC_ZONES.get(dest_zone)

    if not z_orig or not z_dest:
        return 100.0  # Fallback default distance

    gc_dist = haversine_distance(z_orig["lat"], z_orig["lon"], z_dest["lat"], z_dest["lon"])
    circuity = CIRCUITY_FACTORS.get(mode, 1.20)
    return round(max(gc_dist * circuity, 15.0), 1)

def get_zone_name(zone_code: int) -> str:
    """Return friendly name for zone code."""
    zone = FAF6_DOMESTIC_ZONES.get(zone_code)
    return zone["name"] if zone else f"Zone {zone_code}"

def get_zone_coords(zone_code: int) -> Optional[Tuple[float, float]]:
    """Return (lat, lon) tuple for zone."""
    zone = FAF6_DOMESTIC_ZONES.get(zone_code)
    return (zone["lat"], zone["lon"]) if zone else None
