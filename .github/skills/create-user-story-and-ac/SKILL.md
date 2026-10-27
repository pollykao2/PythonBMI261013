---
name: create-user-story-and-ac
description: Implement and verify the preliminary Taiwan military service BMI assessment while preserving the distinction between general BMI guidance and official military service classification.
---

# Create User Story and Acceptance Criteria

Use this skill when implementing or reviewing the Taiwan military service BMI assessment feature in this repository.

## User Story

As a user, I want to receive a preliminary BMI-based military service assessment so that I can understand that further verification against the latest official Taiwan regulations is required.

## Acceptance Criteria

- The system clearly labels the result as a preliminary assessment and not an official military service classification.
- The system does not claim to determine official Taiwan military service status from general adult BMI categories.
- The result includes guidance to verify eligibility using the latest official Taiwan regulations or an authorized authority.
- The assessment uses the user-provided height and weight values and handles invalid or missing values with a clear validation message.
- The assessment does not present invented, outdated, or unverified Taiwan military service standards as official requirements.

## Implementation Requirements

1. Reuse the existing BMI input validation and calculation flow.
2. Show the assessment only after valid height and weight values have been submitted.
3. Present the calculated BMI and the submitted height and weight as preliminary information only.
4. Keep general adult BMI health guidance separate from the military service assessment.
5. Preserve existing BMI history behavior and existing validation messages unless a change is required to satisfy the acceptance criteria.
6. Add or update automated tests for:
   - successful display of the preliminary assessment;
   - explicit non-official classification wording;
   - guidance to consult the latest official regulations or an authorized authority;
   - invalid or missing input behavior.
7. Update user-facing documentation when the feature behavior changes.

## Taiwan Military Service Safety Rules

- Never invent, infer, or state Taiwan military-service height, weight, BMI, or body-status thresholds as official standards.
- Never describe general adult BMI categories as formal military-service eligibility or body-status rules.
- Never label the result as a military-service classification, eligibility decision, conscription decision, or official determination.
- Always identify the result as a preliminary assessment.
- Always direct users to the latest official Taiwan regulations or an authorized government or professional authority for the formal determination.
- If official standards are needed in the future, verify them against a current authoritative source before implementing or documenting them.

## Verification

Run the repository's focused test suite after changes:

```powershell
python -m unittest discover -s tests -v
```

Confirm that the tests pass and that the rendered result contains the preliminary-assessment disclaimer without presenting unofficial military-service thresholds.
