import React, { useMemo, useState } from 'react';
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
  Divider
} from '@mui/material';

interface OntologyPropertyRef {
  uri: string;
  label?: string;
  comment?: string;
}

interface ManualMappingModalProps {
  open: boolean;
  columnName: string | null;
  currentProperty?: string | null;
  properties: OntologyPropertyRef[];
  onClose: () => void;
  onMap: (column: string, propertyUri: string) => void;
}

const ManualMappingModal: React.FC<ManualMappingModalProps> = ({
  open,
  columnName,
  currentProperty,
  properties,
  onClose,
  onMap
}) => {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return properties;
    return properties.filter(p => {
      const localName = p.uri.split('#').pop()?.split('/').pop() || p.uri;
      return (p.label || '').toLowerCase().includes(q) || localName.toLowerCase().includes(q);
    });
  }, [query, properties]);

  const handleConfirm = () => {
    if (columnName && selected) {
      onMap(columnName, selected);
      setSelected(null);
      setQuery('');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Manual Mapping{columnName ? ` – ${columnName}` : ''}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <Typography variant="body2" color="text.secondary">
            Select a property from the ontology to map this column. Use search to filter. This updates the current mapping locally (backend override API TBD).
          </Typography>
          {currentProperty && (
            <Typography variant="caption" color="text.secondary">
              Current mapping: <code>{currentProperty.split('#').pop()?.split('/').pop()}</code>
            </Typography>
          )}
          <TextField
            label="Search properties"
            size="small"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type part of label or local name..."
          />
          <Box sx={{ maxHeight: 340, overflow: 'auto', border: '1px solid', borderColor: 'divider', p:1, borderRadius:1 }}>
            <Stack spacing={1}>
              {filtered.slice(0,400).map(p => {
                const localName = p.uri.split('#').pop()?.split('/').pop() || p.uri;
                const isSelected = selected === p.uri;
                return (
                  <Box
                    key={p.uri}
                    onClick={() => setSelected(p.uri)}
                    sx={{
                      p:1,
                      borderRadius:1,
                      cursor:'pointer',
                      bgcolor: isSelected ? 'primary.light' : 'background.paper',
                      border: '1px solid',
                      borderColor: isSelected ? 'primary.main' : 'divider',
                      '&:hover': { bgcolor: isSelected ? 'primary.light' : 'action.hover' }
                    }}
                  >
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb:0.5 }}>
                      <Chip size="small" label={localName} color={isSelected ? 'primary' : 'default'} />
                      {p.label && p.label !== localName && (
                        <Typography variant="caption" color="text.secondary">{p.label}</Typography>
                      )}
                    </Stack>
                    {p.comment && (
                      <Typography variant="caption" color="text.secondary" sx={{ display:'block' }}>{p.comment}</Typography>
                    )}
                  </Box>
                );
              })}
              {filtered.length === 0 && (
                <Typography variant="caption" color="text.secondary">No properties match your search.</Typography>
              )}
              {filtered.length > 400 && (
                <Typography variant="caption" color="text.secondary">Showing first 400 results, refine search to narrow further.</Typography>
              )}
            </Stack>
          </Box>
          <Divider />
          <Typography variant="caption" color="text.secondary">
            Future: include graph context and alternate suggestions here.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={!selected || !columnName}
        >
          Map Column
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManualMappingModal;

