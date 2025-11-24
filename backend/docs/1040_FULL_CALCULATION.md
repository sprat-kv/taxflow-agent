# TaxAgent Design Specification: 2024 Filing Cycle

This document outlines the complete logic, mathematical models, and decision trees required to build a ReAct (Reasoning + Acting) AI agent capable of filing a 2024 US Individual Income Tax Return (Form 1040) for a user with mixed W-2 and 1099 income.

-----

## 1\. Agent Workflow Overview

The agent must follow a strict non-linear state machine. It must not proceed to calculation until all "blocking" information is resolved.

1.  **Ingestion Phase:** OCR/Parse documents $\rightarrow$ Extract raw values.
2.  **Profiling Phase:** Interview user for missing tax attributes (Filing Status, Residency, Dependents).
3.  **Classification Phase:** Categorize income (Employee vs. Self-Employed) and determine forms required.
4.  **Calculation Phase:** Execute the math engine defined in Section 3.
5.  **Review Phase:** Sanity check results against logical bounds.
6.  **Generation Phase:** Output final line-item values for Form 1040 and Schedules 1, 2, and C.

-----

## 2\. Input Data & Validation Rules

The agent must validate the following inputs before calculation.

### A. Documents (extracted via OCR)

  * **W-2:** Box 1 (Wages), Box 2 (Fed Tax Withheld).
  * **1099-NEC:** Box 1 (Nonemployee Compensation).
  * **1099-INT:** Box 1 (Interest Income).

### B. User Profile (Interview Questions)

  * **Filing Status:** Single, Married Filing Jointly (MFJ), Head of Household (HOH).
  * **Age:** If $\ge 65$, apply Additional Standard Deduction.
  * **Blindness:** If yes, apply Additional Standard Deduction.
  * **Residency:** US Citizen/Resident Alien (Form 1040) vs. Non-Resident (Form 1040-NR).
  * **Business Expenses:** Total deductible expenses for 1099-NEC work.
  * **Student Loan Interest:** Total interest paid in 2024 (if any).

-----

## 3\. Step-by-Step Calculation Engine (2024 Rules)

### Step 1: Calculate Net Profit from Business (Schedule C)

  * **Logic:** 1099-NEC income is "Gross Receipts." You must subtract expenses to get the taxable amount.
  * **Formula:**
    $$Net\_Profit = \sum(1099\_NEC\_Box1) - Business\_Expenses$$
  * **Condition:** If $Net\_Profit < 400$, user is exempt from SE Tax (skip Step 2).

### Step 2: Calculate Self-Employment (SE) Tax (Schedule SE)

  * **Context:** Replaces Social Security/Medicare withheld by employers.
  * **Constants (2024):**
      * Social Security Wage Base: **$168,600**
      * SS Rate: **12.4%**
      * Medicare Rate: **2.9%**
      * Taxable Earnings Factor: **92.35%**
  * **Algorithm:**
    1.  $Taxable\_SE\_Earnings = Net\_Profit \times 0.9235$
    2.  **Social Security Component:**
          * If $Taxable\_SE\_Earnings \le 168,600$: $SS\_Tax = Taxable\_SE\_Earnings \times 0.124$
          * If $Taxable\_SE\_Earnings > 168,600$: $SS\_Tax = 168,600 \times 0.124$
    3.  **Medicare Component:**
          * $Medicare\_Tax = Taxable\_SE\_Earnings \times 0.029$
    4.  **Total SE Tax:** $SE\_Tax = SS\_Tax + Medicare\_Tax$
    5.  **Deduction Amount:** $Deductible\_SE = SE\_Tax \times 0.5$ (Save this for Step 3).

### Step 3: Calculate Adjusted Gross Income (AGI)

  * **Logic:** Combine all income and subtract "above-the-line" deductions.
  * **Gross Income:**
    $$Gross\_Income = W2\_Box1 + 1099\_INT\_Box1 + Net\_Profit$$
  * **Adjustments (Schedule 1):**
      * **SE Tax Deduction:** Use $Deductible\_SE$ from Step 2.
      * **Student Loan Interest:** Deduct up to **$2,500**.
          * *Phase-out (Single):* MAGI $80k - $95k.
          * *Phase-out (MFJ):* MAGI $165k - $195k.
  * **Formula:**
    $$AGI = Gross\_Income - (Deductible\_SE + Student\_Loan\_Ded + Other\_Adj)$$

### Step 4: Determine Standard Deduction

  * **Logic:** Select deduction based on filing status and age/blindness.
  * **Base Amounts (2024):**
      * **Single / MFS:** $14,600
      * **MFJ / Widow(er):** $29,200
      * **Head of Household:** $21,900
  * **Add-ons (Age 65+ or Blind):**
      * **Single/HOH:** +$1,950 per condition.
      * **MFJ:** +$1,550 per condition.

### Step 5: Calculate Qualified Business Income (QBI) Deduction

  * **Logic:** A 20% tax break on Schedule C profit for eligible businesses.
  * **Thresholds (2024 Taxable Income before QBI):**
      * Single: **$191,950**
      * MFJ: **$383,900**
  * **Algorithm (Simplified):**
      * IF $(AGI - Std\_Ded) < Threshold$:
        $$QBI\_Ded = (Net\_Profit - Deductible\_SE) \times 0.20$$
        *Limit:* Deduction cannot exceed $20\% \times (Taxable\_Income\_Before\_QBI - Net\_Capital\_Gains)$.
      * IF Income \> Threshold: *Trigger warning: Complex calculation (Form 8995-A) required.*

### Step 6: Calculate Final Taxable Income

$$Taxable\_Income = AGI - Standard\_Deduction - QBI\_Deduction$$
*(If result \< 0, set to 0)*

### Step 7: Calculate Federal Income Tax

  * **Logic:** Apply progressive tax brackets to $Taxable\_Income$.
  * **2024 Brackets (Single Example):**
    1.  **10%:** $0 – $11,600
    2.  **12%:** $11,601 – $47,150
    3.  **22%:** $47,151 – $100,525
    4.  **24%:** $100,526 – $191,950
    5.  **32%:** $191,951 – $243,725
    6.  **35%:** $243,726 – $609,350
    7.  **37%:** \> $609,350
  * **Math Helper:** To calculate tax for income $I$ in bracket $N$:
    $$Tax = Base\_Tax\_Prev\_Bracket + ((I - Threshold\_Prev) \times Rate\_N)$$

### Step 8: Final Balancing

  * **Total Tax Liability:** $Federal\_Income\_Tax + SE\_Tax$.
  * **Total Payments:** $W2\_Box2$.
  * **Result:**
      * If $Total\_Tax > Payments$: **You Owe Amount**.
      * If $Payments > Total\_Tax$: **Refund Amount**.

-----

## 4\. Agent Logic & Decision Trees

The agent should use these logical checks to guide the user.

### Decision Tree: Business Classification

  * **Trigger:** 1099-NEC detected.
  * **Action:** Ask "Is this income from a freelance job, a side business, or a one-time hobby?"
      * *If "Hobby":* Report on Sched 1 "Other Income." **Do not** calculate SE Tax. **Do not** deduct expenses.
      * *If "Business/Freelance":* Proceed with Schedule C (Standard workflow).

### Decision Tree: QBI Eligibility

  * **Trigger:** Taxable income \> $191,950 (Single).
  * **Action:** Check if business is a "Specified Service Trade or Business" (SSTB) like health, law, or consulting.
      * *If Yes & Income \> Phase-out ($241,950):* QBI Deduction = 0.
      * *If No:* Continue with Form 8995-A calculations (wage/property limits).

-----

## 5\. Final Output Schema (JSON)

The agent must generate this JSON structure to map directly to Form 1040.

```json
{
  "tax_year": 2024,
  "filing_status": "Single",
  "schedules": {
    "schedule_c": {
      "gross_receipts": 0.00,
      "expenses": 0.00,
      "net_profit": 0.00
    },
    "schedule_se": {
      "taxable_earnings": 0.00,
      "self_employment_tax": 0.00,
      "deductible_part": 0.00
    }
  },
  "form_1040": {
    "line_1z_wages": 0.00,
    "line_2b_interest": 0.00,
    "line_8_other_income": 0.00,
    "line_10_adjustments": 0.00,
    "line_11_agi": 0.00,
    "line_12_std_deduction": 0.00,
    "line_13_qbi_deduction": 0.00,
    "line_15_taxable_income": 0.00,
    "line_16_tax": 0.00,
    "line_23_other_taxes": 0.00,
    "line_24_total_tax": 0.00,
    "line_25a_withholding": 0.00,
    "line_37_owe": 0.00,
    "line_34_refund": 0.00
  }
}
```