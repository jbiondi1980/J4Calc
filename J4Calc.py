import streamlit as st
import math
import pandas as pd
from datetime import date
import pdfkit
import tempfile
import base64
import numpy as np
import os

# Today's date
st.set_page_config(page_title="J4 Energy Solutions - Solar Investment Calculator", layout="wide")
today = date.today().strftime("%m/%d/%Y")

# --- HEADER ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("J4logo.png", width=200)
with col2:
    st.markdown("### **J4 Energy Solutions**")
    st.markdown("#### Solar Investment Calculator")
    st.markdown(f"**Preparation Date:** {today}")

st.markdown("---")

# --- FORM HELPER FUNCTION ---
def input_row(label, key, value="", help_text=None):
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write(f"**{label}**")
    with col2:
        val = st.text_input(label, value=value, label_visibility="collapsed", key=key)
        if help_text:
            st.caption(help_text)
        return val

# --- CLIENT INFORMATION ---
st.header("Client Information")

client_name = input_row("Name", "name")
client_address = input_row("Address", "address")
client_city = input_row("City", "city")
client_state = input_row("State", "state")
client_zip = input_row("Zip Code", "zip")
client_phone = input_row("Phone Number", "phone")
client_email = input_row("Email Address", "email")

st.markdown("---")

# --- PANEL PROJECTION ---
st.header("Panel Projection")

# 1. Kilowatt hours annual
kwh_annual_str = input_row("Kilowatt Hours Annual", "kwh_annual", help_text="*Based on current utility bill*")
kwh_annual = float(kwh_annual_str) if kwh_annual_str.strip() else 0

# 2. Average Monthly Electric Bill
monthly_bill_str = input_row("Average Monthly Electric Bill", "monthly_bill", help_text="*Based on current utility bill*")
monthly_bill = float(monthly_bill_str.replace("$", "").replace(",", "")) if monthly_bill_str.strip() else 0

# 3. Panel Type Selection (dropdown)
panel_options = [
    "Qcell Qtron+ 425w cell Blk/blk",
    "Jinko 425 all black",
    "Solaria 390w 60-Cell Black on Black",
    "REC 420 Q pure",
    "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)",
    "Add New"
]
selected_panel = st.selectbox("Select Panel Type", panel_options, index=0)

# Final panel type (used later for cost calculations)
final_panel_type = selected_panel

# Panel Size Lookup
panel_size_lookup = {
    "Qcell Qtron+ 425w cell Blk/blk": 425,
    "Jinko 425 all black": 425,
    "Solaria 390w 60-Cell Black on Black": 390,
    "REC 420 Q pure": 420,
    "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)": 425
}

# 4. Panel Size
if selected_panel == "Add New":
    custom_panel_name = st.text_input("Enter Custom Panel Name", key="custom_panel_name")
    panel_size_str = input_row("Panel Size (watts)", "panel_size_custom", value="425")
    panel_size = float(panel_size_str) if panel_size_str.strip() else 425
    final_panel_type = custom_panel_name if custom_panel_name.strip() else "Custom Panel"
else:
    panel_size = panel_size_lookup[selected_panel]
    final_panel_type = selected_panel
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("**Panel Size (watts)**")
    with col2:
        st.text_input("Panel Size (watts)", value=str(panel_size), disabled=True)

# 5. Projected Panels (calculated)
projected_panels_calc = math.ceil(kwh_annual / panel_size) if panel_size > 0 else 0
projected_panels_str = input_row("Projected Panels", "projected_panels", value=str(projected_panels_calc))

# 6. Add'l Panels
additional_panels_str = input_row("Add'l Panels", "additional_panels", value="1")
additional_panels = int(additional_panels_str) if additional_panels_str.strip() else 0

# 7. Total Panels
total_panels_calc = projected_panels_calc + additional_panels
total_panels_str = input_row("Total Panels", "total_panels", value=str(total_panels_calc))

# 8. Production Factor
prod_factor_str = input_row("Production Factor", "prod_factor", value="1.15")
prod_factor = float(prod_factor_str) if prod_factor_str.strip() else 1.15

# 9. Output: Watts
output_watts = total_panels_calc * panel_size
output_watts_str = input_row("Output: Watts", "output_watts", value=str(output_watts))

# 10. Output: kWh (Output Watts * Production Factor)
output_kwh = output_watts * prod_factor
output_kwh_str = input_row("Output: kWh", "output_kwh", value=str(round(output_kwh, 2)))

# 11. Projected Production Offset
if kwh_annual > 0:
    offset_calc = (total_panels_calc * panel_size) / kwh_annual
else:
    offset_calc = 0
offset_percent = f"{offset_calc:.0%}"
offset_str = input_row("Projected Production Offset", "offset", value=offset_percent)

st.markdown("---")

# --- ITEMIZED COSTS ---
st.header("Itemized Costs")

# Default cost lookup by panel type
panel_cost_lookup = {
    "Qcell Qtron+ 425w cell Blk/blk": 230,
    "Jinko 425 all black": 180,
    "Solaria 390w 60-Cell Black on Black": 254,
    "REC 420 Q pure": 350,
    "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)": 230,
}

# Determine display name for header
display_panel_type = final_panel_type if final_panel_type else "Selected Panel"

# Get default or custom cost per panel
default_cost_per_panel = panel_cost_lookup.get(selected_panel, 0)

# Input for panel cost and calculated total
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write(f"**Panels ({display_panel_type})**")

with col2:
    if default_cost_per_panel == 0 and selected_panel == "Add New":
        if "dismiss_custom_panel_cost" not in st.session_state:
            st.session_state.dismiss_custom_panel_cost = False

        if not st.session_state.dismiss_custom_panel_cost:
            with st.expander("⚠️ No default cost found for custom panel. (Click to dismiss)", expanded=True):
                if st.button("Dismiss", key="dismiss_custom_panel_cost_btn"):
                    st.session_state.dismiss_custom_panel_cost = True

    cost_per_panel_str = st.text_input("Panel Cost", value=str(default_cost_per_panel), key="cost_per_panel")
    cost_per_panel = float(cost_per_panel_str) if cost_per_panel_str.strip() else 0

with col3:
    panel_cost_total = total_panels_calc * cost_per_panel
    panels_cost_str = st.text_input("Total", value=f"${panel_cost_total:.2f}", key="panels_cost")

    # Solarinsure line item
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Solarinsure**")

with col2:
    solarinsure_rate_str = st.text_input("Cost per Watt", value="0.10", key="solarinsure_rate")
    solarinsure_rate = float(solarinsure_rate_str) if solarinsure_rate_str.strip() else 0

with col3:
    solarinsure_total = output_watts * solarinsure_rate
    solarinsure_total_str = st.text_input("Total", value=f"${solarinsure_total:,.2f}", key="solarinsure_total")

# A/C Trunk Cable cost per panel lookup
trunk_cable_rate_lookup = {
    "Qcell Qtron+ 425w cell Blk/blk": 20,
    "Jinko 425 all black": 20,
    "Solaria 390w 60-Cell Black on Black": 20,
    "REC 420 Q pure": 20,
    "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)": 22,
}

default_trunk_rate = trunk_cable_rate_lookup.get(selected_panel, 0)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**A/C Trunk Cable**")

with col2:
    if default_trunk_rate == 0 and selected_panel == "Add New":
        if "dismiss_custom_trunk_cost" not in st.session_state:
            st.session_state.dismiss_custom_trunk_cost = False

        if not st.session_state.dismiss_custom_trunk_cost:
            with st.expander("⚠️ No trunk cable cost found for custom panel. (Click to dismiss)", expanded=True):
                if st.button("Dismiss", key="dismiss_custom_trunk_cost_btn"):
                    st.session_state.dismiss_custom_trunk_cost = True

    trunk_rate_str = st.text_input("Cost per Panel", value=str(default_trunk_rate), key="trunk_rate")
    trunk_rate = float(trunk_rate_str) if trunk_rate_str.strip() else 0

with col3:
    trunk_total = total_panels_calc * trunk_rate
    trunk_total_str = st.text_input("Total", value=f"${trunk_total:,.2f}", key="trunk_total")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Enphase Micros IQ-8+ (300-watt) / IQ8A with 445's**")

with col2:
    enphase_rate_str = st.text_input("Cost per Unit", value="190.00", key="enphase_rate")
    enphase_rate = float(enphase_rate_str) if enphase_rate_str.strip() else 0

with col3:
    enphase_total = total_panels_calc * enphase_rate
    enphase_total_str = st.text_input("Total", value=f"${enphase_total:,.2f}", key="enphase_total")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Enphase 10yr Labor Buy Up**")

with col2:
    labor_buyup_rate_str = st.text_input("Cost per Panel", value="6.00", key="labor_buyup_rate")
    labor_buyup_rate = float(labor_buyup_rate_str) if labor_buyup_rate_str.strip() else 0

with col3:
    labor_buyup_total = total_panels_calc * labor_buyup_rate
    labor_buyup_total_str = st.text_input("Total", value=f"${labor_buyup_total:,.2f}", key="labor_buyup_total")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Envoy-S Metered with 10-year monitoring**")

with col2:
    envoy_cost_str = st.text_input("Cost", value="585.47", key="envoy_cost")
    envoy_cost = float(envoy_cost_str) if envoy_cost_str.strip() else 0

with col3:
    envoy_total_str = st.text_input("Total", value=f"${envoy_cost:,.2f}", key="envoy_total")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Boxes and Hardware**")

with col2:
    boxes_cost_str = st.text_input("Cost", value="1200.00", key="boxes_cost")
    boxes_cost = float(boxes_cost_str) if boxes_cost_str.strip() else 0

with col3:
    boxes_total_str = st.text_input("Total", value=f"${boxes_cost:,.2f}", key="boxes_total")

# Racking cost per panel lookup by panel type
racking_cost_lookup = {
    "Qcell Qtron+ 425w cell Blk/blk": 80,
    "Jinko 425 all black": 80,
    "Solaria 390w 60-Cell Black on Black": 80,
    "REC 420 Q pure": 80,
    "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)": 175,
}

default_racking_rate = racking_cost_lookup.get(selected_panel, 0)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Racking and Hardware**")

with col2:
    if default_racking_rate == 0 and selected_panel == "Add New":
        if "dismiss_custom_racking_cost" not in st.session_state:
            st.session_state.dismiss_custom_racking_cost = False

        if not st.session_state.dismiss_custom_racking_cost:
            with st.expander("⚠️ No racking cost found for custom panel. (Click to dismiss)", expanded=True):
                if st.button("Dismiss", key="dismiss_custom_racking_cost_btn"):
                    st.session_state.dismiss_custom_racking_cost = True

    racking_rate_str = st.text_input("Cost per Panel", value=str(default_racking_rate), key="racking_rate")
    racking_rate = float(racking_rate_str) if racking_rate_str.strip() else 0

with col3:
    racking_total = total_panels_calc * racking_rate
    racking_total_str = st.text_input("Total", value=f"${racking_total:,.2f}", key="racking_total")

# --- Ground Screw Costs ---

# Set ground screw rate based on selected panel
default_ground_screw_rate = 230.00 if selected_panel == "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)" else 0.00

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Ground Screw Costs**")

with col2:
    ground_screw_rate_str = st.text_input("Cost per Panel", value=f"{default_ground_screw_rate:.2f}", key="ground_screw_rate")
    ground_screw_rate = float(ground_screw_rate_str) if ground_screw_rate_str.strip() else 0

with col3:
    ground_screw_total = total_panels_calc * ground_screw_rate
    ground_screw_total_str = st.text_input("Total", value=f"${ground_screw_total:,.2f}", key="ground_screw_total")

# --- Dirt Work ---

# Set default Dirt Work flat cost
default_dirt_work_cost = 2000.00 if selected_panel == "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)" else 0.00

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Dirt Work**")

with col2:
    dirt_work_cost_str = st.text_input("Cost", value=f"{default_dirt_work_cost:.2f}", key="dirt_work_cost")
    dirt_work_cost = float(dirt_work_cost_str) if dirt_work_cost_str.strip() else 0

with col3:
    dirt_work_total_str = st.text_input("Total", value=f"${dirt_work_cost:,.2f}", key="dirt_work_total")

# --- Underground Location ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.write("**Underground Location**")
with col2:
    underground_cost_str = st.text_input("Cost", value="200.00", key="underground_cost")
    underground_cost = float(underground_cost_str.strip()) if underground_cost_str.strip() else 0
with col3:
    underground_total = underground_cost
    st.text_input("Total", value=f"${underground_total:,.2f}", key="underground_total", disabled=True)

# --- Permits ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.write("**Permits**")
with col2:
    permits_cost_str = st.text_input("Cost", value="900.00", key="permits_cost")
    permits_cost = float(permits_cost_str.strip()) if permits_cost_str.strip() else 0
with col3:
    permits_total = permits_cost
    st.text_input("Total", value=f"${permits_total:,.2f}", key="permits_total", disabled=True)

# --- Labor ---

default_labor_rate = 0.69

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.write("**Labor**")

with col2:
    labor_rate_str = st.text_input("Cost per Watt", value=f"{default_labor_rate:.2f}", key="labor_rate")
    labor_rate = float(labor_rate_str) if labor_rate_str.strip() else 0

with col3:
    labor_total = output_watts * labor_rate
    labor_total_str = st.text_input("Total", value=f"${labor_total:,.2f}", key="labor_total")

# --- Additional Costs ---

st.header("Additional Costs (Optional)")

additional_cost_items = [
    "Loam and Seed",
    "Man Lift Rental ($500 each)",
    "Trench Run ($20.00/foot for all roofs and any feet over 100 for ground array)",
    "Enphase Cell Card for Areas with No WiFI access (5yr plan) $500",
    "Enphase Line Filter  (All system with greater than 200' from micro's to Envoy). ($450)",
    "Septic Vent Pipe Relocation ($900)",
    "SunModo Ledge Drilling ($50/panel)",
    "Other Upgrades (Panel Replacement, Service Upgrade Etc.)",
    "Multiple Arrays beyond 2 ($600 per additional array)",
    "Additional Margin"
]

for item in additional_cost_items:
    cost_key = f"{item}_cost"
    total_key = f"{item}_total"

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.write(f"**{item}**")
    with col2:
        cost_val = st.text_input("Cost", value="", key=cost_key)
    with col3:
        try:
            # Convert to float and format as currency
            formatted_total = f"${float(cost_val):,.2f}" if cost_val.strip() else ""
        except ValueError:
            formatted_total = "Invalid input"
        st.text_input("Total", value=formatted_total, key=total_key, disabled=True)

# --- TOTAL PROJECT COST ---

# Collect all itemized cost variables (assuming these have been defined earlier)
itemized_totals = [
    panel_cost_total,
    solarinsure_total,
    trunk_total,
    enphase_total,
    labor_buyup_total,
    envoy_cost,
    boxes_cost,
    racking_total,
    ground_screw_total if 'ground_screw_total' in locals() else 0,
    dirt_work_total if 'dirt_work_total' in locals() else 0,
    underground_total, 
    permits_total, 
    labor_total if 'labor_total' in locals() else 0,
]

# Additional manual costs from text_inputs
additional_total = 0
for item in additional_cost_items:
    cost_val = st.session_state.get(f"{item}_cost", "")
    try:
        additional_total += float(cost_val) if cost_val.strip() else 0
    except ValueError:
        pass  # Ignore invalid inputs

# Calculate grand total
grand_total = sum(itemized_totals) + additional_total

# Display total row
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.subheader("**Fixed Project Cost**")
with col2:
    st.write("")  # empty space
with col3:
    st.subheader(f"${grand_total:,.2f}")

# --- Total Project Cost ---

# Determine default $/watt based on logic
if selected_panel == "Fixed Ground SunModo racking with Jinko 425w (Even numbers only)":
    default_per_watt = 1.40
elif output_watts < 12000:
    default_per_watt = 3.05
elif 12000 <= output_watts < 18000:
    default_per_watt = 2.98
else:
    default_per_watt = 2.90

# Input for per watt cost (manually adjustable)
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("### **Total Project Cost**")  # Matches "Fixed Project Cost" styling

with col2:
    cost_per_watt_str = st.text_input("$/Watt", value=f"{default_per_watt:.2f}", key="cost_per_watt")
    cost_per_watt = float(cost_per_watt_str.strip()) if cost_per_watt_str.strip() else default_per_watt

with col3:
    total_project_cost = output_watts * cost_per_watt
    st.markdown(f"<div style='font-size: 36px; font-weight: bold;'>${total_project_cost:,.2f}</div>", unsafe_allow_html=True)

# --- Inputs ---
st.subheader("Financing Options Inputs")
col1, col2, col3 = st.columns(3)

with col1:
    deposit_amount = st.number_input("Deposit Amount (Non ITC deposits only)", value=0.0, step=100.0, format="%.2f")

with col2:
    rate_15yr = st.number_input("15-Year Rate (%)", value=8.5, step=0.01, format="%.2f")

with col3:
    rate_20yr = st.number_input("20-Year Rate (%)", value=9.5, step=0.01, format="%.2f")

# --- Assume these are already calculated from earlier code ---
# Replace with your real calculations
# total_project_cost = 45600.00
# output_watts = 15000

# --- Labels ---
row_labels = [
    "Customer Cost", 
    "Cost per Watt", 
    "Sales Based Commision", 
    "Margin Above Fixed Job Costs",
    "Margin %", 
    "Federal Tax Credit", 
    "Final NET Customer Cost",
    "Financed Payment Amount w/ITC (Estimate Only)", 
    "Financed Payment Amount w/o ITC (Estimate Only)", 
    "Rate"
]

column_labels = ["Client Funded", "15yr Financed", "20yr Financed"]

# --- Calculations ---
customer_cost = total_project_cost
customer_cost_dep = total_project_cost-deposit_amount
cost_per_watt = total_project_cost / output_watts if output_watts else 0
sales_based_commission = total_project_cost * 0.12

fixed_job_cost = grand_total

margin_above_fixed = (total_project_cost * 0.95) - fixed_job_cost
margin_percent = (margin_above_fixed / fixed_job_cost) * 100
federal_tax_credit = total_project_cost * 0.30
net_customer_cost = customer_cost - federal_tax_credit
net_customer_cost_dep = customer_cost - federal_tax_credit - deposit_amount

financed_w_itc_idx = row_labels.index("Financed Payment Amount w/ITC (Estimate Only)")
financed_wo_itc_idx = row_labels.index("Financed Payment Amount w/o ITC (Estimate Only)")
rate_idx = row_labels.index("Rate")

def calculate_monthly_payment(principal, annual_rate, years):
    monthly_rate = annual_rate / 100 / 12
    n = years * 12
    payment = principal * (monthly_rate + monthly_rate / ((1 + monthly_rate) ** n - 1))
    return payment

principal_ITC = net_customer_cost * .7
principal = net_customer_cost_dep
annual_rate_15 = rate_15yr
annual_rate_20 = rate_20yr
years_15_ITC = 13
years_20_ITC = 19
years_15 = 15
years_20 = 20
pymt_15_itc = f"${calculate_monthly_payment(principal_ITC, annual_rate_15, years_15_ITC):,.2f}"
pymt_20_itc = f"${calculate_monthly_payment(principal_ITC, annual_rate_20, years_20_ITC):,.2f}"
pymt_15 = f"${calculate_monthly_payment(principal, annual_rate_15,years_15):,.2f}"
pymt_20 = f"${calculate_monthly_payment(principal, annual_rate_20,years_20):,.2f}"

# --- Populate grid data with numeric values or np.nan ---
grid_data = [
    [customer_cost, customer_cost, customer_cost],                   # Row 1
    [cost_per_watt, cost_per_watt, cost_per_watt],                   # Row 2
    [sales_based_commission, sales_based_commission, sales_based_commission],                                        # Row 3
    [margin_above_fixed, margin_above_fixed, margin_above_fixed],                                        # Row 4
    [margin_percent, margin_percent, margin_percent],                                        # Row 5
    [federal_tax_credit, federal_tax_credit, federal_tax_credit],                                        # Row 6
    [net_customer_cost, net_customer_cost, net_customer_cost],                                        # Row 7
    ["N/A", pymt_15_itc, pymt_20_itc],                                        # Row 8
    ["N/A", pymt_15, pymt_20],                                        # Row 9
    ["N/A", rate_15yr, rate_20yr],                   # Row 10
]

df_grid = pd.DataFrame(grid_data, index=row_labels, columns=column_labels)

# --- Create and display table ---
# For example, only format rows except those with 'N/A' in columns
numeric_rows = df_grid[~df_grid[["Client Funded", "15yr Financed", "20yr Financed"]].isin(['N/A']).any(axis=1)].index

st.table(
    df_grid.style
    .format("${:,.2f}", subset=pd.IndexSlice[numeric_rows, ["Client Funded", "15yr Financed", "20yr Financed"]])
    .format("{:.2f}%", subset=pd.IndexSlice["Margin %", :])
)

# --- HTML Proposal Template Function ---
def get_encoded_logo():
    import base64
    logo_path = "J4logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f'data:image/png;base64,{encoded}'
    return ""

def generate_proposal_html():
    logo_url = get_encoded_logo()
    return f"""
    <html>
    <head>
        <style>
            @page {{ size: Letter; margin: .5in; }}
            body {{ font-family: Arial, sans-serif; margin: 0; }}
            h2, h3 {{ color: #003366; }}
            ul {{ margin-top: -10px; }}
            .section {{ margin-top: 0px; }}
            .logo {{ width: 100px; }}
            .pagebreak {{ page-break-before: always; }}
        </style>
    </head>
    <body>
        <table style="width: 100%; margin-bottom: 20px;">
          <tr>
            <td style="width: 120px;">
              <img src="{logo_url}" alt="J4 Logo" style="width: 100px;"/>
            </td>
            <td style="vertical-align: middle;">
              <h2 style="margin: 0; color: #003366;">Solar Investment Details Prepared on {today}</h2>
            </td>
          </tr>
        </table>
        <p><strong>Client:</strong> {client_name}, {client_address}, {client_city}, {client_state}, {client_zip}</p>

        <div class="section">
            <h3>Included:</h3>
            <ul>
                <li>Construction of a {int(output_watts):,}W roof-mounted solar array</li>
                <li>({total_panels_calc}) 425 monocrystalline solar modules</li>
                <li>({total_panels_calc}) Enphase IQ 8m AC micro inverters</li>
                <li>IronRidge Black anodized aluminum rail mount system</li>
                <li>Configured with My Enlighten monitoring system</li>
                <li>Full permitting, inspection, and installation services</li>
                <li>12-year workmanship warranty</li>
                <li>25-year panel & inverter warranties</li>
                <li>30-year 3rd-party warranty coverage</li>
            </ul>
        </div>

        <div class="section">
            <h3>System Information</h3>
            <ul>
                <li>Annual Usage (kWh): <strong>{kwh_annual:,.0f}</strong></li>
                <li>Panel Count: <strong>{total_panels_calc}</strong></li>
                <li>Array Output (DC Watts): <strong>{int(output_watts):,}</strong></li>
                <li>Estimated Annual Production (kWh): <strong>{output_kwh:,.0f}</strong></li>
                <li>Monthly Electric Bill: <strong>${monthly_bill:,.2f}</strong></li>
                <li>Production Offset: <strong>{offset_percent}</strong></li>
            <ul>
        </div>

        <div class="section">
            <h3>Financing Overview</h3>
            <ul>
                <p>Gross System Cost: <strong>${total_project_cost:,.2f}</strong></p>
                <p>Federal Tax Credit: <strong>${federal_tax_credit:,.2f}</strong></p>
                <p>Net Cost After Incentives: <strong>${net_customer_cost:,.2f}</strong></p>
                <p>15yr Loan w/o ITC: <strong>{pymt_15}</strong></p>
                <p>20yr Loan w/o ITC: <strong>{pymt_20}</strong></p>
                <p>15yr Loan w/ ITC: <strong>{pymt_15_itc}</strong></p>
                <p>20yr Loan w/ ITC: <strong>{pymt_20_itc}</strong></p>
                <p>15-Year Rate: <strong>{rate_15yr:.2f}%</strong></p>
                <p>20-Year Rate: <strong>{rate_20yr:.2f}%</strong></p>
            <ul>
        </div>

        <div class="section">
            <h3>Contact</h3>
            <p>J4 Energy Solutions<br>
            (603) 270-6127<br>
            info@j4nrg.com<br>
            www.j4energysolutions.com<br>
            11 South Main St, Concord, NH 03301</p>
        </div>

        <div style="page-break-before: always;"></div>

        <div class="section">
            <img src="{logo_url}" style="width: 65%; max-width: 700px; display: block; margin: 0 auto 30px auto;" alt="J4 Logo Large"/>
            <h2 style="font-size: 32pt; text-align: center; margin-bottom: 20px;">Additional Services</h2>
            <p style="font-size: 20pt; text-align: center;"><strong>Enhance your solar investment with these premium upgrades:</strong></p>
            <ul style="font-size: 18pt;">
                <li><strong>Whole Home Generac Generator</strong></li>
                <li><strong>Battery Back-up</strong></li>
                <li><strong>High-Efficiency Heat Pumps</strong></li>
                <li><strong>New Asphalt or Metal Roof</strong></li>
            </ul>
            <p style="font-size: 14pt; text-align: center;">Ask your sales rep for more info on our additional services.</p>
        </div>

        <div class="section">
            <h3 style="font-size: 18pt; text-align: center;">Our Promise</h3>
            <p style="font-size: 16pt; text-align: center;">
                We will match or beat any legitimate solar estimate provided to us for review.<br><br>
                From my family to yours, we appreciate your time and the opportunity to earn your business.<br><br>
                <strong>Team J4</strong><br>
                <em>Family owned and operated</em>
            </p>
        </div>
    </body>
    </html>
    """

# --- Proposal Section ---
# Setup wkhtmltopdf path and config
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Suppress print media lookup, smart shrinking, etc.
options = {
    'enable-local-file-access': '',
    'no-print-media-type': '',
    'disable-smart-shrinking': '',
    'quiet': ''
}

if st.button("Download Proposal as PDF", key="download_proposal_pdf"):
    html = generate_proposal_html()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdfkit.from_string(html, tmpfile.name, configuration=config, options=options)

        tmpfile.seek(0)
        b64 = base64.b64encode(tmpfile.read()).decode()

    href = f'<a href="data:application/pdf;base64,{b64}" download="J4_Solar_Proposal.pdf">📥 Download Proposal PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
        
    

























