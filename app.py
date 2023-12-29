import time
import streamlit as st
from openai import OpenAI
import config
from datastore import Datastore

client = OpenAI(api_key=config.OPENAI_API_KEY)
db = Datastore()
query = st.experimental_get_query_params()
cid = query["cid"][0]

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id
    db.upsert_chat(thread.id)

st.title("#{}".format(st.session_state["thread_id"]))

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

        messages = client.beta.threads.messages.list(
            thread_id=st.session_state["thread_id"],
        )

        for message in messages:
            # Extract the message content
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []

            # Iterate over the annotations and add footnotes
            for index, annotation in enumerate(annotations):
                # Replace the text with a footnote
                message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

                # Gather citations based on annotation attributes
                if (file_citation := getattr(annotation, 'file_citation', None)):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
                elif (file_path := getattr(annotation, 'file_path', None)):
                    cited_file = client.files.retrieve(file_path.file_id)
                    citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                    # Note: File download functionality not implemented above for brevity

            # Add footnotes to the end of the message before displaying to user
            # message_content.value += '\n\n' + '\n'.join(citations)
            st.session_state.messages.append({"role": message.role, "content": message_content.value})
            message_placeholder.markdown(message_content.value)

            db.push_chat_history(st.session_state["thread_id"], prompt, message_content.value)

            # retrieve only the newest message
            break