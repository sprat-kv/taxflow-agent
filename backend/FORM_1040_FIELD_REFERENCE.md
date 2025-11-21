# Form 1040 Field Mapping Quick Reference

## Overview
This document provides a quick reference for all PDF field mappings used in Form 1040 generation.

## Personal Information (Page 1)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| filer_first_name | f1_04[0] | First name and middle initial | - |
| filer_last_name | f1_05[0] | Last name | - |
| filer_ssn | f1_06[0] | Social Security Number | - |

## Address (Page 1)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| home_address | f1_10[0] | Street address | - |
| city | f1_12[0] | City, town or post office | - |
| state | f1_13[0] | State (2-letter code) | - |
| zip | f1_14[0] | ZIP code | - |

## Income (Page 1)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| line_1a | f1_32[0] | Wages, tips, other compensation | 1a |
| line_1z | f1_41[0] | Total wages | 1z |
| line_2b | f1_43[0] | Taxable interest | 2b |
| line_8 | f1_53[0] | Additional income (1099-NEC) | 8 |
| line_9 | f1_54[0] | Total income | 9 |

## Adjustments & Deductions (Page 1)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| line_11 | f1_56[0] | Adjusted Gross Income | 11 |
| line_12 | f1_57[0] | Standard deduction | 12 |
| line_15 | f1_60[0] | Taxable income | 15 |

## Tax (Page 2)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| line_16 | f2_02[0] | Tax amount | 16 |
| line_24 | f2_10[0] | Total tax | 24 |

## Payments (Page 2)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| line_25a | f2_11[0] | Federal income tax withheld | 25a |
| line_33 | f2_22[0] | Total payments | 33 |

## Refund or Amount Owed (Page 2)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| line_34 | f2_23[0] | Amount you overpaid (refund) | 34 |
| line_37 | f2_28[0] | Amount you owe | 37 |

## Signature Section (Page 2)

| Our Data Key | PDF Field | Description | Line |
|--------------|-----------|-------------|------|
| occupation | f2_33[0] | Your occupation | - |
| phone | f2_37[0] | Phone number | - |

## Data Sources

### From `personal_info`
- filer_name → split into filer_first_name, filer_last_name
- filer_ssn
- home_address → parsed into street, city, state, zip
- occupation
- phone

### From `aggregated_data`
- total_wages → line_1a, line_1z
- total_interest → line_2b
- total_nec_income → line_8
- total_withholding → line_25a, line_33

### From `calculation_result`
- gross_income → line_9, line_11
- standard_deduction → line_12
- taxable_income → line_15
- tax_liability → line_16, line_24
- total_withholding → line_25a, line_33
- refund_or_owed → line_34 (if refund) or line_37 (if owed)
- status → determines which line to fill (34 or 37)

## Filing Status Checkboxes (NOT CURRENTLY FILLED)

These checkboxes are available in the template but not currently used:

| Status | Checkbox Field | Value |
|--------|---------------|-------|
| Single | topmostSubform[0].Page1[0].c1_1[0] | /1 |
| Married Filing Jointly | topmostSubform[0].Page1[0].c1_2[0] | /1 |
| Married Filing Separately | topmostSubform[0].Page1[0].c1_3[0] | /2 |
| Head of Household | topmostSubform[0].Page1[0].c1_3[1] | /5 |
| Qualifying Surviving Spouse | topmostSubform[0].Page1[0].c1_4[0] | /1 |

## Notes

1. **Currency Formatting**: All numeric values are formatted as `"1,234.56"` (comma separator, 2 decimals)
2. **Empty Values**: Fields with zero or missing values are set to empty string `""`
3. **Conditional Fields**: Line 34 (refund) and Line 37 (owed) are mutually exclusive
4. **Page Handling**: Fields are updated on both Page 1 and Page 2 in a single operation
5. **Address Parsing**: Currently supports "Street, City, State ZIP" format only

## See Also

- `backend/app/services/form_1040_service.py` - Implementation
- `1040_field_mapping_template.json` - Complete field reference with all 37 checkboxes
- `backend/FORM_1040_IMPLEMENTATION_SUMMARY.md` - Full implementation details

