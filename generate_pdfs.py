import os
from fpdf import FPDF

# Ensure the documents directory exists
os.makedirs("data/documents", exist_ok=True)

policies = {
    "Leave_Policy.pdf": """TechNova Pvt. Ltd. - Leave Policy
1. Annual Leave Entitlement: Every full-time employee receives 12 Earned Leaves, 8 Casual Leaves, and 5 Sick Leaves per year.
2. Carry Over: A maximum of 5 Earned Leaves can be carried over to the next financial year.
3. Applying for Leave: All leave applications must be submitted via the TechNova Assistant App or HR Portal at least 2 days in advance for casual leave.""",

    "Travel_Policy.pdf": """TechNova Pvt. Ltd. - Travel & Reimbursement Policy
1. Lodging Allowance: Employees traveling for official business are entitled to up to $150 per night for hotel accommodation.
2. Daily Allowance (Per Diem): A daily allowance of $50 is provided for meals and local transit.
3. Claims Process: Receipts must be submitted within 14 days of travel completion using the OCR document scanner in the HR portal.""",

    "Work_From_Home_Policy.pdf": """TechNova Pvt. Ltd. - Work From Home (WFH) Policy
1. Monthly Allowance: Employees are allowed up to 4 WFH days per calendar month with prior manager approval.
2. Core Hours: Employees working remotely must remain available on Slack and email during core business hours (10:00 AM to 4:00 PM).
3. Equipment: TechNova provides a one-time reimbursement of $200 for home office setup equipment."""
}

for filename, content in policies.items():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    
    output_path = os.path.join("data", "documents", filename)
    pdf.output(output_path)
    print(f"Created: {output_path}")

print("\nAll synthetic policy PDFs generated successfully!")