
import streamlit as st
import pandas as pd

from data_loader import load_dataset
from analytics import (
    count_equipment,
    average_health_score,
    find_recorded_failures,
    find_maintenance_due,
)

# 1. Configure the webpage
st.set_page_config(
    page_title="EdgeSight Query Nexus",
    page_icon="🤖",
    layout="wide",
)

# 2. Display the application title
st.title("🤖 EdgeSight Query Nexus")
st.write(
    "Ask questions about your IoT equipment and "
    "explore your dataset."
)

# 3. Load the dataset
@st.cache_data
def get_data():
    return load_dataset()

try:
    df = get_data()
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.info(
        "Check that the CSV is in the data folder "
        "and that data_loader.py works correctly."
    )
    st.stop()

# 4. Prepare the conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Create the example questions
st.subheader("Try an example question")

examples = [
    "How many records are in the dataset?",
    "What is the average health score?",
    "How many recorded failures are there?",
    "How many maintenance records are due?",
]

columns = st.columns(2)

for index, question in enumerate(examples):
    if columns[index % 2].button(
        question,
        key=f"example_{index}",
        use_container_width=True,
    ):
        st.session_state.pending_question = question

# 6. Display the results area
st.subheader("Conversation")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if "table" in message:
            st.dataframe(
                message["table"],
                use_container_width=True,
            )

# 7. Create the chat input
question = st.chat_input(
    "Ask a question about your IoT dataset..."
)

# Process either a typed question or an example question
if question:
    st.session_state.pending_question = question

if "pending_question" in st.session_state:
    user_question = st.session_state.pop("pending_question")

    # Save and display the user's question
    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    normalized = user_question.casefold()
    answer = ""
    result_table = None

    # 8. Match the question to an analytics function
    if "how many records" in normalized or (
        "total records" in normalized
    ):
        counts = count_equipment(df)
        answer = (
            f"The dataset contains "
            f"{counts['total_records']:,} records."
        )

    elif "unique assets" in normalized or (
        "distinct assets" in normalized
    ):
        counts = count_equipment(df)
        answer = (
            f"The dataset contains "
            f"{counts['unique_assets']:,} unique asset IDs."
        )

    elif "average health" in normalized or (
        "health score" in normalized
    ):
        score = average_health_score(df)

        if score is None:
            answer = "No numeric health scores were found."
        else:
            answer = f"The average recorded health score is {score}."

    elif "failure" in normalized:
        failures = find_recorded_failures(df)
        answer = (
            f"I found {len(failures):,} records marked "
            "as unscheduled failures."
        )
        result_table = failures.head(10)

    elif "maintenance" in normalized:
        maintenance = find_maintenance_due(df)
        answer = (
            f"I found {len(maintenance):,} records marked "
            "as maintenance due within 7 days."
        )
        result_table = maintenance.head(10)

    else:
        answer = (
            "I don't recognize that question yet. "
            "Try one of the example questions above."
        )

    # 9. Save the answer and any matching records
    assistant_message = {
        "role": "assistant",
        "content": answer,
    }

    if result_table is not None:
        assistant_message["table"] = result_table

    st.session_state.messages.append(assistant_message)

    # 10. Refresh the page to show the new response
    st.rerun()
