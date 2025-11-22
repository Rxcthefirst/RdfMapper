# 📋 CLI Workflow for Mapping Generation (RML/YARRRML)

**Current Status**: November 22, 2025  
**Document Purpose**: Clarify mapping generation workflow and identify gaps

---

## 🎯 Current CLI Workflow

### Step 1: Generate Mapping Configuration with AI

```bash
# Interactive wizard (AI-powered matching)
rdfmap init --output my_mapping.yaml

# With template
rdfmap init --template financial-loans --output loans_mapping.yaml
```

**What happens**:
1. User provides data file path (CSV, Excel, JSON, XML)
2. User provides ontology file path (TTL, RDF/XML, etc.)
3. User specifies target class
4. **AI generates mappings** (95% auto-mapping)
5. Saves internal YAML format to `my_mapping.yaml`

**Output Format**: Internal YAML format (not YARRRML, not RML)

**Location**: `src/rdfmap/cli/main.py` → `init()` command

---

### Step 2: Convert Data to RDF

```bash
# Use the generated mapping to convert data
rdfmap convert --mapping my_mapping.yaml --output output.ttl

# With validation
rdfmap convert --mapping my_mapping.yaml --validate --output output.ttl

# Supports RML input
rdfmap convert --mapping existing.rml.ttl --output output.ttl
```

**What happens**:
1. Loads mapping config (internal YAML, YARRRML, or RML)
2. Parses data file
3. Applies mappings
4. Generates RDF triples
5. Saves to output file

**Input Formats Supported**:
- ✅ Internal YAML format
- ✅ YARRRML format (.yarrrml.yaml)
- ✅ RML format (.rml.ttl) - **NEW!**

**Output**: RDF data (Turtle, N-Triples, JSON-LD, etc.)

**Location**: `src/rdfmap/cli/main.py` → `convert()` command

---

## ❌ What's Missing: Export Mappings

### Current Gap

**Problem**: Users can generate mappings with `init`, but can only save in internal YAML format.

**What users want**:
1. Generate mappings with AI (`rdfmap init`)
2. **Export to YARRRML or RML** for sharing/interoperability
3. Use exported mappings with other tools

**Currently NOT possible**:
```bash
# This command doesn't exist yet:
rdfmap export --format rml my_mapping.yaml -o output.rml.ttl  # ❌
rdfmap export --format yarrrml my_mapping.yaml -o output.yarrrml.yaml  # ❌
```

---

## ✅ Proposed Solution: Add `export` Command

### New CLI Command

```bash
# Export to RML
rdfmap export --format rml --config my_mapping.yaml -o mapping.rml.ttl

# Export to YARRRML  
rdfmap export --format yarrrml --config my_mapping.yaml -o mapping.yarrrml.yaml

# Export with alignment report
rdfmap export --format rml --config my_mapping.yaml \
    --alignment-report alignment.json \
    -o mapping.rml.ttl
```

### Implementation Location

**File**: `src/rdfmap/cli/main.py`

**New function**:
```python
@app.command()
def export(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to internal mapping configuration file",
        exists=True,
    ),
    format: str = typer.Option(
        "rml",
        "--format",
        "-f",
        help="Output format: rml, yarrrml",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path",
    ),
    alignment_report: Optional[Path] = typer.Option(
        None,
        "--alignment-report",
        help="Path to save alignment report (JSON)",
    ),
):
    """
    Export mapping configuration to standard formats.
    
    Converts internal YAML mapping to:
    - RML (W3C standard, for RMLMapper, Morph-KGC)
    - YARRRML (human-friendly, for research)
    
    AI metadata (x-alignment) saved separately for interoperability.
    """
    # Implementation here
```

---

## 🔄 Complete Workflow (With Export)

### Scenario 1: Generate and Export to RML

```bash
# Step 1: Generate mappings with AI
rdfmap init --output my_mapping.yaml

# Step 2: Export to RML for interoperability
rdfmap export --format rml --config my_mapping.yaml -o mapping.rml.ttl

# Step 3: Use with any RML tool
rmlmapper -m mapping.rml.ttl -o output.ttl
```

### Scenario 2: Generate and Export to YARRRML

```bash
# Step 1: Generate mappings with AI
rdfmap init --output my_mapping.yaml

# Step 2: Export to YARRRML for human editing
rdfmap export --format yarrrml --config my_mapping.yaml -o mapping.yarrrml.yaml

# Step 3: Edit YARRRML (human-friendly)
vim mapping.yarrrml.yaml

# Step 4: Convert data with edited mapping
rdfmap convert --mapping mapping.yarrrml.yaml --output output.ttl
```

### Scenario 3: Import RML, Enhance with AI, Export

```bash
# Step 1: Convert existing RML to internal format
rdfmap convert --mapping existing.rml.ttl --dry-run  # Just validates

# Step 2: (Future) Re-run AI matching on existing mapping
rdfmap enhance --mapping existing.rml.ttl --output enhanced.yaml

# Step 3: Export enhanced mapping
rdfmap export --format rml --config enhanced.yaml -o enhanced.rml.ttl
```

---

## 📊 Current vs Proposed Workflow

### Current Workflow

```
1. rdfmap init → my_mapping.yaml (internal format)
2. rdfmap convert --mapping my_mapping.yaml → output.ttl (RDF data)
```

**Limitation**: Can't export mappings to standard formats

### Proposed Workflow

```
1. rdfmap init → my_mapping.yaml (internal format)
2. rdfmap export --format rml → mapping.rml.ttl (standard format) ✨ NEW
3. Use mapping.rml.ttl with any tool (RMLMapper, Morph-KGC, etc.)
```

**Benefit**: Full interoperability

---

## 🎯 Implementation Plan

### Phase 1: Add `export` Command ✅ (Code Ready)

**Status**: Backend code exists
- ✅ `rml_generator.py` - Generate RML
- ✅ `yarrrml_generator.py` - Generate YARRRML
- ❌ CLI command - **NEEDS TO BE ADDED**

**Task**: Add CLI wrapper around existing generators

**Time**: 1-2 hours

### Phase 2: Integrate with `init` Wizard

**Option 1**: Ask user for export format during init

```python
# In wizard.py
export_format = Prompt.ask(
    "Export format",
    choices=["internal", "rml", "yarrrml"],
    default="internal"
)

if export_format != "internal":
    # Export after saving
    export_mapping(config, format=export_format)
```

**Option 2**: Keep init simple, user exports separately

```bash
rdfmap init --output my_mapping.yaml
rdfmap export --format rml --config my_mapping.yaml -o mapping.rml.ttl
```

**Recommendation**: Option 2 (cleaner separation of concerns)

### Phase 3: Add `--export-format` Flag to `init`

**Future enhancement**: One-command export

```bash
rdfmap init --output mapping --export-format rml

# Generates:
# - mapping.yaml (internal)
# - mapping.rml.ttl (exported)
# - mapping.alignment.json (AI metadata)
```

---

## 📝 CLI Help Text

### `rdfmap init --help`

```
Usage: rdfmap init [OPTIONS]

  🎯 Interactive configuration wizard with automatic mapping generation.

  Creates a complete, production-ready mapping configuration by:
    1. Collecting data source and ontology information
    2. Automatically matching columns to ontology properties (AI-powered)
    3. Detecting foreign key relationships
    4. Generating a well-commented configuration file

  The wizard uses AI-powered semantic matching to achieve 95%+ success rates.

  To export to standard formats (RML, YARRRML), use:
    rdfmap export --format rml --config mapping.yaml -o output.rml.ttl

Options:
  -o, --output PATH     Path to save configuration (default: mapping_config.yaml)
  -t, --template TEXT   Use pre-built template
  --help                Show this message and exit
```

### `rdfmap export --help` (Proposed)

```
Usage: rdfmap export [OPTIONS]

  📤 Export mapping configuration to standard formats.

  Converts internal YAML mapping to:
    - RML (W3C standard, for RMLMapper, Morph-KGC, SDM-RDFizer)
    - YARRRML (human-friendly, for editing and research)

  AI metadata (x-alignment) is saved separately as JSON for transparency
  and standards compliance.

Options:
  -c, --config PATH              Path to internal mapping config [required]
  -f, --format [rml|yarrrml]    Output format [default: rml]
  -o, --output PATH              Output file path [required]
  --alignment-report PATH        Path to save alignment report (JSON)
  --help                         Show this message and exit

Examples:
  # Export to RML
  rdfmap export -f rml -c my_mapping.yaml -o mapping.rml.ttl

  # Export to YARRRML with alignment report
  rdfmap export -f yarrrml -c my_mapping.yaml -o mapping.yarrrml.yaml \
      --alignment-report alignment.json

  # Use exported RML with other tools
  rmlmapper -m mapping.rml.ttl -o output.ttl
```

### `rdfmap convert --help` (Updated)

```
Usage: rdfmap convert [OPTIONS]

  🔄 Convert data to RDF using mapping configuration.

  Supports multiple mapping formats:
    - Internal YAML format (from 'rdfmap init')
    - YARRRML format (.yarrrml.yaml)
    - RML format (.rml.ttl, .rdf, .nt)

  This command converts DATA (CSV, Excel, JSON) to RDF triples.
  To export MAPPINGS, use 'rdfmap export'.

Options:
  -m, --mapping PATH      Path to mapping configuration [required]
  -o, --output PATH       Output RDF file path
  -f, --format TEXT       Output RDF format [default: ttl]
  --validate              Run SHACL validation
  --help                  Show this message and exit
```

---

## 🎓 User Mental Model

### Clear Distinction

**`rdfmap init`**: Generate mapping configuration (with AI)
**`rdfmap export`**: Export mapping to standard format  
**`rdfmap convert`**: Convert data to RDF using mapping

### Analogy

```
init    = "Write the recipe" (mapping configuration)
export  = "Share the recipe" (export to standard format)
convert = "Cook the meal" (apply mapping to data)
```

---

## ✅ Current Implementation Status

### What Works Now

1. ✅ **Generate mappings**: `rdfmap init`
2. ✅ **Import RML**: `rdfmap convert --mapping file.rml.ttl`
3. ✅ **Import YARRRML**: `rdfmap convert --mapping file.yarrrml.yaml`
4. ✅ **Backend code exists**: `rml_generator.py`, `yarrrml_generator.py`

### What Needs to Be Added

1. ❌ **CLI export command**: `rdfmap export`
2. ❌ **Help text updates**: Clarify init vs export vs convert
3. ❌ **Documentation**: User guide for export workflow
4. ❌ **Examples**: Demo scripts showing export

### Implementation Checklist

- [ ] Add `export` command to `src/rdfmap/cli/main.py`
- [ ] Import `rml_generator.py` and `yarrrml_generator.py`
- [ ] Add format validation (rml, yarrrml)
- [ ] Handle alignment report export
- [ ] Update help text for all commands
- [ ] Add examples to documentation
- [ ] Test end-to-end workflow
- [ ] Update README with export examples

---

## 🚀 Immediate Next Step

**Add the `export` command to CLI**:

```python
# In src/rdfmap/cli/main.py

@app.command()
def export(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to internal mapping configuration file",
        exists=True,
    ),
    format: str = typer.Option(
        "rml",
        "--format",
        "-f",
        help="Output format: rml, yarrrml",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path",
    ),
    alignment_report: Optional[Path] = typer.Option(
        None,
        "--alignment-report",
        help="Path to save alignment report (JSON)",
    ),
):
    """
    📤 Export mapping configuration to standard formats.
    """
    try:
        # Load internal config
        from ..config.loader import load_mapping_config
        mapping_config = load_mapping_config(config)
        
        # Load alignment report if it exists
        alignment = None
        alignment_path = config.parent / f"{config.stem}_alignment.json"
        if alignment_path.exists():
            import json
            with open(alignment_path) as f:
                alignment = json.load(f)
        
        if format.lower() == "rml":
            from ..config.rml_generator import internal_to_rml
            rml_content, alignment_json = internal_to_rml(
                mapping_config.dict(),
                alignment
            )
            
            # Save RML
            with open(output, 'w') as f:
                f.write(rml_content)
            
            console.print(f"[green]✓[/green] RML exported to [cyan]{output}[/cyan]")
            
            # Save alignment report if requested
            if alignment_report and alignment_json:
                with open(alignment_report, 'w') as f:
                    f.write(alignment_json)
                console.print(f"[green]✓[/green] Alignment report saved to [cyan]{alignment_report}[/cyan]")
                
        elif format.lower() == "yarrrml":
            from ..config.yarrrml_generator import internal_to_yarrrml
            yarrrml_dict = internal_to_yarrrml(
                mapping_config.dict(),
                alignment
            )
            
            # Save YARRRML
            import yaml
            with open(output, 'w') as f:
                yaml.dump(yarrrml_dict, f, default_flow_style=False, sort_keys=False)
            
            console.print(f"[green]✓[/green] YARRRML exported to [cyan]{output}[/cyan]")
            
        else:
            console.print(f"[red]Error: Unknown format '{format}'[/red]")
            console.print("Supported formats: rml, yarrrml")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error exporting mapping: {e}[/red]")
        raise typer.Exit(1)
```

**Time to implement**: 1-2 hours  
**Impact**: Full bidirectional interoperability ✅

---

## 📊 Summary

### Current State
- ✅ Can generate mappings (AI-powered)
- ✅ Can import RML/YARRRML
- ❌ **Cannot export to RML/YARRRML**

### After Adding `export`
- ✅ Complete workflow
- ✅ Full interoperability
- ✅ No vendor lock-in
- ✅ Standards compliance

### User Flow
```
rdfmap init           → Generate with AI
rdfmap export         → Share in standard format  ← ADD THIS
rdfmap convert        → Convert data to RDF
```

**Status**: Backend ready, CLI wrapper needed  
**ETA**: 1-2 hours to complete  
**Priority**: High (completes RML support story)

