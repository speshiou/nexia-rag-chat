import time
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
query = st.experimental_get_query_params()
cid = query["cid"][0]

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id

st.title("Thread #{}".format(st.session_state["thread_id"]))

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    message = client.beta.threads.messages.create(
        thread_id=st.session_state["thread_id"],
        role="user",
        content=prompt
    )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        run = client.beta.threads.runs.create(
            thread_id=st.session_state["thread_id"],
            assistant_id=cid,
        )

        message_placeholder.markdown(run.status)
        with st.spinner("Loading..."):
            # TODO: timeout
            while run.status != "completed":
                time.sleep(1)

                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state["thread_id"],
                    run_id=run.id
                )
                message_placeholder.markdown(run.status)
                print(run)

        messages = client.beta.threads.messages.list(
            thread_id=st.session_state["thread_id"]
        )

        for message in messages:
            print(message)
            content = message.content[0].text.value
            st.session_state.messages.append({"role": message.role, "content": content})
            message_placeholder.markdown(content)
            break