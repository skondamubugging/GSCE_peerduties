import pandas as pd
import random
import streamlit as st
import logging
from datetime import datetime, timedelta

# Suppress Streamlit warnings
logging.getLogger("streamlit").setLevel(logging.ERROR)

# -----------------------------------
# Function to generate peer assignments
# -----------------------------------
def generate_peer_assignments(input_file):

    # -------------------------------
    # Weekly randomness
    # -------------------------------
    week_seed = datetime.now().strftime("%Y-%U")
    random.seed(week_seed)

    # -------------------------------
    # Calculate Week Start & End Date
    # -------------------------------
    today = datetime.today()
    week_start = today - timedelta(days=today.weekday())   # Monday
    week_end = week_start + timedelta(days=4)              # Friday

    week_start_str = week_start.strftime("%d-%m-%Y")
    week_end_str = week_end.strftime("%d-%m-%Y")

    # -------------------------------
    # Read Excel
    # -------------------------------
    peerslots = pd.read_excel(input_file, sheet_name="Peerslots")
    busy_fac = pd.read_excel(input_file, sheet_name="Busy_fac")

    peerslots.columns = peerslots.columns.str.strip()
    busy_fac.columns = busy_fac.columns.str.strip()

    free_peers = peerslots[peerslots["Status"].str.lower() == "free"]

    peer_assignments = []
    assigned_peers = set()

    # -------------------------------
    # Assignment Logic
    # -------------------------------
    for (day, slot), free_group in free_peers.groupby(["Day", "Time Slot"]):

        busy_classes = busy_fac[
            (busy_fac["Day"] == day) &
            (busy_fac["Time Slot"] == slot)
        ]

        if busy_classes.empty or free_group.empty:
            peer_assignments.append({
                "Week Start Date": week_start_str,
                "Week End Date": week_end_str,
                "Day": day,
                "Time Slot": slot,
                "Faculty Name": "None",
                "Class": "No Class",
                "Peer Faculty": "None",
                "Alternative Faculty": "None"
            })
            continue

        chosen_class = busy_classes.sample(1).iloc[0]

        eligible_peers = free_group[
            free_group["Emp ID"] != chosen_class["Emp ID"]
        ]["Faculty Name"].unique().tolist()

        if not eligible_peers:
            peer_assignments.append({
                "Week Start Date": week_start_str,
                "Week End Date": week_end_str,
                "Day": day,
                "Time Slot": slot,
                "Faculty Name": chosen_class["Faculty Name"],
                "Class": chosen_class["Subject"],
                "Peer Faculty": "None",
                "Alternative Faculty": "None"
            })
            continue

        available_peers = [p for p in eligible_peers if p not in assigned_peers]
        if not available_peers:
            assigned_peers.clear()
            available_peers = eligible_peers

        peer = random.choice(available_peers)
        assigned_peers.add(peer)

        alternatives = [p for p in eligible_peers if p != peer]
        random.shuffle(alternatives)
        alternatives = alternatives[:3]

        peer_assignments.append({
            "Week Start Date": week_start_str,
            "Week End Date": week_end_str,
            "Day": day,
            "Time Slot": slot,
            "Faculty Name": chosen_class["Faculty Name"],
            "Class": chosen_class["Subject"],
            "Peer Faculty": peer,
            "Alternative Faculty": ", ".join(alternatives) if alternatives else "None"
        })

    peer_df = pd.DataFrame(peer_assignments)
    return peer_df


# -----------------------------------
# Streamlit Dashboard
# -----------------------------------
def main():
    st.set_page_config(page_title="Peer Assignment Dashboard", layout="wide")
    st.title("Faculty Peer Assignment Dashboard")

    excel_file = "Peer_Job_Fixedslots.xlsx"
    peer_df = generate_peer_assignments(excel_file)

    # Display week info
    week_info = peer_df[["Week Start Date", "Week End Date"]].iloc[0]
    st.info(f"Allocation Week: {week_info['Week Start Date']}  to  {week_info['Week End Date']}")

    # Sidebar filters
    st.sidebar.header("Filters")
    faculty_filter = st.sidebar.multiselect(
        "Select Peer Faculty",
        options=peer_df["Peer Faculty"].unique(),
        default=peer_df["Peer Faculty"].unique()
    )

    class_filter = st.sidebar.multiselect(
        "Select Subject",
        options=peer_df["Class"].unique(),
        default=peer_df["Class"].unique()
    )

    # Day Tabs
    days = sorted(peer_df["Day"].unique())
    tabs = st.tabs(days)

    for i, day in enumerate(days):
        with tabs[i]:
            st.subheader(f"Peer Assignments – {day}")

            filtered_df = peer_df[
                (peer_df["Day"] == day) &
                (peer_df["Peer Faculty"].isin(faculty_filter)) &
                (peer_df["Class"].isin(class_filter))
            ]

            if filtered_df.empty:
                st.info("No assignments found.")
            else:
                st.dataframe(
                    filtered_df[
                        [
                            "Week Start Date",
                            "Week End Date",
                            "Day",
                            "Time Slot",
                            "Faculty Name",
                            "Class",
                            "Peer Faculty",
                            "Alternative Faculty"
                        ]
                    ],
                    use_container_width=True
                )


if __name__ == "__main__":
    main()
