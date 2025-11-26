import React, { useMemo } from 'react'
import { Box, Typography, IconButton, Stack, Chip, Alert } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import yaml from 'js-yaml'

interface MappingPreviewProps {
  mappingYaml: string
  onEdit?: (columnName: string, currentProperty: string) => void
  readOnly?: boolean
}

interface ParsedMapping {
  format: 'v1' | 'v2'
  sources: any[]
  namespaces?: Record<string, string>
  baseIri?: string
}

const MappingPreview: React.FC<MappingPreviewProps> = ({
  mappingYaml,
  onEdit,
  readOnly = false
}) => {
  const parsed = useMemo(() => {
    try {
      const config = yaml.load(mappingYaml) as any

      // Detect v1 vs v2 format
      const isV2 = 'mapping' in config

      if (isV2) {
        // V2 format
        const mappingDef = config.mapping

        // Check if external file reference
        if (typeof mappingDef === 'object' && mappingDef.file) {
          return {
            format: 'v2' as const,
            isExternal: true,
            externalFile: mappingDef.file,
            sources: []
          }
        }

        return {
          format: 'v2' as const,
          sources: mappingDef.sources || [],
          namespaces: mappingDef.namespaces,
          baseIri: mappingDef.base_iri
        }
      } else {
        // V1 format
        return {
          format: 'v1' as const,
          sources: config.sheets || [],
          namespaces: config.namespaces,
          baseIri: config.defaults?.base_iri
        }
      }
    } catch (error) {
      console.error('Failed to parse mapping YAML:', error)
      return null
    }
  }, [mappingYaml])

  if (!parsed) {
    return (
      <Alert severity="error">
        Failed to parse mapping configuration. Please check the file format.
      </Alert>
    )
  }

  if ((parsed as any).isExternal) {
    return (
      <Alert severity="info">
        External mapping file: <strong>{(parsed as any).externalFile}</strong>
        <br />
        This configuration references an external RML or YARRRML file.
      </Alert>
    )
  }

  if (parsed.sources.length === 0) {
    return (
      <Alert severity="warning">
        No mapping sources found in configuration.
      </Alert>
    )
  }

  return (
    <Box>
      {/* Header info */}
      {parsed.baseIri && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          Base IRI: {parsed.baseIri}
        </Typography>
      )}

      {/* Each source/sheet */}
      {parsed.sources.map((source: any, idx: number) => {
        const isV2 = parsed.format === 'v2'
        const sourceName = source.name
        const entityClass = isV2 ? source.entity?.class : source.row_resource?.class
        const properties = isV2 ? source.properties : source.columns
        const relationships = isV2 ? source.relationships : source.objects

        return (
          <Box
            key={idx}
            sx={{
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              p: 2,
              mb: 2
            }}
          >
            {/* Source header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">
                {sourceName} → {entityClass || 'Unknown Class'}
              </Typography>
              <Chip
                label={`${Object.keys(properties || {}).length} properties`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>

            {/* Data properties */}
            <Typography variant="caption" color="text.secondary" fontWeight="bold" display="block" sx={{ mb: 1 }}>
              Data Properties:
            </Typography>
            <Stack spacing={0.5} sx={{ ml: 2, mb: 2 }}>
              {Object.entries(properties || {}).map(([columnName, propConfig]: [string, any]) => {
                const predicate = isV2 ? propConfig.predicate : propConfig.as
                const datatype = propConfig.datatype

                return (
                  <Box
                    key={columnName}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      p: 1,
                      borderRadius: 1,
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                  >
                    <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                      <strong>{columnName}</strong> → {predicate}
                      {datatype && <span style={{ color: '#666' }}> ({datatype.split('#').pop()})</span>}
                    </Typography>
                    {!readOnly && onEdit && (
                      <IconButton
                        size="small"
                        onClick={() => onEdit(columnName, predicate)}
                        title="Edit mapping"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                )
              })}
            </Stack>

            {/* Relationships */}
            {relationships && (Array.isArray(relationships) ? relationships.length > 0 : Object.keys(relationships).length > 0) && (
              <>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" display="block" sx={{ mb: 1 }}>
                  Relationships:
                </Typography>
                <Stack spacing={1} sx={{ ml: 2 }}>
                  {(Array.isArray(relationships) ? relationships : Object.entries(relationships)).map((rel: any, relIdx: number) => {
                    let relPredicate, relClass, relProperties

                    if (Array.isArray(relationships)) {
                      // V2 format (array of relationships)
                      relPredicate = rel.predicate
                      relClass = rel.class
                      relProperties = rel.properties || {}
                    } else {
                      // V1 format (object with relationships)
                      const [relName, relConfig] = rel
                      relPredicate = relConfig.predicate
                      relClass = relConfig.class
                      relProperties = relConfig.properties || []
                    }

                    return (
                      <Box
                        key={relIdx}
                        sx={{
                          p: 1.5,
                          bgcolor: 'action.hover',
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>
                          → {relPredicate} ({relClass?.split('#').pop() || relClass})
                        </Typography>
                        <Stack spacing={0.5} sx={{ ml: 2 }}>
                          {(Array.isArray(relProperties) ? relProperties : Object.entries(relProperties)).map((prop: any, propIdx: number) => {
                            let colName, propPredicate

                            if (Array.isArray(relProperties)) {
                              // V2 or V1 array format
                              colName = prop.column || Object.keys(prop)[0]
                              propPredicate = prop.predicate || prop.as || prop[colName]?.predicate || prop[colName]?.as
                            } else {
                              // V2 dict format
                              [colName, propPredicate] = [prop[0], prop[1].predicate || prop[1].as]
                            }

                            return (
                              <Typography key={propIdx} variant="body2" sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
                                <strong>{colName}</strong> → {propPredicate?.split('#').pop() || propPredicate}
                              </Typography>
                            )
                          })}
                        </Stack>
                      </Box>
                    )
                  })}
                </Stack>
              </>
            )}
          </Box>
        )
      })}
    </Box>
  )
}

export default MappingPreview

