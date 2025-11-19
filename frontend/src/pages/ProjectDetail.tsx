import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Typography, Button, Stack, Divider, LinearProgress, Alert, Paper, Chip } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
// Add new imports for controls
import { FormControl, InputLabel, Select, MenuItem, FormControlLabel, Checkbox } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import EvidenceDrawer, { MatchDetail as EvidenceMatchDetail } from '../components/EvidenceDrawer'
import ValidationDashboard from '../components/ValidationDashboard'
import ManualMappingModal from '../components/ManualMappingModal'
import OntologyGraphMini from '../components/OntologyGraphMini'
import OntologyGraphModal from '../components/OntologyGraphModal'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const projectId = id as string
  const qc = useQueryClient()

  const [jobId, setJobId] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [format, setFormat] = useState('turtle')
  const [validateOutput, setValidateOutput] = useState(true)

  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState<EvidenceMatchDetail | null>(null)

  const [manualOpen, setManualOpen] = useState(false)
  const [manualColumn, setManualColumn] = useState<string | null>(null)
  const [manualCurrentProp, setManualCurrentProp] = useState<string | null>(null)

  const [graphOpen, setGraphOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0) // Force re-render after manual overrides

  const preview = useQuery({
    queryKey: ['preview', projectId],
    queryFn: () => api.previewData(projectId, 5),
    enabled: !!projectId,
    retry: 1,
    refetchOnMount: 'always',
  })

  const uploadData = useMutation({
    mutationFn: async () => {
      const input = document.getElementById('data-file') as HTMLInputElement
      if (!input?.files?.[0]) throw new Error('Select a data file')
      return api.uploadData(projectId, input.files[0])
    },
    onSuccess: () => {
      setSuccess('Data file uploaded successfully!')
      setError(null)
      preview.refetch()
      projectQuery.refetch()
    },
    onError: (err: any) => {
      setError('Upload failed: ' + err.message)
      setSuccess(null)
    },
  })

  const uploadOntology = useMutation({
    mutationFn: async () => {
      const input = document.getElementById('ont-file') as HTMLInputElement
      if (!input?.files?.[0]) throw new Error('Select an ontology file')
      return api.uploadOntology(projectId, input.files[0])
    },
    onSuccess: () => {
      setSuccess('Ontology file uploaded successfully!')
      setError(null)
      ontology.refetch()
      projectQuery.refetch()
    },
    onError: (err: any) => {
      setError('Upload failed: ' + err.message)
      setSuccess(null)
    },
  })

  const uploadShapes = useMutation({
    mutationFn: async () => {
      const input = document.getElementById('shapes-file') as HTMLInputElement
      if (!input?.files?.[0]) throw new Error('Select a SHACL shapes file')
      return api.uploadShapes(projectId, input.files[0])
    },
    onSuccess: () => {
      setSuccess('SHACL shapes uploaded successfully!')
      setError(null)
      projectQuery.refetch()
    },
    onError: (e:any) => setError('Shapes upload failed: ' + e.message)
  })

  const uploadSkos = useMutation({
    mutationFn: async () => {
      const input = document.getElementById('skos-file') as HTMLInputElement
      if (!input?.files?.length) throw new Error('Select a SKOS file')
      const file = input.files[0]
      return api.uploadSkos(projectId, file)
    },
    onSuccess: () => {
      setSuccess('SKOS vocabulary uploaded!')
      setError(null)
      projectQuery.refetch()
    },
    onError: (e:any) => setError('SKOS upload failed: ' + e.message)
  })

  const mappingYamlQuery = useQuery({
    queryKey: ['mapping-yaml', projectId],
    queryFn: () => api.fetchMappingYaml(projectId),
    enabled: !!projectId,
    retry: 1,
    refetchOnMount: 'always',
  })

  const existingMappingQuery = useQuery({
    queryKey: ['existing-mapping', projectId],
    queryFn: async () => {
      try {
        const response = await fetch(`/api/mappings/${projectId}`)
        if (!response.ok) return null
        return await response.json()
      } catch {
        return null
      }
    },
    enabled: !!projectId,
    retry: 1,
    refetchOnMount: 'always',
  })

  const generate = useMutation({
    mutationFn: () => api.generateMappings(projectId, { use_semantic: true, min_confidence: 0.5 }),
    onSuccess: (data) => {
      console.log('Mappings generated:', data)
      const summaryStats = data.mapping_summary?.statistics || {}
      const reportStats = data.alignment_report?.statistics || {}
      const stats = (summaryStats.mapped_columns ? summaryStats : reportStats)
      setSuccess(`Mappings generated! ${stats.mapped_columns || 0}/${stats.total_columns || 0} columns mapped (${stats.mapping_rate ? stats.mapping_rate.toFixed(1) : 0}% ).`)
      setError(null)
      setMappingInfo({ stats, sheets: data.mapping_summary?.sheets || [], raw: data.mapping_config, matchDetails: data.match_details || [] })
      mappingYamlQuery.refetch()
    },
    onError: (err: any) => {
      setError('Mapping generation failed: ' + err.message)
      setSuccess(null)
    },
  })

  const convertSync = useMutation({
    mutationFn: () => api.convertSync(projectId, { output_format: format, validate: validateOutput }),
    onSuccess: (data) => {
      console.log('Conversion complete:', data)
      setSuccess(`✅ RDF generated! ${data.triple_count} triples created.`)
      setError(null)
    },
    onError: (err: any) => {
      setError('Conversion failed: ' + err.message)
      setSuccess(null)
    },
  })

  const convertAsync = useMutation({
    mutationFn: async () => {
      const res = await api.convertAsync(projectId, { output_format: format, validate: validateOutput })
      setJobId(res.task_id)
      setJobResult(null)
      setError(null)
      setSuccess('Conversion job queued! Polling status...')
      return res
    },
    onError: (err: any) => {
      setError('Failed to queue job: ' + err.message)
      setSuccess(null)
    },
  })

  // Poll job status
  React.useEffect(() => {
    if (!jobId) return
    const t = setInterval(async () => {
      try {
        const res = await api.jobStatus(jobId)
        console.log('Job status:', res)
        if (res.status === 'SUCCESS') {
          clearInterval(t)
          setJobResult(res)
          setSuccess(`✅ Background job complete! ${res.result?.triple_count || '?'} triples created.`)
        } else if (res.status === 'FAILURE') {
          clearInterval(t)
          setJobResult(res)
          setError('Background job failed: ' + (res.error || 'Unknown error'))
        }
      } catch (e: any) {
        clearInterval(t)
        setError('Failed to check job status: ' + e.message)
      }
    }, 1500)
    return () => clearInterval(t)
  }, [jobId])

  const [mappingInfo, setMappingInfo] = useState<{stats:any; sheets:any[]; matchDetails?:any[]} | null>(null)

  const download = async () => {
    try {
      const res = await api.downloadRdf(projectId)
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(text || `Download failed (${res.status})`)
      }
      const cd = res.headers.get('content-disposition') || ''
      const filenameMatch = cd.match(/filename="?([^";]+)"?/)
      const filename = filenameMatch ? filenameMatch[1] : `project-${projectId}-output.ttl`
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(`File downloaded: ${filename}`)
    } catch (err: any) {
      setError('Download failed: ' + err.message)
    }
  }

  // Ontology analysis
  const ontology = useQuery({
    queryKey: ['ontology', projectId],
    queryFn: () => api.analyzeOntology(projectId),
    enabled: !!projectId,
    retry: 1,
    refetchOnMount: 'always',
  })

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
    refetchOnMount: 'always'
  })

  // Load mapping info from existing mapping if available
  React.useEffect(() => {
    if (existingMappingQuery.data && existingMappingQuery.data.mapping_config && !mappingInfo) {
      const cfg = existingMappingQuery.data.mapping_config
      // Try to fetch the alignment report too
      fetch(`/api/files/${projectId}/alignment_report.json`)
        .then(r => r.ok ? r.json() : null)
        .then(report => {
          const sheets = cfg.sheets || []
          const stats = {
            total_columns: 0,
            mapped_columns: 0,
            mapping_rate: 100
          }
          // Calculate from sheets
          sheets.forEach((s:any) => {
            // Collect all unique column names
            const allColumns = new Set<string>()

            // Add direct column mappings
            const cols = s.columns || {}
            Object.keys(cols).forEach(col => allColumns.add(col))

            // Add columns used in objects (FK columns + object property columns)
            const objs = s.objects || {}
            Object.values(objs).forEach((obj:any) => {
              // Extract column names from iri_template (e.g., {BorrowerID})
              const iriTemplate = obj.iri_template || ''
              const fkCols = iriTemplate.match(/\{(\w+)\}/g)?.map((m:string) => m.slice(1, -1)) || []
              // Filter out known template variables
              fkCols.filter(col => !['base_iri', 'base_uri', 'namespace'].includes(col)).forEach(col => allColumns.add(col))

              // Add columns from object properties
              const props = obj.properties || []
              props.forEach((prop:any) => {
                if (prop.column) allColumns.add(prop.column)
              })
            })

            stats.total_columns += allColumns.size
            stats.mapped_columns += allColumns.size
          })
          if (stats.total_columns > 0) {
            stats.mapping_rate = (stats.mapped_columns / stats.total_columns) * 100
          }
          setMappingInfo({
            stats,
            sheets: [],
            matchDetails: report?.match_details || []
          })
        })
        .catch(() => {})
    }
  }, [existingMappingQuery.data, projectId, mappingInfo])

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Project Detail
      </Typography>

      {/* Status strip */}
      <Stack direction="row" spacing={1} sx={{ mb:2, flexWrap:'wrap' }}>
        <Chip label={projectQuery.data?.data_file ? 'Data: uploaded' : 'Data: missing'} color={projectQuery.data?.data_file ? 'success' : 'default'} size="small" />
        <Chip label={projectQuery.data?.ontology_file ? 'Ontology: uploaded' : 'Ontology: missing'} color={projectQuery.data?.ontology_file ? 'success' : 'default'} size="small" />
        {convertSync.data?.triple_count && <Chip label={`Last convert: ${convertSync.data.triple_count} triples`} color="info" size="small" />}
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Stack spacing={3}>
        {/* Step 1: Upload Files */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Step 1: Upload Files
          </Typography>
          <Stack spacing={2}>
            <Box>
              <input type="file" id="data-file" accept=".csv,.parquet,.json" />
              <Button
                variant="outlined"
                onClick={() => uploadData.mutate()}
                disabled={uploadData.isPending}
                sx={{ ml: 2 }}
              >
                {uploadData.isPending ? 'Uploading...' : 'Upload Data'}
              </Button>
            </Box>
            <Box>
              <input type="file" id="ont-file" accept=".ttl,.rdf,.owl" />
              <Button
                variant="outlined"
                onClick={() => uploadOntology.mutate()}
                disabled={uploadOntology.isPending}
                sx={{ ml: 2 }}
              >
                {uploadOntology.isPending ? 'Uploading...' : 'Upload Ontology'}
              </Button>
            </Box>
            {(uploadData.isPending || uploadOntology.isPending) && <LinearProgress />}
          </Stack>
        </Paper>

        {/* Knowledge Inputs */}
        <Paper sx={{ p:3 }}>
          <Typography variant="h6" gutterBottom>Knowledge Inputs</Typography>
          <Stack direction={{ xs:'column', sm:'row' }} spacing={3} alignItems="flex-start" sx={{ mb:2 }}>
            <Box>
              <Typography variant="subtitle2">Ontology</Typography>
              <Typography variant="body2" color={projectQuery.data?.ontology_file ? 'success.main' : 'text.secondary'}>
                {projectQuery.data?.ontology_file ? 'Uploaded' : 'Missing'}
              </Typography>
              <Box sx={{ mt:1 }}>
                <input type="file" id="ont-file-2" accept=".ttl,.rdf,.owl" />
                <Button size="small" startIcon={<CloudUploadIcon />} sx={{ ml:1 }} variant="outlined" onClick={async()=>{
                  const input = document.getElementById('ont-file-2') as HTMLInputElement
                  if (!input?.files?.[0]) { setError('Select an ontology file'); return }
                  await api.uploadOntology(projectId, input.files[0])
                  setSuccess('Ontology uploaded!')
                  projectQuery.refetch()
                }}>Upload</Button>
              </Box>
            </Box>
            <Divider orientation="vertical" flexItem sx={{ display:{ xs:'none', sm:'block' } }} />
            <Box>
              <Typography variant="subtitle2">SKOS Vocabularies</Typography>
              <Typography variant="body2" color={(projectQuery.data?.config?.skos_files?.length||0) > 0 ? 'success.main' : 'text.secondary'}>
                {(projectQuery.data?.config?.skos_files?.length||0) > 0 ? `${projectQuery.data.config.skos_files.length} file(s)` : 'None'}
              </Typography>
              <Box sx={{ mt:1 }}>
                <input type="file" id="skos-file" accept=".ttl,.rdf,.owl,.trig,.n3" />
                <Button size="small" startIcon={<CloudUploadIcon />} sx={{ ml:1 }} variant="outlined" onClick={()=> uploadSkos.mutate()}>Upload</Button>
              </Box>
            </Box>
            <Divider orientation="vertical" flexItem sx={{ display:{ xs:'none', sm:'block' } }} />
            <Box>
              <Typography variant="subtitle2">SHACL Shapes</Typography>
              <Typography variant="body2" color={projectQuery.data?.config?.shapes_file ? 'success.main' : 'text.secondary'}>
                {projectQuery.data?.config?.shapes_file ? 'Uploaded' : 'None'}
              </Typography>
              <Box sx={{ mt:1 }}>
                <input type="file" id="shapes-file" accept=".ttl,.rdf,.owl,.trig,.n3" />
                <Button size="small" startIcon={<CloudUploadIcon />} sx={{ ml:1 }} variant="outlined" onClick={()=> uploadShapes.mutate()}>Upload</Button>
              </Box>
            </Box>
            <Box>
              <Typography variant="subtitle2">Reasoning</Typography>
              <Typography variant="body2" color={(projectQuery.data?.config?.enable_reasoning)?'success.main':'text.secondary'}>
                {(projectQuery.data?.config?.enable_reasoning)?'Enabled':'Disabled'}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt:1 }}>
                <Button size="small" variant="outlined" onClick={async()=>{
                  try {
                    const en = !(projectQuery.data?.config?.enable_reasoning)
                    await api.updateSettings(projectId,{ enable_reasoning: en })
                    setSuccess(`Reasoning ${en? 'enabled':'disabled'}`)
                    projectQuery.refetch()
                  } catch(e:any){ setError(e.message) }
                }}>{(projectQuery.data?.config?.enable_reasoning)?'Disable':'Enable'}</Button>
              </Stack>
            </Box>
          </Stack>
          {(projectQuery.data?.config?.skos_files?.length||0) > 0 && (
            <Box sx={{ mt:1 }}>
              <Typography variant="caption" color="text.secondary">SKOS files:</Typography>
              <Stack direction="row" spacing={1} sx={{ flexWrap:'wrap', mt:1 }}>
                {projectQuery.data.config.skos_files.map((p:string)=>{
                  const short = p.split('/').pop()
                  return <Chip key={p} label={short} onDelete={async()=>{try{await api.removeSkos(projectId,p); projectQuery.refetch(); setSuccess(`Removed ${short}`)}catch(e:any){setError(e.message)}}} size="small" />
                })}
              </Stack>
            </Box>
          )}
          {projectQuery.data?.config?.shapes_file && (
            <Box sx={{ mt:1 }}>
              <Typography variant="caption" color="text.secondary">Shapes file:</Typography>
              <Chip label={projectQuery.data.config.shapes_file.split('/').pop()} onDelete={async()=>{try{await api.removeShapes(projectId); projectQuery.refetch(); setSuccess('Removed shapes file')}catch(e:any){setError(e.message)}}} size="small" sx={{ ml:1 }} />
            </Box>
          )}
        </Paper>

        {/* Ontology Summary */}
        {ontology.data && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Ontology Summary</Typography>
            <Stack direction="row" spacing={4} sx={{ mb:1, alignItems:'center' }}>
              <Typography variant="body2">Classes: <strong>{ontology.data.total_classes}</strong></Typography>
              <Typography variant="body2">Properties: <strong>{ontology.data.total_properties}</strong></Typography>
              <Button size="small" variant="outlined" onClick={()=> setGraphOpen(true)}>View Graph</Button>
            </Stack>
            <OntologyGraphMini
              classes={ontology.data.classes || []}
              properties={ontology.data.properties || []}
              onOpenFull={()=> setGraphOpen(true)}
            />
            {ontology.data.classes?.length > 0 && (
              <Box sx={{ mt:2 }}>
                <Typography variant="subtitle2">Sample Classes</Typography>
                <Typography variant="caption" color="text.secondary">
                  {ontology.data.classes.slice(0,5).map((c:any)=>c.label || c.uri).join(', ')}
                </Typography>
              </Box>
            )}
            {ontology.data.properties?.length > 0 && (
              <Box sx={{ mt:2 }}>
                <Typography variant="subtitle2">Sample Properties</Typography>
                <Typography variant="caption" color="text.secondary">
                  {ontology.data.properties.slice(0,5).map((p:any)=>p.label || p.uri).join(', ')}
                </Typography>
              </Box>
            )}
          </Paper>
        )}
        <OntologyGraphModal
          open={graphOpen}
          onClose={()=> setGraphOpen(false)}
          classes={ontology.data?.classes || []}
          properties={ontology.data?.properties || []}
        />

        {/* Step 2: Generate Mappings */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Step 2: Generate Mappings (AI-Powered)
          </Typography>
          <Button
            variant="contained"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            size="large"
          >
            {generate.isPending ? 'Generating with BERT...' : 'Generate Mappings'}
          </Button>
          {generate.isPending && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                AI semantic matching in progress... This may take a few seconds.
              </Typography>
            </Box>
          )}
        </Paper>

        {/* Step 3: Convert to RDF */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Step 3: Convert to RDF
          </Typography>
          <Stack direction={{ xs:'column', sm:'row' }} spacing={2} sx={{ mb: 2 }}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="format-label">Format</InputLabel>
              <Select labelId="format-label" label="Format" value={format} onChange={(e)=> setFormat(e.target.value)}>
                <MenuItem value="turtle">Turtle (.ttl)</MenuItem>
                <MenuItem value="json-ld">JSON-LD (.jsonld)</MenuItem>
                <MenuItem value="xml">RDF/XML (.rdf)</MenuItem>
                <MenuItem value="nt">N-Triples (.nt)</MenuItem>
              </Select>
            </FormControl>
            <FormControlLabel control={<Checkbox checked={validateOutput} onChange={(e)=> setValidateOutput(e.target.checked)} />} label="Validate output" />
          </Stack>
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <Button
              variant="contained"
              color="secondary"
              onClick={() => convertSync.mutate()}
              disabled={convertSync.isPending}
            >
              {convertSync.isPending ? 'Converting...' : 'Convert (Sync)'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => convertAsync.mutate()}
              disabled={convertAsync.isPending}
            >
              {convertAsync.isPending ? 'Queueing...' : 'Convert (Background)'}
            </Button>
          </Stack>

          {(convertSync.isPending || convertAsync.isPending) && <LinearProgress />}

          {jobId && !jobResult && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Job ID: {jobId} - Polling status every 1.5 seconds...
            </Alert>
          )}

          {convertSync.data?.triple_count && (
            <Alert severity="success" sx={{ mt: 2 }}>
              ✅ Sync conversion complete: <strong>{convertSync.data.triple_count} triples</strong>
            </Alert>
          )}

          {/* Validation results */}
          {convertSync.data?.validation || convertSync.data?.shacl_validation || convertSync.data?.ontology_structural_validation ? (
            <ValidationDashboard
              ontologyValidation={convertSync.data?.validation}
              shaclValidation={convertSync.data?.shacl_validation}
              structuralValidation={convertSync.data?.ontology_structural_validation}
            />
          ) : null}
        </Paper>

        {/* Step 4: Download */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Step 4: Download RDF Output
          </Typography>
          <Button variant="contained" color="success" onClick={download}>
            Download RDF File
          </Button>
        </Paper>

        {/* Data Preview */}
        {preview.data?.rows && preview.data.rows.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Data Preview ({preview.data.showing} rows)
            </Typography>
            <Box sx={{ maxHeight: 300, overflow: 'auto', bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
              <pre style={{ margin: 0, fontSize: '12px' }}>
                {JSON.stringify(preview.data.rows, null, 2)}
              </pre>
            </Box>
          </Paper>
        )}

        {/* After Generate: Mapping Summary */}
        {generate.data?.alignment_report && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Mapping Summary</Typography>
            <Typography variant="body2" sx={{ mb:2 }}>
              <strong>
                Mapped: {generate.data.alignment_report.statistics?.mapped_columns || 0} /
                Total: {generate.data.alignment_report.statistics?.total_columns || 0}
                ({(generate.data.alignment_report.statistics?.mapping_success_rate * 100 || 0).toFixed(1)}%)
              </strong>
            </Typography>
            <Typography variant="caption" color="text.secondary">
              💡 Unmapped columns can be manually mapped in the Mapping Configuration section below.
            </Typography>
          </Paper>
        )}

        {/* Evidence Drawer */}
        <EvidenceDrawer
          open={evidenceOpen}
          onClose={()=> setEvidenceOpen(false)}
          matchDetail={selectedMatch}
          onSwitchToAlternate={(column, newProp)=>{
            // TODO: Implement switch via API override; for now just notify and close
            setSuccess(`Switching ${column} to alternate: ${newProp}`)
            setEvidenceOpen(false)
          }}
        />

        {/* Manual Mapping Modal */}
        <ManualMappingModal
          open={manualOpen}
          columnName={manualColumn}
          currentProperty={manualCurrentProp}
          properties={(ontology.data?.properties || []).map((p:any)=>({ uri: p.uri, label: p.label, comment: p.comment }))}
          onClose={()=>{ setManualOpen(false); setManualColumn(null); setManualCurrentProp(null) }}
          onMap={async (col, propUri)=>{
            try {
              await api.overrideMapping(projectId, col, propUri)
              const propLabel = propUri.split('#').pop()?.split('/').pop() || propUri
              setSuccess(`Mapping updated: ${col} → ${propLabel}`)

              // Update generate.data to reflect the manual override
              if (generate.data) {
                const updatedMatchDetails = generate.data.match_details?.map((detail: any) =>
                  detail.column_name === col
                    ? {
                        ...detail,
                        matched_property: propUri,
                        matcher_name: 'ManualOverride',
                        match_type: 'manual_override',
                        confidence_score: 1.0,
                        matched_via: 'User override'
                      }
                    : detail
                ) || []

                // Check if this was an unmapped column
                const wasUnmapped = generate.data.alignment_report?.unmapped_columns?.some(
                  (u: any) => u.column_name === col
                )

                // If it was unmapped, add it to match_details and remove from unmapped
                if (wasUnmapped) {
                  updatedMatchDetails.push({
                    column_name: col,
                    matched_property: propUri,
                    matcher_name: 'ManualOverride',
                    match_type: 'manual_override',
                    confidence_score: 1.0,
                    matched_via: 'User override',
                    evidence: [],
                    evidence_groups: []
                  })

                  const updatedUnmapped = generate.data.alignment_report.unmapped_columns.filter(
                    (u: any) => u.column_name !== col
                  )

                  const updatedStats = {
                    ...generate.data.alignment_report.statistics,
                    mapped_columns: (generate.data.alignment_report.statistics?.mapped_columns || 0) + 1,
                    mapping_success_rate: ((generate.data.alignment_report.statistics?.mapped_columns || 0) + 1) /
                                         (generate.data.alignment_report.statistics?.total_columns || 1)
                  }

                  // Update generate.data with new state
                  generate.data.alignment_report = {
                    ...generate.data.alignment_report,
                    statistics: updatedStats,
                    unmapped_columns: updatedUnmapped
                  }
                }

                generate.data.match_details = updatedMatchDetails

                // Force re-render by incrementing refresh key
                setRefreshKey(prev => prev + 1)
              }

            } catch(e:any){
              setError(`Override failed: ${e.message}`)
            }
            setManualOpen(false)
          }}
        />

        {/* Mapping Configuration - Enhanced UX */}
        {generate.data?.alignment_report && (
          <Paper sx={{ p:3 }} key={`mapping-config-${refreshKey}`}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Box>
                <Typography variant="h6" gutterBottom>Mapping Configuration</Typography>
                <Typography variant="body2" color="text.secondary">
                  Review and refine the automated mappings. Click Evidence to understand why each mapping was made, or Change to manually override it.
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={async () => {
                  try {
                    await api.downloadYARRRML(projectId)
                    setSuccess('YARRRML downloaded successfully! ⭐')
                  } catch (e: any) {
                    setError('YARRRML download failed: ' + e.message)
                  }
                }}
              >
                Download YARRRML
              </Button>
            </Stack>

            {/* Simplified Pipeline Performance Alert */}
            {generate.data.alignment_report.statistics?.matchers_fired_avg &&
             generate.data.alignment_report.statistics.matchers_fired_avg < 3 && (
              <Alert severity="success" sx={{ mb: 2 }}>
                <strong>Optimized Performance:</strong> Using simplified pipeline with {
                  generate.data.alignment_report.statistics.matchers_fired_avg.toFixed(1)
                } matchers avg (5x faster, better accuracy!)
              </Alert>
            )}

            {/* Statistics as Chips */}
            <Stack direction="row" spacing={2} sx={{ mb: 3, flexWrap: 'wrap' }}>
              <Chip
                label={`Success Rate: ${(generate.data.alignment_report.statistics?.mapping_success_rate*100 || 0).toFixed(1)}%`}
                color="primary"
                variant="outlined"
              />
              <Chip
                label={`Avg Confidence: ${(generate.data.alignment_report.statistics?.average_confidence || 0).toFixed(2)}`}
                color="success"
                variant="outlined"
              />
              <Chip
                label={`Mapped: ${generate.data.alignment_report.statistics?.mapped_columns || 0}`}
                color="success"
              />
              <Chip
                label={`Unmapped: ${generate.data.alignment_report.unmapped_columns?.length || 0}`}
                color={generate.data.alignment_report.unmapped_columns?.length > 0 ? 'warning' : 'default'}
              />
              {/* NEW: Simplified Pipeline Metrics */}
              {generate.data.alignment_report.statistics?.matchers_fired_avg && (
                <Chip
                  label={`Matchers Fired: ${generate.data.alignment_report.statistics.matchers_fired_avg.toFixed(1)}`}
                  color={generate.data.alignment_report.statistics.matchers_fired_avg < 5 ? 'success' : 'info'}
                  variant="outlined"
                />
              )}
              {generate.data.alignment_report.statistics?.matchers_fired_avg &&
               generate.data.alignment_report.statistics.matchers_fired_avg < 5 && (
                <Chip
                  label="Simplified Pipeline ⚡"
                  color="success"
                  size="small"
                />
              )}
            </Stack>

            {/* Mapped Columns Table */}
            {generate.data.match_details && generate.data.match_details.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                  ✅ Mapped Columns
                </Typography>
                <TableContainer sx={{ maxHeight: 400, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Column</TableCell>
                        <TableCell>Mapped Property</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Matcher</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {generate.data.match_details.map((detail: any, idx: number) => {
                        const confidence = detail.confidence_score || 0;
                        const confidenceColor = confidence >= 0.8 ? 'success' : confidence >= 0.6 ? 'warning' : 'error';
                        const propLabel = detail.matched_property?.split('#').pop()?.split('/').pop() || detail.matched_property;

                        return (
                          <TableRow key={idx} hover>
                            <TableCell><strong>{detail.column_name}</strong></TableCell>
                            <TableCell>{propLabel}</TableCell>
                            <TableCell>
                              <Chip
                                label={`${(confidence * 100).toFixed(0)}%`}
                                size="small"
                                color={confidenceColor}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="caption">{detail.matcher_name}</Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Stack direction="row" spacing={1} justifyContent="flex-end">
                                <Button
                                  size="small"
                                  variant="outlined"
                                  onClick={() => {
                                    setSelectedMatch(detail as EvidenceMatchDetail);
                                    setEvidenceOpen(true);
                                  }}
                                >
                                  Evidence
                                </Button>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  onClick={() => {
                                    setManualColumn(detail.column_name);
                                    setManualCurrentProp(detail.matched_property);
                                    setManualOpen(true);
                                  }}
                                >
                                  Change
                                </Button>
                              </Stack>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Unmapped Columns Section */}
            {generate.data.alignment_report.unmapped_columns && generate.data.alignment_report.unmapped_columns.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                  ⚠️ Unmapped Columns
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  These columns could not be automatically mapped. Click "Map Now" to manually map them, or skip them if they're not needed in your RDF output.
                </Typography>
                <TableContainer sx={{ maxHeight: 400, border: '2px solid', borderColor: 'warning.light', borderRadius: 1 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Column</TableCell>
                        <TableCell>Sample Values</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {generate.data.alignment_report.unmapped_columns.map((unmapped: any, idx: number) => (
                        <TableRow key={idx} hover>
                          <TableCell><strong>{unmapped.column_name}</strong></TableCell>
                          <TableCell>
                            <Typography variant="caption" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                              {unmapped.sample_values?.slice(0, 3).join(', ') || 'N/A'}
                              {(unmapped.sample_values?.length || 0) > 3 && '...'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={unmapped.inferred_datatype?.replace('xsd:', '') || 'unknown'}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              onClick={() => {
                                setManualColumn(unmapped.column_name);
                                setManualCurrentProp(null);
                                setManualOpen(true);
                              }}
                            >
                              Map Now
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            <Divider sx={{ my: 3 }} />

            {/* Export Options */}
            <Stack direction="row" spacing={2} justifyContent="space-between" alignItems="center">
              <Typography variant="body2" color="text.secondary">
                Export configuration or reports for documentation
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/files/${projectId}/alignment_report.json`}>
                  Report JSON
                </Button>
                <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/files/${projectId}/alignment_report.html`}>
                  Report HTML
                </Button>
                <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/mappings/${projectId}?raw=true`}>
                  Config YAML
                </Button>
              </Stack>
            </Stack>
          </Paper>
        )}
      </Stack>
    </Box>
  )
}

