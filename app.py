import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="TB Visit Pivot Tool", layout="wide")

st.title("📊 TB Visit Pivot Tool")
st.markdown("Upload your TB/TPT visit data — the app will pivot all visit rows into columns per patient.")

st.info("""
Expected columns:
**Tsp**, **TB or TPT**, **Registration number**, **Patient Name**,  
**Visit date**, **Sputum Result**, **Gene Xpert Result**, **Truenet Result**, **Lab Number**, **Remark**
""")

uploaded = st.file_uploader("📤 Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded:
    # --- Read file
    if uploaded.name.lower().endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded, dtype=str)
    
    st.subheader("🧾 Raw Data Preview")
    st.dataframe(df.head(10))

    # --- Normalize columns
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

    # --- Parse dates
    df["Visit_date"] = pd.to_datetime(df["Visit_date"], errors="coerce")

    # --- Sort and assign visit numbers
    df = df.sort_values(["Registration_number", "Visit_date"], ascending=[True, True]).reset_index(drop=True)
    df["visit_no"] = df.groupby("Registration_number").cumcount() + 1

    # --- Pivot
    pivot = df.pivot_table(
        index=["Registration_number", "Tsp", "TB_or_TPT", "Patient_Name"],
        columns="visit_no",
        values=[
            "Visit_date", "Sputum_Result", "Gene_Xpert_Result",
            "Truenet_Result", "Lab_Number", "Remark"
        ],
        aggfunc="first"
    )

    # --- Flatten column names
    pivot.columns = [f"{col[0]}_{col[1]}" for col in pivot.columns]
    pivot = pivot.reset_index()

    # --- Format dates
    for c in pivot.columns:
        if c.startswith("Visit_date_"):
            pivot[c] = pd.to_datetime(pivot[c], errors="coerce").dt.strftime("%Y-%m-%d")

    st.subheader("✅ Pivoted Output Preview")
    st.dataframe(pivot.head(10))

    # --- Download section
    csv = pivot.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download as CSV", csv, "pivot_visits_by_registration.csv", "text/csv")

    excel_buffer = io.BytesIO()
    pivot.to_excel(excel_buffer, index=False)
    st.download_button("⬇️ Download as Excel (.xlsx)", excel_buffer.getvalue(), "pivot_visits_by_registration.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.success("✅ Pivot completed! You can now download the transformed data.")

else:
    st.warning("Please upload a data file to begin.")
