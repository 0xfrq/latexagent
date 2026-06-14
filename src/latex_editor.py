import os
import streamlit.components.v1 as components

# Declare the component. We serve the frontend directory.
_component_func = components.declare_component(
    "latex_editor",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "latex_editor_frontend")
)

def st_latex_editor(value="", height=500, key=None):
    """
    Create a new instance of "latex_editor".

    Parameters
    ----------
    value: str
        The initial code to show in the editor.
    height: int
        The height of the editor in pixels.
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    str
        The current content of the editor.
    """
    # Call the component function to create it
    component_value = _component_func(value=value, height=height, key=key, default=value)
    return component_value
