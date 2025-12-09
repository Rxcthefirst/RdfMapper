#!/usr/bin/env python3
"""
Create realistic nested JSON and XML test data for RML testing.

Tests complex nested structures:
- JSON: Nested objects and arrays (mortgage application with borrower details, employment history, etc.)
- XML: Hierarchical data with multiple levels (loan portfolio with nested entities)
"""

import json
from pathlib import Path

def create_nested_json():
    """Create realistic nested JSON for mortgage applications."""

    # Complex nested structure with multiple levels
    data = [
        {
            "applicationId": "APP-2024-001",
            "submittedDate": "2024-01-15",
            "status": "approved",
            "loanDetails": {
                "requestedAmount": 450000,
                "loanTerm": 360,
                "interestRate": 4.25,
                "loanType": "conventional",
                "purpose": "purchase"
            },
            "property": {
                "propertyId": "PROP-12345",
                "address": {
                    "street": "123 Oak Street",
                    "city": "Portland",
                    "state": "OR",
                    "zipCode": "97201",
                    "country": "USA"
                },
                "details": {
                    "propertyType": "single-family",
                    "yearBuilt": 1995,
                    "squareFeet": 2400,
                    "bedrooms": 4,
                    "bathrooms": 2.5
                },
                "appraisal": {
                    "appraisedValue": 485000,
                    "appraisalDate": "2024-01-20",
                    "appraiser": {
                        "name": "Jane Smith",
                        "licenseNumber": "APR-98765"
                    }
                }
            },
            "borrowers": [
                {
                    "borrowerId": "BOR-001",
                    "borrowerType": "primary",
                    "personalInfo": {
                        "firstName": "John",
                        "lastName": "Anderson",
                        "dateOfBirth": "1985-03-15",
                        "ssn": "XXX-XX-1234",
                        "maritalStatus": "married"
                    },
                    "contactInfo": {
                        "email": "john.anderson@email.com",
                        "phone": {
                            "home": "503-555-0100",
                            "mobile": "503-555-0101"
                        },
                        "currentAddress": {
                            "street": "456 Elm Ave",
                            "city": "Portland",
                            "state": "OR",
                            "zipCode": "97202"
                        }
                    },
                    "employment": {
                        "current": {
                            "employer": "Tech Corp Inc",
                            "position": "Senior Software Engineer",
                            "startDate": "2018-06-01",
                            "annualIncome": 125000,
                            "employmentType": "full-time",
                            "contact": {
                                "phone": "503-555-0200",
                                "supervisor": "Mike Johnson"
                            }
                        },
                        "history": [
                            {
                                "employer": "StartUp LLC",
                                "position": "Software Developer",
                                "startDate": "2015-01-15",
                                "endDate": "2018-05-31",
                                "annualIncome": 85000
                            }
                        ]
                    },
                    "financials": {
                        "income": {
                            "base": 125000,
                            "bonus": 15000,
                            "other": 5000
                        },
                        "assets": [
                            {
                                "type": "checking",
                                "institution": "First Bank",
                                "accountNumber": "****1234",
                                "balance": 45000
                            },
                            {
                                "type": "401k",
                                "institution": "Retirement Fund Inc",
                                "accountNumber": "****5678",
                                "balance": 180000
                            }
                        ],
                        "liabilities": [
                            {
                                "type": "auto-loan",
                                "creditor": "Auto Finance Co",
                                "balance": 18000,
                                "monthlyPayment": 450
                            }
                        ]
                    },
                    "creditReport": {
                        "score": 760,
                        "reportDate": "2024-01-10",
                        "bureau": "TransUnion"
                    }
                },
                {
                    "borrowerId": "BOR-002",
                    "borrowerType": "co-borrower",
                    "personalInfo": {
                        "firstName": "Sarah",
                        "lastName": "Anderson",
                        "dateOfBirth": "1987-07-22",
                        "ssn": "XXX-XX-5678",
                        "maritalStatus": "married"
                    },
                    "contactInfo": {
                        "email": "sarah.anderson@email.com",
                        "phone": {
                            "mobile": "503-555-0102"
                        }
                    },
                    "employment": {
                        "current": {
                            "employer": "Healthcare Partners",
                            "position": "Registered Nurse",
                            "startDate": "2016-09-01",
                            "annualIncome": 85000,
                            "employmentType": "full-time"
                        }
                    },
                    "financials": {
                        "income": {
                            "base": 85000,
                            "bonus": 5000,
                            "other": 0
                        },
                        "assets": [
                            {
                                "type": "savings",
                                "institution": "First Bank",
                                "balance": 35000
                            }
                        ]
                    },
                    "creditReport": {
                        "score": 745,
                        "reportDate": "2024-01-10",
                        "bureau": "Equifax"
                    }
                }
            ],
            "documents": [
                {
                    "documentId": "DOC-001",
                    "type": "paystub",
                    "borrowerId": "BOR-001",
                    "uploadDate": "2024-01-12",
                    "verified": True
                },
                {
                    "documentId": "DOC-002",
                    "type": "tax-return",
                    "borrowerId": "BOR-001",
                    "year": 2023,
                    "uploadDate": "2024-01-13",
                    "verified": True
                }
            ],
            "underwriting": {
                "underwriterId": "UW-123",
                "underwriterName": "Lisa Chen",
                "reviewDate": "2024-01-25",
                "decision": "approved",
                "conditions": [
                    {
                        "conditionId": "COND-001",
                        "description": "Provide final verification of employment",
                        "status": "satisfied"
                    }
                ],
                "notes": "Strong application with excellent credit and stable employment"
            }
        },
        {
            "applicationId": "APP-2024-002",
            "submittedDate": "2024-02-01",
            "status": "pending",
            "loanDetails": {
                "requestedAmount": 325000,
                "loanTerm": 300,
                "interestRate": 4.5,
                "loanType": "FHA",
                "purpose": "refinance"
            },
            "property": {
                "propertyId": "PROP-67890",
                "address": {
                    "street": "789 Pine Road",
                    "city": "Seattle",
                    "state": "WA",
                    "zipCode": "98101"
                },
                "details": {
                    "propertyType": "condo",
                    "yearBuilt": 2010,
                    "squareFeet": 1800,
                    "bedrooms": 3,
                    "bathrooms": 2
                }
            },
            "borrowers": [
                {
                    "borrowerId": "BOR-003",
                    "borrowerType": "primary",
                    "personalInfo": {
                        "firstName": "Michael",
                        "lastName": "Chen",
                        "dateOfBirth": "1990-11-03",
                        "ssn": "XXX-XX-9012"
                    },
                    "employment": {
                        "current": {
                            "employer": "Design Studio",
                            "position": "Creative Director",
                            "startDate": "2020-03-01",
                            "annualIncome": 95000,
                            "employmentType": "full-time"
                        }
                    },
                    "creditReport": {
                        "score": 720,
                        "reportDate": "2024-02-01"
                    }
                }
            ]
        }
    ]

    output_dir = Path('../test_formats')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'mortgage_applications_nested.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Created nested JSON: {output_file}")
    print(f"   - Structure depth: 6+ levels")
    print(f"   - Arrays: borrowers, assets, liabilities, documents")
    print(f"   - Nested objects: loanDetails, property.address, employment.current")
    return output_file

def create_nested_xml():
    """Create realistic nested XML for loan portfolio."""

    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<loanPortfolio>
  <portfolio portfolioId="PORT-2024-001">
    <portfolioInfo>
      <name>Residential Mortgage Portfolio 2024</name>
      <manager>
        <managerId>MGR-001</managerId>
        <name>David Martinez</name>
        <email>david.martinez@bank.com</email>
      </manager>
      <totalValue>5000000</totalValue>
      <numberOfLoans>15</numberOfLoans>
    </portfolioInfo>
    
    <loans>
      <loan loanId="LOAN-2024-001">
        <loanInfo>
          <originationDate>2024-01-15</originationDate>
          <principalAmount>450000</principalAmount>
          <currentBalance>448500</currentBalance>
          <interestRate>4.25</interestRate>
          <loanTerm>360</loanTerm>
          <loanType>conventional</loanType>
          <status>current</status>
        </loanInfo>
        
        <borrower>
          <borrowerId>BOR-1001</borrowerId>
          <personalDetails>
            <firstName>John</firstName>
            <lastName>Anderson</lastName>
            <dateOfBirth>1985-03-15</dateOfBirth>
            <ssn>XXX-XX-1234</ssn>
          </personalDetails>
          <contactDetails>
            <email>john.anderson@email.com</email>
            <phones>
              <phone type="mobile">503-555-0101</phone>
              <phone type="home">503-555-0100</phone>
            </phones>
            <address>
              <street>456 Elm Ave</street>
              <city>Portland</city>
              <state>OR</state>
              <zipCode>97202</zipCode>
              <country>USA</country>
            </address>
          </contactDetails>
          <employment>
            <currentEmployment>
              <employer>Tech Corp Inc</employer>
              <position>Senior Software Engineer</position>
              <startDate>2018-06-01</startDate>
              <annualIncome>125000</annualIncome>
              <employmentType>full-time</employmentType>
            </currentEmployment>
            <employmentHistory>
              <previousEmployment>
                <employer>StartUp LLC</employer>
                <position>Software Developer</position>
                <startDate>2015-01-15</startDate>
                <endDate>2018-05-31</endDate>
                <annualIncome>85000</annualIncome>
              </previousEmployment>
            </employmentHistory>
          </employment>
          <creditProfile>
            <creditScore>760</creditScore>
            <scoreDate>2024-01-10</scoreDate>
            <bureau>TransUnion</bureau>
            <debtToIncome>0.28</debtToIncome>
          </creditProfile>
        </borrower>
        
        <coBorrowers>
          <coBorrower>
            <borrowerId>BOR-1002</borrowerId>
            <personalDetails>
              <firstName>Sarah</firstName>
              <lastName>Anderson</lastName>
              <dateOfBirth>1987-07-22</dateOfBirth>
            </personalDetails>
            <employment>
              <currentEmployment>
                <employer>Healthcare Partners</employer>
                <position>Registered Nurse</position>
                <annualIncome>85000</annualIncome>
              </currentEmployment>
            </employment>
            <creditProfile>
              <creditScore>745</creditScore>
            </creditProfile>
          </coBorrower>
        </coBorrowers>
        
        <collateral>
          <property propertyId="PROP-12345">
            <propertyType>single-family</propertyType>
            <address>
              <street>123 Oak Street</street>
              <city>Portland</city>
              <state>OR</state>
              <zipCode>97201</zipCode>
            </address>
            <propertyDetails>
              <yearBuilt>1995</yearBuilt>
              <squareFeet>2400</squareFeet>
              <bedrooms>4</bedrooms>
              <bathrooms>2.5</bathrooms>
              <lotSize>8000</lotSize>
            </propertyDetails>
            <valuation>
              <appraisedValue>485000</appraisedValue>
              <appraisalDate>2024-01-20</appraisalDate>
              <appraiser>
                <name>Jane Smith</name>
                <licenseNumber>APR-98765</licenseNumber>
                <company>Professional Appraisals Inc</company>
              </appraiser>
              <loanToValue>0.927</loanToValue>
            </valuation>
            <insurance>
              <provider>HomeInsure Co</provider>
              <policyNumber>POL-789456</policyNumber>
              <annualPremium>1800</annualPremium>
              <coverageAmount>485000</coverageAmount>
            </insurance>
          </property>
        </collateral>
        
        <paymentSchedule>
          <monthlyPayment>
            <principalAndInterest>2200</principalAndInterest>
            <escrow>
              <propertyTax>400</propertyTax>
              <insurance>150</insurance>
            </escrow>
            <totalPayment>2750</totalPayment>
          </monthlyPayment>
          <nextPaymentDate>2024-03-01</nextPaymentDate>
          <paymentsRemaining>358</paymentsRemaining>
        </paymentSchedule>
        
        <paymentHistory>
          <payment paymentId="PAY-001">
            <paymentDate>2024-02-01</paymentDate>
            <amount>2750</amount>
            <principalPaid>833</principalPaid>
            <interestPaid>1367</interestPaid>
            <escrowPaid>550</escrowPaid>
            <status>paid</status>
          </payment>
          <payment paymentId="PAY-002">
            <paymentDate>2024-01-01</paymentDate>
            <amount>2750</amount>
            <principalPaid>830</principalPaid>
            <interestPaid>1370</interestPaid>
            <escrowPaid>550</escrowPaid>
            <status>paid</status>
          </payment>
        </paymentHistory>
        
        <servicing>
          <servicer>
            <servicerId>SERV-001</servicerId>
            <name>Mortgage Servicing Corp</name>
            <contact>
              <phone>1-800-555-LOAN</phone>
              <email>service@mortgageserv.com</email>
            </contact>
          </servicer>
          <escrowAccount>
            <accountNumber>ESC-123456</accountNumber>
            <currentBalance>3200</currentBalance>
            <lastAnalysisDate>2024-01-15</lastAnalysisDate>
          </escrowAccount>
        </servicing>
      </loan>
      
      <loan loanId="LOAN-2024-002">
        <loanInfo>
          <originationDate>2024-02-01</originationDate>
          <principalAmount>325000</principalAmount>
          <currentBalance>324500</currentBalance>
          <interestRate>4.50</interestRate>
          <loanTerm>300</loanTerm>
          <loanType>FHA</loanType>
          <status>current</status>
        </loanInfo>
        <borrower>
          <borrowerId>BOR-2001</borrowerId>
          <personalDetails>
            <firstName>Michael</firstName>
            <lastName>Chen</lastName>
            <dateOfBirth>1990-11-03</dateOfBirth>
          </personalDetails>
          <employment>
            <currentEmployment>
              <employer>Design Studio</employer>
              <position>Creative Director</position>
              <annualIncome>95000</annualIncome>
            </currentEmployment>
          </employment>
          <creditProfile>
            <creditScore>720</creditScore>
          </creditProfile>
        </borrower>
        <collateral>
          <property propertyId="PROP-67890">
            <propertyType>condo</propertyType>
            <address>
              <street>789 Pine Road</street>
              <city>Seattle</city>
              <state>WA</state>
              <zipCode>98101</zipCode>
            </address>
            <propertyDetails>
              <yearBuilt>2010</yearBuilt>
              <squareFeet>1800</squareFeet>
              <bedrooms>3</bedrooms>
              <bathrooms>2</bathrooms>
            </propertyDetails>
            <valuation>
              <appraisedValue>340000</appraisedValue>
              <appraisalDate>2024-01-25</appraisalDate>
            </valuation>
          </property>
        </collateral>
      </loan>
    </loans>
  </portfolio>
</loanPortfolio>'''

    output_dir = Path('../test_formats')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'loan_portfolio_nested.xml'
    with open(output_file, 'w') as f:
        f.write(xml_content)

    print(f"✅ Created nested XML: {output_file}")
    print(f"   - Structure depth: 8+ levels")
    print(f"   - Multiple loans with nested borrower, property, payment data")
    print(f"   - Hierarchical: portfolio > loans > loan > borrower > employment > history")
    return output_file

if __name__ == "__main__":
    print("="*60)
    print("Creating Realistic Nested Test Data")
    print("="*60)
    print()

    json_file = create_nested_json()
    print()
    xml_file = create_nested_xml()

    print()
    print("="*60)
    print("✅ Test data created successfully!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Create RML mappings for these nested structures")
    print("2. Test JSONPath queries (e.g., $.borrowers[*].employment.current)")
    print("3. Test XPath queries (e.g., //loan/borrower/employment/currentEmployment)")
    print("4. Verify nested object property mappings")

