# IRS Form 1040: Mandatory Data Fields Specification (Tax Year 2024)

**Purpose:** This document outlines the required fields for filing a valid US Individual Income Tax Return. It distinguishes between fields that are mandatory for *every* filer and fields that are conditionally mandatory based on specific financial situations.

---

## 1. Universally Mandatory Fields
*The following fields must be populated for the return to be accepted by the IRS. Omission results in immediate rejection.*

### A. Personal Identification (Page 1, Header)
* **Filer Name:** Must match Social Security Administration (SSA) records exactly.
* **Filer SSN:** The primary Social Security Number.
* **Spouse Name & SSN:** Mandatory **only if** Filing Status is *Married Filing Jointly*.
* **Home Address:** Street, City, State, and ZIP Code.

### B. Filing Status (Page 1, Top)
You **must** select exactly one of the following checkboxes:
* [ ] Single
* [ ] Married Filing Jointly
* [ ] Married Filing Separately
* [ ] Head of Household
* [ ] Qualifying Surviving Spouse

### C. The "Digital Assets" Question (Page 1)
You **must** mark a checkbox ("Yes" or "No") for the question:
> "At any time during 2024, did you: (a) receive (as a reward, award, or payment for property or services); or (b) sell, exchange, gift, or otherwise dispose of a digital asset (or a financial interest in a digital asset)?"

### D. Signatures (Page 2, Bottom)
* **Your Signature:** Required.
* **Date:** Required.
* **Your Occupation:** Required (e.g., "Engineer", "Student", "Unemployed").
* **Spouse Signature:** Mandatory if filing *Married Filing Jointly*.

---



## 2. Conditionally Mandatory Fields
*These fields are required based on the specific income or claims present in the return. Leaving these blank when data exists elsewhere (e.g., on a W-2) causes calculation errors.*

### A. Income Section (Lines 1–9)
* **Line 1a (Total Amount from Form(s) W-2, Box 1):** Mandatory if the user uploaded a W-2.
* **Line 2b (Taxable Interest):** Mandatory if 1099-INT Box 1 > $0.
* **Line 8 (Other Income):** Mandatory if 1099-NEC (freelance) income exists.
    * *Note:* This flows from **Schedule 1**.
* **Line 9 (Total Income):** The mathematical sum of Lines 1z through 8.

### B. Deductions & Taxable Income (Lines 12–15)
* **Line 12 (Standard Deduction or Itemized):** You **must** enter a value here.
    * *2024 Standard Values:* Single ($14,600), MFJ ($29,200), HOH ($21,900).
* **Line 15 (Taxable Income):** Line 9 minus Line 14. If negative, must be 0.

### C. Tax & Credits (Lines 16–24)
* **Line 16 (Tax):** The calculated tax liability from the tax tables.
* **Line 24 (Total Tax):** The final liability amount.

### D. Payments & Refund/Owed (Lines 25–37)
* **Line 25a (Federal Income Tax Withheld):** Mandatory. Must match the sum of Box 2 from all W-2s and 1099s.
* **Line 34 (Overpaid Amount):** Mandatory if Line 33 > Line 24.
* **Line 35a (Refund Amount):** The amount to be returned to the user.
* **Line 37 (Amount You Owe):** Mandatory if Line 24 > Line 33.

---

## 3. Validation Checklist
*Use this list to validate the extracted and calculated data before PDF generation.*

- [ ] **Identity:** Are Name and SSN present and formatted correctly?
- [ ] **Status:** Is exactly one Filing Status checked?
- [ ] **Compliance:** Is the Digital Assets question answered?
- [ ] **Logic:** Does Line 9 equal the sum of income lines?
- [ ] **Logic:** Does Line 15 (Taxable Income) equal Line 9 minus Deductions?
- [ ] **Logic:** Does Line 25a match the total withholding extracted from uploaded docs?
- [ ] **Balance:** Is either Line 34 (Refund) OR Line 37 (Owe) populated? (Never both).
- [ ] **Authentication:** Is the Occupation field filled?