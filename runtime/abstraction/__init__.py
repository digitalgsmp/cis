"""
abstraction/__init__.py — CIS Abstraction Layer
The dispatch boundary between the control plane and Hermes backend.

Per DEV-PIVOT-05 §5: Maps CIS verbs to Hermes mechanisms.
Isolates CIS from Hermes version changes — only this module changes
when Hermes updates.
"""
