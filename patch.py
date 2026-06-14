import re

def update_tab_review():
    with open('src/ui/tab_review.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the page input columns
    old_section = '''    col_r1, col_r2 = st.columns([1, 3])
    with col_r1:
        rev_page = st.number_input(
            "Page", min_value=1, max_value=max(page_count, 1), value=1,
            key=f"revpage_{current_topic['id']}",
        )
    with col_r2:
        rev_desc = st.text_area(
            "What to change",
            placeholder="e.g. replace the diagram with a flowchart, or add more detail about methodology...",
            height=60,
            key=f"revdesc_{current_topic['id']}",
        )'''
    
    new_section = '''    rev_desc = st.text_area(
        "What to change",
        placeholder="e.g. replace the diagram with a flowchart, or add more detail about methodology...",
        height=80,
        key=f"revdesc_{current_topic['id']}",
    )'''

    if old_section in content:
        content = content.replace(old_section, new_section)
    else:
        print("old_section not found in tab_review")

    old_apply = '''    if apply_rev:
        _handle_revision(current_topic, rc, latex_input, cached_pdf, rev_page, rev_desc)'''

    new_apply = '''    if apply_rev:
        import re
        page_match = re.search(r"Page (\d+)", rev_desc, re.IGNORECASE)
        parsed_page = int(page_match.group(1)) if page_match else 1
        _handle_revision(current_topic, rc, latex_input, cached_pdf, parsed_page, rev_desc)'''
        
    if old_apply in content:
        content = content.replace(old_apply, new_apply)
    else:
        print("old_apply not found in tab_review")

    with open('src/ui/tab_review.py', 'w', encoding='utf-8') as f:
        f.write(content)

def update_viewer():
    with open('src/viewer_template.html', 'r', encoding='utf-8') as f:
        content = f.read()

    old_js = '''      const el = document.createElement('textarea');
      el.value = "Page " + (window._revSelection.page + 1) + " | Area: x=" + 
                 Math.round(window._revSelection.x*100) + "%-" + Math.round(window._revSelection.x2*100) + 
                 "%, y=" + Math.round(window._revSelection.y*100) + "%-" + Math.round(window._revSelection.y2*100) + 
                 "% | Request: " + desc;
      document.body.appendChild(el);
      el.select();
      try {
        document.execCommand('copy');
        alert("Revision request copied to clipboard! Paste it in the 'What to change' box in the sidebar.");
      } catch(err) {
        console.error('Oops, unable to copy');
      }
      document.body.removeChild(el);'''

    new_js = '''      const finalRevText = "Page " + (window._revSelection.page + 1) + " | Area: x=" + 
                 Math.round(window._revSelection.x*100) + "%-" + Math.round(window._revSelection.x2*100) + 
                 "%, y=" + Math.round(window._revSelection.y*100) + "%-" + Math.round(window._revSelection.y2*100) + 
                 "% | Request: " + desc;
      
      try {
        const parentDoc = window.parent.document;
        const tas = parentDoc.querySelectorAll('textarea');
        let targetTa = null;
        for(let ta of tas) {
            if(ta.placeholder && ta.placeholder.includes("replace the diagram")) {
                targetTa = ta;
                break;
            }
        }
        if(targetTa) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            nativeInputValueSetter.call(targetTa, finalRevText);
            targetTa.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            throw new Error("Textarea not found");
        }
      } catch(e) {
        // fallback to copy
        const el = document.createElement('textarea');
        el.value = finalRevText;
        document.body.appendChild(el);
        el.select();
        try {
          document.execCommand('copy');
          alert("Revision request copied to clipboard! Paste it in the 'What to change' box in the sidebar.");
        } catch(err) {
          console.error('Oops, unable to copy');
        }
        document.body.removeChild(el);
      }'''

    if old_js in content:
        content = content.replace(old_js, new_js)
    else:
        print("old_js not found in viewer")
        
    with open('src/viewer_template.html', 'w', encoding='utf-8') as f:
        f.write(content)

update_tab_review()
update_viewer()
