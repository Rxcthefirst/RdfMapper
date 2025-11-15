"""Template library for common domain mappings.

Provides pre-built configuration templates for common use cases:
- Financial (loans, transactions, accounts)
- Healthcare (patients, visits, procedures)
- E-commerce (products, orders, customers)
- Academic (courses, students, enrollments)
- HR (employees, departments, positions)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class MappingTemplate:
    """A pre-built mapping template for a specific domain."""

    def __init__(
        self,
        name: str,
        description: str,
        domain: str,
        example_ontology: Optional[str] = None,
        example_data: Optional[str] = None,
        template_config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.domain = domain
        self.example_ontology = example_ontology
        self.example_data = example_data
        self.template_config = template_config or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "example_ontology": self.example_ontology,
            "example_data": self.example_data,
            "template_config": self.template_config
        }


class TemplateLibrary:
    """Library of pre-built mapping templates."""

    def __init__(self):
        self.templates: Dict[str, MappingTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """Load built-in templates."""
        # Financial templates
        self.add_template(MappingTemplate(
            name="financial-loans",
            description="Mortgage loans with borrower and property information",
            domain="financial",
            example_ontology="examples/mortgage/ontology/mortgage.ttl",
            example_data="examples/mortgage/data/loans.csv",
            template_config={
                "expected_columns": [
                    "LoanID", "BorrowerID", "PropertyID", "Principal",
                    "InterestRate", "LoanTerm", "OriginationDate"
                ],
                "target_classes": ["MortgageLoan", "Borrower", "Property"],
                "relationships": ["hasBorrower", "collateralProperty"]
            }
        ))

        self.add_template(MappingTemplate(
            name="financial-transactions",
            description="Financial transactions with accounts and categories",
            domain="financial",
            template_config={
                "expected_columns": [
                    "TransactionID", "AccountID", "Date", "Amount",
                    "Type", "Category", "Description"
                ],
                "target_classes": ["Transaction", "Account", "Category"],
                "relationships": ["fromAccount", "hasCategory"]
            }
        ))

        self.add_template(MappingTemplate(
            name="financial-accounts",
            description="Bank accounts with customer information",
            domain="financial",
            template_config={
                "expected_columns": [
                    "AccountID", "CustomerID", "AccountNumber", "AccountType",
                    "Balance", "OpenDate", "Status"
                ],
                "target_classes": ["Account", "Customer"],
                "relationships": ["accountHolder"]
            }
        ))

        # Healthcare templates
        self.add_template(MappingTemplate(
            name="healthcare-patients",
            description="Patient records with demographics and visits",
            domain="healthcare",
            template_config={
                "expected_columns": [
                    "PatientID", "FirstName", "LastName", "DateOfBirth",
                    "Gender", "Address", "Phone", "Email"
                ],
                "target_classes": ["Patient", "Address", "ContactInfo"],
                "relationships": ["hasAddress", "hasContactInfo"]
            }
        ))

        self.add_template(MappingTemplate(
            name="healthcare-visits",
            description="Medical visits with diagnoses and procedures",
            domain="healthcare",
            template_config={
                "expected_columns": [
                    "VisitID", "PatientID", "ProviderID", "VisitDate",
                    "DiagnosisCode", "ProcedureCode", "Notes"
                ],
                "target_classes": ["Visit", "Patient", "Provider", "Diagnosis", "Procedure"],
                "relationships": ["patient", "provider", "hasDiagnosis", "hasProcedure"]
            }
        ))

        # E-commerce templates
        self.add_template(MappingTemplate(
            name="ecommerce-products",
            description="Product catalog with categories and pricing",
            domain="ecommerce",
            template_config={
                "expected_columns": [
                    "ProductID", "ProductName", "CategoryID", "Price",
                    "Description", "SKU", "Stock", "Manufacturer"
                ],
                "target_classes": ["Product", "Category", "Manufacturer"],
                "relationships": ["inCategory", "manufacturedBy"]
            }
        ))

        self.add_template(MappingTemplate(
            name="ecommerce-orders",
            description="Customer orders with line items",
            domain="ecommerce",
            template_config={
                "expected_columns": [
                    "OrderID", "CustomerID", "OrderDate", "TotalAmount",
                    "ShippingAddress", "Status", "PaymentMethod"
                ],
                "target_classes": ["Order", "Customer", "Address", "Payment"],
                "relationships": ["customer", "shippingAddress", "paymentMethod"]
            }
        ))

        self.add_template(MappingTemplate(
            name="ecommerce-customers",
            description="Customer profiles with contact and billing info",
            domain="ecommerce",
            template_config={
                "expected_columns": [
                    "CustomerID", "FirstName", "LastName", "Email",
                    "Phone", "BillingAddress", "ShippingAddress", "JoinDate"
                ],
                "target_classes": ["Customer", "Address"],
                "relationships": ["billingAddress", "shippingAddress"]
            }
        ))

        # Academic templates
        self.add_template(MappingTemplate(
            name="academic-students",
            description="Student records with enrollment information",
            domain="academic",
            template_config={
                "expected_columns": [
                    "StudentID", "FirstName", "LastName", "Email",
                    "Major", "Year", "GPA", "EnrollmentDate"
                ],
                "target_classes": ["Student", "Major", "Enrollment"],
                "relationships": ["hasMajor", "enrolled"]
            }
        ))

        self.add_template(MappingTemplate(
            name="academic-courses",
            description="Course catalog with instructors and schedules",
            domain="academic",
            template_config={
                "expected_columns": [
                    "CourseID", "CourseName", "InstructorID", "Credits",
                    "Department", "Schedule", "Room", "Capacity"
                ],
                "target_classes": ["Course", "Instructor", "Department", "Room"],
                "relationships": ["instructor", "inDepartment", "assignedRoom"]
            }
        ))

        self.add_template(MappingTemplate(
            name="academic-enrollments",
            description="Student course enrollments with grades",
            domain="academic",
            template_config={
                "expected_columns": [
                    "EnrollmentID", "StudentID", "CourseID", "Semester",
                    "Year", "Grade", "Status"
                ],
                "target_classes": ["Enrollment", "Student", "Course"],
                "relationships": ["student", "course"]
            }
        ))

        # HR templates
        self.add_template(MappingTemplate(
            name="hr-employees",
            description="Employee records with departments and positions",
            domain="hr",
            template_config={
                "expected_columns": [
                    "EmployeeID", "FirstName", "LastName", "Email",
                    "DepartmentID", "PositionID", "HireDate", "Salary"
                ],
                "target_classes": ["Employee", "Department", "Position"],
                "relationships": ["inDepartment", "hasPosition"]
            }
        ))

        self.add_template(MappingTemplate(
            name="hr-departments",
            description="Organizational departments with managers",
            domain="hr",
            template_config={
                "expected_columns": [
                    "DepartmentID", "DepartmentName", "ManagerID",
                    "Budget", "Location", "EmployeeCount"
                ],
                "target_classes": ["Department", "Employee", "Location"],
                "relationships": ["manager", "location"]
            }
        ))

    def add_template(self, template: MappingTemplate):
        """Add a template to the library."""
        self.templates[template.name] = template

    def get_template(self, name: str) -> Optional[MappingTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_templates(self, domain: Optional[str] = None) -> List[MappingTemplate]:
        """List all templates, optionally filtered by domain."""
        templates = list(self.templates.values())
        if domain:
            templates = [t for t in templates if t.domain == domain]
        return templates

    def list_domains(self) -> List[str]:
        """List all available domains."""
        domains = set(t.domain for t in self.templates.values())
        return sorted(domains)

    def apply_template(
        self,
        template_name: str,
        ontology_file: str,
        data_file: str,
        base_iri: str = "http://example.org/"
    ) -> Dict[str, Any]:
        """Apply a template to create a starter configuration.

        Args:
            template_name: Name of the template to apply
            ontology_file: Path to ontology file
            data_file: Path to data file
            base_iri: Base IRI for generated resources

        Returns:
            Starter configuration dictionary
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Create basic configuration structure
        config = {
            "namespaces": {
                "ex": f"{base_iri}#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            },
            "defaults": {
                "base_iri": base_iri
            },
            "sheets": [
                {
                    "name": Path(data_file).stem,
                    "source": data_file,
                    "row_resource": {
                        "class": "ex:ClassName",  # Will be replaced by actual generation
                        "iri_template": "{base_iri}resource/{ID}"
                    },
                    "columns": {},
                    "objects": {}
                }
            ],
            "options": {
                "on_error": "report",
                "skip_empty_values": True
            },
            "_template": {
                "name": template.name,
                "domain": template.domain,
                "description": template.description,
                "expected_columns": template.template_config.get("expected_columns", []),
                "target_classes": template.template_config.get("target_classes", []),
                "relationships": template.template_config.get("relationships", [])
            }
        }

        return config


# Global template library instance
_library = None


def get_template_library() -> TemplateLibrary:
    """Get the global template library instance."""
    global _library
    if _library is None:
        _library = TemplateLibrary()
    return _library

