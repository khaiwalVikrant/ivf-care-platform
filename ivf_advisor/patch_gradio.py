"""Patch gradio_client.utils to handle complex Pydantic schemas in gradio==5.7.1.

This fixes APIInfoParseError and TypeError crashes when tool return types
contain complex nested schemas (e.g. Optional fields, dict[str, list[str]]).
"""
import gradio_client.utils as u

path = u.__file__

with open(path) as f:
    src = f.read()

patched = False

# Patch 1: get_type — handle non-dict schema values
old1 = 'def get_type(schema: dict):\n    if "const" in schema:'
new1 = 'def get_type(schema: dict):\n    if not isinstance(schema, dict): return "any"\n    if "const" in schema:'
if old1 in src:
    src = src.replace(old1, new1)
    patched = True
    print("Applied patch 1: get_type non-dict guard")

# Patch 2: _json_schema_to_python_type — catch APIInfoParseError on additionalProperties
old2 = '        f"str, {_json_schema_to_python_type(schema[\'additionalProperties\'], defs)}"'
new2 = '        f"str, {_json_schema_to_python_type(schema[\'additionalProperties\'], defs) if isinstance(schema.get(\'additionalProperties\'), dict) else \'any\'}"'
if old2 in src:
    src = src.replace(old2, new2)
    patched = True
    print("Applied patch 2: additionalProperties non-dict guard")

# Patch 3: wrap the raise APIInfoParseError to return "any" instead
old3 = '        raise APIInfoParseError(f"Cannot parse schema {schema}")'
new3 = '        return "any"  # patched: was raise APIInfoParseError'
if old3 in src:
    src = src.replace(old3, new3)
    patched = True
    print("Applied patch 3: APIInfoParseError -> return 'any'")

if patched:
    with open(path, "w") as f:
        f.write(src)
    print("gradio_client.utils patched successfully")
else:
    print("No patches needed or already applied")
