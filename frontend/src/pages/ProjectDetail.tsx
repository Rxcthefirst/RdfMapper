import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Typography, Button, Stack, Divider, LinearProgress, Alert, Paper, Chip, Tabs, Tab, Stepper, Step, StepLabel, StepContent, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress } from '@mui/material'
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
import MappingPreview from '../components/MappingPreview'
import NestedEntityMappingPreview from '../components/NestedEntityMappingPreview'
import AddNestedEntityModal from '../components/AddNestedEntityModal'
import ComprehensiveMappingTable, { MappingRow } from '../components/ComprehensiveMappingTable'
import EnhancedMappingModal from '../components/EnhancedMappingModal'

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
  const [mappingFormat, setMappingFormat] = useState('inline') // NEW: v2 mapping format
  const [mappingTab, setMappingTab] = useState('view') // NEW: 'view' or 'generate'

  // Stepper state
  const [activeStep, setActiveStep] = useState(0)

  // Config options state
  const [chunkSize, setChunkSize] = useState(10000)
  const [onError, setOnError] = useState('report')
  const [skipEmptyValues, setSkipEmptyValues] = useState(true)
  const [aggregateDuplicates, setAggregateDuplicates] = useState(true)

  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState<EvidenceMatchDetail | null>(null)

  const [manualOpen, setManualOpen] = useState(false)
  const [manualColumn, setManualColumn] = useState<string | null>(null)
  const [manualCurrentProp, setManualCurrentProp] = useState<string | null>(null)

  const [graphOpen, setGraphOpen] = useState(false)
  const [dataPreviewOpen, setDataPreviewOpen] = useState(false)
  const [mappingPreviewOpen, setMappingPreviewOpen] = useState(false)
  const [skosPreviewOpen, setSkosPreviewOpen] = useState(false)
  const [shapesPreviewOpen, setShapesPreviewOpen] = useState(false)
  const [addNestedEntityOpen, setAddNestedEntityOpen] = useState(false)
  const [enhancedMappingOpen, setEnhancedMappingOpen] = useState(false)
  const [selectedMappingRow, setSelectedMappingRow] = useState<MappingRow | null>(null)
  const [parentEntityIndexForNested, setParentEntityIndexForNested] = useState(0)
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

  const uploadExistingMapping = useMutation({
    mutationFn: async () => {
      const input = document.getElementById('existing-mapping-file') as HTMLInputElement
      if (!input?.files?.length) throw new Error('Select a mapping file')
      const file = input.files[0]
      return api.uploadExistingMapping(projectId, file, {
        chunk_size: chunkSize,
        on_error: onError,
        skip_empty_values: skipEmptyValues,
        aggregate_duplicates: aggregateDuplicates
      })
    },
    onSuccess: (data) => {
      setSuccess(`${data.format} mapping imported! Config created automatically.`)
      setError(null)
      mappingYamlQuery.refetch()
      projectQuery.refetch()
    },
    onError: (e:any) => setError('Import failed: ' + e.message)
  })

  const mappingYamlQuery = useQuery({
    queryKey: ['mapping-yaml', projectId],
    queryFn: () => api.fetchMappingYaml(projectId),
    enabled: !!projectId,
    retry: 1,
    refetchOnMount: 'always',
  })

  const mappingPreview = useQuery({
    queryKey: ['mappingPreview', projectId],
    queryFn: () => api.getMappingPreview(projectId, 100),
    enabled: !!projectId && !!mappingYamlQuery.data,
    retry: 1,
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
    mutationFn: () => api.generateMappings(projectId, {
      use_semantic: true,
      min_confidence: 0.5,
      output_format: mappingFormat
    }),
    onSuccess: (data) => {
      console.log('Mappings generated:', data)
      const summaryStats = data.mapping_summary?.statistics || {}
      const reportStats = data.alignment_report?.statistics || {}
      const stats = (summaryStats.mapped_columns ? summaryStats : reportStats)
      const formatLabel = mappingFormat === 'inline' ? 'v2 inline' : mappingFormat === 'rml/ttl' ? 'v2 + RML Turtle' : mappingFormat === 'rml/xml' ? 'v2 + RML RDF/XML' : 'v2 + YARRRML'
      setSuccess(`Mappings generated (${formatLabel})! ${stats.mapped_columns || 0}/${stats.total_columns || 0} columns mapped (${stats.mapping_rate ? stats.mapping_rate.toFixed(1) : 0}% ).`)
      setError(null)
      setMappingInfo({ stats, sheets: data.mapping_summary?.sheets || [], raw: data.mapping_config, matchDetails: data.match_details || [], format: data.output_format })
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
      {/* Project Header */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.dark', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          {projectQuery.data?.name || 'Project Detail'}
        </Typography>
        {projectQuery.data?.description && (
          <Typography variant="body1" sx={{ opacity: 0.9 }}>
            {projectQuery.data.description}
          </Typography>
        )}
        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
          <Chip
            label={`ID: ${projectId}`}
            size="small"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip
            label={projectQuery.data?.status || 'active'}
            size="small"
            color="success"
          />
        </Stack>
      </Paper>

      {/* Alerts */}
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

      {/* Stepper Workflow */}
      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} orientation="vertical">

          {/* STEP 1: Load Data */}
          <Step>
            <StepLabel>
              <Typography variant="h6">Load Data & Configuration</Typography>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Upload required files and configure processing options
              </Typography>

              <Stack spacing={3}>
                {/* Required Files */}
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    📁 Required Files
                  </Typography>

                  <Stack spacing={2}>
                    {/* Data File */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        📊 Data File {!projectQuery.data?.data_file && <Chip label="Required" size="small" color="error" sx={{ ml: 1 }} />}
                      </Typography>
                      {projectQuery.data?.data_file ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Chip label={projectQuery.data.data_file.split('/').pop()} color="success" />
                          <Button size="small" variant="outlined" onClick={() => setDataPreviewOpen(true)}>
                            Preview
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={async () => {
                              if (confirm('Delete data file? This cannot be undone.')) {
                                try {
                                  await api.deleteDataFile(projectId);
                                  setSuccess('Data file deleted');
                                  projectQuery.refetch();
                                } catch (e: any) {
                                  setError(`Failed to delete: ${e.message}`);
                                }
                              }
                            }}
                          >
                            Delete
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <input type="file" id="data-file" accept=".csv,.xlsx,.json,.xml" />
                          <Button
                            variant="outlined"
                            onClick={() => uploadData.mutate()}
                            disabled={uploadData.isPending}
                            startIcon={<CloudUploadIcon />}
                          >
                            Upload
                          </Button>
                        </Box>
                      )}
                    </Box>

                    {/* Ontology File */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        🎯 Ontology File {!projectQuery.data?.ontology_file && <Chip label="Required" size="small" color="error" sx={{ ml: 1 }} />}
                      </Typography>
                      {projectQuery.data?.ontology_file ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Chip label={projectQuery.data.ontology_file.split('/').pop()} color="success" />
                          <Button size="small" variant="outlined" onClick={() => setGraphOpen(true)}>
                            View Graph
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={async () => {
                              if (confirm('Delete ontology file? This cannot be undone.')) {
                                try {
                                  await api.deleteOntologyFile(projectId);
                                  setSuccess('Ontology file deleted');
                                  projectQuery.refetch();
                                  ontology.refetch();
                                } catch (e: any) {
                                  setError(`Failed to delete: ${e.message}`);
                                }
                              }
                            }}
                          >
                            Delete
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <input type="file" id="ont-file" accept=".ttl,.rdf,.owl,.n3" />
                          <Button
                            variant="outlined"
                            onClick={() => uploadOntology.mutate()}
                            disabled={uploadOntology.isPending}
                            startIcon={<CloudUploadIcon />}
                          >
                            Upload
                          </Button>
                        </Box>
                      )}
                    </Box>

                    {/* Optional: Import Existing Mapping */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        📦 Existing Mapping <Chip label="Optional" size="small" sx={{ ml: 1 }} />
                      </Typography>
                      {mappingYamlQuery.data ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Chip label="✓ Mapping loaded" color="info" />
                          {mappingPreview.data && (
                            <Chip
                              label={`${mappingPreview.data.format} format`}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => setMappingPreviewOpen(true)}
                          >
                            Preview Mapping
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={async () => {
                              if (confirm('Delete mapping file? This cannot be undone.')) {
                                try {
                                  await api.deleteMappingFile(projectId);
                                  setSuccess('Mapping file deleted');
                                  mappingYamlQuery.refetch();
                                } catch (e: any) {
                                  setError(`Failed to delete: ${e.message}`);
                                }
                              }
                            }}
                          >
                            Delete
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <input type="file" id="existing-mapping-file" accept=".ttl,.rdf,.yaml,.yml" />
                          <Button
                            variant="outlined"
                            onClick={() => uploadExistingMapping.mutate()}
                            startIcon={<CloudUploadIcon />}
                          >
                            Import RML/YARRRML
                          </Button>
                        </Box>
                      )}
                    </Box>
                  </Stack>
                </Paper>

                {/* Optional Knowledge Files */}
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    📚 Optional Knowledge Files
                  </Typography>

                  <Stack spacing={2}>
                    {/* SKOS Vocabularies */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        📖 SKOS Vocabularies <Chip label="Optional" size="small" sx={{ ml: 1 }} />
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                        Add controlled vocabularies for enhanced semantic alignment
                      </Typography>
                      {projectQuery.data?.config?.skos_files && projectQuery.data.config.skos_files.length > 0 ? (
                        <Stack spacing={1}>
                          {projectQuery.data.config.skos_files.map((file: string, idx: number) => (
                            <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                              <Chip label={file.split('/').pop()} color="success" size="small" />
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => {
                                  // TODO: Add SKOS preview functionality
                                  setSkosPreviewOpen(true);
                                }}
                              >
                                Preview
                              </Button>
                              <Button
                                size="small"
                                variant="outlined"
                                color="error"
                                onClick={async () => {
                                  if (confirm('Delete this SKOS file?')) {
                                    try {
                                      await api.removeSkos(projectId, file);
                                      setSuccess('SKOS file deleted');
                                      projectQuery.refetch();
                                    } catch (e: any) {
                                      setError(`Failed to delete: ${e.message}`);
                                    }
                                  }
                                }}
                              >
                                Delete
                              </Button>
                            </Box>
                          ))}
                        </Stack>
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <input type="file" id="skos-file" accept=".ttl,.rdf,.owl,.n3" />
                          <Button
                            variant="outlined"
                            onClick={() => uploadSkos.mutate()}
                            disabled={uploadSkos.isPending}
                            startIcon={<CloudUploadIcon />}
                          >
                            Upload SKOS
                          </Button>
                        </Box>
                      )}
                    </Box>

                    {/* SHACL Shapes */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        ✓ SHACL Shapes <Chip label="Optional" size="small" sx={{ ml: 1 }} />
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                        Add validation constraints for data quality checking
                      </Typography>
                      {projectQuery.data?.config?.shapes_file ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Chip label={projectQuery.data.config.shapes_file.split('/').pop()} color="success" size="small" />
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => setShapesPreviewOpen(true)}
                          >
                            Preview
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={async () => {
                              if (confirm('Delete SHACL shapes file?')) {
                                try {
                                  await api.removeShapes(projectId);
                                  setSuccess('Shapes file deleted');
                                  projectQuery.refetch();
                                } catch (e: any) {
                                  setError(`Failed to delete: ${e.message}`);
                                }
                              }
                            }}
                          >
                            Delete
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <input type="file" id="shapes-file" accept=".ttl,.rdf,.owl,.n3" />
                          <Button
                            variant="outlined"
                            onClick={() => uploadShapes.mutate()}
                            disabled={uploadShapes.isPending}
                            startIcon={<CloudUploadIcon />}
                          >
                            Upload Shapes
                          </Button>
                        </Box>
                      )}
                    </Box>
                  </Stack>
                </Paper>
              </Stack>

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(1)}
                  disabled={!projectQuery.data?.data_file || !projectQuery.data?.ontology_file}
                >
                  Continue to Mapping
                </Button>
              </Box>
            </StepContent>
          </Step>

          {/* STEP 2: Mapping Review */}
          <Step>
            <StepLabel>
              <Typography variant="h6">Mapping Review & Generation</Typography>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Generate or review mappings between your data and ontology
              </Typography>

              {mappingYamlQuery.data ? (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    ✓ Mapping available! Review and edit as needed.
                  </Alert>

                  <ComprehensiveMappingTable
                    mappingYaml={mappingYamlQuery.data}
                    projectId={projectId}
                    onEditMapping={(row) => {
                      setSelectedMappingRow(row);
                      setEnhancedMappingOpen(true);
                    }}
                  />

                  <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                    <Button variant="outlined" startIcon={<DownloadIcon />} onClick={async () => {
                      try {
                        await api.downloadRML(projectId, 'turtle')
                        setSuccess('RML downloaded')
                      } catch (e: any) {
                        setError(e.message)
                      }
                    }}>
                      Download RML
                    </Button>
                    <Button variant="outlined" startIcon={<DownloadIcon />} onClick={async () => {
                      try {
                        await api.downloadYARRRML(projectId)
                        setSuccess('YARRRML downloaded')
                      } catch (e: any) {
                        setError(e.message)
                      }
                    }}>
                      Download YARRRML
                    </Button>
                  </Stack>
                </Box>
              ) : (
                <Box>
                  <FormControl size="small" sx={{ mb: 2, minWidth: 250 }}>
                    <InputLabel>Mapping Format</InputLabel>
                    <Select value={mappingFormat} onChange={(e) => setMappingFormat(e.target.value)}>
                      <MenuItem value="inline">v2 Inline (Recommended)</MenuItem>
                      <MenuItem value="rml/ttl">v2 + RML Turtle</MenuItem>
                      <MenuItem value="rml/xml">v2 + RML RDF/XML</MenuItem>
                      <MenuItem value="yarrrml">v2 + YARRRML</MenuItem>
                    </Select>
                  </FormControl>

                  <Box>
                    <Button
                      variant="contained"
                      onClick={() => generate.mutate()}
                      disabled={generate.isPending}
                    >
                      {generate.isPending ? 'Generating...' : 'Generate Mappings with AI'}
                    </Button>
                  </Box>
                </Box>
              )}

              <Box sx={{ mt: 2 }}>
                <Button onClick={() => setActiveStep(0)} sx={{ mr: 1 }}>
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(2)}
                  disabled={!mappingYamlQuery.data}
                >
                  Continue to Analysis
                </Button>
              </Box>
            </StepContent>
          </Step>

          {/* STEP 3: Analysis */}
          <Step>
            <StepLabel>
              <Typography variant="h6">Data & Mapping Analysis</Typography>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Analyze mapping coverage and data quality
              </Typography>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>📊 Coverage Analysis</Typography>
                <Alert severity="info">
                  Analysis features coming soon: Column coverage, property coverage, data quality metrics
                </Alert>
                {/* TODO: Add analysis components */}
              </Paper>

              <Box sx={{ mt: 2 }}>
                <Button onClick={() => setActiveStep(1)} sx={{ mr: 1 }}>
                  Back
                </Button>
                <Button variant="contained" onClick={() => setActiveStep(3)}>
                  Continue to Conversion
                </Button>
              </Box>
            </StepContent>
          </Step>

          {/* STEP 4: Convert */}
          <Step>
            <StepLabel>
              <Typography variant="h6">Convert to RDF</Typography>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Transform your data to RDF format
              </Typography>

              <Stack spacing={2}>
                <FormControl size="small" sx={{ maxWidth: 200 }}>
                  <InputLabel>Output Format</InputLabel>
                  <Select value={format} onChange={(e) => setFormat(e.target.value)}>
                    <MenuItem value="turtle">Turtle (.ttl)</MenuItem>
                    <MenuItem value="json-ld">JSON-LD (.jsonld)</MenuItem>
                    <MenuItem value="xml">RDF/XML (.rdf)</MenuItem>
                    <MenuItem value="nt">N-Triples (.nt)</MenuItem>
                  </Select>
                </FormControl>

                <Stack direction="row" spacing={2}>
                  <Button
                    variant="contained"
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
                    Convert (Background)
                  </Button>
                </Stack>

                {convertSync.isPending && <LinearProgress />}

                {convertSync.data && (
                  <Alert severity="success">
                    ✓ Converted! Generated {convertSync.data.triple_count} triples
                    <Button size="small" onClick={download} sx={{ ml: 2 }}>
                      Download RDF
                    </Button>
                  </Alert>
                )}
              </Stack>

              <Box sx={{ mt: 2 }}>
                <Button onClick={() => setActiveStep(2)} sx={{ mr: 1 }}>
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(4)}
                  disabled={!convertSync.data}
                >
                  Continue to Validation
                </Button>
              </Box>
            </StepContent>
          </Step>

          {/* STEP 5: Validation */}
          <Step>
            <StepLabel>
              <Typography variant="h6">Validation & Quality Check</Typography>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Validate RDF output against SHACL shapes
              </Typography>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>✓ Validation Results</Typography>
                <Alert severity="info">
                  SHACL validation features coming soon
                </Alert>
                {/* TODO: Add validation dashboard */}
              </Paper>

              <Box sx={{ mt: 2 }}>
                <Button onClick={() => setActiveStep(3)} sx={{ mr: 1 }}>
                  Back
                </Button>
                <Button variant="contained" color="success" onClick={() => setActiveStep(0)}>
                  Complete
                </Button>
              </Box>
            </StepContent>
          </Step>
        </Stepper>
      </Paper>

      {/* Modals */}
      <OntologyGraphModal
        open={graphOpen}
        onClose={() => setGraphOpen(false)}
        classes={ontology.data?.classes || []}
        properties={ontology.data?.properties || []}
      />

      <ManualMappingModal
        open={manualOpen}
        onClose={() => setManualOpen(false)}
        columnName={manualColumn || ''}
        currentProperty={manualCurrentProp || ''}
        properties={ontology.data?.properties || []}
        onMap={async (column, property) => {
          try {
            await api.overrideMapping(projectId, column, property)
            setSuccess(`Mapping updated: ${column} → ${property}`)
            mappingYamlQuery.refetch()
            setManualOpen(false)
          } catch (e: any) {
            setError(e.message)
          }
        }}
      />

      <EvidenceDrawer
        open={evidenceOpen}
        onClose={() => setEvidenceOpen(false)}
        matchDetail={selectedMatch}
      />

      {/* Data Preview Dialog */}
      <Dialog
        open={dataPreviewOpen}
        onClose={() => setDataPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Data Preview - {projectQuery.data?.data_file?.split('/').pop()}
        </DialogTitle>
        <DialogContent dividers>
          {preview.isLoading ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Loading data preview...
              </Typography>
            </Box>
          ) : preview.error ? (
            <Alert severity="error">
              Failed to load preview: {(preview.error as any)?.message || 'Unknown error'}
            </Alert>
          ) : preview.data?.rows && preview.data.rows.length > 0 ? (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Showing first {preview.data.showing} rows of {preview.data.total_rows || 'unknown total'} rows
              </Alert>
              <Box sx={{ maxHeight: 400, overflow: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                <pre style={{ margin: 0, padding: 16, fontSize: '12px', fontFamily: 'monospace' }}>
                  {JSON.stringify(preview.data.rows, null, 2)}
                </pre>
              </Box>
              {preview.data.columns && preview.data.columns.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Columns ({preview.data.columns.length}):
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {preview.data.columns.map((col: any) => {
                      // Handle both string columns and object columns with 'name' property
                      const colName = typeof col === 'string' ? col : col?.name || String(col);
                      return (
                        <Chip key={colName} label={colName} size="small" variant="outlined" />
                      );
                    })}
                  </Stack>
                </Box>
              )}
            </Box>
          ) : (
            <Alert severity="warning">
              No data available to preview
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDataPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Mapping Preview Dialog */}
      <Dialog
        open={mappingPreviewOpen}
        onClose={() => setMappingPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Mapping Preview
          {mappingPreview.data && (
            <Chip
              label={mappingPreview.data.format}
              size="small"
              color="primary"
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>
        <DialogContent dividers>
          {mappingPreview.isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Loading mapping preview...</Typography>
            </Box>
          ) : mappingPreview.error ? (
            <Alert severity="error">
              Failed to load mapping preview: {(mappingPreview.error as any)?.message || 'Unknown error'}
            </Alert>
          ) : mappingPreview.data ? (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Showing first {mappingPreview.data.showing_lines} lines of {mappingPreview.data.total_lines} total
                {mappingPreview.data.is_truncated && ' (truncated)'}
              </Alert>
              <Box
                sx={{
                  maxHeight: 600,
                  overflow: 'auto',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  bgcolor: '#f5f5f5'
                }}
              >
                <pre style={{
                  margin: 0,
                  padding: 16,
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}>
                  {mappingPreview.data.preview}
                </pre>
              </Box>
            </Box>
          ) : (
            <Alert severity="warning">No mapping preview available</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMappingPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* SKOS Preview Dialog */}
      <Dialog
        open={skosPreviewOpen}
        onClose={() => setSkosPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>SKOS Vocabulary Preview</DialogTitle>
        <DialogContent dividers>
          <Alert severity="info" sx={{ mb: 2 }}>
            SKOS vocabularies provide controlled terms for semantic alignment
          </Alert>
          <Box
            sx={{
              maxHeight: 600,
              overflow: 'auto',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: '#f5f5f5'
            }}
          >
            <pre style={{
              margin: 0,
              padding: 16,
              fontSize: '12px',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap'
            }}>
              {/* TODO: Fetch and display SKOS content */}
              Preview not yet implemented. File uploaded successfully.
            </pre>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSkosPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* SHACL Shapes Preview Dialog */}
      <Dialog
        open={shapesPreviewOpen}
        onClose={() => setShapesPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>SHACL Shapes Preview</DialogTitle>
        <DialogContent dividers>
          <Alert severity="info" sx={{ mb: 2 }}>
            SHACL shapes define validation constraints for your data
          </Alert>
          <Box
            sx={{
              maxHeight: 600,
              overflow: 'auto',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: '#f5f5f5'
            }}
          >
            <pre style={{
              margin: 0,
              padding: 16,
              fontSize: '12px',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap'
            }}>
              {/* TODO: Fetch and display Shapes content */}
              Preview not yet implemented. File uploaded successfully.
            </pre>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShapesPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Add Nested Entity Modal */}
      <AddNestedEntityModal
        open={addNestedEntityOpen}
        onClose={() => setAddNestedEntityOpen(false)}
        parentEntityIndex={parentEntityIndexForNested}
        ontologyClasses={ontology.data?.classes || []}
        ontologyProperties={ontology.data?.properties || []}
        dataColumns={preview.data?.columns?.map((col: any) => typeof col === 'string' ? col : col?.name) || []}
        onSave={async (data) => {
          try {
            await api.addNestedEntity(
              projectId,
              parentEntityIndexForNested,
              data.joinColumn,
              data.targetClass,
              data.iriTemplate,
              data.properties
            );
            setSuccess('Nested entity added successfully!');
            mappingYamlQuery.refetch();
            setAddNestedEntityOpen(false);
          } catch (e: any) {
            setError(`Failed to add nested entity: ${e.message}`);
          }
        }}
      />

      {/* Enhanced Mapping Modal with Graph */}
      <EnhancedMappingModal
        open={enhancedMappingOpen}
        onClose={() => setEnhancedMappingOpen(false)}
        projectId={projectId}
        mappingRow={selectedMappingRow}
        ontologyClasses={ontology.data?.classes || []}
        ontologyProperties={ontology.data?.properties || []}
        onSave={async (newPropertyUri) => {
          if (!selectedMappingRow) return;

          try {
            // Determine if it's a simple override or nested override
            if (selectedMappingRow.mappingType === 'nested-data' &&
                selectedMappingRow.parentEntityIndex !== undefined &&
                selectedMappingRow.nestedEntityIndex !== undefined) {
              // Nested property override
              await api.overrideNestedMapping(
                projectId,
                selectedMappingRow.parentEntityIndex,
                selectedMappingRow.nestedEntityIndex,
                selectedMappingRow.columnName,
                newPropertyUri
              );
            } else {
              // Simple property override
              await api.overrideMapping(projectId, selectedMappingRow.columnName, newPropertyUri);
            }

            setSuccess(`Mapping updated: ${selectedMappingRow.columnName} → ${newPropertyUri.split('#').pop()?.split('/').pop()}`);
            mappingYamlQuery.refetch();
          } catch (e: any) {
            setError(`Failed to update mapping: ${e.message}`);
          }
        }}
      />
    </Box>
  )
}

