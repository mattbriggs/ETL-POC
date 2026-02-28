"""I/O isolation layer.

All filesystem and subprocess interactions are confined to this sub-package.
Modules outside ``dita_etl.io`` must not import ``os``, ``shutil``, or
``subprocess`` directly — they receive I/O capabilities via dependency
injection.
"""
