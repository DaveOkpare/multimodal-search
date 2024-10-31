import streamlit as st

from embed_ingest_utils import initialize_model, search_posts, setup_qdrant_client


def app():
    st.markdown(
        "<p style='text-align: center;'> Uncover the brilliance of multimodal search.</p>",
        unsafe_allow_html=True,
    )

    input_text = st.text_input("Search:", key="query_input")

    post_limit = st.select_slider(
        "Select number of results to display",
        options=[1, 2, 3, 4, 5, 6],
        value=(3),
    )

    model = initialize_model()
    client = setup_qdrant_client()

    if st.button("Search"):
        output_data = search_posts(client, model, input_text, post_limit)
        show_results(output_data, input_text)


def show_results(output_data, input_text):
    aa = 0

    st.info(f"Showing results for: {input_text}")

    # Show the cards
    N_cards_per_row = 3
    for n_row, post in enumerate(output_data):
        i = n_row % N_cards_per_row
        if i == 0:
            st.write("---")
            cols = st.columns(N_cards_per_row, gap="large")
        # Draw the card
        with cols[n_row % N_cards_per_row]:
            st.markdown(f"![image]({post.payload["image_url"].strip()})")
            st.caption(f"{post.payload["title"].strip()}")
            st.markdown(f"**{post.payload["permalink"].strip()}**")

        aa += 1

    if aa == 0:
        st.info("No results found. Please try again.")
    else:
        st.info(f"Results shown for: {input_text}")


if __name__ == "__main__":
    app()
