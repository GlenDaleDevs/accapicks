"""Favourable Matchups model, vendored from the PredictionModel project.

Source of truth lives at C:\\Users\\glend\\Projects\\PredictionModel — see its
README for how the cross-division ladder and the measured division offsets
work. Only cli.py is omitted; everything else is a verbatim copy apart from
config.CACHE_DIR, which is made env-overridable here because the AccaPicks
container runs as a non-root user on an ephemeral filesystem.

Swap this for a real dependency once PredictionModel has a git remote and
packaging: the import path is identical, so nothing calling it needs to change.
"""
