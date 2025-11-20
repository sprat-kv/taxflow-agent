# 2024 US Tax Calculation & Filing Logic Specification

This document outlines the mathematical logic, constants, and procedural steps required to calculate 2024 US Federal Income Tax and generate a filled Form 1040 PDF.

## Part 1: Tax Calculation Logic

### 1. Constants & Configuration (Tax Year 2024)

Use these exact values for calculations.

**Standard Deductions:**
* **Single:** $14,600
* **Married Filing Jointly (MFJ):** $29,200
* **Head of Household (HOH):** $21,900

**Tax Brackets (Marginal Rates):**

| Rate | Single Taxable Income | MFJ Taxable Income | HOH Taxable Income |
| :--- | :--- | :--- | :--- |
| **10%** | \$0 – \$11,600 | \$0 – \$23,200 | \$0 – \$16,550 |
| **12%** | \$11,601 – \$47,150 | \$23,201 – \$94,300 | \$16,551 – \$63,100 |
| **22%** | \$47,151 – \$100,525 | \$94,301 – \$201,050 | \$63,101 – \$100,500 |
| **24%** | \$100,526 – \$191,950 | \$201,051 – \$383,900 | \$100,501 – \$191,950 |
| **32%** | \$191,951 – \$243,725 | \$383,901 – \$487,450 | \$191,951 – \$243,700 |
| **35%** | \$243,726 – \$609,350 | \$487,451 – \$731,200 | \$243,701 – \$609,350 |
| **37%** | > \$609,350 | > \$731,200 | > \$609,350 |

### 2. Aggregation Logic (Data Preparation)



Extract numerical values from parsed documents and sum them by category.

* **Total Wages (`line_1a`):** Sum of Box 1 from all W-2s.
* **Total Interest (`line_2b`):** Sum of Box 1 from all 1099-INTs.
* **Other Income (`line_8`):** Sum of Box 1 (Nonemployee Compensation) from all 1099-NECs.
    * *Note: For this prototype, treat NEC income as generic "Other Income" to avoid implementing Schedule C/SE Tax complexity.*
* **Total Withholding (`line_25a`):** Sum of Box 2 (Fed Income Tax Withheld) from all W-2s.

### 3. Computation Steps

**Step A: Calculate Gross Income**
$$Gross\_Income = Total\_Wages + Total\_Interest + Other\_Income$$

**Step B: Determine Taxable Income**
1.  Identify the `Standard_Deduction` based on the user's Filing Status.
2.  Calculate:
    $$Taxable\_Income = Gross\_Income - Standard\_Deduction$$
3.  **Constraint:** If `Taxable_Income` < 0, set to 0.

**Step C: Calculate Tax Liability (Progressive Algorithm)**
Iterate through the brackets for the specific filing status.
1.  Initialize `Total_Tax = 0`.
2.  Initialize `Remaining_Income = Taxable_Income`.
3.  For each bracket `(Limit, Rate)`:
    * Determine the income chunk falling into this bracket.
    * `Chunk = Min(Remaining_Income, Limit - Previous_Limit)`
    * `Tax_For_Chunk = Chunk * Rate`
    * `Total_Tax += Tax_For_Chunk`
    * `Remaining_Income -= Chunk`
    * If `Remaining_Income <= 0`, break loop.

**Step D: Final Balance**
$$Balance = Total\_Tax - Total\_Withholding$$

* If `Balance < 0`: Result is **REFUND**. (Absolute value is the refund amount).
* If `Balance > 0`: Result is **OWED**.

---

## Part 2: Form 1040 Generation Logic

### Field Mapping Strategy

To fill the PDF programmatically, you must map your calculated variables to the PDF's internal AcroForm field names.

*Action:* Use a PDF inspection tool (or script using `pypdf.PdfReader.get_form_text_fields()`) on the official 2024 Form 1040 to obtain exact keys.

**Representative Mapping Table:**

| Logical Variable | 1040 PDF Field Key (Example) |
| :--- | :--- |
| First Name | `topmostSubform[0].Page1[0].f1_02[0]` |
| Last Name | `topmostSubform[0].Page1[0].f1_03[0]` |
| Filing Status Checkbox | `topmostSubform[0].Page1[0].c1_01[0]` |
| **Line 1a (Wages)** | `topmostSubform[0].Page1[0].f1_10[0]` |
| **Line 2b (Interest)** | `topmostSubform[0].Page1[0].f1_11[0]` |
| **Line 8 (Other Income)** | `topmostSubform[0].Page1[0].f1_16[0]` |
| **Line 9 (Total Income)** | `topmostSubform[0].Page1[0].f1_17[0]` |
| **Line 12 (Std Ded)** | `topmostSubform[0].Page1[0].f1_19[0]` |
| **Line 15 (Taxable Inc)**| `topmostSubform[0].Page1[0].f1_22[0]` |
| **Line 16 (Tax)** | `topmostSubform[0].Page1[0].f1_23[0]` |
| **Line 24 (Total Tax)** | `topmostSubform[0].Page1[0].f1_32[0]` |
| **Line 25a (Withholding)**| `topmostSubform[0].Page1[0].f1_33[0]` |
| **Line 34 (Refund)** | `topmostSubform[0].Page1[0].f1_45[0]` |
| **Line 37 (Owe)** | `topmostSubform[0].Page1[0].f1_48[0]` |

---

## Part 3: Verification & Testing

Use these mock scenarios to verify the logic before deployment.

**Test Case A: Simple Single (Refund)**
* **Input:** Single. W-2 Wages: $50,000. Withholding: $5,000.
* **Expected Math:**
    * Standard Deduction: $14,600
    * Taxable Income: $35,400
    * Tax (10% of 11.6k + 12% of Remainder): $1,160 + $2,856 = $4,016
    * Result: **Refund of $984** ($5,000 - $4,016).

**Test Case B: Freelancer (Owe)**
* **Input:** Single. 1099-NEC: $20,000. No Withholding.
* **Expected Math:**
    * Standard Deduction: $14,600
    * Taxable Income: $5,400
    * Tax (10% bracket): $540
    * Result: **Owe $540**.