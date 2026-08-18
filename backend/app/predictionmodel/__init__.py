"""Football results and league tables, vendored from the PredictionModel project.

Source of truth lives at C:\\Users\\glend\\Projects\\PredictionModel — see its
README for how the cross-division ladder and the measured division offsets
work. Only cli.py is omitted; everything else is a verbatim copy apart from
config.CACHE_DIR, which is made env-overridable here because the AccaPicks
container runs as a non-root user on an ephemeral filesystem.

The Favourable Matchups feature this was originally vendored for has been
removed — what remains is the football-data.co.uk results layer and the
home/away table builder, which the Form tab's standings are built from.
"""
