// Shared ontology graph element builder for Cytoscape.
// Ensures consistent label fallback and optional stub node creation.

export interface OntClass {
  uri: string;
  label?: string | null;
  pref_label?: string | null;
  comment?: string | null;
}

export interface OntProperty {
  uri: string;
  label?: string | null;
  pref_label?: string | null;
  comment?: string | null;
  domain?: string | null;
  range?: string | null;
  is_object_property?: boolean;
}

export interface BuildOptions {
  maxClasses?: number;
  maxProperties?: number;
  includeStubs?: boolean;
  allowDataProperties?: boolean;
  debug?: boolean; // console debug
  mappedClassUris?: Set<string>; // enrichment: mapped coverage
  mappedPropertyUris?: Set<string>;
  origin?: 'ontology' | 'unified';
}

function fallbackLabel(primary?: string | null, secondary?: string | null, tertiary?: string | null, uri?: string): string {
  const raw = primary || secondary || tertiary || (uri ? uri.split('#').pop() || uri.split('/').pop() : '') || '';
  return raw.replace(/_/g, ' ').trim();
}

export function buildOntologyElements(classes: OntClass[], properties: OntProperty[], opts: BuildOptions = {}) {
  const { maxClasses = 200, maxProperties = 400, includeStubs = true, allowDataProperties = false, debug = false, mappedClassUris, mappedPropertyUris } = opts;
  const classSubset = classes.slice(0, maxClasses);
  const elements: any[] = [];
  const classSet = new Set<string>();

  // Build class nodes
  for (const cls of classSubset) {
    const lbl = fallbackLabel(cls.pref_label, cls.label, cls.comment, cls.uri);
    const id = String(cls.uri);
    const covered = mappedClassUris?.has(id) || false;
    elements.push({ data: { id, label: lbl || id, type: 'class', stub: false, coverage: covered ? 'mapped' : 'unmapped' } });
    classSet.add(id);
  }

  let propCount = 0;
  for (const p of properties) {
    if (propCount >= maxProperties) break;
    let domainRaw = p.domain as any;
    let rangeRaw = p.range as any;
    const domain = domainRaw ? String(domainRaw) : undefined;
    const range = rangeRaw ? String(rangeRaw) : undefined;

    if (!domain || !range) continue;

    const isDatatypeRange = /xsd\b|XMLSchema/.test(range);
    if (isDatatypeRange && !allowDataProperties) continue;

    if (includeStubs) {
      if (domain && !classSet.has(domain) && !isDatatypeRange) {
        const stubLabel = fallbackLabel(undefined, undefined, undefined, domain);
        elements.push({ data: { id: domain, label: stubLabel || domain, type: 'class', stub: true } });
        classSet.add(domain);
      }
      if (range && !classSet.has(range) && !isDatatypeRange) {
        const stubLabel = fallbackLabel(undefined, undefined, undefined, range);
        elements.push({ data: { id: range, label: stubLabel || range, type: 'class', stub: true } });
        classSet.add(range);
      }
    }

    const edgeLabel = fallbackLabel(p.pref_label, p.label, p.comment, p.uri) || String(p.uri);
    if (!isDatatypeRange) {
      if (domain && range && domain !== range) {
        const mappedEdge = mappedPropertyUris?.has(String(p.uri)) || false;
        elements.push({ data: { id: `${p.uri}-edge`, source: domain, target: range, label: edgeLabel, type: 'property', coverage: mappedEdge ? 'mapped' : 'unmapped' } });
        propCount++;
      } else if (debug) {
        console.warn('[ontologyGraphUtils] Skipping edge with invalid domain/range', { domain, range, uri: p.uri });
      }
    }
  }
  return elements;
}
