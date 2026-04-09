import streamlit as st
import sqlite3
import pandas as pd

# database
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS materials
             (name TEXT, quantity INTEGER, cost INTEGER, site TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS payments
             (amount INTEGER, description TEXT, site TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS sites
             (name TEXT,budget INTEGER, deleted INTEGER DEFAULT 0 )''')
try:
    c.execute("ALTER TABLE sites ADD COLUMN labour_cost INTEGER DEFAULT 0")
    c.execute("ALTER TABLE sites ADD COLUMN other_cost INTEGER DEFAULT 0")
    c.execute("ALTER TABLE sites ADD COLUMN revenue INTEGER DEFAULT 0")
    conn.commit()
except:
    pass
try:
    c.execute("ALTER TABLE sites ADD COLUMN deleted INTEGER DEFAULT 0 ")
    conn.commit()
except:
    pass 

# UI
st.set_page_config(page_title="BuildSmart", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: white;
}
h1, h2, h3 {
    color: #4CAF50;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# login
users = {
    "admin": {"password": "123", "role": "Admin"},
    "manager": {"password": "123", "role": "Manager"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success("Login Successful")
        else:
            st.error("Invalid credentials")

    st.stop()

# sidebar
st.title("🏗 BuildSmart: Construction OS")

menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Materials",
    "Payments",
    "Smart Insights",
    "Invoice",
    "Manage Sites",
    "Financial Analysis"
])

# Load sites dynamically
site_data = pd.read_sql("SELECT name FROM sites", conn)

if not site_data.empty:
    sites = site_data["name"].tolist()
else:
    sites = ["Default Site"]

selected_site = st.sidebar.selectbox("Select Site", sites)

# dashboard
if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    materials = pd.read_sql(f"SELECT * FROM materials WHERE site='{selected_site}'", conn)
    payments = pd.read_sql(f"SELECT * FROM payments WHERE site='{selected_site}'", conn)

    total_cost = materials["cost"].sum() if not materials.empty else 0
    total_payment = payments["amount"].sum() if not payments.empty else 0

    col1, col2 = st.columns(2)

    col1.metric("Material Cost", total_cost)
    col2.metric("Total Payments", total_payment)

    if not materials.empty:
        st.line_chart(materials["cost"])

    # Comparison
    if st.checkbox("Compare All Sites"):
        st.subheader("📊 Site Comparison")
        for s in sites:
            data = pd.read_sql(f"SELECT * FROM materials WHERE site='{s}'", conn)
            total = data["cost"].sum() if not data.empty else 0
            st.write(f"{s}: {total}")

# materials
elif menu == "Materials":
    st.subheader("📦 Materials")

    name = st.text_input("Material Name")
    quantity = st.number_input("Quantity", 1)
    cost = st.number_input("Cost", 1)

    if st.button("Add Material"):
        c.execute("INSERT INTO materials VALUES (?,?,?,?)",
                  (name, quantity, cost, selected_site))
        conn.commit()
        st.success("Material Added!")

    st.subheader("🗑 Delete Material")

    materials_data = pd.read_sql(
    f"SELECT rowid, * FROM materials WHERE site='{selected_site}'", conn
)

    if not materials_data.empty:
        selected_id = st.selectbox(
            "Select Material to Delete",
            materials_data["rowid"]
        )

        if st.button("Delete Material"):
            c.execute("DELETE FROM materials WHERE rowid=?", (selected_id,))
            conn.commit()
            st.success("Material deleted!")
            st.rerun()
    else:
        st.info("No materials available")
# payments
elif menu == "Payments":
    st.subheader("💰 Payments")

    amount = st.number_input("Amount", 1)
    desc = st.text_input("Description")

    if st.button("Add Payment"):
        c.execute("INSERT INTO payments VALUES (?,?,?)",
                  (amount, desc, selected_site))
        conn.commit()
        st.success("Payment Added!")

# smart insights
elif menu == "Smart Insights":
    st.subheader("🧠 Smart Insights")

    materials = pd.read_sql(f"SELECT * FROM materials WHERE site='{selected_site}'", conn)
    total_cost = materials["cost"].sum() if not materials.empty else 0

    # Prediction
    predicted = total_cost * 1.2
    st.write(f"🔮 Predicted Future Cost: {predicted: 2f}")

    site_info = pd.read_sql(
        f"SELECT * FROM sites WHERE name='{selected_site}' AND deleted=0",
        conn
    )

    if not site_info.empty:
        budget = site_info["budget"].values[0]
    else:
        budget = 100000

    st.write(f"💰 Budget: ₹{budget}")

    # Budget check
    if total_cost > budget:
        st.error(f"⚠ Budget Exceeded by ₹{total_cost - budget}")
    else:
        st.success(f"✅ Within Budget (Remaining ₹{budget - total_cost})")
# invoice
elif menu == "Invoice":
    st.subheader("🧾 Invoice")

    materials = pd.read_sql(f"SELECT * FROM materials WHERE site='{selected_site}'", conn)
    total = materials["cost"].sum() if not materials.empty else 0

    st.write(materials)
    st.write(f"### Total Cost: {total}")

    if st.button("Generate Invoice"):
        invoice = f"""
        ---- Invoice ----
        Site: {selected_site}
        Total Cost: {total}
        Thank You!
        """
        st.download_button("Download Invoice", invoice, file_name="invoice.txt")

# manage sites menu
elif menu == "Manage Sites":
    st.subheader("🏗 Manage Sites")

    # add site
    new_site = st.text_input("Enter New Site Name")

    if st.button("Add Site"):
        if new_site.strip() != "":
            c.execute("INSERT INTO sites (name) VALUES (?)", (new_site.strip(),))
            conn.commit()
            st.success(f"{new_site} added!")
            st.rerun()
        else:
            st.warning("Enter valid name")

    # show sites
    st.write("### Existing Sites")
    site_data = pd.read_sql("SELECT name FROM sites WHERE deleted=0", conn)

    if not site_data.empty:
        st.dataframe(site_data)

        # delet site
        st.subheader("🗑 Delete Site")

        selected_delete = st.selectbox("Select Site to Delete", site_data["name"])

        if st.button("Delete Site"):
            c.execute("UPDATE sites SET deleted=1 WHERE name=?", (selected_delete,))
            conn.commit()

            
            st.success(f"{selected_delete} deleted successfully!")
            st.rerun()
        st.subheader("♻ Restore Deleted Site")

    deleted_sites = pd.read_sql("SELECT name FROM sites WHERE deleted=1", conn)

    if not deleted_sites.empty:
        restore_site = st.selectbox("Select Site", deleted_sites["name"])

        col1, col2 = st.columns(2)

    # restore
        with col1:
            if st.button("Restore"):
                c.execute("UPDATE sites SET deleted=0 WHERE name=?", (restore_site,))
                conn.commit()
                st.success(f"{restore_site} restored!")
                st.rerun()

    # permanent delete
        with col2:
            confirm = st.checkbox("Confirm Permanent Delete")

            if st.button("Delete Permanently") and confirm:
                c.execute("DELETE FROM sites WHERE name=?", (restore_site,))
                conn.commit()

            # ALSO DELETE RELATED DATA
                c.execute("DELETE FROM materials WHERE site=?", (restore_site,))
                c.execute("DELETE FROM payments WHERE site=?", (restore_site,))
                conn.commit()

                st.success(f"{restore_site} permanently deleted!")
                st.rerun()
    else:
        st.subheader("✏ Update Budget")

    # IMPORTANT: fetch full data
    site_data = pd.read_sql("SELECT * FROM sites WHERE deleted=0", conn)

    if not site_data.empty:
        selected = st.selectbox("Select Site to Update", site_data["name"])

    # 👉 Show current budget
        current_budget = site_data[site_data["name"] == selected]["budget"].values[0]
        st.write(f"Current Budget: ₹{current_budget}")

        new_budget = st.number_input("New Budget", min_value=1000, value=int(current_budget))

        if st.button("Update Budget"):
            c.execute(
                "UPDATE sites SET budget=? WHERE name=?",
                (int(new_budget), selected)
            )
            conn.commit()

            st.success(f"Budget updated for {selected}!")
            st.rerun()
    else:
        st.info("No sites available")
        
elif menu == "Financial Analysis":
    st.subheader("💰 Financial Analysis")

    # fetch data
    materials = pd.read_sql(f"SELECT * FROM materials WHERE site='{selected_site}'", conn)
    total_material_cost = materials["cost"].sum() if not materials.empty else 0

    st.write(f"### 🧱 Material Cost: ₹{total_material_cost}")

    # calc GST
    gst_rate = st.number_input("GST (%)", value=18)
    gst_amount = (gst_rate / 100) * total_material_cost
    
    st.write(f"GST Amount: ₹{gst_amount:.2f}")

    # labour and other expenses
    site_info = pd.read_sql(f"SELECT * FROM sites WHERE name='{selected_site}'", conn)

    labour_cost = st.number_input(
        "Labour Cost",
        value=int(site_info["labour_cost"][0]) if not site_info.empty else 0
    )

    other_cost = st.number_input(
        "Other Expenses",
        value=int(site_info["other_cost"][0]) if not site_info.empty else 0
    )
    total_expense= total_material_cost +gst_amount + labour_cost + other_cost 

    revenue = st.number_input(
        "Project Revenue",
        value=int(site_info["revenue"][0]) if not site_info.empty else 0
    )
    profit = revenue - total_expense
    st.write(f"### 💵 Profit: ₹{profit:.2f}")

    if st.button("Save Financial Data"):
        c.execute("""
            UPDATE sites 
            SET labour_cost=?, other_cost=?, revenue=? 
            WHERE name=?
            """, (labour_cost, other_cost, revenue, selected_site))
    
        conn.commit()
        st.success("Saved for this site!")
    
    # status
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Expense", f"₹{total_expense:.2f}")
        col2.metric("Revenue", f"₹{revenue:.2f}")
        col3.metric("Profit", f"₹{profit:.2f}")
    else:
        st.error("⚠ Project is in Loss")

    # key insights
        st.markdown("### 📌 Key Insight")

    if profit > 0:
        st.info("Project is generating profit with controlled expenses.")
    else:
        st.warning("Expenses are higher than revenue. Cost control needed.")

    #cost breakdown
        st.subheader("📊 Cost Breakdown")

        cost_data = pd.DataFrame({
            "Category": ["Material", "GST", "Labour", "Other"],
            "Amount": [total_material_cost, gst_amount, labour_cost, other_cost]
        })

        st.bar_chart(cost_data.set_index("Category"))

    # profit analysis
        st.subheader("📈 Profit Analysis")

        profit_data = pd.DataFrame({
            "Type": ["Revenue", "Expense", "Profit"],
            "Amount": [revenue, total_expense, profit]
        })

        st.bar_chart(profit_data.set_index("Type"))