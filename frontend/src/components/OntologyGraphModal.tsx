import React, { useLayoutEffect, useRef, useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, IconButton, Box, Typography, Stack, Chip, Button } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { getCytoscape, waitForContainer } from '../lib/cytoscapeLoader';
import { buildOntologyElements } from './ontologyGraphUtils'

interface OntologyGraphModalProps {
  open: boolean;
  onClose: () => void;
  classes: { uri: string; label?: string | null; comment?: string | null }[];
  properties: { uri: string; label?: string | null; comment?: string | null; domain?: string | null; range?: string | null }[];
}

const OntologyGraphModal: React.FC<OntologyGraphModalProps> = ({ open, onClose, classes, properties }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [debugInfo, setDebugInfo] = useState<string>('')
  const initFlag = useRef(0)
  const [dataWaiting, setDataWaiting] = useState(false)
  const [initialized, setInitialized] = useState(false)

  const mappedClassUris = React.useMemo(()=> new Set((properties||[]).map(p=> p.domain).filter(Boolean) as string[]), [properties])
  const mappedPropertyUris = React.useMemo(()=> new Set((properties||[]).map(p=> p.uri)), [properties])
  const buildElements = () => buildOntologyElements(classes as any, properties as any, { maxClasses: 120, maxProperties: 300, includeStubs: true, allowDataProperties: false, mappedClassUris, mappedPropertyUris })

  // Simplified initialization state
  const rebuildCounter = useRef(0)

  const dataReady = (classes && classes.length > 0) || (properties && properties.length > 0)

  // Wait for data readiness when modal opens
  useEffect(() => {
    if (!open) {
      setDataWaiting(false)
      setInitialized(false)
      return
    }
    if (initialized) return
    if (dataReady) {
      // Trigger initial graph build via rebuild counter
      rebuildCounter.current += 1
      setDataWaiting(false)
    } else {
      setDataWaiting(true)
      setDebugInfo('waiting-data')
      let attempts = 0
      const maxAttempts = 60 // ~3s at 50ms
      const interval = setInterval(() => {
        attempts++
        if (classes.length > 0 || properties.length > 0) {
          clearInterval(interval)
          setDataWaiting(false)
          rebuildCounter.current += 1
        } else if (attempts >= maxAttempts) {
          clearInterval(interval)
          setDataWaiting(false)
          setLoadError('Ontology data not loaded (timeout)')
          setLoading(false)
          setDebugInfo(prev => prev + ' | data-timeout')
        }
      }, 50)
      return () => clearInterval(interval)
    }
  }, [open, dataReady, initialized, classes.length, properties.length])

  useEffect(() => {
    let cancelled = false
    if (!open) return
    // Only initialize when rebuildCounter changes AND data is ready
    if (!dataReady) return
    if (initialized && rebuildCounter.current === 0) return

    const init = async () => {
      setLoading(true)
      setLoadError(null)
      setDebugInfo('init')
      const el = ref.current
      if (!el) { setDebugInfo('no-container'); setLoading(false); return }
      const sized = await waitForContainer(el, 15, 40)
      if (!sized) { el.style.minHeight = '400px'; setDebugInfo(prev=> prev + ' | forced-height') }
      try {
        const cytoscape = getCytoscape()
        if (cancelled) return
        if (cyRef.current) { try { cyRef.current.destroy() } catch {} }
        const elements = buildElements()
        if (elements.length === 0) {
          const fallbackNodes = (classes || []).slice(0,3).map(c => ({ data:{ id:String(c.uri), label: c.label || String(c.uri).split('#').pop(), type:'class' }}))
          elements.push(...fallbackNodes)
        }
        cyRef.current = cytoscape({
          container: el,
          elements,
          style: [
            { selector: 'node[type="class"][coverage = "mapped"]', style: { 'background-color': '#2e7d32' } },
            { selector: 'node[type="class"][coverage = "unmapped"]', style: { 'background-color': '#455a64' } },
            { selector: 'node[type="class"]', style: { 'label': 'data(label)', 'color': '#fff', 'font-size': 12, 'text-wrap':'wrap', 'text-max-width': 160, 'padding':'6px', 'shape':'round-rectangle', 'text-valign':'center', 'text-halign':'center', 'font-weight':'500' } },
            { selector: 'node[stub = "true"]', style: { 'opacity':0.55 } },
            { selector: 'edge[type="property"]', style: { 'line-color':'#757575', 'width':2, 'target-arrow-shape':'triangle', 'target-arrow-color':'#757575', 'curve-style':'bezier', 'label':'data(label)', 'font-size':10, 'color':'#222', 'text-background-color':'#fafafa', 'text-background-opacity':0.9, 'text-background-shape':'round-rectangle', 'text-border-color':'#ccc', 'text-border-width':1, 'text-wrap':'wrap', 'text-max-width':140 } },
            { selector: 'node:selected', style: { 'border-color':'#ff9800', 'border-width':3 } },
            { selector: 'edge:selected', style: { 'line-color':'#ff9800', 'target-arrow-color':'#ff9800', 'width':3 } }
          ],
          layout: { name: 'cola', maxSimulationTime: 800, fit: true, padding: 32 }
        })
        ;(window as any).cyOntology = cyRef.current
        setDebugInfo(prev => prev + ` | elements=${cyRef.current.elements().length}`)
        setInitialized(true)
        setTimeout(()=> { if(!cancelled){ setLoading(false); setDebugInfo(p=> p + ' | t1') } }, 850)
        setTimeout(()=> { if(!cancelled && loading){ setLoading(false); setDebugInfo(p=> p + ' | t2-force-clear') } }, 1500)
      } catch(e:any) {
        setLoadError(e.message || 'init failed')
        setLoading(false)
        setDebugInfo(prev=> prev + ' | error')
      }
    }
    init()
    return () => { cancelled = true }
  }, [open, rebuildCounter.current, dataReady])

  // Update elements when classes/properties change while open
  useEffect(() => {
    if (!open) return
    if (!cyRef.current) return
    try {
      const cy = cyRef.current
      const updated = buildOntologyElements(classes as any, properties as any, { maxClasses: 120, maxProperties: 300, includeStubs: true })
      cy.batch(()=>{ cy.elements().remove(); cy.add(updated) })
      cy.layout({ name:'cola', maxSimulationTime: 500, fit:true, padding:30 }).run()
      cy.resize(); cy.fit();
      setDebugInfo(prev=> prev + ` | update=${updated.length}`)
    } catch(e:any) {
      setLoadError(e.message || 'update failed')
      setDebugInfo(prev=> prev + ' | update-error')
    } finally {
      setLoading(false)
    }
  }, [classes, properties, open])

  const forceRebuild = () => {
    if (!open) return
    rebuildCounter.current += 1
    setDebugInfo('force-rebuild')
    if (cyRef.current) { try { cyRef.current.destroy() } catch {} cyRef.current = null }
    setLoading(true)
  }

  return (
    <Dialog fullScreen open={open} onClose={onClose}>
      <DialogTitle sx={{ pr: 6 }}>
        Ontology Graph
        <IconButton onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8 }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        {loadError && (
          <Box sx={{ mb: 2 }}>
            <Typography color="error" variant="body2">{loadError}</Typography>
          </Box>
        )}
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ height: '100%' }}>
          <Box sx={{ flex: 3, minHeight: 400, position: 'relative' }}>
            {(dataWaiting && !loadError) && (
              <Box sx={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', bgcolor:'rgba(255,255,255,0.6)', zIndex:2 }}>
                <Typography variant='body2'>Waiting for ontology data…</Typography>
                <Typography variant='caption' sx={{ mt:1 }}>{debugInfo}</Typography>
              </Box>
            )}
            {loading && !dataWaiting && (
              <Box sx={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', bgcolor:'rgba(255,255,255,0.6)', zIndex:1 }}>
                <Typography variant="body2">Building graph…</Typography>
              </Box>
            )}
            {(!loading && !loadError && cyRef.current && cyRef.current.elements().length === 0) && (
              <Box sx={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', zIndex:1 }}>
                <Typography variant="body2" color="text.secondary">No connectable properties found (domain/range mismatch).</Typography>
              </Box>
            )}
            {loadError && (
              <Box sx={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', p:2 }}>
                <Typography variant="body2" color="error">{loadError}</Typography>
              </Box>
            )}
            <Box ref={ref} sx={{ width:'100%', height:'100%', border:'1px solid', borderColor:'divider', borderRadius:1, position:'relative' }} />
            {!loading && debugInfo && (
              <Typography variant='caption' sx={{ position:'absolute', left:8, bottom:8, color:'rgba(255,255,255,0.6)' }}>debug: {debugInfo}</Typography>
            )}
          </Box>
          <Box sx={{ flex: 1, minHeight: 400, overflow: 'auto' }}>
            <Typography variant="subtitle1" gutterBottom>Legend</Typography>
            <Chip label="Class" size="small" sx={{ bgcolor: '#0288d1', color: '#fff', mr: 1 }} />
            <Chip label="Property edge" size="small" variant="outlined" sx={{ mr: 1 }} />
            <Typography variant="subtitle2" sx={{ mt: 2 }}>Usage</Typography>
            <Typography variant="caption" sx={{ display: 'block', mb: 1 }}>Drag to explore. Click a node to highlight connected properties.</Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>Future enhancements: mapping coverage coloring, property search, alternate suggestions.</Typography>
          </Box>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

export default OntologyGraphModal;
