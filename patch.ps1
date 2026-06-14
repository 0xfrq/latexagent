$tabReview = Get-Content -Raw src/ui/tab_review.py
$oldSection = @"
    col_r1, col_r2 = st.columns([1, 3])
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
        )
"@
$newSection = @"
    rev_desc = st.text_area(
        "What to change",
        placeholder="e.g. replace the diagram with a flowchart, or add more detail about methodology...",
        height=80,
        key=f"revdesc_{current_topic['id']}",
    )
"@

$oldApply = @"
    if apply_rev:
        _handle_revision(current_topic, rc, latex_input, cached_pdf, rev_page, rev_desc)
"@
$newApply = @"
    if apply_rev:
        import re
        page_match = re.search(r"Page (\d+)", rev_desc, re.IGNORECASE)
        parsed_page = int(page_match.group(1)) if page_match else 1
        _handle_revision(current_topic, rc, latex_input, cached_pdf, parsed_page, rev_desc)
"@

$tabReview = $tabReview.Replace($oldSection, $newSection)
$tabReview = $tabReview.Replace($oldApply, $newApply)
Set-Content -Path src/ui/tab_review.py -Value $tabReview


$viewer = Get-Content -Raw src/viewer_template.html
$oldJs = @"
      const el = document.createElement('textarea');
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
      document.body.removeChild(el);
"@

$newJs = @"
      const finalRevText = "Page " + (window._revSelection.page + 1) + " | Area: x=" + 
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
      }
"@
$viewer = $viewer.Replace($oldJs, $newJs)
Set-Content -Path src/viewer_template.html -Value $viewer
