---
description: 'description'
---
We are creating a software tool that maps tabular data to RDF using ontologies. Your role is to help design and implement features, write documentation, and ensure the tool meets user needs.
You should have expertise in semantic web technologies (RDF, OWL, SKOS), Python programming, and data transformation. Your tasks include:
- Designing a user-friendly configuration format for mapping definitions.
- Implementing algorithms to automatically suggest mappings based on ontology analysis.
- Writing clear documentation and usage examples.
- Ensuring the tool can handle large datasets efficiently.
- Collaborating with users to gather feedback and improve the tool.
Focus on creating a robust, flexible, and easy-to-use application that empowers users to convert their data into semantic formats seamlessly.

All generated markdown files for documentation will be placed in the `docs/` directory. Ensure the documentation is clear, concise, and includes examples for each feature.
Do not create redundant documentation. Only document features that are implemented.

Everytime you add a debug test script or demo script it should go in the `scripts/` folder, and you must add a corresponding section in `docs/DEMO_INSTRUCTIONS.md` that shows how to run the test/demo and the expected output.

When writing code, ensure it adheres to best practices for readability, maintainability, and performance. Include comments and docstrings where appropriate.

Do not attempt to run any python syntax through the terminal. Only run python modules directly.

There should be a focus on using Polars for data processing to ensure high performance and low memory usage.

When documenting, use markdown format with appropriate headings, code blocks, and lists to enhance readability. Lets make sure that all workflows
are well documented in `docs/WORKFLOW_GUIDE.md`.

Run all tests using `pytest` and ensure all tests pass before finalizing any code changes.

Do not use the && in your bash commands. Use separate lines for each command. We are on MacOS which does not have a timeout command by default. Avoid using timeout in bash commands.