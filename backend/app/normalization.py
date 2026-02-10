"""Team name normalization for fuzzy matching during settlement."""

# Common abbreviation mappings
ABBREVIATIONS = {
    "man utd": "manchester united",
    "man united": "manchester united",
    "man city": "manchester city",
    "wolves": "wolverhampton wanderers",
    "spurs": "tottenham hotspur",
    "brighton": "brighton and hove albion",
    "west ham": "west ham united",
    "newcastle": "newcastle united",
    "nottm forest": "nottingham forest",
    "nott'm forest": "nottingham forest",
    "sheffield utd": "sheffield united",
    "leeds": "leeds united",
    "leicester": "leicester city",
    "norwich": "norwich city",
    "west brom": "west bromwich albion",
    "stoke": "stoke city",
    "hull": "hull city",
    "swansea": "swansea city",
    "cardiff": "cardiff city",
    "qpr": "queens park rangers",
    "atletico madrid": "atletico de madrid",
    "atletico": "atletico de madrid",
    "real sociedad": "real sociedad de futbol",
    "betis": "real betis balompie",
    "real betis": "real betis balompie",
    "hertha bsc": "hertha berlin",
    "gladbach": "borussia monchengladbach",
    "monchengladbach": "borussia monchengladbach",
    "dortmund": "borussia dortmund",
    "bayern": "bayern munich",
    "fc bayern": "bayern munich",
    "psg": "paris saint-germain",
    "paris saint germain": "paris saint-germain",
    "saint-etienne": "as saint-etienne",
    "st etienne": "as saint-etienne",
}

# Suffixes to strip (order matters — check longer ones first)
STRIP_SUFFIXES = [" afc", " fc", " sc", " cf", " ssc", " us", " as"]


def normalize(name: str) -> str:
    """Normalize a team name for comparison.

    Lowercases, strips whitespace, removes common suffixes,
    and applies abbreviation mappings.
    """
    if not name:
        return ""

    n = name.lower().strip()

    # Strip common suffixes
    for suffix in STRIP_SUFFIXES:
        if n.endswith(suffix):
            n = n[: -len(suffix)].strip()
            break

    # Check abbreviation map
    if n in ABBREVIATIONS:
        return ABBREVIATIONS[n]

    return n
