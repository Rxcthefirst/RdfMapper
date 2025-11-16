# Mortgage SKOS Vocabulary

This folder contains a modular SKOS vocabulary for the Mortgage ontology. The goal is to provide human-friendly labels (prefLabel), synonyms (altLabel), and common database-style variants (hiddenLabel) for classes and properties in `../ontology/mortgage.ttl`.

Why? Better labels improve automatic matching and make the alignment report more explainable.

How to use in the app:
- In the UI Project Detail page:
  1. Upload your ontology file (mortgage.ttl)
  2. Upload your SKOS file (this `mortgage_skos.ttl`) using the "Upload SKOS" in the Knowledge Inputs panel
  3. (Optional) Upload a SHACL shapes file
  4. Generate mappings and then Convert with "Validate output" checked

Under the hood:
- The generator and converter add SKOS files into the mapping `imports`, so SKOS labels are loaded even when the vocabulary is modular.
- If `imports` are missing in older mapping configs, the converter repairs them.

You can add additional SKOS vocab files here and upload them too; the app supports multiple SKOS files per project.

