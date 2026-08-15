"""Team-name reconciliation: The-Odds-API vocabulary -> football-data.co.uk.

The two feeds disagree on most clubs outside the Premier League. The mapping is
an EXPLICIT table rather than suffix-stripping heuristics, because the obvious
heuristic is actively wrong: stripping "City"/"Rovers" collapses Bristol City
and Bristol Rovers onto the same key, and the same trap exists for the several
Counties, Towns and Uniteds in Leagues One and Two.

Only a light normaliser (case, punctuation, trailing FC/AFC) is applied
automatically; everything else is listed by hand.
"""

import re

# The-Odds-API name -> football-data.co.uk name
ALIASES = {
    # Premier League
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    "Brighton and Hove Albion": "Brighton",
    "Leeds United": "Leeds",
    # Championship
    "Birmingham City": "Birmingham",
    "Blackburn Rovers": "Blackburn",
    "Charlton Athletic": "Charlton",
    "Coventry City": "Coventry",
    "Derby County": "Derby",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leicester City": "Leicester",
    "Norwich City": "Norwich",
    "Oxford United": "Oxford",
    "Preston North End": "Preston",
    "Queens Park Rangers": "QPR",
    "Sheffield Wednesday": "Sheffield Weds",
    "Stoke City": "Stoke",
    "Swansea City": "Swansea",
    "West Bromwich Albion": "West Brom",
    # League One
    "Bolton Wanderers": "Bolton",
    "Bradford City": "Bradford",
    "Burton Albion": "Burton",
    "Cardiff City": "Cardiff",
    "Doncaster Rovers": "Doncaster",
    "Exeter City": "Exeter",
    "Huddersfield Town": "Huddersfield",
    "Lincoln City": "Lincoln",
    "Mansfield Town": "Mansfield",
    "Northampton Town": "Northampton",
    "Peterborough United": "Peterboro",
    "Plymouth Argyle": "Plymouth",
    "Rotherham United": "Rotherham",
    "Stockport County": "Stockport",
    "Wigan Athletic": "Wigan",
    "Wimbledon": "AFC Wimbledon",
    "Wycombe Wanderers": "Wycombe",
    # League Two
    "Accrington Stanley": "Accrington",
    "Bristol Rovers": "Bristol Rvs",
    "Cambridge United": "Cambridge",
    "Cheltenham Town": "Cheltenham",
    "Colchester United": "Colchester",
    "Crewe Alexandra": "Crewe",
    "Grimsby Town": "Grimsby",
    "Oldham Athletic": "Oldham",
    "Salford City": "Salford",
    "Shrewsbury Town": "Shrewsbury",
    "Swindon Town": "Swindon",
    "Tranmere Rovers": "Tranmere",
    # Promoted from the National League
    "York City": "York",
    # Other National League clubs (ladder-only, but mapped for completeness)
    "Boston United": "Boston Utd",
    "Forest Green Rovers": "Forest Green",
    "FC Halifax Town": "Halifax",
    "Hartlepool United": "Hartlepool",
    "Southend United": "Southend",
    "Sutton United": "Sutton",
    "Yeovil Town": "Yeovil",
}

_PUNCT = re.compile(r"[^a-z0-9 ]")
_TRAILING_CLUB_SUFFIX = re.compile(r"\s+(fc|afc)$")


def normalise(name):
    """Lowercase, strip punctuation and a trailing FC/AFC. Nothing more --
    anything cleverer risks merging two genuinely different clubs."""
    if not name:
        return ""
    n = name.lower().strip()
    n = _PUNCT.sub("", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = _TRAILING_CLUB_SUFFIX.sub("", n).strip()
    return n


# Aliases are matched on the normalised form so that incidental suffixes in the
# feed ("Stockport County FC") still hit the "Stockport County" entry.
_ALIAS_INDEX = {normalise(k): v for k, v in ALIASES.items()}


def build_index(ladder):
    """Map normalised ladder names -> canonical ladder names."""
    return {normalise(team): team for team in ladder}


def resolve(name, index):
    """Return the canonical ladder name, or None if unresolved."""
    key = normalise(name)

    # Direct hit on the ladder vocabulary wins before any aliasing.
    if key in index:
        return index[key]

    alias = _ALIAS_INDEX.get(key)
    if alias:
        return index.get(normalise(alias))

    return None
