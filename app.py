import streamlit as st
import pandas as pd
import io

# --------------------------------------------------
# STREAMLIT CONFIGURATION
# --------------------------------------------------
st.set_page_config(page_title="TB Visit Pivot Tool", layout="wide")

st.title("📊 TB Visit Pivot Tool")
st.markdown("""
Upload your TB/TPT patient data to pivot all visit records into one wide-format row per registration number.
""")

st.info("""
### 🧾 Expected Columns
**Tsp**, **TB or TPT**, **Registration number**, **Patient Name**,  
**Visit date**, **Sputum Result**, **Gene Xpert Result**, **Truenet Result**,  
**Lab Number**, **Remark**
""")

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------
uploaded = st.file_uploader("📤 Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded:
    # --- Attempt to read file
    try:
        if uploaded.name.lower().endswith(('.xls', '.xlsx')):
            try:
                df = pd.read_excel(uploaded)
            except ImportError:
                st.error("⚠️ Missing library: Please install 'openpyxl' for Excel file support (`pip install openpyxl`).")
                st.stop()
        else:
            df = pd.read_csv(uploaded, dtype=str)
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
        st.stop()

    st.subheader("📋 Raw Data Preview")
    st.dataframe(df.head(10))

    # --------------------------------------------------
    # DATA VALIDATION & CLEANING
    # --------------------------------------------------
    df.columns = df.columns.str.strip().str.lower()

    expected = {
        "tsp", "tb or tpt", "registration number", "patient name",
        "visit date", "sputum result", "gene xpert result",
        "truenet result", "lab number", "remark"
    }

    missing = expected - set(df.columns)
    if missing:
        st.error(f"❌ Missing expected columns: {missing}")
        st.stop()

    # Rename to canonical names
    rename_map = {
        "tsp": "Tsp",
        "tb or tpt": "TB_or_TPT",
        "registration number": "Registration_number",
        "patient name": "Patient_Name",
        "visit date": "Visit_date",
        "sputum result": "Sputum_Result",
        "gene xpert result": "Gene_Xpert_Result",
        "truenet result": "Truenet_Result",
        "lab number": "Lab_Number",
        "remark": "Remark"
    }
    df = df.rename(columns=rename_map)

    # Convert Visit_date
    df["Visit_date"] = pd.to_datetime(df["Visit_date"], errors="coerce")

    # Sort and assign visit numbers
    df = df.sort_values(["Registration_number", "Visit_date"], ascending=[True, True]).reset_index(drop=True)
    df["visit_no"] = df.groupby("Registration_number").cumcount() + 1

    # --------------------------------------------------
    # PIVOT OPERATION
    # --------------------------------------------------
    with st.spinner("Transforming data..."):
        pivot = df.pivot_table(
            index=["Registration_number", "Tsp", "TB_or_TPT", "Patient_Name"],
            columns="visit_no",
            values=[
                "Visit_date", "Sputum_Result", "Gene_Xpert_Result",
                "Truenet_Result", "Lab_Number", "Remark"
            ],
            aggfunc="first"
        )

        # Flatten multi-level columns
        pivot.columns = [f"{col[0]}_{col[1]}" for col in pivot.columns]
        pivot = pivot.reset_index()

        # Format dates
        for c in pivot.columns:
            if c.startswith("Visit_date_"):
                pivot[c] = pd.to_datetime(pivot[c], errors="coerce").dt.strftime("%Y-%m-%d")

    st.success("✅ Pivot successful!")
    st.subheader("📈 Pivoted Data Preview")
    st.dataframe(pivot.head(15))

    # --------------------------------------------------
    # DOWNLOAD BUTTONS
    # --------------------------------------------------
    csv_data = pivot.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name="pivot_visits_by_registration.csv",
        mime="text/csv"
    )

    excel_buffer = io.BytesIO()
    pivot.to_excel(excel_buffer, index=False)
    st.download_button(
        label="⬇️ Download Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name="pivot_visits_by_registration.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --------------------------------------------------
    # OPTIONAL STATS
    # --------------------------------------------------
    st.markdown("### 📊 Summary: Visits per Registration Number")
    visit_counts = df.groupby("Registration_number")["visit_no"].max().reset_index(name="Total_Visits")
    st.dataframe(visit_counts)

else:
    st.warning("Please upload a CSV or Excel file to start.")
