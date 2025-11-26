import yaml from 'js-yaml'

interface ParsedMapping {
  format: 'rml' | 'yarrrml' | 'v2-inline'
  sources: ParsedSource[]
}

interface ParsedSource {
  name: string
  entityClass: string
  iriTemplate: string
  properties: Record<string, PropertyMapping>
  objectProperties: ObjectPropertyMapping[]
}

interface PropertyMapping {
  predicate: string
  datatype?: string
  column: string
}

interface ObjectPropertyMapping {
  predicate: string
  targetClass: string
  targetIriTemplate: string
  joinColumn: string
  properties: Record<string, PropertyMapping>
}

/**
 * Parse RML (Turtle format) into our internal structure
 */
function parseRML(rmlContent: string): ParsedMapping {
  console.log('=== parseRML called ===')
  const sources: ParsedSource[] = []

  // This is a simplified RML parser - for production, consider using a proper RDF parser
  // Parse triple maps - handle both <URI> and prefixed forms
  // Try multiple patterns
  let tripleMapRegex = /<([^>]+)>\s+a\s+rr:TriplesMap\s*[;.]([\s\S]*?)(?=<[^>]+>\s+a\s+rr:TriplesMap|$)/g
  let matches = Array.from(rmlContent.matchAll(tripleMapRegex))

  // If no matches, try alternative format (without angle brackets)
  if (matches.length === 0) {
    console.log('No matches with angle brackets, trying prefixed format...')
    tripleMapRegex = /([a-zA-Z0-9_:-]+)\s+a\s+rr:TriplesMap\s*[;.]([\s\S]*?)(?=[a-zA-Z0-9_:-]+\s+a\s+rr:TriplesMap|$)/g
    matches = Array.from(rmlContent.matchAll(tripleMapRegex))
  }

  console.log('Found', matches.length, 'triple maps')

  if (matches.length === 0) {
    console.error('No triple maps found! Sample content:', rmlContent.substring(0, 500))
  }

  // Store all triple maps for reference resolution
  const tripleMapsByUri: Record<string, any> = {}

  matches.forEach(match => {
    const uri = match[1]
    const content = match[2]

    console.log('Processing triple map:', uri)

    tripleMapsByUri[uri] = {
      uri,
      content,
      subjectClass: extractPattern(content, /rr:class\s+([^;\s]+)/)?.[1],
      subjectTemplate: extractPattern(content, /rr:template\s+"([^"]+)"/)?.[1],
      source: extractPattern(content, /rml:source\s+"([^"]+)"/)?.[1],
      predicateObjects: extractPredicateObjects(content)
    }

    console.log('Triple map details:', {
      uri,
      subjectClass: tripleMapsByUri[uri].subjectClass,
      subjectTemplate: tripleMapsByUri[uri].subjectTemplate,
      predicateObjectsCount: tripleMapsByUri[uri].predicateObjects.length
    })
  })

  // Convert each triple map to our format
  Object.values(tripleMapsByUri).forEach((tm: any) => {
    const properties: Record<string, PropertyMapping> = {}
    const objectProperties: ObjectPropertyMapping[] = []

    tm.predicateObjects.forEach((po: any) => {
      if (po.isObjectProperty && po.parentTriplesMap) {
        // This is an object property pointing to another triple map
        const targetTM = tripleMapsByUri[po.parentTriplesMap]
        if (targetTM) {
          console.log('Found object property:', po.predicate, '→', po.parentTriplesMap)

          // Get properties of the target triple map
          const targetProps: Record<string, PropertyMapping> = {}
          targetTM.predicateObjects.forEach((targetPO: any) => {
            if (!targetPO.isObjectProperty) {
              targetProps[targetPO.column] = {
                predicate: targetPO.predicate,
                datatype: targetPO.datatype,
                column: targetPO.column
              }
            }
          })

          // Infer join column from target template
          // e.g., "http://example.org/borrower/{BorrowerID}" → BorrowerID
          const joinColumn = targetTM.subjectTemplate?.match(/\{([^}]+)\}/)?.[1] || 'Unknown'

          objectProperties.push({
            predicate: po.predicate,
            targetClass: targetTM.subjectClass || 'Unknown',
            targetIriTemplate: targetTM.subjectTemplate || '',
            joinColumn: joinColumn,
            properties: targetProps
          })
        }
      } else if (!po.isObjectProperty && po.column) {
        // This is a data property
        properties[po.column] = {
          predicate: po.predicate,
          datatype: po.datatype,
          column: po.column
        }
      }
    })

    sources.push({
      name: tm.uri.split('/').pop() || tm.uri,
      entityClass: tm.subjectClass || 'Unknown',
      iriTemplate: tm.subjectTemplate || '',
      properties,
      objectProperties
    })
  })

  // Now filter out sources that are only referenced as nested entities (not top-level)
  const referencedUris = new Set<string>()
  Object.values(tripleMapsByUri).forEach((tm: any) => {
    tm.predicateObjects.forEach((po: any) => {
      if (po.isObjectProperty && po.parentTriplesMap) {
        referencedUris.add(po.parentTriplesMap)
      }
    })
  })

  // Keep only sources that are NOT purely nested (or keep all for now - user can see structure)
  // Actually, let's keep only the TOP-LEVEL entities (those not referenced by others)
  const topLevelSources = sources.filter(source => {
    const fullUri = Object.keys(tripleMapsByUri).find(uri => uri.endsWith(source.name))
    return !referencedUris.has(fullUri || '')
  })

  console.log('parseRML result:', topLevelSources.length, 'top-level sources (filtered from', sources.length, 'total)')
  topLevelSources.forEach((source, idx) => {
    console.log(`Source ${idx}:`, {
      name: source.name,
      entityClass: source.entityClass,
      iriTemplate: source.iriTemplate,
      propertiesCount: Object.keys(source.properties).length,
      properties: Object.keys(source.properties),
      objectPropertiesCount: source.objectProperties.length,
      objectProperties: source.objectProperties.map(op => ({
        predicate: op.predicate,
        targetClass: op.targetClass,
        joinColumn: op.joinColumn,
        propertiesCount: Object.keys(op.properties).length,
        properties: Object.keys(op.properties)
      }))
    })
  })

  console.log('All sources before filtering:', sources.map(s => ({
    name: s.name,
    propertiesCount: Object.keys(s.properties).length,
    objectPropertiesCount: s.objectProperties.length
  })))

  return {
    format: 'rml',
    sources: topLevelSources
  }
}

/**
 * Parse YARRRML (YAML format) into our internal structure
 */
function parseYARRRML(yarrrmlContent: string): ParsedMapping {
  const doc = yaml.load(yarrrmlContent) as any
  const sources: ParsedSource[] = []

  const mappings = doc.mappings || {}

  Object.entries(mappings).forEach(([name, mapping]: [string, any]) => {
    const properties: Record<string, PropertyMapping> = {}
    const objectProperties: ObjectPropertyMapping[] = []

    // Parse subject
    const subject = mapping.subject || mapping.s
    const entityClass = typeof subject === 'string' ? subject : subject?.class || subject?.a
    const iriTemplate = typeof subject === 'string' ? '' : subject?.value || ''

    // Parse predicate-objects
    const pos = mapping.predicateobjects || mapping.po || []
    pos.forEach((po: any) => {
      const predicates = Array.isArray(po.predicates || po.p) ? (po.predicates || po.p) : [po.predicates || po.p]
      const objects = Array.isArray(po.objects || po.o) ? (po.objects || po.o) : [po.objects || po.o]

      predicates.forEach((pred: string) => {
        objects.forEach((obj: any) => {
          if (typeof obj === 'string') {
            // Simple reference to column
            properties[obj] = {
              predicate: pred,
              column: obj
            }
          } else if (obj.reference || obj.value) {
            // Column reference with possible datatype
            const column = obj.reference || obj.value
            properties[column] = {
              predicate: pred,
              datatype: obj.datatype,
              column
            }
          } else if (obj.mapping) {
            // Object property pointing to another mapping
            const targetMapping = mappings[obj.mapping]
            if (targetMapping) {
              const targetSubject = targetMapping.subject || targetMapping.s
              const targetClass = typeof targetSubject === 'string' ? targetSubject : targetSubject?.class || targetSubject?.a
              const targetIriTemplate = typeof targetSubject === 'string' ? '' : targetSubject?.value || ''

              // Get target properties
              const targetProps: Record<string, PropertyMapping> = {}
              const targetPOs = targetMapping.predicateobjects || targetMapping.po || []
              targetPOs.forEach((targetPO: any) => {
                const targetPreds = Array.isArray(targetPO.predicates || targetPO.p) ? (targetPO.predicates || targetPO.p) : [targetPO.predicates || targetPO.p]
                const targetObjs = Array.isArray(targetPO.objects || targetPO.o) ? (targetPO.objects || targetPO.o) : [targetPO.objects || targetPO.o]

                targetPreds.forEach((tPred: string) => {
                  targetObjs.forEach((tObj: any) => {
                    if (typeof tObj === 'string') {
                      targetProps[tObj] = {
                        predicate: tPred,
                        column: tObj
                      }
                    } else if (tObj.reference || tObj.value) {
                      const col = tObj.reference || tObj.value
                      targetProps[col] = {
                        predicate: tPred,
                        datatype: tObj.datatype,
                        column: col
                      }
                    }
                  })
                })
              })

              // Find join column from condition
              const joinColumn = obj.condition?.column || 'Unknown'

              objectProperties.push({
                predicate: pred,
                targetClass: targetClass || 'Unknown',
                targetIriTemplate: targetIriTemplate || '',
                joinColumn,
                properties: targetProps
              })
            }
          }
        })
      })
    })

    sources.push({
      name,
      entityClass: entityClass || 'Unknown',
      iriTemplate: iriTemplate || '',
      properties,
      objectProperties
    })
  })

  return {
    format: 'yarrrml',
    sources
  }
}

/**
 * Helper: Extract pattern from RML content
 */
function extractPattern(content: string, regex: RegExp): RegExpMatchArray | null {
  return content.match(regex)
}

/**
 * Helper: Extract predicate-object pairs from RML
 */
function extractPredicateObjects(content: string): any[] {
  const results: any[] = []

  console.log('extractPredicateObjects called, content length:', content.length)

  // The RML structure has multiple comma-separated blocks:
  // rr:predicateObjectMap [ rr:objectMap [ rml:reference "..." ] ; rr:predicate ex:prop ],
  //                       [ rr:objectMap [ ... ] ; rr:predicate ex:prop2 ],
  //                       [ ... ]

  // Strategy: Find ALL bracket blocks [ ... ] that contain either rr:predicate or rr:objectMap
  // and are within the predicateObjectMap section

  // First, find the predicateObjectMap section
  const poSectionMatch = content.match(/rr:predicateObjectMap\s+([\s\S]*?)(?:rr:subjectMap|$)/)
  if (!poSectionMatch) {
    console.log('No predicateObjectMap section found')
    return results
  }

  const poSection = poSectionMatch[1]
  console.log('Found predicateObjectMap section, length:', poSection.length)

  // Now find all top-level bracket blocks [ ... ] in this section
  // We need to handle nested brackets properly
  const blocks: string[] = []
  let depth = 0
  let currentBlock = ''
  let inBlock = false

  for (let i = 0; i < poSection.length; i++) {
    const char = poSection[i]

    if (char === '[') {
      if (depth === 0) {
        inBlock = true
        currentBlock = '['
      } else {
        currentBlock += char
      }
      depth++
    } else if (char === ']') {
      depth--
      currentBlock += char
      if (depth === 0 && inBlock) {
        blocks.push(currentBlock)
        currentBlock = ''
        inBlock = false
      }
    } else if (inBlock) {
      currentBlock += char
    }
  }

  console.log('Found', blocks.length, 'top-level bracket blocks')

  // Process each block
  blocks.forEach((block, idx) => {
    // Extract predicate (should be at this level)
    const predicate = extractPattern(block, /rr:predicate\s+([^;\s\],]+)/)?.[1]

    // Extract objectMap details (inside nested brackets)
    const reference = extractPattern(block, /rml:reference\s+"([^"]+)"/)?.[1]
    const datatype = extractPattern(block, /rr:datatype\s+([^;\s\]]+)/)?.[1]
    const parentTriplesMap = extractPattern(block, /rr:parentTriplesMap\s+<([^>]+)>/)?.[1]

    console.log(`Block ${idx}: predicate=${predicate}, reference=${reference}, isObject=${!!parentTriplesMap}`)

    if (predicate) {
      results.push({
        predicate,
        column: reference || '',
        datatype,
        isObjectProperty: !!parentTriplesMap,
        parentTriplesMap,
        joinColumn: reference
      })
    }
  })

  console.log('extractPredicateObjects returning', results.length, 'results')
  return results
}

/**
 * Helper: Extract join column from RML
 */
function extractJoinColumn(content: string, parentUri: string): string | null {
  // Look for rr:joinCondition or infer from template
  const joinCondition = extractPattern(content, /rr:joinCondition\s*\[[\s\S]*?rr:child\s+"([^"]+)"/)?.[1]
  if (joinCondition) return joinCondition

  // Try to infer from the parent triple map reference context
  const templateMatch = extractPattern(content, /rr:template\s+"[^"]*\{([^}]+)\}[^"]*"/)
  if (templateMatch) return templateMatch[1]

  return null
}

/**
 * Main parser: auto-detects format and parses
 */
export function parseMappingFile(content: string): ParsedMapping | null {
  try {
    console.log('=== Starting parseMappingFile ===')
    console.log('Content length:', content.length)
    console.log('First 200 chars:', content.substring(0, 200))

    // Try YARRRML first (YAML format)
    if (content.trim().startsWith('prefixes:') || content.trim().startsWith('mappings:')) {
      console.log('Detected YARRRML format')
      return parseYARRRML(content)
    }

    // Try RML (Turtle format)
    if (content.includes('rr:TriplesMap') || content.includes('@prefix rr:')) {
      console.log('Detected RML format')
      const result = parseRML(content)
      console.log('RML parse result:', result)
      return result
    }

    // Try as YAML (might be YARRRML without prefixes section)
    try {
      const doc = yaml.load(content) as any
      if (doc.mappings) {
        console.log('Detected YARRRML (no prefix header)')
        return parseYARRRML(content)
      }
    } catch (e) {
      console.log('Not YAML:', e)
    }

    console.error('Could not detect format - no matching patterns found')
    return null
  } catch (error) {
    console.error('Failed to parse mapping file:', error)
    return null
  }
}

export type { ParsedMapping, ParsedSource, PropertyMapping, ObjectPropertyMapping }

