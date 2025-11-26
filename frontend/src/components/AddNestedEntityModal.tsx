import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stack,
  Box,
  Typography,
  IconButton,
  Chip,
  Alert
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'

interface AddNestedEntityModalProps {
  open: boolean
  onClose: () => void
  parentEntityIndex: number
  ontologyClasses: Array<{ uri: string; label?: string }>
  ontologyProperties: Array<{ uri: string; label?: string }>
  dataColumns: string[]
  onSave: (data: {
    joinColumn: string
    targetClass: string
    iriTemplate: string
    properties: Record<string, string>
  }) => void
}

const AddNestedEntityModal: React.FC<AddNestedEntityModalProps> = ({
  open,
  onClose,
  ontologyClasses,
  ontologyProperties,
  dataColumns,
  onSave
}) => {
  const [joinColumn, setJoinColumn] = useState('')
  const [targetClass, setTargetClass] = useState('')
  const [iriTemplate, setIriTemplate] = useState('')
  const [properties, setProperties] = useState<Record<string, string>>({})
  const [newPropColumn, setNewPropColumn] = useState('')
  const [newPropUri, setNewPropUri] = useState('')

  const handleAddProperty = () => {
    if (newPropColumn && newPropUri) {
      setProperties({ ...properties, [newPropColumn]: newPropUri })
      setNewPropColumn('')
      setNewPropUri('')
    }
  }

  const handleRemoveProperty = (column: string) => {
    const updated = { ...properties }
    delete updated[column]
    setProperties(updated)
  }

  const handleSave = () => {
    if (!joinColumn || !targetClass || !iriTemplate) {
      alert('Please fill in all required fields')
      return
    }

    onSave({
      joinColumn,
      targetClass,
      iriTemplate,
      properties
    })

    // Reset
    setJoinColumn('')
    setTargetClass('')
    setIriTemplate('')
    setProperties({})
    onClose()
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add Nested Entity Relationship</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={3}>
          <Alert severity="info">
            Create a nested entity to represent an object property relationship (e.g., Loan → Borrower)
          </Alert>

          {/* Join Column (FK) */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Join Column (Foreign Key) *
            </Typography>
            <TextField
              select
              fullWidth
              size="small"
              value={joinColumn}
              onChange={(e) => setJoinColumn(e.target.value)}
              SelectProps={{ native: true }}
            >
              <option value="">Select column...</option>
              {dataColumns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </TextField>
            <Typography variant="caption" color="text.secondary">
              The column containing the foreign key reference
            </Typography>
          </Box>

          {/* Target Class */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Target Entity Class *
            </Typography>
            <TextField
              select
              fullWidth
              size="small"
              value={targetClass}
              onChange={(e) => setTargetClass(e.target.value)}
              SelectProps={{ native: true }}
            >
              <option value="">Select class...</option>
              {ontologyClasses.map((cls) => (
                <option key={cls.uri} value={cls.uri}>
                  {cls.label || cls.uri.split('#').pop()?.split('/').pop()}
                </option>
              ))}
            </TextField>
            <Typography variant="caption" color="text.secondary">
              The ontology class for the nested entity
            </Typography>
          </Box>

          {/* IRI Template */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              IRI Template *
            </Typography>
            <TextField
              fullWidth
              size="small"
              value={iriTemplate}
              onChange={(e) => setIriTemplate(e.target.value)}
              placeholder="{BorrowerID}"
              helperText='Use {ColumnName} for column values (e.g., "{BorrowerID}")'
            />
          </Box>

          {/* Properties Mapping */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Property Mappings
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Map columns from your data to properties of the nested entity
            </Typography>

            {/* Existing properties */}
            <Stack spacing={0.5} sx={{ mb: 2 }}>
              {Object.entries(properties).map(([col, propUri]) => (
                <Box
                  key={col}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    p: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1
                  }}
                >
                  <Chip label={col} size="small" />
                  <Typography variant="body2">→</Typography>
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {propUri.split('#').pop()?.split('/').pop()}
                  </Typography>
                  <IconButton size="small" onClick={() => handleRemoveProperty(col)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}
            </Stack>

            {/* Add new property */}
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                select
                size="small"
                label="Column"
                value={newPropColumn}
                onChange={(e) => setNewPropColumn(e.target.value)}
                SelectProps={{ native: true }}
                sx={{ flex: 1 }}
              >
                <option value="">Select...</option>
                {dataColumns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </TextField>
              <TextField
                select
                size="small"
                label="Property"
                value={newPropUri}
                onChange={(e) => setNewPropUri(e.target.value)}
                SelectProps={{ native: true }}
                sx={{ flex: 2 }}
              >
                <option value="">Select...</option>
                {ontologyProperties.map((prop) => (
                  <option key={prop.uri} value={prop.uri}>
                    {prop.label || prop.uri.split('#').pop()?.split('/').pop()}
                  </option>
                ))}
              </TextField>
              <Button
                variant="outlined"
                onClick={handleAddProperty}
                startIcon={<AddIcon />}
                disabled={!newPropColumn || !newPropUri}
              >
                Add
              </Button>
            </Box>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!joinColumn || !targetClass || !iriTemplate}
        >
          Save Nested Entity
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default AddNestedEntityModal

