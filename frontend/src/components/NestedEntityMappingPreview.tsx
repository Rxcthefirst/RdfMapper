import React from 'react'
import {
  Box,
  Typography,
  IconButton,
  Stack,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import AddIcon from '@mui/icons-material/Add'
import yaml from 'js-yaml'

interface NestedEntityMappingPreviewProps {
  mappingYaml: string
  projectId: string
  onEditProperty?: (columnName: string, currentProperty: string) => void
  onEditNestedProperty?: (
    parentIndex: number,
    nestedIndex: number,
    columnName: string,
    currentProperty: string
  ) => void
  onAddNestedEntity?: (parentIndex: number) => void
  onDeleteNestedEntity?: (parentIndex: number, nestedIndex: number) => void
  readOnly?: boolean
}

const NestedEntityMappingPreview: React.FC<NestedEntityMappingPreviewProps> = ({
  mappingYaml,
  onEditProperty,
  onEditNestedProperty,
  onAddNestedEntity,
  onDeleteNestedEntity,
  readOnly = false
}) => {
  const parsed = React.useMemo(() => {
    try {
      const config = yaml.load(mappingYaml) as any
      const isV2 = 'mapping' in config

      if (isV2) {
        const mappingDef = config.mapping

        if (typeof mappingDef === 'object' && mappingDef.file) {
          return { format: 'v2' as const, isExternal: true, externalFile: mappingDef.file, sources: [] }
        }

        return {
          format: 'v2' as const,
          sources: mappingDef.sources || [],
          baseIri: mappingDef.base_iri
        }
      }

      return null
    } catch (error) {
      console.error('Failed to parse mapping:', error)
      return null
    }
  }, [mappingYaml])

  if (!parsed) {
    return <Alert severity="error">Failed to parse mapping configuration</Alert>
  }

  if ((parsed as any).isExternal) {
    return (
      <Alert severity="info">
        External mapping file: <strong>{(parsed as any).externalFile}</strong>
        <br />
        Cannot edit external RML/YARRRML files through UI. Regenerate with inline format for editing.
      </Alert>
    )
  }

  if (parsed.sources.length === 0) {
    return <Alert severity="warning">No mapping sources found</Alert>
  }

  return (
    <Box>
      {parsed.baseIri && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
          Base IRI: <strong>{parsed.baseIri}</strong>
        </Typography>
      )}

      {/* Each entity source */}
      {parsed.sources.map((source: any, sourceIdx: number) => {
        const entityClass = source.entity?.class || 'Unknown'
        const iriTemplate = source.entity?.iri_template || ''
        const properties = source.properties || {}
        const nestedEntities = source.nested_entities || []

        return (
          <Accordion key={sourceIdx} defaultExpanded sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Typography variant="h6">
                  {entityClass.split('#').pop()?.split('/').pop()}
                </Typography>
                <Chip label={`${Object.keys(properties).length} properties`} size="small" color="primary" />
                {nestedEntities.length > 0 && (
                  <Chip label={`${nestedEntities.length} nested`} size="small" color="secondary" />
                )}
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={3}>
                {/* Entity metadata */}
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Class: <strong>{entityClass}</strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    IRI Template: <strong>{iriTemplate}</strong>
                  </Typography>
                </Box>

                {/* Data Properties */}
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                    📊 Data Properties
                  </Typography>
                  <Stack spacing={0.5}>
                    {Object.entries(properties).map(([columnName, propertyUri]: [string, any]) => (
                      <Box
                        key={columnName}
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          p: 1,
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'divider',
                          '&:hover': { bgcolor: 'action.hover' }
                        }}
                      >
                        <Typography variant="body2">
                          <strong>{columnName}</strong> → {propertyUri}
                        </Typography>
                        {!readOnly && onEditProperty && (
                          <IconButton
                            size="small"
                            onClick={() => onEditProperty(columnName, propertyUri)}
                            title="Edit mapping"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </Box>

                {/* Nested Entities */}
                {nestedEntities.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      🔗 Nested Entities (Object Properties)
                    </Typography>
                    <Stack spacing={2}>
                      {nestedEntities.map((nested: any, nestedIdx: number) => {
                        const targetClass = nested.target_class || 'Unknown'
                        const joinCondition = nested.join_condition || ''
                        const nestedIriTemplate = nested.iri_template || ''
                        const nestedProperties = nested.properties || {}

                        return (
                          <Box
                            key={nestedIdx}
                            sx={{
                              p: 2,
                              border: '2px solid',
                              borderColor: 'secondary.main',
                              borderRadius: 2,
                              bgcolor: 'action.hover'
                            }}
                          >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="subtitle2" color="secondary.main" fontWeight="bold">
                                {targetClass.split('#').pop()?.split('/').pop()}
                              </Typography>
                              {!readOnly && onDeleteNestedEntity && (
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => onDeleteNestedEntity(sourceIdx, nestedIdx)}
                                  title="Delete nested entity"
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              )}
                            </Box>

                            <Typography variant="caption" color="text.secondary" display="block">
                              Join Column: <strong>{joinCondition}</strong>
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                              Target Class: <strong>{targetClass}</strong>
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                              IRI Template: <strong>{nestedIriTemplate}</strong>
                            </Typography>

                            <Typography variant="caption" fontWeight="bold" display="block" sx={{ mb: 0.5 }}>
                              Properties:
                            </Typography>
                            <Stack spacing={0.5}>
                              {Object.entries(nestedProperties).map(([colName, propUri]: [string, any]) => (
                                <Box
                                  key={colName}
                                  sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    p: 0.5,
                                    pl: 1,
                                    borderRadius: 1,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    bgcolor: 'background.paper',
                                    '&:hover': { bgcolor: 'action.selected' }
                                  }}
                                >
                                  <Typography variant="caption">
                                    <strong>{colName}</strong> → {propUri}
                                  </Typography>
                                  {!readOnly && onEditNestedProperty && (
                                    <IconButton
                                      size="small"
                                      onClick={() => onEditNestedProperty(sourceIdx, nestedIdx, colName, propUri)}
                                      title="Edit nested property"
                                    >
                                      <EditIcon fontSize="inherit" />
                                    </IconButton>
                                  )}
                                </Box>
                              ))}
                            </Stack>
                          </Box>
                        )
                      })}
                    </Stack>
                  </Box>
                )}

                {/* Add Nested Entity Button */}
                {!readOnly && onAddNestedEntity && (
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={() => onAddNestedEntity(sourceIdx)}
                    size="small"
                  >
                    Add Nested Entity
                  </Button>
                )}
              </Stack>
            </AccordionDetails>
          </Accordion>
        )
      })}
    </Box>
  )
}

export default NestedEntityMappingPreview

