### Scripts to run various utilities and demos for the project

# Workflow script to generate alignment report

```bash
python rdfmap generate \
    --ontology examples/ontology/mortgage_ontology.ttl \
    --data examples/data/loans.csv \
    --output generated_mapping.yaml \
    --report alignment_report.json \
    --verbose
```

