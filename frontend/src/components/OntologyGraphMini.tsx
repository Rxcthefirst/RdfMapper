import React, { useLayoutEffect, useRef, useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import { getCytoscape, waitForContainer } from '../lib/cytoscapeLoader';
import { buildOntologyElements } from './ontologyGraphUtils'

export interface OntologyGraphMiniProps {
  classes: { uri: string; label?: string | null }[];
  properties: { uri: string; label?: string | null; domain?: string | null; range?: string | null }[];
  onOpenFull?: () => void;
}

const OntologyGraphMini: React.FC<OntologyGraphMiniProps> = ({ classes, properties, onOpenFull }) => {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const cyRef = useRef<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const initStarted = useRef(false)

  const mappedClassUris = React.useMemo(()=> new Set((properties||[]).map(p=> p.domain).filter(Boolean) as string[]), [properties])
  const mappedPropertyUris = React.useMemo(()=> new Set((properties||[]).map(p=> p.uri)), [properties])

  // Initialization effect (runs once)
  useLayoutEffect(() => {
    let cancelled = false
    let attempts = 0

    const attemptInit = async () => {
      if (cancelled) return
      if (cyRef.current) return // already initialized
      const el = containerRef.current
      if (!el) {
        attempts++
        if (attempts < 20) {
          return setTimeout(attemptInit, 40)
        } else {
          setLoadError('Graph container not found')
          setLoading(false)
          return
        }
      }
      // Container exists; mark loading
      setLoading(true); setLoadError(null)
      // Wait for size
      const sized = await waitForContainer(el, 15, 30)
      if (!sized) {
        el.style.minHeight = '220px'
      }
      try {
        const cytoscape = getCytoscape()
        if (cancelled) return
        const elements = buildOntologyElements(classes as any, properties as any, { maxClasses: 40, maxProperties: 80, includeStubs: true, allowDataProperties: false, mappedClassUris, mappedPropertyUris })
        cyRef.current = cytoscape({
          container: el,
          elements,
          style: [
            { selector: 'node[type="class"]', style: { 'background-color': '#1976d2', 'label': 'data(label)', 'color': '#fff', 'font-size': 8, 'text-wrap': 'wrap', 'text-max-width': 70, 'shape':'round-rectangle', 'padding':'3px' } },
            { selector: 'node[stub = "true"]', style: { 'background-color': '#546e7a', 'opacity': 0.55 } },
            { selector: 'node[type="class"][coverage = "mapped"]', style: { 'background-color': '#2e7d32' } },
            { selector: 'node[type="class"][coverage = "unmapped"]', style: { 'background-color': '#455a64' } },
            { selector: 'node', style: { 'text-wrap': 'wrap', 'text-max-width': 70 } },
            { selector: 'edge[type="property"]', style: { 'line-color': '#616161', 'width': 1.5, 'target-arrow-shape': 'triangle', 'target-arrow-color': '#616161', 'curve-style': 'bezier', 'label':'data(label)', 'font-size':6, 'color':'#222', 'text-background-opacity':0.85, 'text-background-color':'#fafafa', 'text-background-shape':'round-rectangle' } }
          ],
          layout: { name: 'cola', maxSimulationTime: 500, fit: true, padding: 10 }
        })
        cyRef.current.on('ready', () => {
          if (!cancelled) setLoading(false)
        })
      } catch (e:any) {
        if (!cancelled) {
          setLoadError(e.message || 'Graph init failed')
          setLoading(false)
        }
      }
    }

    // Kick off attempts
    setLoading(true)
    attemptInit()

    return () => { cancelled = true; if (cyRef.current) { try { cyRef.current.destroy() } catch {} cyRef.current = null } }
  }, [classes, properties])

  // Update effect (elements only) when data changes
  useEffect(() => {
    if (!cyRef.current) return
    try {
      const cy = cyRef.current
      cy.batch(() => {
        cy.elements().remove()
        const newElements = buildOntologyElements(classes as any, properties as any, { maxClasses: 40, maxProperties: 80, includeStubs: true })
        cy.add(newElements)
      })
      cy.layout({ name: 'cola', maxSimulationTime: 450, fit: true, padding: 8 }).run()
    } catch (e:any) {
      setLoadError(e.message || 'Failed to update preview')
    }
  }, [classes, properties])

  return (
    <Box sx={{ position: 'relative' }}>
      <Box
        sx={{
          width: '100%',
          height: 220,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          bgcolor: 'background.paper',
          overflow: 'hidden',
          cursor: onOpenFull ? 'pointer' : 'default'
        }}
        onClick={() => onOpenFull && onOpenFull()}
      >
        <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
        {loading && (
          <Box sx={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', bgcolor:'rgba(255,255,255,0.6)', zIndex:1 }}>
            <Typography variant="caption">Loading…</Typography>
          </Box>
        )}
        {loadError && !loading && (
          <Box sx={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', p:1 }}>
            <Typography variant="caption" color="error">{loadError}</Typography>
          </Box>
        )}
      </Box>
      <Typography variant="caption" sx={{ position: 'absolute', bottom: 4, right: 8, color: 'text.secondary' }}>
        Ontology Preview
      </Typography>
    </Box>
  );
};

export default OntologyGraphMini;
