# 🎯 CLI Workflow - REVISED (More Intuitive)

**Date**: November 22, 2025  
**Insight**: `generate` should output standard formats directly!

---

## 💡 Key Insight

**You're absolutely right!** Why have two steps when `generate` can output RML/YARRRML directly?

### Current (Confusing) ❌
```bash
rdfmap generate → my_mapping.yaml (internal)
rdfmap export → mapping.rml.ttl (standard)
```
**Problem**: Two commands for one logical operation

### Better (Intuitive) ✅
```bash
rdfmap generate --format rml → mapping.rml.ttl (standard)
rdfmap generate --format yarrrml → mapping.yarrrml.yaml (standard)
```
**Benefit**: Direct, single command!

---

## 🚀 Proposed CLI Design (REVISED)

### `generate` Command (Enhanced)

```bash
# Generate RML directly
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format rml \
    --output mapping.rml.ttl

# Generate YARRRML directly
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format yarrrml \
    --output mapping.yarrrml.yaml

# Generate internal format (for backwards compatibility)
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format yaml \
    --output mapping.yaml
```

**Options**:
- `--format rml` → RML Turtle output
- `--format yarrrml` → YARRRML YAML output
- `--format yaml` → Internal YAML (backwards compatible)

---

## 📊 Updated Workflow

### Simple User Flow

```
┌──────────────────────────────────────┐
│  Step 1: Generate Mapping            │
│                                      │
│  rdfmap generate                     │
│    --format rml/yarrrml/yaml        │
│                                      │
│  Output: mapping file (any format)  │
└──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────┐
│  Step 2: Convert Data                │
│                                      │
│  rdfmap convert                      │
│    --mapping mapping.rml.ttl        │
│                                      │
│  Output: RDF triples                │
└──────────────────────────────────────┘
```

**No export command needed!** 🎉

---

## 🎓 User Mental Model (Simplified)

```
generate = "Create the recipe" (in your preferred format)
convert  = "Cook the meal" (apply recipe to data)
```

**That's it!** Two commands, not three.

---

## 💻 Implementation

### Update `generate` command

```python
@app.command()
def generate(
    ontology: Path,
    data: Path,
    output: Path,
    format: str = typer.Option(
        "rml",
        "--format",
        "-f",
        help="Output format: rml, yarrrml, yaml",
    ),
    alignment_report: Optional[Path] = typer.Option(
        None,
        "--alignment-report",
        help="Path to save AI alignment report (JSON)",
    ),
    # ... other existing options
):
    """
    Generate mapping configuration from ontology and data.
    
    Supports multiple output formats:
    - rml: W3C RML standard (Turtle)
    - yarrrml: YARRRML format (YAML)
    - yaml: Internal format (backwards compatible)
    """
    # Existing analysis code...
    generator = MappingGenerator(...)
    mapping_config, alignment = generator.generate()
    
    # NEW: Format-specific output
    if format.lower() == "rml":
        from ..config.rml_generator import internal_to_rml
        rml_content, alignment_json = internal_to_rml(
            mapping_config.dict(),
            alignment.dict() if alignment else None
        )
        with open(output, 'w') as f:
            f.write(rml_content)
        console.print(f"[green]✓[/green] RML mapping saved to {output}")
        
    elif format.lower() == "yarrrml":
        from ..config.yarrrml_generator import internal_to_yarrrml
        yarrrml = internal_to_yarrrml(
            mapping_config.dict(),
            alignment.dict() if alignment else None
        )
        with open(output, 'w') as f:
            yaml.dump(yarrrml, f, default_flow_style=False)
        console.print(f"[green]✓[/green] YARRRML mapping saved to {output}")
        
    else:  # yaml (internal format)
        # Existing YAML save code
        with open(output, 'w') as f:
            yaml.dump(mapping_config.dict(), f)
        console.print(f"[green]✓[/green] Internal mapping saved to {output}")
    
    # Save alignment report if requested
    if alignment_report and alignment:
        with open(alignment_report, 'w') as f:
            json.dump(alignment.dict(), f, indent=2)
        console.print(f"[green]✓[/green] Alignment report saved to {alignment_report}")
```

---

## 🎯 Complete Workflow Examples

### Example 1: Generate RML, Use with RMLMapper

```bash
# Generate RML mapping
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format rml \
    --output mapping.rml.ttl

# Use with RMLMapper
rmlmapper -m mapping.rml.ttl -o output.ttl
```

### Example 2: Generate YARRRML, Edit, Convert

```bash
# Generate YARRRML (human-friendly)
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format yarrrml \
    --output mapping.yarrrml.yaml

# Edit manually (YAML is easy to edit)
vim mapping.yarrrml.yaml

# Convert data with edited mapping
rdfmap convert \
    --mapping mapping.yarrrml.yaml \
    --output output.ttl
```

### Example 3: Internal Format (Backwards Compatible)

```bash
# Generate internal format
rdfmap generate \
    --ontology ontology.ttl \
    --data data.csv \
    --format yaml \
    --output mapping.yaml

# Convert with internal format
rdfmap convert \
    --mapping mapping.yaml \
    --output output.ttl
```

---

## 📝 Updated Help Text

### `generate --help`

```
Usage: rdfmap generate [OPTIONS]

  🤖 Generate mapping configuration with AI-powered semantic matching.

  Analyzes your ontology and data to automatically create mappings with
  95% accuracy. Supports multiple output formats for maximum flexibility.

Options:
  --ontology PATH                Ontology file (TTL, RDF/XML, etc.) [required]
  --data PATH                    Data file (CSV, Excel, JSON, XML) [required]
  -o, --output PATH              Output mapping file [required]
  -f, --format [rml|yarrrml|yaml]  
                                 Output format [default: rml]
                                 - rml: W3C standard (use with any RML tool)
                                 - yarrrml: Human-friendly YAML
                                 - yaml: Internal format
  --alignment-report PATH        Save AI metadata separately (JSON)
  --class TEXT                   Target class (auto-detected if omitted)
  --help                         Show this message and exit

Examples:
  # Generate RML for interoperability
  rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.ttl

  # Generate YARRRML for manual editing
  rdfmap generate --ontology ont.ttl --data data.csv -f yarrrml -o map.yaml

  # Save AI insights separately
  rdfmap generate --ontology ont.ttl --data data.csv -f rml \
      -o map.rml.ttl --alignment-report alignment.json
```

### `init --help` (Updated)

```
Usage: rdfmap init [OPTIONS]

  🎯 Interactive wizard for creating mapping configurations.

  Guides you through the process with smart questions, then generates
  the mapping using AI. You can choose the output format.

Options:
  -o, --output PATH              Output mapping file [required]
  -f, --format [rml|yarrrml|yaml]  
                                 Output format [default: rml]
  -t, --template TEXT            Use pre-built template
  --help                         Show this message and exit

Note: 
  This wizard calls 'generate' internally with your answers.
  For direct, non-interactive generation, use 'rdfmap generate'.
```

---

## ✅ Benefits of This Approach

### 1. **Simpler Mental Model**
- Before: generate → export → convert (3 steps)
- After: generate → convert (2 steps)

### 2. **More Intuitive**
- Users specify desired format when generating
- No intermediate conversion step needed

### 3. **Backwards Compatible**
- `--format yaml` maintains existing behavior
- No breaking changes for existing users

### 4. **Standards-First**
- RML is the default format
- Encourages interoperability from the start

### 5. **Flexible**
- Users can still generate internal format if needed
- All formats supported in one command

---

## 🔄 Migration Path

### For Existing Users

**Old way** (still works):
```bash
rdfmap generate --ontology ont.ttl --data data.csv -o mapping.yaml
# Implicitly uses --format yaml
```

**New way** (recommended):
```bash
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o mapping.rml.ttl
```

**Migration is easy**: Just add `--format` flag!

---

## 🎯 Decision: Remove `export` Command

**Why we don't need it**:
1. `generate` outputs desired format directly
2. No intermediate conversion needed
3. Simpler for users to understand
4. Fewer commands to maintain

**What if users want to convert between formats?**

Option 1: **Don't support it** (users re-generate)
```bash
# If you have YARRRML and want RML, just re-generate
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.ttl
```

Option 2: **Add `convert-format` command** (if really needed)
```bash
# Convert between mapping formats (not data!)
rdfmap convert-format --input mapping.yaml --format rml -o mapping.rml.ttl
```

**Recommendation**: Option 1 (keep it simple)

---

## 📊 Comparison

### Old Design (Confusing)
```bash
Commands: init, generate, export, convert
Steps: generate → export → convert
Concepts: 4 commands, internal format as intermediate
```

### New Design (Intuitive) ✅
```bash
Commands: init, generate, convert
Steps: generate → convert
Concepts: 3 commands, direct format output
```

**Winner**: New design (simpler, more intuitive)

---

## ✅ Implementation Checklist

- [ ] Add `--format` option to `generate` command
- [ ] Update `generate` to call RML/YARRRML generators based on format
- [ ] Make RML the default format (encourage standards)
- [ ] Update `init` wizard to ask for format preference
- [ ] Update all help text
- [ ] Update README examples
- [ ] Remove references to `export` command from docs
- [ ] Test all format outputs
- [ ] Update user guide

**Time**: 2-3 hours (simpler than adding export!)

---

## 🎉 Summary

**Your insight was correct!** 

**Before** (what I proposed):
```
generate (internal) → export (standard) → convert (data)
```
**Problem**: Unnecessary intermediate step

**After** (your suggestion):
```
generate (any format) → convert (data)
```
**Benefit**: Direct, intuitive, simpler!

**Decision**: 
- ✅ Add `--format` to `generate`
- ✅ Make RML default
- ❌ Don't add `export` command (not needed!)

**This is a much better design!** 🚀

---

**Implementation**: Let's update `generate` to support `--format` option directly!

