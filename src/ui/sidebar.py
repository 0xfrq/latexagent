"""
sidebar.py - komponen sidebar buat topic management
create, switch, rename, delete topik
"""

import streamlit as st
from models import topics


def render():
    """
    render sidebar dengan topic management.
    return current_topic dict atau None.
    """
    with st.sidebar:
        st.markdown("### Topics")

        all_topics = topics.load_all()

        # --- buat topik baru ---
        new_topic_name = st.text_input(
            "New topic name", key="new_topic_name",
            placeholder="e.g. Machine Learning Notes",
        )
        if st.button("+ Create Topic"):
            if new_topic_name.strip():
                tid = topics.create(new_topic_name.strip())
                st.session_state.current_topic_id = tid
                st.experimental_rerun()
            else:
                st.warning("nama topik tidak boleh kosong!")

        st.markdown("---")

        # --- daftar topik & switcher ---
        if all_topics:
            topic_names = {t["id"]: t["name"] for t in all_topics}
            topic_ids = list(topic_names.keys())
            topic_display = [f"{topic_names[tid]} ({tid})" for tid in topic_ids]

            # cari index topik aktif
            current_idx = 0
            if st.session_state.current_topic_id in topic_ids:
                current_idx = topic_ids.index(st.session_state.current_topic_id)

            selected_display = st.selectbox(
                "Switch topic", topic_display,
                index=current_idx, key="topic_selector",
            )
            selected_id = topic_ids[topic_display.index(selected_display)]

            if selected_id != st.session_state.current_topic_id:
                st.session_state.current_topic_id = selected_id
                st.experimental_rerun()

            st.markdown("---")

            # --- info & aksi topik aktif ---
            current_topic = topics.get_by_id(st.session_state.current_topic_id)
            if current_topic:
                st.markdown(f"**{current_topic['name']}**")
                st.caption(f"created: {current_topic['created']}")

                # rename
                new_name = st.text_input(
                    "Rename", value=current_topic["name"], key="rename_input",
                )
                col_r1, col_r2 = st.columns(2)
                if col_r1.button("Rename"):
                    if new_name.strip() and new_name != current_topic["name"]:
                        topics.rename(current_topic["id"], new_name.strip())
                        st.experimental_rerun()

                # delete
                if col_r2.button("Delete", type="secondary"):
                    topics.delete(current_topic["id"])
                    st.session_state.current_topic_id = None
                    st.experimental_rerun()

                return current_topic
        else:
            st.info("belum ada topik. buat satu dulu!")

    return None