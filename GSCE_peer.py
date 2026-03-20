import streamlit as st
import pandas as pd
import random
from datetime import datetime
from io import BytesIO
import os

# -------------------------------------------------
# Helper Function: Extract start time in 24-hour format
# -------------------------------------------------
def extract_mail_slot(time_slot):
    start = time_slot.split("-")[0].strip()

    if "AM" in start.upper() or "PM" in start.upper():
        return datetime.strptime(start.upper(), "%I:%M %p").strftime("%H:%M")

    hour, minute = map(int, start.split(":"))

    if 1 <= hour <= 6:
        hour += 12

    return f"{hour:02d}:{minute:02d}"

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
Peer-to-peer learning is a collaborative approach where faculty members visit an 
assigned class to learn from one another by sharing experiences, teaching strategies, 
and best practices in a real classroom setting.
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
# Load Excel Sheets
# -------------------------------------------------
peerslots_all = pd.read_excel(FILE_PATH, sheet_name="Peerslots")
busy_fac = pd.read_excel(FILE_PATH, sheet_name="Busy_fac")

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

    daily_assigned_subjects = set()  # ✅ Track per day

    peerslots = peerslots_all[
        (peerslots_all["Status"].str.lower() == "free") &
        (peerslots_all["Day"] == selected_day)
    ].copy()

    if peerslots.empty:
        st.warning(f"No free peer slots for {selected_day}")
        st.stop()

    assigned_subjects = []
    assigned_faculty = []
    assigned_room = []
    assigned_sem = []
    assigned_teaching_emp_id = []

    for _, peer in peerslots.iterrows():

        time_slot = peer["Time Slot"]
        peer_emp_id = peer["Emp ID"]

        possible = busy_fac[
            (busy_fac["Day"] == selected_day) &
            (busy_fac["Time Slot"] == time_slot) &
            (busy_fac["Emp ID"] != peer_emp_id) &
            (~busy_fac["Subject"].isin(daily_assigned_subjects))
        ]

        # If no unique subject available → skip instead of duplicate
        if possible.empty:
            assigned_subjects.append("Not Available")
            assigned_faculty.append("N/A")
            assigned_room.append("N/A")
            assigned_sem.append("N/A")
            assigned_teaching_emp_id.append("N/A")
            continue

        chosen = possible.sample(1).iloc[0]

        assigned_subjects.append(chosen["Subject"])
        assigned_faculty.append(chosen["Faculty Name"])
        assigned_room.append(chosen["Building"])
        assigned_sem.append(chosen["Sem"])
        assigned_teaching_emp_id.append(chosen["Emp ID"])

        daily_assigned_subjects.add(chosen["Subject"])  # ✅ Track

    peerslots["Date"] = datetime.now().strftime("%d-%m-%Y")
    peerslots["Peer Faculty Name"] = peerslots["Peer Name"]
    peerslots["Assigned Subject"] = assigned_subjects
    peerslots["Sem"] = assigned_sem
    peerslots["Teaching Faculty"] = assigned_faculty
    peerslots["Teaching Faculty Emp ID"] = assigned_teaching_emp_id
    peerslots["Room"] = assigned_room
    peerslots["Email Id"] = peerslots["Peer Email"]
    peerslots["Mail Slot"] = peerslots["Time Slot"].apply(extract_mail_slot)

    final_df = peerslots[
        [
            "Date", "Day", "Time Slot", "Peer Faculty Name", "Email Id",
            "Assigned Subject", "Sem", "Room",
            "Teaching Faculty", "Teaching Faculty Emp ID", "Mail Slot"
        ]
    ]

    st.success(f"{selected_day} Assignment Generated (Week {week_seed})")
    st.dataframe(final_df, use_container_width=True)

    output = BytesIO()
    final_df.to_excel(output, index=False, engine="openpyxl")
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

    weekly_result = []

    for day in days:

        daily_assigned_subjects = set()  # ✅ RESET every day

        peerslots = peerslots_all[
            (peerslots_all["Status"].str.lower() == "free") &
            (peerslots_all["Day"] == day)
        ].copy()

        if peerslots.empty:
            continue

        assigned_subjects = []
        assigned_faculty = []
        assigned_room = []
        assigned_sem = []
        assigned_teaching_emp_id = []

        for _, peer in peerslots.iterrows():

            time_slot = peer["Time Slot"]
            peer_emp_id = peer["Emp ID"]

            possible = busy_fac[
                (busy_fac["Day"] == day) &
                (busy_fac["Time Slot"] == time_slot) &
                (busy_fac["Emp ID"] != peer_emp_id) &
                (~busy_fac["Subject"].isin(daily_assigned_subjects))
            ]

            # Skip if no unique subject
            if possible.empty:
                assigned_subjects.append("Not Available")
                assigned_faculty.append("N/A")
                assigned_room.append("N/A")
                assigned_sem.append("N/A")
                assigned_teaching_emp_id.append("N/A")
                continue

            chosen = possible.sample(1).iloc[0]

            assigned_subjects.append(chosen["Subject"])
            assigned_faculty.append(chosen["Faculty Name"])
            assigned_room.append(chosen["Building"])
            assigned_sem.append(chosen["Sem"])
            assigned_teaching_emp_id.append(chosen["Emp ID"])

            daily_assigned_subjects.add(chosen["Subject"])  # ✅ Track

        peerslots["Date"] = datetime.now().strftime("%d-%m-%Y")
        peerslots["Peer Faculty Name"] = peerslots["Peer Name"]
        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Sem"] = assigned_sem
        peerslots["Teaching Faculty"] = assigned_faculty
        peerslots["Teaching Faculty Emp ID"] = assigned_teaching_emp_id
        peerslots["Room"] = assigned_room
        peerslots["Email Id"] = peerslots["Peer Email"]
        peerslots["Mail Slot"] = peerslots["Time Slot"].apply(extract_mail_slot)

        final_df = peerslots[
            [
                "Date", "Day", "Time Slot", "Peer Faculty Name", "Email Id",
                "Assigned Subject", "Sem", "Room",
                "Teaching Faculty", "Teaching Faculty Emp ID", "Mail Slot"
            ]
        ]

        weekly_result.append(final_df)

        st.subheader(day)
        st.dataframe(final_df, use_container_width=True)

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
