$tabReview = Get-Content -Raw src/ui/tab_review.py

# Add import
$tabReview = $tabReview -replace 'from viewer import render as render_viewer', "from viewer import render as render_viewer`nfrom latex_editor import st_latex_editor"

$oldTextArea = @"
        latex_input = st.text_area(
            label="kode", value=latex_val, height=500,
            key=f"editor_{current_topic['id']}",
            label_visibility="collapsed",
        )
"@

$newEditor = @"
        latex_input = st_latex_editor(
            value=latex_val, 
            height=600,
            key=f"editor_{current_topic['id']}"
        )
"@

$tabReview = $tabReview.Replace($oldTextArea, $newEditor)
Set-Content -Path src/ui/tab_review.py -Value $tabReview
