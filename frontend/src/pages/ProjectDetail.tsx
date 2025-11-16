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
            const cols = Object.keys(s.columns || {}).length
            const objs = Object.keys(s.objects || {}).length
            stats.total_columns += cols + objs
            stats.mapped_columns += cols + objs
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
            <Stack direction="row" spacing={4} sx={{ mb:1 }}>
              <Typography variant="body2">Classes: <strong>{ontology.data.total_classes}</strong></Typography>
              <Typography variant="body2">Properties: <strong>{ontology.data.total_properties}</strong></Typography>
            </Stack>
            {/* Optional: show first few classes/properties */}
            {ontology.data.classes?.length > 0 && (
              <Box sx={{ mt:1 }}>
                <Typography variant="subtitle2">Sample Classes</Typography>
                <Typography variant="caption" color="text.secondary">
                  {ontology.data.classes.slice(0,5).map((c:any)=>c.label || c.uri).join(', ')}
                </Typography>
              </Box>
            )}
            {ontology.data.properties?.length > 0 && (
              <Box sx={{ mt:1 }}>
                <Typography variant="subtitle2">Sample Properties</Typography>
                <Typography variant="caption" color="text.secondary">
                  {ontology.data.properties.slice(0,5).map((p:any)=>p.label || p.uri).join(', ')}
                </Typography>
              </Box>
            )}
          </Paper>
        )}

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
          {convertSync.data?.validation || convertSync.data?.shacl_validation ? (
            <Paper sx={{ p:2, mt:2 }} variant="outlined">
              <Typography variant="subtitle1" gutterBottom>Validation</Typography>
              {convertSync.data?.validation && (
                <Box sx={{ mb:1 }}>
                  <Typography variant="body2"><strong>Ontology validation:</strong></Typography>
                  {convertSync.data.validation.status === 'skipped' && (
                    <Alert severity="info" sx={{ mt:1 }}>Validation skipped: {convertSync.data.validation.reason}</Alert>
                  )}
                  {convertSync.data.validation.status === 'error' && (
                    <Alert severity="error" sx={{ mt:1 }}>Validation error: {convertSync.data.validation.error}</Alert>
                  )}
                  {convertSync.data.validation.conforms !== undefined && (
                    <Alert severity={convertSync.data.validation.conforms ? 'success' : 'warning'} sx={{ mt:1 }}>
                      SHACL conforms (Ontology constraints): {String(convertSync.data.validation.conforms)}
                    </Alert>
                  )}
                </Box>
              )}
              {convertSync.data?.shacl_validation && (
                <Box>
                  <Typography variant="body2"><strong>SHACL shapes validation:</strong></Typography>
                  {convertSync.data.shacl_validation.status === 'skipped' && (
                    <Alert severity="info" sx={{ mt:1 }}>Validation skipped: {convertSync.data.shacl_validation.reason}</Alert>
                  )}
                  {convertSync.data.shacl_validation.status === 'error' && (
                    <Alert severity="error" sx={{ mt:1 }}>Validation error: {convertSync.data.shacl_validation.error}</Alert>
                  )}
                  {convertSync.data.shacl_validation.conforms !== undefined && (
                    <Alert severity={convertSync.data.shacl_validation.conforms ? 'success' : 'warning'} sx={{ mt:1 }}>
                      SHACL conforms (Uploaded shapes): {String(convertSync.data.shacl_validation.conforms)}
                    </Alert>
                  )}
                </Box>
              )}
            </Paper>
          ) : null}

          {/* Ontology Structural Validation */}
          {convertSync.data?.ontology_structural_validation && (
            <Paper sx={{ p:2, mt:2 }} variant="outlined">
              <Typography variant="subtitle2" gutterBottom>Ontology Structural Validation</Typography>
              {convertSync.data.ontology_structural_validation.status === 'error' && (
                <Alert severity="error">Structural validation error: {convertSync.data.ontology_structural_validation.error}</Alert>
              )}
              {convertSync.data.ontology_structural_validation.status === 'completed' && (
                <Stack spacing={1}>
                  <Alert severity={convertSync.data.ontology_structural_validation.compliance_rate === 1.0 ? 'success' : 'warning'}>
                    Compliance rate: {(convertSync.data.ontology_structural_validation.compliance_rate*100).toFixed(2)}%
                  </Alert>
                  <Typography variant="caption" color="text.secondary">
                    Domain violations: {convertSync.data.ontology_structural_validation.domain_violations} • Range violations: {convertSync.data.ontology_structural_validation.range_violations}
                  </Typography>
                  {(convertSync.data.ontology_structural_validation.violations.domain_samples.length > 0 || convertSync.data.ontology_structural_validation.violations.range_samples.length > 0) && (
                    <Box sx={{ mt:1 }}>
                      <Typography variant="caption" color="text.secondary">Samples:</Typography>
                      <Typography variant="caption" sx={{ display:'block' }}>
                        {convertSync.data.ontology_structural_validation.violations.domain_samples.join('; ')}
                      </Typography>
                      <Typography variant="caption" sx={{ display:'block' }}>
                        {convertSync.data.ontology_structural_validation.violations.range_samples.join('; ')}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              )}
            </Paper>
          )}
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
        {mappingInfo && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Mapping Summary</Typography>
            <Typography variant="body2" sx={{ mb:2 }}>
              <strong>All columns mapped: {mappingInfo.stats.mapped_columns}/{mappingInfo.stats.total_columns} ({mappingInfo.stats.mapping_rate?.toFixed(1)}%)</strong>
            </Typography>
            {mappingInfo.sheets.map(s => (
              <Box key={s.sheet} sx={{ mb:2 }}>
                <Chip label={s.sheet || 'Sheet'} size="small" sx={{ mr:1 }} />
                <Typography variant="body2" sx={{ ml: 3, mt: 1 }}>
                  • Data properties: {s.direct_mappings?.length || 0} ({s.direct_mappings?.join(', ') || 'none'})
                </Typography>
                <Typography variant="body2" sx={{ ml: 3 }}>
                  • Object properties: {s.object_properties || 0} linked objects
                </Typography>
                <Typography variant="body2" sx={{ ml: 3 }}>
                  • Object data properties: {s.object_data_properties?.length || 0} ({s.object_data_properties?.join(', ') || 'none'})
                </Typography>
              </Box>
            ))}
            <Typography variant="caption" color="text.secondary" sx={{ display:'block', mt:2 }}>
              💡 Object properties (e.g., BorrowerID, PropertyID) are foreign keys that link to other entities.
            </Typography>
          </Paper>
        )}

        {mappingInfo?.matchDetails && mappingInfo.matchDetails.length > 0 && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Match Reasons</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb:2 }}>
              Detailed explanation of how each column was matched to an ontology property
            </Typography>
            <TableContainer sx={{ maxHeight: 400 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Column</strong></TableCell>
                    <TableCell><strong>Property</strong></TableCell>
                    <TableCell><strong>Match Type</strong></TableCell>
                    <TableCell><strong>Matcher</strong></TableCell>
                    <TableCell><strong>Matched Via</strong></TableCell>
                    <TableCell align="right"><strong>Confidence</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mappingInfo.matchDetails.map((detail:any, idx:number) => {
                    const propShort = detail.matched_property?.split('#').pop()?.split('/').pop() || detail.matched_property
                    const confColor = detail.confidence_score >= 0.8 ? 'success.main' : detail.confidence_score >= 0.5 ? 'warning.main' : 'error.main'
                    const matchTypeLabel = detail.match_type?.replace(/_/g, ' ').replace(/\b\w/g, (l:string) => l.toUpperCase())
                    return (
                      <TableRow key={idx} hover>
                        <TableCell><strong>{detail.column_name}</strong></TableCell>
                        <TableCell><code style={{ fontSize:'0.85em' }}>{propShort}</code></TableCell>
                        <TableCell><Chip label={matchTypeLabel} size="small" sx={{ fontSize:'0.7em' }} /></TableCell>
                        <TableCell>{detail.matcher_name}</TableCell>
                        <TableCell><em style={{ color:'#666' }}>{detail.matched_via}</em></TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ color: confColor, fontWeight:'bold' }}>
                            {detail.confidence_score?.toFixed(2)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )}

        {mappingYamlQuery.data && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Mapping YAML</Typography>
            <Box sx={{ maxHeight: 300, overflow: 'auto', fontSize: '12px', bgcolor:'#111', color:'#eee', p:2, borderRadius:1 }}>
              <pre style={{ margin:0 }}>{mappingYamlQuery.data}</pre>
            </Box>
          </Paper>
        )}

        {generate.data?.alignment_report && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Alignment Report</Typography>
            <Typography variant="body2" sx={{ mb:1 }}>
              Success rate: {(generate.data.alignment_report.statistics?.mapping_success_rate*100 || 0).toFixed(1)}% • Avg confidence: {(generate.data.alignment_report.statistics?.average_confidence || 0).toFixed(2)}
            </Typography>
            <Typography variant="body2" sx={{ mb:1 }}>
              Weak matches: {generate.data.alignment_report.weak_matches?.length || 0} • Unmapped: {generate.data.alignment_report.unmapped_columns?.length || 0}
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/files/${projectId}/alignment_report.json`}>
                Download JSON
              </Button>
              <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/files/${projectId}/alignment_report.html`}>
                Download HTML
              </Button>
              <Button variant="outlined" size="small" startIcon={<DownloadIcon />} href={`/api/mappings/${projectId}?raw=true`}>
                Download YAML
              </Button>
            </Stack>
          </Paper>
        )}

        {convertSync.data?.reasoning && (
          <Paper sx={{ p:3 }}>
            <Typography variant="h6" gutterBottom>Reasoning Metrics</Typography>
            <Stack direction="row" spacing={3} sx={{ flexWrap:'wrap', mb:2 }}>
              <Chip label={`Inferred types: ${convertSync.data.reasoning.inferred_types}`} size="small" />
              <Chip label={`Inverse links: ${convertSync.data.reasoning.inverse_links_added}`} size="small" />
              <Chip label={`Transitive links: ${convertSync.data.reasoning.transitive_links_added}`} size="small" />
              <Chip label={`Symmetric links: ${convertSync.data.reasoning.symmetric_links_added}`} size="small" />
              <Chip label={`Functional cardinality violations: ${convertSync.data.reasoning.cardinality_violations}`} size="small" color={convertSync.data.reasoning.cardinality_violations>0?'warning':'default'} />
              <Chip label={`Min card violations: ${convertSync.data.reasoning.min_cardinality_violations}`} size="small" color={convertSync.data.reasoning.min_cardinality_violations>0?'warning':'default'} />
              <Chip label={`Max card violations: ${convertSync.data.reasoning.max_cardinality_violations}`} size="small" color={convertSync.data.reasoning.max_cardinality_violations>0?'warning':'default'} />
              <Chip label={`Exact card violations: ${convertSync.data.reasoning.exact_cardinality_violations}`} size="small" color={convertSync.data.reasoning.exact_cardinality_violations>0?'warning':'default'} />
            </Stack>
            <Typography variant="caption" color="text.secondary">Reasoning expands your graph using ontology semantics (subclass, inverse, symmetric, transitive). Cardinality violations highlight constraint issues.</Typography>
          </Paper>
        )}
      </Stack>
    </Box>
  )
}

