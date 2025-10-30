# Development Guide

## Getting Started with Development

### Initial Setup

```bash
# Clone/navigate to repository
cd SemanticModelDataMapper

# Run installation script
./install.sh

# Activate virtual environment
source venv/bin/activate
```

### Project Architecture

#### Module Organization

```
src/rdfmap/
├── models/          # Data models (Pydantic schemas)
├── parsers/         # CSV/XLSX data source parsing
├── transforms/      # Data transformation functions
├── iri/            # IRI generation and templating
├── emitter/        # RDF graph construction (rdflib)
├── validator/      # SHACL validation (pyshacl)
├── config/         # Configuration loading
└── cli/            # Command-line interface (Typer)
```

#### Key Design Patterns

1. **Configuration-Driven**: All behavior controlled by YAML/JSON mapping files
2. **Pydantic Models**: Type-safe configuration and error handling
3. **Registry Pattern**: Extensible transform functions
4. **Builder Pattern**: Incremental RDF graph construction
5. **Streaming**: Large file support with chunking

### Development Workflow

#### 1. Adding a New Transform

**File**: `src/rdfmap/transforms/functions.py`

```python
@register_transform("my_transform")
def my_transform(value: Any) -> Any:
    """Description of transform."""
    # Implementation
    return transformed_value
```

**Test**: `tests/test_transforms.py`

```python
def test_my_transform():
    from rdfmap.transforms.functions import my_transform
    result = my_transform("input")
    assert result == "expected_output"
```

**Usage**: In mapping config:

```yaml
columns:
  MyColumn:
    as: ex:myProperty
    transform: my_transform
```

#### 2. Adding a New Output Format

**File**: `src/rdfmap/emitter/graph_builder.py`

Update `serialize_graph()` function:

```python
def serialize_graph(graph: Graph, format: str, output_path: Optional[Path] = None) -> str:
    format_map = {
        "turtle": "turtle",
        "myformat": "myformat",  # Add new format
        # ...
    }
    # ...
```

#### 3. Extending the Mapping Schema

**File**: `src/rdfmap/models/mapping.py`

Add new fields to Pydantic models:

```python
class ColumnMapping(BaseModel):
    # Existing fields...
    my_new_option: Optional[str] = Field(None, description="New option")
```

**Update**: Graph builder to handle new option:

```python
# src/rdfmap/emitter/graph_builder.py
if column_mapping.my_new_option:
    # Handle new option
    pass
```

### Testing

#### Run All Tests

```bash
pytest
```

#### Run Specific Test File

```bash
pytest tests/test_transforms.py -v
```

#### Run with Coverage

```bash
pytest --cov=rdfmap --cov-report=html
open htmlcov/index.html
```

#### Test Development Tips

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test complete workflows (see `test_mortgage_example.py`)
3. **Use Fixtures**: Share test data across tests
4. **Parametrize**: Test multiple inputs with `@pytest.mark.parametrize`

### Code Quality

#### Type Checking

```bash
mypy src/rdfmap
```

#### Code Formatting

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

#### Linting

```bash
# Run ruff
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Debugging

#### Enable Verbose Logging

```bash
rdfmap convert \
  --mapping config.yaml \
  --verbose \
  --log debug.log
```

#### Python Debugger

Add breakpoint in code:

```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with launch configuration.

#### Test Debugging

```bash
# Run single test with print output
pytest tests/test_transforms.py::TestToDecimal::test_decimal_from_string -s
```

### Common Development Tasks

#### Creating a New Example

1. Create directory: `examples/my_example/`
2. Add subdirectories: `ontology/`, `data/`, `config/`, `shapes/`
3. Create ontology in Turtle format
4. Prepare sample data (CSV/XLSX)
5. Write mapping configuration
6. Define SHACL shapes
7. Add README.md
8. Add integration test

#### Updating Documentation

- **README.md**: Main documentation
- **QUICKSTART.md**: Getting started guide
- **Example READMEs**: Example-specific docs
- **Docstrings**: Keep in sync with code

#### Release Checklist

1. Update version in `setup.py` and `pyproject.toml`
2. Run full test suite: `pytest`
3. Check type hints: `mypy src/rdfmap`
4. Format code: `black src/ tests/`
5. Update CHANGELOG.md
6. Tag release: `git tag v0.1.0`
7. Build package: `python -m build`

### Troubleshooting Development Issues

#### Import Errors

```bash
# Reinstall package in development mode
pip install -e .
```

#### Test Failures After Changes

```bash
# Clear pytest cache
pytest --cache-clear
```

#### Dependency Issues

```bash
# Update dependencies
pip install --upgrade -r requirements.txt
```

### Performance Optimization

#### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

#### Memory Profiling

```bash
pip install memory_profiler

# Add @profile decorator to function
python -m memory_profiler script.py
```

### Contributing Guidelines

1. **Branch Naming**: `feature/description` or `fix/description`
2. **Commit Messages**: Clear, descriptive messages
3. **Pull Requests**: Include tests and documentation
4. **Code Review**: Address all feedback
5. **CI/CD**: Ensure all checks pass

### Resources

- **rdflib Documentation**: https://rdflib.readthedocs.io/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **SHACL Specification**: https://www.w3.org/TR/shacl/
- **OWL 2 Primer**: https://www.w3.org/TR/owl2-primer/
- **Turtle Specification**: https://www.w3.org/TR/turtle/

### Getting Help

- Check existing tests for usage examples
- Review similar implementations in codebase
- Consult documentation links above
- Open GitHub issue for bugs or feature requests
