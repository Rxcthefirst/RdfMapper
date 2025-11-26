import React, { useState, useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Stack,
  Chip,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  CircularProgress
} from '@mui/material'
import { getCytoscape, waitForContainer } from '../lib/cytoscapeLoader'
import type { MappingRow } from './ComprehensiveMappingTable'

interface EnhancedMappingModalProps {
  open: boolean
  onClose: () => void
  projectId: string
  mappingRow: MappingRow | null
  ontologyClasses: Array<{ uri: string; label?: string; comment?: string }>
  ontologyProperties: Array<{ uri: string; label?: string; comment?: string; domain?: string; range?: string }>
  onSave: (newPropertyUri: string) => void
}

const EnhancedMappingModal: React.FC<EnhancedMappingModalProps> = ({
  open,
  onClose,
  projectId,
  mappingRow,
  ontologyClasses,
  ontologyProperties,
  onSave
}) => {
  const cyRef = useRef<HTMLDivElement>(null)
  const cyInstance = useRef<any>(null)
  const [selectedProperty, setSelectedProperty] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [loadingEvidence, setLoadingEvidence] = useState(false)

  // Build subgraph based on current mapping context
  const { graphElements, alternativeSuggestions } = useMemo(() => {
    if (!mappingRow) return { graphElements: [], alternativeSuggestions: [] }

    const elements: any[] = []
    const suggestions: Array<{ uri: string; label: string; reason: string; confidence: number }> = []
    const addedNodes = new Set<string>()
    const addedEdges = new Set<string>()

    console.log('Building graph for property:', mappingRow.mappedProperty)
    console.log('Available ontology properties:', ontologyProperties.length)
    console.log('Sample properties:', ontologyProperties.slice(0, 3).map(p => ({ uri: p.uri, label: p.label })))

    // Helper to expand prefixed URIs
    const expandUri = (uri: string): string => {
      if (uri.startsWith('ex:')) {
        return uri.replace('ex:', 'https://example.com/mortgage#')
      }
      // Add other common prefixes if needed
      if (uri.startsWith('rdf:')) {
        return uri.replace('rdf:', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
      }
      if (uri.startsWith('rdfs:')) {
        return uri.replace('rdfs:', 'http://www.w3.org/2000/01/rdf-schema#')
      }
      if (uri.startsWith('xsd:')) {
        return uri.replace('xsd:', 'http://www.w3.org/2001/XMLSchema#')
      }
      return uri
    }

    // Find current mapped property details (with prefix expansion)
    const expandedUri = expandUri(mappingRow.mappedProperty)
    const currentProp = ontologyProperties.find(p =>
      p.uri === mappingRow.mappedProperty ||
      p.uri === expandedUri
    )

    if (!currentProp) {
      console.warn('Current property not found in ontology')
      console.warn('Looking for:', mappingRow.mappedProperty)
      console.warn('Expanded to:', expandedUri)
      console.warn('All property URIs:', ontologyProperties.map(p => p.uri))

      // Show a simple message instead of empty graph
      return {
        graphElements: [{
          data: {
            id: 'error',
            label: 'Property not found in ontology',
            type: 'error'
          },
          classes: 'error-node'
        }],
        alternativeSuggestions: []
      }
    }

    console.log('Current property:', currentProp)

    // Helper to add node if not already added
    const addNode = (id: string, data: any, classes: string) => {
      if (!addedNodes.has(id)) {
        elements.push({ data: { id, ...data }, classes })
        addedNodes.add(id)
      }
    }

    // Helper to add edge if not already added
    const addEdge = (id: string, source: string, target: string, label?: string) => {
      if (!addedEdges.has(id) && addedNodes.has(source) && addedNodes.has(target)) {
        elements.push({
          data: { id, source, target, label: label || '' }
        })
        addedEdges.add(id)
      }
    }

    // 1. Add the current property (center)
    addNode(currentProp.uri, {
      label: currentProp.label || currentProp.uri.split('#').pop(),
      type: 'property',
      comment: currentProp.comment
    }, 'property-node current-property')

    // 2. Add domain class (left side)
    let domainClass = null
    if (currentProp.domain) {
      domainClass = ontologyClasses.find(c => c.uri === currentProp.domain)
      if (domainClass) {
        addNode(domainClass.uri, {
          label: domainClass.label || domainClass.uri.split('#').pop(),
          type: 'class',
          comment: domainClass.comment
        }, 'class-node domain-class')

        // Edge: domain -> property
        addEdge(`${domainClass.uri}-${currentProp.uri}`, domainClass.uri, currentProp.uri, 'domain')
      }
    }

    // 3. Add range class (right side)
    let rangeClass = null
    if (currentProp.range) {
      rangeClass = ontologyClasses.find(c => c.uri === currentProp.range)
      if (rangeClass) {
        addNode(rangeClass.uri, {
          label: rangeClass.label || rangeClass.uri.split('#').pop(),
          type: 'class',
          comment: rangeClass.comment
        }, 'class-node range-class')

        // Edge: property -> range
        addEdge(`${currentProp.uri}-${rangeClass.uri}`, currentProp.uri, rangeClass.uri, 'range')
      }
    }

    // 4. Add one-hop neighbors of domain class
    if (domainClass) {
      ontologyProperties.forEach(prop => {
        if (prop.uri === currentProp.uri) return

        // Properties with this class as domain
        if (prop.domain === domainClass.uri) {
          addNode(prop.uri, {
            label: prop.label || prop.uri.split('#').pop(),
            type: 'property',
            comment: prop.comment
          }, 'property-node neighbor-property')

          addEdge(`${domainClass.uri}-${prop.uri}`, domainClass.uri, prop.uri, '')

          // Add range of neighbor property if it's a class
          if (prop.range) {
            const neighborRange = ontologyClasses.find(c => c.uri === prop.range)
            if (neighborRange && neighborRange.uri !== domainClass.uri) {
              addNode(neighborRange.uri, {
                label: neighborRange.label || neighborRange.uri.split('#').pop(),
                type: 'class',
                comment: neighborRange.comment
              }, 'class-node neighbor-class')

              addEdge(`${prop.uri}-${neighborRange.uri}`, prop.uri, neighborRange.uri, '')
            }
          }
        }

        // Properties with this class as range (incoming)
        if (prop.range === domainClass.uri && prop.domain !== domainClass.uri) {
          const sourceDomain = ontologyClasses.find(c => c.uri === prop.domain)
          if (sourceDomain) {
            addNode(sourceDomain.uri, {
              label: sourceDomain.label || sourceDomain.uri.split('#').pop(),
              type: 'class',
              comment: sourceDomain.comment
            }, 'class-node neighbor-class')

            addNode(prop.uri, {
              label: prop.label || prop.uri.split('#').pop(),
              type: 'property',
              comment: prop.comment
            }, 'property-node neighbor-property')

            addEdge(`${sourceDomain.uri}-${prop.uri}`, sourceDomain.uri, prop.uri, '')
            addEdge(`${prop.uri}-${domainClass.uri}`, prop.uri, domainClass.uri, '')
          }
        }
      })
    }

    // 5. Add one-hop neighbors of range class
    if (rangeClass) {
      ontologyProperties.forEach(prop => {
        if (prop.uri === currentProp.uri) return

        // Properties with this class as domain
        if (prop.domain === rangeClass.uri) {
          addNode(prop.uri, {
            label: prop.label || prop.uri.split('#').pop(),
            type: 'property',
            comment: prop.comment
          }, 'property-node neighbor-property')

          addEdge(`${rangeClass.uri}-${prop.uri}`, rangeClass.uri, prop.uri, '')

          // Add range of neighbor property
          if (prop.range) {
            const neighborRange = ontologyClasses.find(c => c.uri === prop.range)
            if (neighborRange && neighborRange.uri !== rangeClass.uri && neighborRange.uri !== domainClass?.uri) {
              addNode(neighborRange.uri, {
                label: neighborRange.label || neighborRange.uri.split('#').pop(),
                type: 'class',
                comment: neighborRange.comment
              }, 'class-node neighbor-class')

              addEdge(`${prop.uri}-${neighborRange.uri}`, prop.uri, neighborRange.uri, '')
            }
          }
        }

        // Properties with this class as range (incoming)
        if (prop.range === rangeClass.uri && prop.domain !== rangeClass.uri && prop.domain !== domainClass?.uri) {
          const sourceDomain = ontologyClasses.find(c => c.uri === prop.domain)
          if (sourceDomain) {
            addNode(sourceDomain.uri, {
              label: sourceDomain.label || sourceDomain.uri.split('#').pop(),
              type: 'class',
              comment: sourceDomain.comment
            }, 'class-node neighbor-class')

            addNode(prop.uri, {
              label: prop.label || prop.uri.split('#').pop(),
              type: 'property',
              comment: prop.comment
            }, 'property-node neighbor-property')

            addEdge(`${sourceDomain.uri}-${prop.uri}`, sourceDomain.uri, prop.uri, '')
            addEdge(`${prop.uri}-${rangeClass.uri}`, prop.uri, rangeClass.uri, '')
          }
        }
      })
    }

    console.log('Graph built:', {
      nodes: addedNodes.size,
      edges: addedEdges.size,
      elements: elements.length
    })

    // Find alternative properties (same domain or similar characteristics)
    ontologyProperties.forEach(prop => {
      if (prop.uri === currentProp.uri) return

      let confidence = 0
      let reason = ''

      // Same domain
      if (prop.domain === currentProp.domain) {
        confidence += 0.5
        reason = 'Same domain'
      }

      // Similar label
      const currentLabel = (currentProp.label || currentProp.uri).toLowerCase()
      const propLabel = (prop.label || prop.uri).toLowerCase()
      if (propLabel.includes(currentLabel) || currentLabel.includes(propLabel)) {
        confidence += 0.3
        reason += (reason ? ', ' : '') + 'Similar name'
      }

      // Column name similarity
      const colName = mappingRow.columnName.toLowerCase()
      const propUriPart = prop.uri.split('#').pop()?.split('/').pop()?.toLowerCase() || ''
      if (propUriPart.includes(colName) || colName.includes(propUriPart)) {
        confidence += 0.3
        reason += (reason ? ', ' : '') + 'Matches column name'
      }

      if (confidence > 0.3) {
        suggestions.push({
          uri: prop.uri,
          label: prop.label || prop.uri.split('#').pop() || prop.uri,
          reason,
          confidence
        })
      }
    })

    // Sort suggestions by confidence
    suggestions.sort((a, b) => b.confidence - a.confidence)

    return { graphElements: elements, alternativeSuggestions: suggestions.slice(0, 5) }
  }, [mappingRow, ontologyClasses, ontologyProperties])

  // Fetch evidence data from alignment report
  useEffect(() => {
    if (!open || !mappingRow || !projectId) {
      setEvidenceData(null)
      return
    }

    const fetchEvidence = async () => {
      setLoadingEvidence(true)
      try {
        const response = await fetch(`/api/mappings/${projectId}/evidence/${encodeURIComponent(mappingRow.columnName)}`)
        if (response.ok) {
          const data = await response.json()
          console.log('=== Evidence data received ===')
          console.log('Full response:', data)
          console.log('Evidence detail:', data.evidence_detail)
          if (data.evidence_detail?.evidence) {
            console.log('Evidence array:', data.evidence_detail.evidence)
            data.evidence_detail.evidence.forEach((ev: any, idx: number) => {
              console.log(`Evidence ${idx}:`, {
                type: ev.type,
                matcher: ev.matcher,
                description: ev.description,
                reason: ev.reason,
                score: ev.score,
                allKeys: Object.keys(ev)
              })
            })
          }
          setEvidenceData(data.evidence_detail)
        } else {
          console.warn('No evidence data available for this column')
          setEvidenceData(null)
        }
      } catch (error) {
        console.error('Failed to fetch evidence:', error)
        setEvidenceData(null)
      } finally {
        setLoadingEvidence(false)
      }
    }

    fetchEvidence()
  }, [open, mappingRow, projectId])

  // Initialize Cytoscape with robust async handling (matches OntologyGraphMini pattern)
  useLayoutEffect(() => {
    if (graphElements.length === 0) return

    let cancelled = false
    let attempts = 0

    const attemptInit = async () => {
      if (cancelled) return
      if (cyInstance.current) return // Already initialized

      const el = cyRef.current
      if (!el) {
        attempts++
        if (attempts < 20) {
          return setTimeout(attemptInit, 40)
        } else {
          console.error('Graph container not found after 20 attempts')
          setLoading(false)
          return
        }
      }

      // Container exists; mark loading
      setLoading(true)

      // Wait for container to have dimensions
      const sized = await waitForContainer(el, 15, 30)
      if (!sized) {
        console.warn('Container still has no dimensions, setting min height')
        el.style.minHeight = '400px'
      }

      if (cancelled) return

      try {
        const cytoscape = getCytoscape()
        console.log('Initializing Cytoscape with', graphElements.length, 'elements')

        const cy = cytoscape({
          container: el,
          elements: graphElements,
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'text-valign': 'center',
              'text-halign': 'center',
              'font-size': '11px',
              'text-wrap': 'wrap',
              'text-max-width': '100px',
              'background-color': '#ccc',
              'border-width': 2,
              'border-color': '#999'
            }
          },
          {
            selector: '.class-node',
            style: {
              'shape': 'roundrectangle',
              'width': 80,
              'height': 50,
              'background-color': '#e8f4f8',
              'border-color': '#4a90e2',
              'font-weight': 'bold'
            }
          },
          {
            selector: '.domain-class',
            style: {
              'background-color': '#fff3cd',
              'border-color': '#ffc107',
              'border-width': 3
            }
          },
          {
            selector: '.range-class',
            style: {
              'background-color': '#d4edda',
              'border-color': '#28a745',
              'border-width': 3
            }
          },
          {
            selector: '.neighbor-class',
            style: {
              'background-color': '#f0f0f0',
              'border-color': '#999',
              'border-width': 1,
              'opacity': 0.7
            }
          },
          {
            selector: '.property-node',
            style: {
              'shape': 'ellipse',
              'width': 70,
              'height': 70,
              'background-color': '#fff',
              'border-color': '#666'
            }
          },
          {
            selector: '.current-property',
            style: {
              'background-color': '#d1ecf1',
              'border-color': '#0c5460',
              'border-width': 4,
              'width': 90,
              'height': 90,
              'font-size': '13px',
              'font-weight': 'bold'
            }
          },
          {
            selector: '.neighbor-property',
            style: {
              'background-color': '#fafafa',
              'border-color': '#aaa',
              'border-width': 1,
              'opacity': 0.6,
              'width': 50,
              'height': 50,
              'font-size': '9px'
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 2,
              'line-color': '#999',
              'target-arrow-color': '#999',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'label': 'data(label)',
              'font-size': '9px',
              'text-rotation': 'autorotate',
              'text-background-color': '#fff',
              'text-background-opacity': 0.8,
              'text-background-padding': '2px'
            }
          },
          {
            selector: 'edge[label="domain"]',
            style: {
              'line-color': '#ffc107',
              'target-arrow-color': '#ffc107',
              'width': 3
            }
          },
          {
            selector: 'edge[label="range"]',
            style: {
              'line-color': '#28a745',
              'target-arrow-color': '#28a745',
              'width': 3
            }
          }
        ],
        layout: {
          name: 'cola',
          animate: true,
          randomize: false,
          maxSimulationTime: 3000,
          fit: true,
          padding: 40,
          nodeDimensionsIncludeLabels: true,
          edgeLength: 150,
          nodeSpacing: 50,
          flow: { axis: 'x', minSeparation: 100 }
        }
      })

      // Click handler for property nodes
      cy.on('tap', 'node[type="property"]', (evt: any) => {
        const node = evt.target
        setSelectedProperty(node.data('id'))
      })

      cy.on('ready', () => {
        if (!cancelled) {
          console.log('Cytoscape ready')
          setLoading(false)
        }
      })

      cyInstance.current = cy
      } catch (e: any) {
        if (!cancelled) {
          console.error('Graph init failed:', e)
          setLoading(false)
        }
      }
    }

    // Kick off initialization attempts
    setLoading(true)
    attemptInit()

    return () => {
      cancelled = true
      if (cyInstance.current) {
        try {
          cyInstance.current.destroy()
        } catch (e) {
          console.warn('Error destroying Cytoscape:', e)
        }
        cyInstance.current = null
      }
    }
  }, [graphElements])

  // Set initial selected property
  useEffect(() => {
    if (mappingRow && open) {
      setSelectedProperty(mappingRow.mappedProperty)
    }
  }, [mappingRow, open])

  const handleSave = () => {
    if (selectedProperty) {
      onSave(selectedProperty)
      onClose()
    }
  }

  const handleReloadGraph = () => {
    console.log('Manual graph reload triggered')
    // Destroy existing instance
    if (cyInstance.current) {
      try {
        cyInstance.current.destroy()
      } catch (e) {
        console.warn('Error destroying Cytoscape:', e)
      }
      cyInstance.current = null
    }
    // The useLayoutEffect will automatically reinitialize when cyInstance.current is null
    setLoading(true)
  }

  const filteredProperties = useMemo(() => {
    const query = searchQuery.toLowerCase()
    if (!query) return ontologyProperties

    return ontologyProperties.filter(prop => {
      const label = (prop.label || '').toLowerCase()
      const uri = prop.uri.toLowerCase()
      const localName = uri.split('#').pop()?.split('/').pop() || ''
      return label.includes(query) || localName.includes(query)
    })
  }, [searchQuery, ontologyProperties])

  if (!mappingRow) return null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            Edit Mapping: {mappingRow.columnName}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Chip label={mappingRow.mappingType} size="small" />
            <Chip label={mappingRow.parentEntity} size="small" color="primary" />
            {mappingRow.nestedEntity && (
              <Chip label={`→ ${mappingRow.nestedEntity}`} size="small" color="secondary" />
            )}
          </Stack>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', gap: 2, height: '70vh' }}>
          {/* Left: Graph Visualization */}
          <Paper variant="outlined" sx={{ flex: 2, p: 2, position: 'relative' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2">
                🔍 Mapping Context Graph
              </Typography>
              <Button
                size="small"
                onClick={handleReloadGraph}
                disabled={loading}
                sx={{ minWidth: 'auto', px: 1 }}
              >
                🔄 Reload
              </Button>
            </Box>
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <CircularProgress />
              </Box>
            )}
            <Box
              ref={cyRef}
              sx={{
                width: '100%',
                height: 'calc(100% - 60px)',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                bgcolor: '#fafafa'
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Click on property nodes to select. Dashed lines show alternatives.
            </Typography>
          </Paper>

          {/* Right: Property List & Suggestions */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Current Mapping */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Current Mapping
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>{mappingRow.columnName}</strong> → {mappingRow.mappedPropertyLabel}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                {mappingRow.mappedProperty}
              </Typography>
            </Paper>

            {/* Evidence & Analysis from AI Generation */}
            {evidenceData && (
              <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                <Typography variant="subtitle2" gutterBottom>
                  🤖 AI Analysis
                </Typography>

                {loadingEvidence ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                    <CircularProgress size={20} />
                  </Box>
                ) : (
                  <Stack spacing={1}>
                    {/* Confidence Score */}
                    {typeof evidenceData.confidence_score === 'number' && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Confidence:
                        </Typography>
                        <Chip
                          label={`${(evidenceData.confidence_score * 100).toFixed(1)}%`}
                          size="small"
                          color={evidenceData.confidence_score > 0.8 ? 'success' : evidenceData.confidence_score > 0.6 ? 'warning' : 'default'}
                          sx={{ ml: 1 }}
                        />
                      </Box>
                    )}

                    {/* Matcher Name */}
                    {evidenceData.matcher_name && (
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Matcher: {evidenceData.matcher_name}
                        </Typography>
                      </Box>
                    )}

                    {/* Reasoning Summary */}
                    {evidenceData.reasoning_summary && evidenceData.reasoning_summary.trim() && (
                      <Box>
                        <Typography variant="caption" fontWeight="bold" display="block">
                          Reasoning:
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {evidenceData.reasoning_summary}
                        </Typography>
                      </Box>
                    )}

                    {/* Evidence Items */}
                    {evidenceData.evidence && Array.isArray(evidenceData.evidence) && evidenceData.evidence.length > 0 && (
                      <Box>
                        <Typography variant="caption" fontWeight="bold" display="block" sx={{ mb: 0.5 }}>
                          Evidence ({evidenceData.evidence.length}):
                        </Typography>
                        <Stack spacing={0.5}>
                          {evidenceData.evidence.slice(0, 3).map((ev: any, idx: number) => (
                            <Box key={idx} sx={{ pl: 1, borderLeft: '2px solid', borderColor: 'divider' }}>
                              <Typography variant="caption" display="block">
                                <strong>{ev.matcher_name || 'Unknown'}:</strong> {ev.matched_via || 'No description'}
                              </Typography>
                              {typeof ev.confidence === 'number' && (
                                <Chip
                                  label={`${(ev.confidence * 100).toFixed(0)}%`}
                                  size="small"
                                  sx={{ fontSize: '0.65rem', height: 16, mt: 0.5 }}
                                />
                              )}
                              {ev.evidence_category && ev.evidence_category !== 'other' && (
                                <Chip
                                  label={ev.evidence_category}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.65rem', height: 16, mt: 0.5, ml: 0.5 }}
                                />
                              )}
                            </Box>
                          ))}
                          {evidenceData.evidence.length > 3 && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                              ...and {evidenceData.evidence.length - 3} more
                            </Typography>
                          )}
                        </Stack>
                      </Box>
                    )}

                    {/* Alternate Candidates */}
                    {evidenceData.alternates && Array.isArray(evidenceData.alternates) && evidenceData.alternates.length > 0 && (
                      <Box>
                        <Typography variant="caption" fontWeight="bold" display="block">
                          Other Candidates:
                        </Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5 }}>
                          {evidenceData.alternates.slice(0, 3).map((alt: any, idx: number) => (
                            <Chip
                              key={idx}
                              label={`${alt.property_label || alt.property || 'Unknown'} (${typeof alt.confidence === 'number' ? (alt.confidence * 100).toFixed(0) : '?'}%)`}
                              size="small"
                              variant="outlined"
                              onClick={() => alt.property && setSelectedProperty(alt.property)}
                              sx={{ fontSize: '0.7rem', cursor: 'pointer' }}
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Stack>
                )}
              </Paper>
            )}

            {/* Alternative Suggestions */}
            {alternativeSuggestions.length > 0 && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  💡 Suggested Alternatives
                </Typography>
                <List dense>
                  {alternativeSuggestions.map((suggestion, idx) => (
                    <ListItem key={idx} disablePadding>
                      <ListItemButton
                        selected={selectedProperty === suggestion.uri}
                        onClick={() => setSelectedProperty(suggestion.uri)}
                      >
                        <ListItemText
                          primary={suggestion.label}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {suggestion.reason}
                              </Typography>
                              <Chip
                                label={`${(suggestion.confidence * 100).toFixed(0)}% match`}
                                size="small"
                                color={suggestion.confidence > 0.7 ? 'success' : 'default'}
                                sx={{ mt: 0.5 }}
                              />
                            </Box>
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}

            <Divider />

            {/* Search & Select */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <Typography variant="subtitle2" gutterBottom>
                All Properties
              </Typography>
              <TextField
                size="small"
                placeholder="Search properties..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                sx={{ mb: 1 }}
              />
              <List dense sx={{ flex: 1, overflow: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                {filteredProperties.slice(0, 100).map((prop) => (
                  <ListItem key={prop.uri} disablePadding>
                    <ListItemButton
                      selected={selectedProperty === prop.uri}
                      onClick={() => setSelectedProperty(prop.uri)}
                    >
                      <ListItemText
                        primary={prop.label || prop.uri.split('#').pop()}
                        secondary={prop.uri}
                        secondaryTypographyProps={{
                          style: { fontSize: '0.7rem', wordBreak: 'break-all' }
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Box>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!selectedProperty || selectedProperty === mappingRow.mappedProperty}
        >
          Save Mapping
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default EnhancedMappingModal

