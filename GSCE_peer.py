import streamlit as st
import pandas as pd
import random
from datetime import datetime
from io import BytesIO
import os

# -------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="GSCE - Peer to Peer Duties Assignment",
    layout="wide"
)

st.image("gitm.png", width=150)
st.title("GSCE - Peer to Peer Duties Assignment")

st.markdown("""
This system generates **day-wise and weekly peer duty assignments**
using a **deterministic weekly seed**.
Each subject is assigned **only once per week when possible**,
and **always assigned at any cost** using fallback rules.
""")

# -------------------------------------------------
# Excel File Path
# -------------------------------------------------
FILE_PATH = "Peer_Job_Fixedslots_withoutsecondperson_emails.xlsx"

if not os.path.exists(FILE_PATH):
    st.error("Required Excel file not found in repository.")
    st.stop()

st.success("Excel file loaded successfully.")

# -------------------------------------------------
# Load Excel Once
# -------------------------------------------------
peerslots_all = pd.read_excel(FILE_PATH, sheet_name="Peerslots")
busy_fac = pd.read_excel(FILE_PATH, sheet_name="Busy_fac")

# -------------------------------------------------
# Safety Check
# -------------------------------------------------
if busy_fac.empty:
    st.error("Busy_fac sheet is empty. Cannot generate assignments.")
    st.stop()

# -------------------------------------------------
# Deterministic Weekly Seed
# -------------------------------------------------
week_seed = datetime.now().strftime("%Y-%U")
random.seed(week_seed)

# -------------------------------------------------
# Days
# -------------------------------------------------
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# -------------------------------------------------
# Day-wise Generation
# -------------------------------------------------
selected_day = st.selectbox("Select Day (Day-wise Generation)", days)

if st.button("Generate / Regenerate Day-wise Assignment"):
    weekly_assigned_subjects = set()

    peerslots = peerslots_all[
        (peerslots_all["Status"].str.lower() == "free") &
        (peerslots_all["Day"] == selected_day)
    ].copy()

    if peerslots.empty:
        st.warning(f"No free peer slots for {selected_day}")
        st.stop()

    assigned_subjects = []
    assigned_faculty = []
    assigned_building = []
    assigned_room = []

    for _, peer in peerslots.iterrows():
        time_slot = peer["Time Slot"]
        peer_emp_id = peer["Emp ID"]

        # Level 1: Ideal
        possible = busy_fac[
            (busy_fac["Day"] == selected_day) &
            (busy_fac["Time Slot"] == time_slot) &
            (busy_fac["Emp ID"] != peer_emp_id) &
            (~busy_fac["Subject"].isin(weekly_assigned_subjects))
        ]

        # Level 2: Allow subject repetition
        if possible.empty:
            possible = busy_fac[
                (busy_fac["Day"] == selected_day) &
                (busy_fac["Time Slot"] == time_slot) &
                (busy_fac["Emp ID"] != peer_emp_id)
            ]

        # Level 3: Allow faculty clash
        if possible.empty:
            possible = busy_fac[
                (busy_fac["Day"] == selected_day) &
                (busy_fac["Time Slot"] == time_slot)
            ]

        # Level 4: Ignore time slot
        if possible.empty:
            possible = busy_fac[
                (busy_fac["Day"] == selected_day)
            ]

        chosen = possible.sample(1).iloc[0]

        assigned_subjects.append(chosen["Subject"])
        assigned_faculty.append(chosen["Faculty Name"])
        assigned_building.append(chosen["Building"])
        assigned_room.append(chosen["Room No."])

        weekly_assigned_subjects.add(chosen["Subject"])

    peerslots["Assigned Subject"] = assigned_subjects
    peerslots["Teaching Faculty"] = assigned_faculty
    peerslots["Building"] = assigned_building
    peerslots["Room No."] = assigned_room

    st.success(f"{selected_day} Assignment Generated (Week {week_seed})")
    st.dataframe(peerslots, use_container_width=True)

    output = BytesIO()
    peerslots.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "Download Day-wise Assignment",
        data=output,
        file_name=f"Peer_Duty_{selected_day}_Week_{week_seed}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------------------------
# Weekly Generation
# -------------------------------------------------
st.divider()

if st.button("Generate Weekly Assignment (Mon–Sat)"):

    weekly_assigned_subjects = set()
    weekly_result = []

    for day in days:

        peerslots = peerslots_all[
            (peerslots_all["Status"].str.lower() == "free") &
            (peerslots_all["Day"] == day)
        ].copy()

        if peerslots.empty:
            continue

        assigned_subjects = []
        assigned_faculty = []
        assigned_building = []
        assigned_room = []

        for _, peer in peerslots.iterrows():
            time_slot = peer["Time Slot"]
            peer_emp_id = peer["Emp ID"]

            # Level 1
            possible = busy_fac[
                (busy_fac["Day"] == day) &
                (busy_fac["Time Slot"] == time_slot) &
                (busy_fac["Emp ID"] != peer_emp_id) &
                (~busy_fac["Subject"].isin(weekly_assigned_subjects))
            ]

            # Level 2
            if possible.empty:
                possible = busy_fac[
                    (busy_fac["Day"] == day) &
                    (busy_fac["Time Slot"] == time_slot) &
                    (busy_fac["Emp ID"] != peer_emp_id)
                ]

            # Level 3
            if possible.empty:
                possible = busy_fac[
                    (busy_fac["Day"] == day) &
                    (busy_fac["Time Slot"] == time_slot)
                ]

            # Level 4
            if possible.empty:
                possible = busy_fac[
                    (busy_fac["Day"] == day)
                ]

            chosen = possible.sample(1).iloc[0]

            assigned_subjects.append(chosen["Subject"])
            assigned_faculty.append(chosen["Faculty Name"])
            assigned_building.append(chosen["Building"])
            assigned_room.append(chosen["Room No."])

            weekly_assigned_subjects.add(chosen["Subject"])

        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Teaching Faculty"] = assigned_faculty
        peerslots["Building"] = assigned_building
        peerslots["Room No."] = assigned_room

        weekly_result.append(peerslots)

        st.subheader(day)
        st.dataframe(peerslots, use_container_width=True)

    if weekly_result:
        weekly_df = pd.concat(weekly_result, ignore_index=True)

        output = BytesIO()
        weekly_df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        st.download_button(
            "Download Weekly Assignment",
            data=output,
            file_name=f"Peer_Duty_Weekly_Week_{week_seed}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success(f"Weekly Assignment Generated (Week {week_seed})")
