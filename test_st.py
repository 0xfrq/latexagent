import streamlit as st
import streamlit.components.v1 as components

st.text_area("What to change", placeholder="e.g. replace the diagram with a flowchart", key="my_text_area")

html = """
<button id="btn">Click me</button>
<script>
document.getElementById('btn').addEventListener('click', () => {
    try {
        const parentDoc = window.parent.document;
        const tas = parentDoc.querySelectorAll('textarea');
        let targetTa = null;
        for(let ta of tas) {
            if(ta.placeholder.includes("replace the diagram")) {
                targetTa = ta;
                break;
            }
        }
        if(targetTa) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            nativeInputValueSetter.call(targetTa, "Hello from iframe!");
            targetTa.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            alert("textarea not found");
        }
    } catch(e) {
        alert("Error: " + e.message);
    }
});
</script>
"""
components.html(html)
