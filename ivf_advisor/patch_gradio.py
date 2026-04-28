"""Patch gradio to prevent APIInfoParseError crashes with complex Pydantic schemas.

Monkey-patches get_api_info to return empty info instead of crashing.
This is safe — it only affects the /info API endpoint, not the chat UI.
"""
try:
    import gradio.blocks as blocks

    _original_get_api_info = blocks.Blocks.get_api_info

    def _safe_get_api_info(self):
        try:
            return _original_get_api_info(self)
        except Exception:
            return {"named_endpoints": {}, "unnamed_endpoints": {}}

    blocks.Blocks.get_api_info = _safe_get_api_info
    print("Patched Blocks.get_api_info to suppress schema errors")
except Exception as e:
    print(f"Patch failed (non-fatal): {e}")
