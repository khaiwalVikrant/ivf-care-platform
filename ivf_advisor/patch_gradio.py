"""Patch gradio_client.utils.get_type to handle non-dict schema values.

This fixes a bug in gradio==5.7.1 where get_type crashes with
'TypeError: argument of type bool is not iterable' when a Pydantic
model field has a bool schema value.
"""
import gradio_client.utils as u

path = u.__file__

with open(path) as f:
    src = f.read()

old = 'def get_type(schema: dict):\n    if "const" in schema:'
new = 'def get_type(schema: dict):\n    if not isinstance(schema, dict): return "any"\n    if "const" in schema:'

if old in src:
    with open(path, "w") as f:
        f.write(src.replace(old, new))
    print("Patched gradio_client.utils.get_type successfully")
else:
    print("Patch not needed or already applied")
