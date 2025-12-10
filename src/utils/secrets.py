import os
import streamlit as st


def get_openai_api_key() -> str:
    """Return the OpenAI API key from Streamlit secrets or environment.

    Order of lookup:
    1. `st.secrets["OPENAI_API_KEY"]` (preferred for Streamlit Cloud)
    2. Environment variable `OPENAI_API_KEY`
    3. Environment variable `OPEN_API_KEY` (accepted as an alternative)

    Raises RuntimeError if no key is found.
    """
    # 1) Streamlit secrets
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        # st.secrets may not be available in non-streamlit contexts
        pass

    # 2) Environment variables (support two common names)
    for env_name in ("OPENAI_API_KEY", "OPEN_API_KEY"):
        key = os.getenv(env_name)
        if key and key.strip():
            return key.strip()

    raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY or OPEN_API_KEY in Streamlit secrets or environment.")
