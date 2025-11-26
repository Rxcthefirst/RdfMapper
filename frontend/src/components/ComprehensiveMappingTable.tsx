import React, { useMemo, useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Alert,
  Tooltip,
  Stack,
  CircularProgress
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import LinkIcon from '@mui/icons-material/Link'
import DataObjectIcon from '@mui/icons-material/DataObject'
import yaml from 'js-yaml'
import { parseMappingFile } from '../utils/mappingParser'

interface MappingRow {
  columnName: string
  columnPath: string // For nested JSON/XML
  mappedProperty: string
  mappedPropertyLabel: string
  mappingType: 'data' | 'object' | 'nested-data'
  parentEntity?: string
  nestedEntity?: string
  datatype?: string
  parentEntityIndex?: number
  nestedEntityIndex?: number
}

interface ComprehensiveMappingTableProps {
  mappingYaml: string
  projectId: string
  onEditMapping: (row: MappingRow) => void
  readOnly?: boolean
}

const ComprehensiveMappingTable: React.FC<ComprehensiveMappingTableProps> = ({
  mappingYaml,
  projectId,
  onEditMapping,
  readOnly = false
}) => {
  const [externalMappingContent, setExternalMappingContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check if config references external file and fetch it
  useEffect(() => {
    const fetchExternalMapping = async () => {
      try {
        const config = yaml.load(mappingYaml) as any
        if (config.mapping?.file) {
          setLoading(true)
          const filename = config.mapping.file.split('/').pop() || config.mapping.file
          const response = await fetch(`/api/projects/${projectId}/files/${filename}`)
          if (!response.ok) {
            throw new Error(`Failed to fetch mapping file: ${response.statusText}`)
          }
          const content = await response.text()
          setExternalMappingContent(content)
          setError(null)
        } else {
          setExternalMappingContent(null)
        }
      } catch (err: any) {
        console.error('Error fetching external mapping:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchExternalMapping()
  }, [mappingYaml, projectId])

  const rows = useMemo(() => {
    try {
      const config = yaml.load(mappingYaml) as any
      const mappingRows: MappingRow[] = []

      if (!config.mapping) {
        console.warn('No mapping section in config')
        return []
      }

      // If external file is referenced but not loaded yet, return null to show loading
      if (config.mapping.file && !externalMappingContent && !error) {
        console.log('External file referenced but not loaded yet')
        return null
      }

      // If external file, use parsed content
      if (config.mapping.file && externalMappingContent) {
        console.log('Parsing external mapping file...')
        const parsed = parseMappingFile(externalMappingContent)
        if (!parsed) {
          console.error('Failed to parse external mapping file')
          return []
        }

        console.log('Parsed mapping for table:', {
          format: parsed.format,
          sourcesCount: parsed.sources.length,
          sources: parsed.sources.map(s => ({
            name: s.name,
            entityClass: s.entityClass,
            propertiesCount: Object.keys(s.properties).length,
            objectPropertiesCount: s.objectProperties.length
          }))
        })

        // Convert parsed format to table rows
        parsed.sources.forEach((source, sourceIdx) => {
          const entityLabel = source.entityClass.split('#').pop()?.split('/').pop() || source.entityClass

          console.log(`Processing source ${sourceIdx} (${entityLabel}):`, {
            properties: Object.keys(source.properties).length,
            objectProperties: source.objectProperties.length
          })

          // Data properties
          Object.entries(source.properties).forEach(([colName, prop]) => {
            const propLabel = prop.predicate.split('#').pop()?.split('/').pop() || prop.predicate
            mappingRows.push({
              columnName: colName,
              columnPath: colName,
              mappedProperty: prop.predicate,
              mappedPropertyLabel: propLabel,
              mappingType: 'data',
              parentEntity: entityLabel,
              datatype: prop.datatype,
              parentEntityIndex: sourceIdx
            })
          })

          // Object properties
          source.objectProperties.forEach((objProp, objIdx) => {
            const targetLabel = objProp.targetClass.split('#').pop()?.split('/').pop() || objProp.targetClass

            console.log(`Object property ${objIdx}:`, {
              predicate: objProp.predicate,
              targetClass: objProp.targetClass,
              joinColumn: objProp.joinColumn,
              nestedPropertiesCount: Object.keys(objProp.properties).length,
              nestedProperties: Object.keys(objProp.properties)
            })

            // FK column row
            mappingRows.push({
              columnName: objProp.joinColumn,
              columnPath: objProp.joinColumn,
              mappedProperty: objProp.targetClass,
              mappedPropertyLabel: `→ ${targetLabel}`,
              mappingType: 'object',
              parentEntity: entityLabel,
              nestedEntity: targetLabel,
              parentEntityIndex: sourceIdx,
              nestedEntityIndex: objIdx
            })

            // Nested properties
            Object.entries(objProp.properties).forEach(([colName, prop]) => {
              const propLabel = prop.predicate.split('#').pop()?.split('/').pop() || prop.predicate
              mappingRows.push({
                columnName: colName,
                columnPath: `${objProp.joinColumn}.${colName}`,
                mappedProperty: prop.predicate,
                mappedPropertyLabel: propLabel,
                mappingType: 'nested-data',
                parentEntity: entityLabel,
                nestedEntity: targetLabel,
                datatype: prop.datatype,
                parentEntityIndex: sourceIdx,
                nestedEntityIndex: objIdx
              })
            })
          })
        })

        return mappingRows
      }

      // Otherwise use v2 inline format
      const sources = config.mapping.sources || []

      console.log('Processing v2 inline format, sources:', sources.length)

      sources.forEach((source: any, sourceIdx: number) => {
        const entityClass = source.entity?.class || 'Unknown'
        const entityLabel = entityClass.split('#').pop()?.split('/').pop() || entityClass

        console.log(`V2 Source ${sourceIdx} (${entityLabel}):`, {
          propertiesCount: Object.keys(source.properties || {}).length,
          relationshipsCount: (source.relationships || []).length,
          relationships: source.relationships
        })

        // Parent entity data properties
        const properties = source.properties || {}
        Object.entries(properties).forEach(([colName, propValue]: [string, any]) => {
          const propUri = typeof propValue === 'string' ? propValue : propValue?.predicate || propValue?.property
          const propLabel = propUri?.split('#').pop()?.split('/').pop() || propUri
          const datatype = typeof propValue === 'object' ? propValue?.datatype : undefined

          mappingRows.push({
            columnName: colName,
            columnPath: colName,
            mappedProperty: propUri || '',
            mappedPropertyLabel: propLabel || '',
            mappingType: 'data',
            parentEntity: entityLabel,
            datatype,
            parentEntityIndex: sourceIdx
          })
        })

        // Nested entities (object properties) - v2 format uses 'relationships'
        const relationships = source.relationships || []
        console.log(`Processing ${relationships.length} relationships for ${entityLabel}`)

        relationships.forEach((rel: any, relIdx: number) => {
          const targetClass = rel.class || 'Unknown'
          const targetLabel = targetClass.split('#').pop()?.split('/').pop() || targetClass
          const predicate = rel.predicate

          console.log(`Relationship ${relIdx} raw data:`, {
            iri_template: rel.iri_template,
            allKeys: Object.keys(rel),
            fullRelObject: rel
          })

          // Infer join column from IRI template
          // Support multiple patterns: {column}, $(column), $[column], or just the last path segment
          let joinCol = 'Unknown'

          if (rel.iri_template) {
            const template = rel.iri_template

            // Try pattern 1: {ColumnName}
            let match = template.match(/\{([^}]+)\}/)
            if (match) {
              joinCol = match[1]
            }

            // Try pattern 2: $(ColumnName) - YARRRML style
            if (joinCol === 'Unknown') {
              match = template.match(/\$\(([^)]+)\)/)
              if (match && match[1] !== 'base_iri') {
                joinCol = match[1]
              }
            }

            // Try pattern 3: $[ColumnName]
            if (joinCol === 'Unknown') {
              match = template.match(/\$\[([^\]]+)\]/)
              if (match) {
                joinCol = match[1]
              }
            }

            // Try pattern 4: Extract last path segment if it's a column reference
            if (joinCol === 'Unknown') {
              const lastSegment = template.split('/').pop()
              if (lastSegment && !lastSegment.includes('$(base_iri)')) {
                joinCol = lastSegment
              }
            }
          }

          // Fallback: Infer from target class name + "ID"
          if (joinCol === 'Unknown' || joinCol === 'base_iri') {
            const classLabel = targetClass.split('#').pop()?.split('/').pop()
            if (classLabel) {
              joinCol = `${classLabel}ID`
            }
          }

          console.log(`Relationship ${relIdx}:`, {
            targetClass,
            targetLabel,
            predicate,
            joinCol,
            propertiesCount: Object.keys(rel.properties || {}).length,
            properties: rel.properties
          })

          // Add row for the FK column itself (object property)
          mappingRows.push({
            columnName: joinCol,
            columnPath: joinCol,
            mappedProperty: predicate,
            mappedPropertyLabel: `→ ${targetLabel}`,
            mappingType: 'object',
            parentEntity: entityLabel,
            nestedEntity: targetLabel,
            parentEntityIndex: sourceIdx,
            nestedEntityIndex: relIdx
          })

          // Add rows for nested entity's data properties
          const nestedProps = rel.properties || {}
          Object.entries(nestedProps).forEach(([colName, propValue]: [string, any]) => {
            const propUri = typeof propValue === 'string' ? propValue : propValue?.predicate || propValue?.property
            const propLabel = propUri?.split('#').pop()?.split('/').pop() || propUri
            const datatype = typeof propValue === 'object' ? propValue?.datatype : undefined

            mappingRows.push({
              columnName: colName,
              columnPath: `${joinCol}.${colName}`,
              mappedProperty: propUri || '',
              mappedPropertyLabel: propLabel || '',
              mappingType: 'nested-data',
              parentEntity: entityLabel,
              nestedEntity: targetLabel,
              datatype,
              parentEntityIndex: sourceIdx,
              nestedEntityIndex: relIdx
            })
          })
        })
      })

      return mappingRows
    } catch (error) {
      console.error('Failed to parse mapping:', error)
      return []
    }
  }, [mappingYaml, externalMappingContent])

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading external mapping file...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load external mapping file: {error}
      </Alert>
    )
  }

  // If rows is null, external file is still loading
  if (rows === null) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Parsing mapping file...</Typography>
      </Box>
    )
  }

  if (rows.length === 0) {
    return (
      <Alert severity="warning">
        No mappings found in the configuration. The mapping file may be empty or in an unsupported format.
      </Alert>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Column Mappings ({rows.length} total)
        </Typography>
        <Stack direction="row" spacing={1}>
          <Chip icon={<DataObjectIcon />} label={`${rows.filter(r => r.mappingType === 'data').length} Data Props`} size="small" />
          <Chip icon={<LinkIcon />} label={`${rows.filter(r => r.mappingType === 'object').length} Object Props`} size="small" color="secondary" />
          <Chip icon={<DataObjectIcon />} label={`${rows.filter(r => r.mappingType === 'nested-data').length} Nested Props`} size="small" color="primary" />
        </Stack>
      </Box>

      <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell width="25%"><strong>Column / Path</strong></TableCell>
              <TableCell width="20%"><strong>Entity Context</strong></TableCell>
              <TableCell width="30%"><strong>Mapped To</strong></TableCell>
              <TableCell width="15%"><strong>Type</strong></TableCell>
              <TableCell width="10%" align="right"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow
                key={idx}
                hover
                sx={{
                  bgcolor: row.mappingType === 'nested-data'
                    ? 'action.hover'
                    : row.mappingType === 'object'
                    ? 'secondary.light'
                    : 'background.paper'
                }}
              >
                {/* Column Name/Path */}
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {row.mappingType === 'nested-data' && (
                      <span style={{ color: '#999', marginRight: 4 }}>├─</span>
                    )}
                    <strong>{row.columnName}</strong>
                  </Typography>
                  {row.columnPath !== row.columnName && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {row.columnPath}
                    </Typography>
                  )}
                </TableCell>

                {/* Entity Context */}
                <TableCell>
                  <Stack spacing={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      {row.parentEntity}
                    </Typography>
                    {row.nestedEntity && (
                      <Typography variant="caption" color="secondary.main" sx={{ fontWeight: 'bold' }}>
                        → {row.nestedEntity}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>

                {/* Mapped Property */}
                <TableCell>
                  <Box>
                    <Typography variant="body2">
                      {row.mappedPropertyLabel}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                      {row.mappedProperty}
                    </Typography>
                  </Box>
                </TableCell>

                {/* Type */}
                <TableCell>
                  <Stack spacing={0.5}>
                    <Chip
                      label={
                        row.mappingType === 'data' ? 'Data Property' :
                        row.mappingType === 'object' ? 'Object Property' :
                        'Nested Data'
                      }
                      size="small"
                      color={
                        row.mappingType === 'data' ? 'default' :
                        row.mappingType === 'object' ? 'secondary' :
                        'primary'
                      }
                      variant="outlined"
                    />
                    {row.datatype && (
                      <Typography variant="caption" color="text.secondary">
                        {row.datatype.split('#').pop()}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>

                {/* Actions */}
                <TableCell align="right">
                  {!readOnly && (
                    <Tooltip title="Edit mapping - View graph context">
                      <IconButton
                        size="small"
                        onClick={() => onEditMapping(row)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default ComprehensiveMappingTable
export type { MappingRow }

