#!/usr/bin/env python
"""Test the _find_matching_sheet logic."""

# Test the logic directly
entity_lower = "customer"

plural_forms = [
    entity_lower + 's',      # customer -> customers
    entity_lower + 'es',     # address -> addresses
    entity_lower + 'ies',    # category -> categories (handled separately)
]

if entity_lower.endswith('y') and len(entity_lower) > 1:
    plural_forms.append(entity_lower[:-1] + 'ies')

print(f"Entity: '{entity_lower}'")
print(f"Plural forms: {plural_forms}")

# Test against "Customers"
sheet_names = ["Customers", "Orders"]

for sheet_name in sheet_names:
    sheet_lower = sheet_name.lower()
    print(f"\nSheet: '{sheet_name}' (lower: '{sheet_lower}')")
    print(f"  sheet_lower in plural_forms: {sheet_lower in plural_forms}")
    print(f"  any(form in sheet_lower for form in plural_forms): {any(form in sheet_lower for form in plural_forms)}")

    if sheet_lower in plural_forms:
        print(f"  ✓ MATCH via exact plural")
    elif any(form in sheet_lower for form in plural_forms):
        print(f"  ✓ MATCH via contains")

