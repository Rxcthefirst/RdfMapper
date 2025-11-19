import React from 'react';
import {
  Drawer,
  Box,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { EvidenceExplorer } from './EvidenceExplorer';

interface EvidenceItem {
  matcher_name: string;
  match_type: string;
  confidence: number;
  matched_via: string;
  evidence_category?: string;
}

interface EvidenceGroup {
  category: string;
  evidence_items: EvidenceItem[];
  avg_confidence: number;
  description: string;
}

interface AdjustmentItem {
  type: string;
  value: number;
}

interface AlternateCandidate {
  property: string;
  combined_confidence: number;
  evidence_count: number;
}

interface PerformanceMetrics {
  execution_time_ms?: number;
  matchers_fired?: number;
  matchers_succeeded?: number;
  parallel_speedup?: number;
}

export interface MatchDetail {
  column_name: string;
  matched_property: string;
  match_type: string;
  confidence_score: number;
  matcher_name: string;
  matched_via: string;
  evidence?: EvidenceItem[];
  evidence_groups?: EvidenceGroup[];
  reasoning_summary?: string;
  boosters_applied?: AdjustmentItem[];
  penalties_applied?: AdjustmentItem[];
  ambiguity_group_size?: number | null;
  alternates?: AlternateCandidate[];
  performance_metrics?: PerformanceMetrics;
}

interface EvidenceDrawerProps {
  open: boolean;
  onClose: () => void;
  matchDetail: MatchDetail | null;
  onSwitchToAlternate?: (columnName: string, newProperty: string) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  open,
  onClose,
  matchDetail,
  onSwitchToAlternate,
}) => {
  if (!matchDetail) return null;

  // Extract property label from URI
  const propertyLabel = matchDetail.matched_property.split('#').pop()?.split('/').pop() || matchDetail.matched_property;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 500, md: 650 },
          padding: 2,
        },
      }}
    >
      <Box sx={{ position: 'relative' }}>
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 0,
            top: 0,
            zIndex: 1,
          }}
        >
          <CloseIcon />
        </IconButton>

        <Box sx={{ mt: 6 }}>
          {/* Use the new EvidenceExplorer component with rich evidence categorization */}
          <EvidenceExplorer
            matchDetail={matchDetail}
            propertyLabel={propertyLabel}
          />
        </Box>
      </Box>
    </Drawer>
  );
};

      {/* Ambiguity Warning */}
      {hasAmbiguity && (
        <Alert severity="warning" icon={<WarningAmberIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Ambiguity Detected:</strong> {matchDetail.ambiguity_group_size} properties had similar confidence scores. An ambiguity penalty was applied. Review alternates below.
          </Typography>
        </Alert>
      )}

      {/* Evidence Stack */}
      {hasEvidence && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoOutlinedIcon fontSize="small" />
              Evidence Stack ({matchDetail.evidence!.length} matchers)
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Matcher</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Score</TableCell>
                    <TableCell>Matched Via</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {matchDetail.evidence!.map((ev, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {ev.matcher_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={getMatchTypeLabel(ev.match_type)} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color={`${getConfidenceColor(ev.confidence)}.main`} sx={{ fontWeight: 600 }}>
                          {(ev.confidence * 100).toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {ev.matched_via}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Adjustments (Boosters & Penalties) */}
      {(hasBoosters || hasPenalties) && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon fontSize="small" />
              Confidence Adjustments
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              {hasBoosters && (
                <Box>
                  <Typography variant="subtitle2" color="success.main" gutterBottom>
                    Boosters Applied
                  </Typography>
                  {matchDetail.boosters_applied!.map((boost, idx) => (
                    <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <TrendingUpIcon fontSize="small" color="success" />
                      <Typography variant="body2">
                        {boost.type.replace(/_/g, ' ')}: <strong>+{(boost.value * 100).toFixed(1)}%</strong>
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
              {hasPenalties && (
                <Box>
                  <Typography variant="subtitle2" color="warning.main" gutterBottom>
                    Penalties Applied
                  </Typography>
                  {matchDetail.penalties_applied!.map((penalty, idx) => (
                    <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <TrendingDownIcon fontSize="small" color="warning" />
                      <Typography variant="body2">
                        {penalty.type.replace(/_/g, ' ')}: <strong>−{(penalty.value * 100).toFixed(1)}%</strong>
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Stack>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Alternate Properties */}
      {hasAlternates && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1">
              Alternate Properties ({matchDetail.alternates!.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              These properties were also considered but had lower combined confidence scores.
            </Typography>
            <Stack spacing={1} sx={{ mt: 2 }}>
              {matchDetail.alternates!.map((alt, idx) => (
                <Paper
                  key={idx}
                  variant="outlined"
                  sx={{ p: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', '&:hover': { bgcolor: 'action.hover' } }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {alt.property.split('#').pop()?.split('/').pop()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {alt.evidence_count} evidence item{alt.evidence_count !== 1 ? 's' : ''}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="Combined confidence score">
                      <Chip label={`${(alt.combined_confidence * 100).toFixed(1)}%`} size="small" color={getConfidenceColor(alt.combined_confidence)} />
                    </Tooltip>
                    {onSwitchToAlternate && (
                      <Button size="small" variant="outlined" onClick={() => onSwitchToAlternate(matchDetail.column_name, alt.property)}>Use</Button>
                    )}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Matched Via Details */}
      <Paper elevation={1} sx={{ p: 2, mt: 3, bgcolor: 'background.default' }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Primary Match Reason
        </Typography>
        <Typography variant="body2">{matchDetail.matched_via}</Typography>
      </Paper>

      {/* Help Text */}
      <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>How to interpret:</strong> The evidence stack shows all matchers that contributed to this decision. The final score combines the base confidence with boosters (e.g., type compatibility) and penalties (e.g., ambiguity).
        </Typography>
      </Alert>
    </Drawer>
  );
};
export default EvidenceDrawer;

