import React from 'react';
import { Box, Paper, Typography, Alert, Stack, Chip } from '@mui/material';

interface ValidationSection {
  status?: string;
  reason?: string;
  error?: string;
  conforms?: boolean;
}

interface StructuralValidation {
  status: string;
  compliance_rate: number;
  domain_violations: number;
  range_violations: number;
  violations: {
    domain_samples: string[];
    range_samples: string[];
  };
}

interface ValidationDashboardProps {
  ontologyValidation?: ValidationSection;
  shaclValidation?: ValidationSection;
  structuralValidation?: StructuralValidation;
}

const ValidationDashboard: React.FC<ValidationDashboardProps> = ({
  ontologyValidation,
  shaclValidation,
  structuralValidation
}) => {
  const hasAny = ontologyValidation || shaclValidation || structuralValidation;
  if (!hasAny) return null;

  return (
    <Paper sx={{ p:3, mt:3 }}>
      <Typography variant="h6" gutterBottom>Validation Dashboard</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb:2 }}>
        Consolidated validation results from ontology constraints, uploaded SHACL shapes, and structural ontology checks.
      </Typography>

      {/* Ontology Validation */}
      {ontologyValidation && (
        <Box sx={{ mb:2 }}>
          <Typography variant="subtitle2" gutterBottom>Ontology SHACL Constraints</Typography>
          {ontologyValidation.status === 'skipped' && (
            <Alert severity="info">Validation skipped: {ontologyValidation.reason}</Alert>
          )}
          {ontologyValidation.status === 'error' && (
            <Alert severity="error">Validation error: {ontologyValidation.error}</Alert>
          )}
          {ontologyValidation.conforms !== undefined && (
            <Alert severity={ontologyValidation.conforms ? 'success' : 'warning'}>
              SHACL conforms (Ontology constraints): {String(ontologyValidation.conforms)}
            </Alert>
          )}
        </Box>
      )}

      {/* SHACL Shapes Validation */}
      {shaclValidation && (
        <Box sx={{ mb:2 }}>
          <Typography variant="subtitle2" gutterBottom>Uploaded SHACL Shapes</Typography>
          {shaclValidation.status === 'skipped' && (
            <Alert severity="info">Validation skipped: {shaclValidation.reason}</Alert>
          )}
          {shaclValidation.status === 'error' && (
            <Alert severity="error">Validation error: {shaclValidation.error}</Alert>
          )}
          {shaclValidation.conforms !== undefined && (
            <Alert severity={shaclValidation.conforms ? 'success' : 'warning'}>
              SHACL conforms (Uploaded shapes): {String(shaclValidation.conforms)}
            </Alert>
          )}
        </Box>
      )}

      {/* Structural Validation */}
      {structuralValidation && (
        <Box sx={{ mb:2 }}>
          <Typography variant="subtitle2" gutterBottom>Ontology Structural Validation</Typography>
          {structuralValidation.status === 'error' && (
            <Alert severity="error">Structural validation error encountered.</Alert>
          )}
          {structuralValidation.status === 'completed' && (
            <Stack spacing={1} sx={{ mb:1 }}>
              <Alert severity={structuralValidation.compliance_rate === 1.0 ? 'success' : 'warning'}>
                Compliance rate: {(structuralValidation.compliance_rate * 100).toFixed(2)}%
              </Alert>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Chip label={`Domain violations: ${structuralValidation.domain_violations}`} size="small" color={structuralValidation.domain_violations>0?'warning':'default'} />
                <Chip label={`Range violations: ${structuralValidation.range_violations}`} size="small" color={structuralValidation.range_violations>0?'warning':'default'} />
              </Stack>
              {(structuralValidation.violations.domain_samples.length > 0 || structuralValidation.violations.range_samples.length > 0) && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Samples:</Typography>
                  {structuralValidation.violations.domain_samples.slice(0,5).map((s,i)=>(
                    <Typography variant="caption" key={i} sx={{ display:'block' }}>{s}</Typography>
                  ))}
                  {structuralValidation.violations.range_samples.slice(0,5).map((s,i)=>(
                    <Typography variant="caption" key={i} sx={{ display:'block' }}>{s}</Typography>
                  ))}
                </Box>
              )}
            </Stack>
          )}
        </Box>
      )}

      <Alert severity="info" sx={{ mt:1 }}>
        Future enhancements: rich violation drill-down, auto-fix suggestions, and downloadable consolidated report.
      </Alert>
    </Paper>
  );
};

export default ValidationDashboard;

