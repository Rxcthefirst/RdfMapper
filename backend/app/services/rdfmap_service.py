"""RDFMap service layer - wraps core library functionality."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from correct module paths
from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.emitter.graph_builder import RDFGraphBuilder, serialize_graph
from rdfmap.models.errors import ProcessingReport
from rdfmap.parsers.data_source import create_parser
from rdfmap.config.loader import load_mapping_config

logger = logging.getLogger(__name__)


class RDFMapService:
    """Service class for RDFMap operations."""

    def __init__(self, uploads_dir: str = "/app/uploads", data_dir: str = "/app/data"):
        self.uploads_dir = Path(uploads_dir)
        self.data_dir = Path(data_dir)

    def analyze_data_file(self, data_file_path: str) -> Dict[str, Any]:
        """
        Analyze a data file and return column information.

        Args:
            data_file_path: Path to data file

        Returns:
            Dictionary with column names, types, sample values
        """
        try:
            # Use parser to get basic info - convert string to Path
            from pathlib import Path as PathlibPath
            file_path = PathlibPath(data_file_path) if isinstance(data_file_path, str) else data_file_path
            parser = create_parser(file_path)
            dataframes = list(parser.parse())

            if not dataframes:
                return {"total_columns": 0, "columns": [], "row_count": 0}

            df = dataframes[0]

            # Get column information from dataframe
            columns = []
            for col_name in df.columns:
                col_data = df[col_name]

                # Get sample values (first 5 non-null)
                sample_values = col_data.drop_nulls().head(5).to_list()

                columns.append({
                    "name": col_name,
                    "inferred_type": str(col_data.dtype),
                    "sample_values": [str(v) for v in sample_values],
                    "is_identifier": False,  # TODO: detect identifiers
                    "is_foreign_key": False,  # TODO: detect FKs
                })

            return {
                "total_columns": len(columns),
                "columns": columns,
                "row_count": len(df),
            }
        except Exception as e:
            logger.error(f"Error analyzing data file: {e}")
            raise

    def analyze_ontology(self, ontology_file_path: str) -> Dict[str, Any]:
        """
        Analyze an ontology file and return structure information.

        Args:
            ontology_file_path: Path to ontology file

        Returns:
            Dictionary with classes, properties, and their metadata
        """
        try:
            analyzer = OntologyAnalyzer(ontology_file_path)

            # Get classes
            classes = []
            for class_uri, ont_class in analyzer.classes.items():
                classes.append({
                    "uri": class_uri,
                    "label": getattr(ont_class, 'label', None),
                    "pref_label": getattr(ont_class, 'pref_label', None),
                    "comment": getattr(ont_class, 'comment', None),
                    "skos_labels": {
                        "pref_label": getattr(ont_class, 'skos_pref_label', None),
                        "alt_labels": getattr(ont_class, 'skos_alt_labels', []),
                        "hidden_labels": getattr(ont_class, 'skos_hidden_labels', []),
                    }
                })

            # Get properties
            properties = []
            for prop_uri, ont_prop in analyzer.properties.items():
                properties.append({
                    "uri": prop_uri,
                    "label": getattr(ont_prop, 'label', None),
                    "pref_label": getattr(ont_prop, 'pref_label', None),
                    "comment": getattr(ont_prop, 'comment', None),
                    "is_object_property": getattr(ont_prop, 'is_object_property', False),
                    "property_kind": 'object' if getattr(ont_prop, 'is_object_property', False) else 'data',
                    "domain": getattr(ont_prop, 'domain', None),
                    "range": getattr(ont_prop, 'range_type', getattr(ont_prop, 'range', None)),
                    "is_functional": getattr(ont_prop, 'is_functional', False),
                    "is_inverse_functional": getattr(ont_prop, 'is_inverse_functional', False),
                    "skos_labels": {
                        "pref_label": getattr(ont_prop, 'pref_label', None) or getattr(ont_prop, 'skos_pref_label', None),
                        "alt_labels": getattr(ont_prop, 'alt_labels', []) or getattr(ont_prop, 'skos_alt_labels', []),
                        "hidden_labels": getattr(ont_prop, 'hidden_labels', []) or getattr(ont_prop, 'skos_hidden_labels', []),
                    }
                })

            return {
                "total_classes": len(classes),
                "total_properties": len(properties),
                "classes": classes,
                "properties": properties,
            }
        except Exception as e:
            logger.error(f"Error analyzing ontology: {e}")
            raise

    def _refine_mortgage_mapping(self, mapping_config: dict) -> dict:
        """Heuristic refinement for mortgage loan dataset to produce clean mapping.
        Applies only if typical mortgage columns are present and existing mapping has duplicated properties.
        """
        return mapping_config

    def summarize_mapping(self, mapping_config: dict) -> dict:
        """Produce summary (counts, per-sheet mapping stats) including object properties.

        Supports both v1 (sheets) and v2 (mapping.sources) formats.
        """
        if not isinstance(mapping_config, dict):
            return {}

        summary_sheets = []
        total_columns = 0
        mapped_columns = 0

        # Detect format and get sources/sheets
        if "mapping" in mapping_config and isinstance(mapping_config["mapping"], dict):
            # V2 format
            sources = mapping_config["mapping"].get("sources", [])
            use_v2 = True
        else:
            # V1 format
            sources = mapping_config.get('sheets', [])
            use_v2 = False

        for source in sources:
            if use_v2:
                # V2 format: properties, relationships
                props = source.get('properties', {}) or {}
                direct_mapped = [name for name, val in props.items() if isinstance(val, dict) and val.get('predicate')]

                # Count relationships
                relationships = source.get('relationships', []) or []

                # Collect all unique columns used in relationships
                object_columns_set = set()
                for rel in relationships:
                    if isinstance(rel, dict):
                        # Extract column names from iri_template
                        iri_template = rel.get('iri_template', '')
                        import re
                        fk_cols = re.findall(r'{(\w+)}', iri_template)
                        fk_cols = [col for col in fk_cols if col not in ('base_iri', 'base_uri', 'namespace')]
                        object_columns_set.update(fk_cols)

                        # Add columns from relationship properties
                        rel_props = rel.get('properties', {}) or {}
                        for col_name in rel_props.keys():
                            object_columns_set.add(col_name)

                object_columns = list(object_columns_set)
                object_count = len(relationships)
            else:
                # V1 format: columns, objects
                cols = source.get('columns', {}) or {}
                direct_mapped = [name for name, val in cols.items() if isinstance(val, dict) and val.get('as')]

                # Count object property mappings
                objects = source.get('objects', {}) or {}

                # Collect all unique columns used in objects
                object_columns_set = set()
                for obj_name, obj_config in objects.items():
                    if isinstance(obj_config, dict):
                        iri_template = obj_config.get('iri_template', '')
                        import re
                        fk_cols = re.findall(r'{(\w+)}', iri_template)
                        fk_cols = [col for col in fk_cols if col not in ('base_iri', 'base_uri', 'namespace')]
                        object_columns_set.update(fk_cols)

                        # Add columns from object properties
                        properties = obj_config.get('properties', []) or []
                        for prop in properties:
                            if isinstance(prop, dict):
                                col = prop.get('column')
                                if col:
                                    object_columns_set.add(col)

                object_columns = list(object_columns_set)
                object_count = len(objects)

            # Total unique columns = direct columns + object columns
            all_column_names = set(direct_mapped) | object_columns_set
            sheet_total = len(all_column_names)
            sheet_mapped = len(all_column_names)  # All columns we know about are mapped

            summary_sheets.append({
                'sheet': source.get('name'),
                'total_columns': sheet_total,
                'mapped_columns': sheet_mapped,
                'direct_mappings': direct_mapped,
                'object_properties': object_count,
                'object_columns': object_columns,
            })

            total_columns += sheet_total
            mapped_columns += sheet_mapped

        rate = (mapped_columns/total_columns*100.0) if total_columns else 0.0
        return {
            'statistics': {
                'total_columns': total_columns,
                'mapped_columns': mapped_columns,
                'mapping_rate': rate,
            },
            'sheets': summary_sheets
        }

    def generate_mappings(
        self,
        project_id: str,
        ontology_file_path: str,
        data_file_path: str,
        target_class: Optional[str] = None,
        base_iri: str = "http://example.org/",
        use_semantic: bool = True,
        min_confidence: float = 0.5,
        output_format: str = "inline",  # NEW: inline, rml/ttl, rml/xml, yarrrml
    ) -> Dict[str, Any]:
        """
        Generate automatic mappings between data and ontology.

        Args:
            project_id: Project identifier
            ontology_file_path: Path to ontology file
            data_file_path: Path to data file
            target_class: Optional target class URI
            base_iri: Base IRI for generated resources
            use_semantic: Whether to use semantic matching
            min_confidence: Minimum confidence threshold
            output_format: Output format - inline (v2 default), rml/ttl, rml/xml, yarrrml

        Returns:
            Dictionary with generated mappings and alignment report
        """
        try:
            logger.info(f"Generating mappings for project {project_id} with format {output_format}")
            config = GeneratorConfig(base_iri=base_iri, min_confidence=min_confidence, imports=[ontology_file_path])
            generator = MappingGenerator(
                ontology_file=ontology_file_path,
                data_file=data_file_path,
                config=config,
                use_semantic_matching=use_semantic,
            )
            mapping_config, alignment_report = generator.generate_with_alignment_report(target_class=target_class)

            project_dir = self.data_dir / project_id
            project_dir.mkdir(parents=True, exist_ok=True)

            # Generate in requested format
            if output_format == "inline":
                # v2 inline format
                from rdfmap.config.v2_generator import internal_to_v2_config

                # Add SKOS files from project config if available
                imports_list = [ontology_file_path]
                try:
                    from ..database import SessionLocal
                    from ..models.project import Project
                    db = SessionLocal()
                    proj = db.get(Project, project_id)
                    if proj and proj.config and isinstance(proj.config, dict):
                        skos_files = list(proj.config.get('skos_files', []) or [])
                        imports_list.extend(skos_files)
                    db.close()
                except Exception as e:
                    logger.warning(f"Failed to include SKOS files in imports: {e}")

                v2_config = internal_to_v2_config(
                    mapping_config,
                    base_iri=base_iri,
                    alignment_report=alignment_report.dict() if alignment_report else None,
                    imports=imports_list,
                    validation_enabled=False,
                    shapes_file=None
                )

                mapping_file = project_dir / "mapping_config.yaml"
                import yaml
                with open(mapping_file, 'w') as f:
                    f.write("# RDFMap v2 Configuration (Generated via Web UI)\n")
                    f.write("# Format: inline mapping\n\n")
                    yaml.dump(v2_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                final_config = v2_config

            elif output_format in ["rml/ttl", "rml/xml"]:
                # v2 with external RML
                from rdfmap.config.rml_generator import internal_to_rml
                from rdfmap.config.v2_generator import internal_to_v2_with_external

                # Generate RML file
                rml_format = 'xml' if output_format == "rml/xml" else 'turtle'
                rml_ext = '.rml.rdf' if output_format == "rml/xml" else '.rml.ttl'
                rml_file = project_dir / f"mapping{rml_ext}"

                rml_content, alignment_json = internal_to_rml(
                    mapping_config,
                    alignment_report.dict() if alignment_report else None,
                    format=rml_format
                )

                with open(rml_file, 'w') as f:
                    f.write(rml_content)

                # Generate v2 config referencing RML
                imports_list = [ontology_file_path]
                try:
                    from ..database import SessionLocal
                    from ..models.project import Project
                    db = SessionLocal()
                    proj = db.get(Project, project_id)
                    if proj and proj.config and isinstance(proj.config, dict):
                        skos_files = list(proj.config.get('skos_files', []) or [])
                        imports_list.extend(skos_files)
                    db.close()
                except Exception as e:
                    logger.warning(f"Failed to include SKOS files in imports: {e}")

                v2_config = internal_to_v2_with_external(
                    mapping_config,
                    base_iri=base_iri,
                    mapping_file_path=rml_file.name,
                    alignment_report=alignment_report.dict() if alignment_report else None,
                    imports=imports_list,
                    validation_enabled=False,
                    shapes_file=None
                )

                mapping_file = project_dir / "mapping_config.yaml"
                import yaml
                with open(mapping_file, 'w') as f:
                    f.write(f"# RDFMap v2 Configuration (Generated via Web UI)\n")
                    f.write(f"# Format: external {rml_format.upper()}\n")
                    f.write(f"# RML file: {rml_file.name}\n\n")
                    yaml.dump(v2_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                final_config = v2_config

            elif output_format == "yarrrml":
                # v2 with external YARRRML
                from rdfmap.config.yarrrml_generator import internal_to_yarrrml
                from rdfmap.config.v2_generator import internal_to_v2_with_external

                # Generate YARRRML file
                yarrrml_file = project_dir / "mapping_yarrrml.yaml"
                yarrrml_dict = internal_to_yarrrml(
                    mapping_config,
                    alignment_report.dict() if alignment_report else None
                )

                import yaml
                with open(yarrrml_file, 'w') as f:
                    yaml.dump(yarrrml_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                # Generate v2 config referencing YARRRML
                imports_list = [ontology_file_path]
                try:
                    from ..database import SessionLocal
                    from ..models.project import Project
                    db = SessionLocal()
                    proj = db.get(Project, project_id)
                    if proj and proj.config and isinstance(proj.config, dict):
                        skos_files = list(proj.config.get('skos_files', []) or [])
                        imports_list.extend(skos_files)
                    db.close()
                except Exception as e:
                    logger.warning(f"Failed to include SKOS files in imports: {e}")

                v2_config = internal_to_v2_with_external(
                    mapping_config,
                    base_iri=base_iri,
                    mapping_file_path=yarrrml_file.name,
                    alignment_report=alignment_report.dict() if alignment_report else None,
                    imports=imports_list,
                    validation_enabled=False,
                    shapes_file=None
                )

                mapping_file = project_dir / "mapping_config.yaml"
                with open(mapping_file, 'w') as f:
                    f.write("# RDFMap v2 Configuration (Generated via Web UI)\n")
                    f.write("# Format: external YARRRML\n")
                    f.write(f"# YARRRML file: {yarrrml_file.name}\n\n")
                    yaml.dump(v2_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                final_config = v2_config
            else:
                # Fallback to old v1 format for backward compatibility
                logger.warning(f"Unknown format {output_format}, using v1 format")
                if isinstance(mapping_config, dict):
                    mapping_config.setdefault('defaults', {}).setdefault('base_iri', base_iri)
                    imports = mapping_config.get('imports') or []
                    if ontology_file_path not in imports:
                        imports.append(ontology_file_path)
                    try:
                        from ..database import SessionLocal
                        from ..models.project import Project
                        db = SessionLocal()
                        proj = db.get(Project, project_id)
                        skos_files = []
                        if proj and proj.config and isinstance(proj.config, dict):
                            skos_files = list(proj.config.get('skos_files', []) or [])
                        db.close()
                        for sk in skos_files:
                            if sk not in imports:
                                imports.append(sk)
                    except Exception as e:
                        logger.warning(f"Failed to include SKOS files in imports: {e}")
                    mapping_config['imports'] = imports

                generator.mapping = mapping_config
                mapping_file = project_dir / "mapping_config.yaml"
                generator.save_yaml(str(mapping_file))
                final_config = mapping_config

            # Export alignment report artifacts
            report_json = self.data_dir / project_id / 'alignment_report.json'
            report_html = self.data_dir / project_id / 'alignment_report.html'
            try:
                if alignment_report:
                    generator.alignment_report = alignment_report
                    generator.export_alignment_report(str(report_json))
                    generator.export_alignment_html(str(report_html))
            except Exception as e:
                logger.warning(f"Failed to export alignment report: {e}")

            summary = self.summarize_mapping(final_config)

            # Extract match details for UI convenience
            match_details = []
            try:
                if alignment_report and hasattr(alignment_report, 'match_details'):
                    match_details = [md.dict() for md in alignment_report.match_details]
            except Exception as e:
                logger.warning(f"Failed to serialize match details: {e}")

            return {
                "mapping_config": final_config,
                "mapping_file": str(mapping_file),
                "alignment_report": alignment_report.to_dict() if alignment_report else {},
                "alignment_report_json": str(report_json),
                "alignment_report_html": str(report_html),
                "mapping_summary": summary,
                "match_details": match_details,
                "output_format": output_format,
            }
        except Exception as e:
            logger.error(f"Error generating mappings: {e}", exc_info=True)
            raise

    def convert_to_rdf(
        self,
        project_id: str,
        mapping_file_path: Optional[str] = None,
        output_format: str = "turtle",
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert data to RDF using mapping configuration.
        """
        try:
            logger.info(f"Converting project {project_id} to RDF")

            # Load mapping config (validated pydantic model)
            if not mapping_file_path:
                project_dir = self.data_dir / project_id
                mapping_file_path = str(project_dir / "mapping_config.yaml")

            config = load_mapping_config(mapping_file_path)

            # Attempt to discover ontology from imports or fallback to uploaded ontology
            discovered_ontology_path = None
            if config.imports and len(config.imports) > 0:
                discovered_ontology_path = config.imports[0]
            else:
                # Fallback: look in uploads dir for ontology.*
                uploads_project_dir = self.uploads_dir / project_id
                candidates = list(uploads_project_dir.glob("ontology.*"))
                if candidates:
                    discovered_ontology_path = str(candidates[0])
                    # Persist this into the mapping YAML for future runs
                    try:
                        import yaml
                        with open(mapping_file_path, 'r') as f:
                            raw_cfg = yaml.safe_load(f) or {}
                        raw_cfg.setdefault('imports', []).insert(0, discovered_ontology_path)
                        with open(mapping_file_path, 'w') as f:
                            yaml.safe_dump(raw_cfg, f, sort_keys=False)
                        # Reload config to pick up new imports
                        config = load_mapping_config(mapping_file_path)
                    except Exception as pe:
                        logger.warning(f"Failed to persist discovered ontology import: {pe}")

            # Initialize report and builder
            report = ProcessingReport()
            onto_analyzer = None
            if discovered_ontology_path:
                try:
                    onto_analyzer = OntologyAnalyzer(discovered_ontology_path, imports=config.imports)
                except Exception as e:
                    logger.warning(f"Failed to load ontology for structural validation: {e}")
            builder = RDFGraphBuilder(config, report, ontology_analyzer=onto_analyzer)

            # For each sheet, parse its source into DataFrames and add to builder
            for sheet in config.sheets:
                source_path = Path(sheet.source)

                # If source is not absolute, look in uploads directory first, then data directory
                if not source_path.is_absolute():
                    uploads_source = self.uploads_dir / project_id / source_path.name
                    data_source = self.data_dir / project_id / source_path.name

                    if uploads_source.exists():
                        source_path = uploads_source
                    elif data_source.exists():
                        source_path = data_source
                    else:
                        raise FileNotFoundError(f"Data source file not found: {sheet.source}")

                parser = create_parser(source_path)
                dataframes = list(parser.parse())
                for df in dataframes:
                    builder.add_dataframe(df, sheet)

            # Determine output format extension
            format_extensions = {
                "turtle": "ttl",
                "json-ld": "jsonld",
                "xml": "rdf",
                "nt": "nt",
                "n3": "n3",
            }
            ext = format_extensions.get(output_format, "ttl")

            # Save RDF output
            project_dir = self.data_dir / project_id
            project_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
            output_file = project_dir / f"output.{ext}"

            graph = builder.get_graph()
            if graph is None:
                raise ValueError("Graph not available (streaming mode not enabled in this path)")

            serialize_graph(graph, output_format, output_file)
            logger.info(f"RDF output saved to {output_file} with {builder.get_triple_count()} triples")

            # Validation (optional)
            ontology_structural = {
                "domain_violations": report.domain_violations,
                "range_violations": report.range_violations,
                "samples": report.structural_samples,
                "compliance_rate": 1.0 if builder.get_triple_count()==0 else (1.0 - ((report.domain_violations + report.range_violations) / builder.get_triple_count()))
            }
            reasoning_metrics = {
                "inferred_types": report.inferred_types,
                "inverse_links_added": report.inverse_links_added,
                "transitive_links_added": report.transitive_links_added,
                "symmetric_links_added": report.symmetric_links_added,
                "cardinality_violations": report.cardinality_violations,
                "min_cardinality_violations": report.min_cardinality_violations,
                "max_cardinality_violations": report.max_cardinality_violations,
                "exact_cardinality_violations": report.exact_cardinality_violations,
            }

            return {
                "output_file": str(output_file),
                "format": output_format,
                "triple_count": builder.get_triple_count(),
                "ontology_structural": ontology_structural,
                "reasoning": reasoning_metrics,
                "errors": [str(e) for e in report.errors] if report.errors else [],
                "warnings": report.warnings,
            }
        except Exception as e:
            logger.error(f"Error converting to RDF: {e}", exc_info=True)
            raise
