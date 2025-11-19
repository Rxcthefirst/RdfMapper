"""
Comprehensive Matcher Testing Suite

This module creates a contrived but realistic dataset designed to exercise
every matcher in the pipeline and demonstrate their unique contributions.
"""

# Employee Management System - Contrived Example
# Design Goals:
# 1. Test each matcher independently
# 2. Show how matchers work in combination
# 3. Demonstrate the value of each matcher

COLUMNS_BY_MATCHER = {
    "ExactPrefLabelMatcher": [
        "Employee ID",  # Will match ex:employeeID (skos:prefLabel)
    ],

    "ExactRdfsLabelMatcher": [
        "Full Name",  # Will match ex:fullName (rdfs:label)
    ],

    "ExactAltLabelMatcher": [
        "Birth Date",  # Will match ex:dateOfBirth (skos:altLabel "Birth Date")
    ],

    "ExactHiddenLabelMatcher": [
        "emp_num",  # Will match ex:employeeNumber (skos:hiddenLabel for legacy DB column)
        "hire_dt",  # Will match ex:hireDate (skos:hiddenLabel for legacy DB column)
    ],

    "ExactLocalNameMatcher": [
        "startDate",  # Will match ex:startDate (camelCase local name)
    ],

    "SemanticSimilarityMatcher": [
        "EmpID",  # Will match ex:employeeNumber via embeddings (0.85+)
        "Compensation",  # Will match ex:annualSalary via embeddings
        "Office Location",  # Will match ex:workLocation via embeddings
    ],

    "LexicalMatcher": [
        "annual_comp",  # Substring of "annualCompensation"
        "mgr",  # Abbreviation, will use token matching
        "phone",  # Partial match to "phoneNumber"
    ],

    "DataTypeInferenceMatcher": [
        # Acts as booster only - validates that integer→integer, string→string, etc.
        # All columns benefit from this
    ],

    "PropertyHierarchyMatcher": [
        "ContactEmail",  # Will match ex:email (child of ex:contactInformation)
    ],

    "OWLCharacteristicsMatcher": [
        "SSN",  # Will match ex:socialSecurityNumber (InverseFunctionalProperty)
    ],

    "GraphReasoningMatcher": [
        "DepartmentID",  # Foreign key to Department (detected as relationship)
        "ManagerID",  # Foreign key to Manager (detected as relationship)
    ],

    "StructuralMatcher": [
        "Team",  # Detected as related to ex:teamName via co-occurrence
    ],

    "PartialStringMatcher": [
        "pos",  # Partial match to "position" or "positionTitle"
    ],

    "FuzzyStringMatcher": [
        "adrs",  # Fuzzy match to "address" (typo/abbreviation)
    ]
}

# Generate CSV data
CSV_DATA = """EmployeeID,Employee ID,Full Name,Birth Date,emp_num,hire_dt,startDate,EmpID,Compensation,Office Location,annual_comp,mgr,phone,ContactEmail,SSN,DepartmentID,ManagerID,Team,pos,adrs
1001,E1001,John Smith,1985-03-15,EN-1001,2020-01-15,2020-01-15,E1001,95000,Building A - Floor 3,95000,M501,555-0101,john.smith@company.com,123-45-6789,D001,M501,Engineering,Senior Engineer,123 Main St
1002,E1002,Jane Doe,1990-07-22,EN-1002,2019-05-20,2019-05-20,E1002,87000,Building B - Floor 2,87000,M501,555-0102,jane.doe@company.com,234-56-7890,D001,M501,Engineering,Engineer,456 Oak Ave
1003,E1003,Bob Wilson,1988-11-30,EN-1003,2021-03-10,2021-03-10,E1003,78000,Building A - Floor 3,78000,M501,555-0103,bob.wilson@company.com,345-67-8901,D001,M501,Engineering,Junior Engineer,789 Pine Rd
M501,EM501,Alice Manager,1982-05-18,MG-M501,2015-08-01,2015-08-01,EM501,120000,Building A - Floor 5,120000,C100,555-0501,alice.manager@company.com,456-78-9012,D001,C100,Management,Engineering Manager,321 Elm St
1004,E1004,Carol Davis,1992-09-14,SA-1004,2022-01-05,2022-01-05,E1004,72000,Building B - Floor 1,72000,M502,555-0104,carol.davis@company.com,567-89-0123,D002,M502,Sales,Account Executive,654 Maple Dr
"""

print("✅ Test dataset designed to exercise all matchers")
print(f"📊 Total columns: {len([col for cols in COLUMNS_BY_MATCHER.values() for col in cols])}")
print(f"🎯 Matchers to test: {len(COLUMNS_BY_MATCHER)}")

