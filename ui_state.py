from typing import Callable

import streamlit as st


def _store_widget_value(state_key: str, widget_key: str) -> None:
    st.session_state[state_key] = st.session_state[widget_key]


def render_persistent_selectbox(
    label: str,
    options: list[str],
    state_key: str,
    widget_key: str,
    default: str | None = None,
    format_func: Callable[[str], str] | None = None,
):
    if not options:
        raise ValueError(f"No options available for state key '{state_key}'.")

    current_value = st.session_state.get(state_key)
    if current_value not in options:
        if default is not None and default in options:
            st.session_state[state_key] = default
        else:
            st.session_state[state_key] = options[0]

    st.session_state[widget_key] = st.session_state[state_key]

    selectbox_kwargs = {
        "label": label,
        "options": options,
        "key": widget_key,
        "on_change": _store_widget_value,
        "args": (state_key, widget_key),
    }
    if format_func is not None:
        selectbox_kwargs["format_func"] = format_func

    return st.selectbox(
        **selectbox_kwargs,
    )
