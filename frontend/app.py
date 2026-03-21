import streamlit as st
import requests
import os

# Config
API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

# Page config
st.set_page_config(
    page_title="HarshGPT",
    page_icon="🤖",
    layout="centered"
)

# Header
st.title("🤖 HarshGPT")
st.markdown("*Ask me anything about Harsh's projects, internships and skills!*")
st.divider()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📄 Sources"):
                for source in message["sources"]:
                    st.caption(f"📁 {source['source']} — Page {source['page']}")

# Chat input
if prompt := st.chat_input("Ask about Harsh's experience, skills or projects..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer from FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]

                    st.markdown(answer)

                    if sources:
                        with st.expander("📄 Sources"):
                            for source in sources:
                                st.caption(f"📁 {source['source']} — Page {source['page']}")

                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

                elif response.status_code == 429:
                    st.error("⚠️ Rate limit reached. Please try again in an hour.")
                elif response.status_code == 400:
                    st.error("⚠️ Please enter a valid question.")
                else:
                    st.error("⚠️ Something went wrong. Please try again.")

            except requests.exceptions.ConnectionError:
                st.error("⚠️ Cannot connect to HarshGPT API. Please try again later.")
            except requests.exceptions.Timeout:
                st.error("⚠️ Request timed out. Please try again.")