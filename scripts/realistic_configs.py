"""Realistic mapping configurations for employee and project data."""

from pathlib import Path
from src.rdfmap.models.mapping import (
    MappingConfig, SheetMapping, RowResource, ColumnMapping,
    DefaultsConfig, ProcessingOptions, LinkedObject, ObjectPropertyMapping
)


def create_employee_mapping_config(file_path: Path) -> MappingConfig:
    """Create realistic employee mapping configuration with rich ontology mapping."""

    return MappingConfig(
        namespaces={
            'ex': 'http://example.org/hr#',
            'foaf': 'http://xmlns.com/foaf/0.1/',
            'org': 'http://www.w3.org/ns/org#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'skos': 'http://www.w3.org/2004/02/skos/core#'
        },
        defaults=DefaultsConfig(
            base_iri='http://data.company.com/',
            language='en'
        ),
        sheets=[
            SheetMapping(
                name='employees',
                source=str(file_path),
                row_resource=RowResource(
                    **{'class': 'ex:Employee'},
                    iri_template='{base_iri}employee/{EmployeeID}'
                ),
                columns={
                    # Identity
                    'EmployeeID': ColumnMapping(**{
                        'as': 'ex:employeeId',
                        'datatype': 'xsd:string'
                    }),
                    'FirstName': ColumnMapping(**{
                        'as': 'foaf:givenName',
                        'datatype': 'xsd:string',
                        'transform': 'strip'
                    }),
                    'LastName': ColumnMapping(**{
                        'as': 'foaf:familyName',
                        'datatype': 'xsd:string',
                        'transform': 'strip'
                    }),
                    'FullName': ColumnMapping(**{
                        'as': 'foaf:name',
                        'datatype': 'xsd:string'
                    }),
                    'Email': ColumnMapping(**{
                        'as': 'foaf:mbox',
                        'datatype': 'xsd:string',
                        'transform': 'lowercase'
                    }),

                    # Employment details
                    'Department': ColumnMapping(**{
                        'as': 'org:memberOf',
                        'datatype': 'xsd:string'
                    }),
                    'JobTitle': ColumnMapping(**{
                        'as': 'ex:jobTitle',
                        'datatype': 'xsd:string'
                    }),
                    'Salary': ColumnMapping(**{
                        'as': 'ex:annualSalary',
                        'datatype': 'xsd:decimal'
                    }),
                    'HireDate': ColumnMapping(**{
                        'as': 'ex:hireDate',
                        'datatype': 'xsd:date'
                    }),
                    'YearsExperience': ColumnMapping(**{
                        'as': 'ex:yearsExperience',
                        'datatype': 'xsd:integer'
                    }),

                    # Personal details
                    'Age': ColumnMapping(**{
                        'as': 'foaf:age',
                        'datatype': 'xsd:integer'
                    }),
                    'City': ColumnMapping(**{
                        'as': 'ex:workCity',
                        'datatype': 'xsd:string'
                    }),
                    'State': ColumnMapping(**{
                        'as': 'ex:workState',
                        'datatype': 'xsd:string',
                        'transform': 'uppercase'
                    }),

                    # Performance and status
                    'IsActive': ColumnMapping(**{
                        'as': 'ex:isActive',
                        'datatype': 'xsd:boolean'
                    }),
                    'PerformanceRating': ColumnMapping(**{
                        'as': 'ex:performanceRating',
                        'datatype': 'xsd:decimal'
                    }),
                    'LastReviewDate': ColumnMapping(**{
                        'as': 'ex:lastReviewDate',
                        'datatype': 'xsd:date'
                    }),

                    # Additional info
                    'Skills': ColumnMapping(**{
                        'as': 'ex:skills',
                        'datatype': 'xsd:string',
                        'multi_valued': True,
                        'delimiter': ', '
                    }),
                    'Notes': ColumnMapping(**{
                        'as': 'rdfs:comment',
                        'datatype': 'xsd:string',
                        'transform': 'trim'
                    }),
                },
                objects={
                    'manager': LinkedObject(
                        predicate='ex:reportsTo',
                        **{'class': 'ex:Employee'},
                        iri_template='{base_iri}employee/{ManagerID}',
                        properties=[
                            ObjectPropertyMapping(
                                column='ManagerID',
                                **{'as': 'ex:employeeId'},
                                datatype='xsd:string'
                            )
                        ]
                    )
                }
            )
        ],
        options=ProcessingOptions(
            chunk_size=50000,
            header=True,
            delimiter=',',
            on_error='report'
        )
    )


def create_project_mapping_config(file_path: Path) -> MappingConfig:
    """Create realistic project mapping configuration."""

    return MappingConfig(
        namespaces={
            'ex': 'http://example.org/projects#',
            'foaf': 'http://xmlns.com/foaf/0.1/',
            'org': 'http://www.w3.org/ns/org#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'dcterms': 'http://purl.org/dc/terms/'
        },
        defaults=DefaultsConfig(
            base_iri='http://data.company.com/',
            language='en'
        ),
        sheets=[
            SheetMapping(
                name='projects',
                source=str(file_path),
                row_resource=RowResource(
                    **{'class': 'ex:Project'},
                    iri_template='{base_iri}project/{ProjectID}'
                ),
                columns={
                    # Project identity
                    'ProjectID': ColumnMapping(**{
                        'as': 'ex:projectId',
                        'datatype': 'xsd:string'
                    }),
                    'ProjectName': ColumnMapping(**{
                        'as': 'dcterms:title',
                        'datatype': 'xsd:string'
                    }),
                    'Description': ColumnMapping(**{
                        'as': 'dcterms:description',
                        'datatype': 'xsd:string',
                        'transform': 'trim'
                    }),

                    # Timeline
                    'StartDate': ColumnMapping(**{
                        'as': 'ex:startDate',
                        'datatype': 'xsd:date'
                    }),
                    'EndDate': ColumnMapping(**{
                        'as': 'ex:endDate',
                        'datatype': 'xsd:date'
                    }),

                    # Financial
                    'Budget': ColumnMapping(**{
                        'as': 'ex:budget',
                        'datatype': 'xsd:decimal'
                    }),

                    # Status and management
                    'Status': ColumnMapping(**{
                        'as': 'ex:status',
                        'datatype': 'xsd:string'
                    }),
                    'Priority': ColumnMapping(**{
                        'as': 'ex:priority',
                        'datatype': 'xsd:string'
                    }),
                    'DepartmentOwner': ColumnMapping(**{
                        'as': 'ex:owningDepartment',
                        'datatype': 'xsd:string'
                    }),

                    # Effort tracking
                    'EstimatedHours': ColumnMapping(**{
                        'as': 'ex:estimatedHours',
                        'datatype': 'xsd:integer'
                    }),
                    'ActualHours': ColumnMapping(**{
                        'as': 'ex:actualHours',
                        'datatype': 'xsd:integer'
                    }),
                    'CompletionPercentage': ColumnMapping(**{
                        'as': 'ex:completionPercentage',
                        'datatype': 'xsd:integer'
                    }),

                    # Risk and quality
                    'RiskLevel': ColumnMapping(**{
                        'as': 'ex:riskLevel',
                        'datatype': 'xsd:string'
                    }),

                    # Notes
                    'Notes': ColumnMapping(**{
                        'as': 'rdfs:comment',
                        'datatype': 'xsd:string',
                        'transform': 'trim'
                    }),
                },
                objects={
                    'project_manager': LinkedObject(
                        predicate='ex:managedBy',
                        **{'class': 'ex:Employee'},
                        iri_template='{base_iri}employee/{ProjectManagerID}',
                        properties=[
                            ObjectPropertyMapping(
                                column='ProjectManagerID',
                                **{'as': 'ex:employeeId'},
                                datatype='xsd:string'
                            )
                        ]
                    ),
                    'client': LinkedObject(
                        predicate='ex:clientProject',
                        **{'class': 'ex:Client'},
                        iri_template='{base_iri}client/{ClientID}',
                        properties=[
                            ObjectPropertyMapping(
                                column='ClientID',
                                **{'as': 'ex:clientId'},
                                datatype='xsd:string'
                            )
                        ]
                    )
                }
            )
        ],
        options=ProcessingOptions(
            chunk_size=50000,
            header=True,
            delimiter=',',
            on_error='report'
        )
    )
