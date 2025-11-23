"""Debug RML parser output."""

from pathlib import Path
from rdfmap.config.rml_parser import parse_rml
import tempfile
import json

# Create a simple RML mapping
rml_content = """
@prefix rr: <http://www.w3.org/ns/r2rml#>.
@prefix rml: <http://semweb.mmlab.be/ns/rml#>.
@prefix ql: <http://semweb.mmlab.be/ns/ql#>.
@prefix schema: <http://schema.org/>.
@prefix ex: <http://example.org/>.

<#PersonMapping>
    a rr:TriplesMap;
    
    rml:logicalSource [
        rml:source "data/people.csv";
        rml:referenceFormulation ql:CSV
    ];
    
    rr:subjectMap [
        rr:template "http://example.org/person/{id}";
        rr:class schema:Person
    ];
    
    rr:predicateObjectMap [
        rr:predicate schema:name;
        rr:objectMap [ rml:reference "name" ]
    ];
    
    rr:predicateObjectMap [
        rr:predicate schema:age;
        rr:objectMap [ 
            rml:reference "age";
            rr:datatype <http://www.w3.org/2001/XMLSchema#integer>
        ]
    ].
"""

# Write to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
    f.write(rml_content)
    temp_path = Path(f.name)

try:
    # Parse RML
    result = parse_rml(temp_path)

    # Pretty print result
    print("=" * 60)
    print("RML Parser Output:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print("=" * 60)

finally:
    # Cleanup
    temp_path.unlink()

