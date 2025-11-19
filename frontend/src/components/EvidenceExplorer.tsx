/**
 * EvidenceExplorer Component
 *
 * Displays rich evidence from the 17-matcher system showing:
 * - Semantic reasoning (✅)
 * - Ontological validation (⭐)
 * - Structural context (🔗)
 * - Performance metrics
 * - Alternate candidates
 * - Human-readable reasoning summary
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Tooltip,
  IconButton,
  Badge,
  Stack,
  Divider,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  Link as LinkIcon,
  Speed as SpeedIcon,
  Info as InfoIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';

interface EvidenceItem {
  matcher_name: string;
  match_type: string;
  confidence: number;
  matched_via: string;
  evidence_category: string;
}

interface EvidenceGroup {
  category: string;
  evidence_items: EvidenceItem[];
  avg_confidence: number;
  description: string;
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

interface MatchDetail {
  column_name: string;
  matched_property: string;
  match_type: string;
  confidence_score: number;
  matcher_name: string;
  matched_via: string;
  evidence: EvidenceItem[];
  evidence_groups?: EvidenceGroup[];
  reasoning_summary?: string;
  alternates?: AlternateCandidate[];
  performance_metrics?: PerformanceMetrics;
  ambiguity_group_size?: number;
}

interface EvidenceExplorerProps {
  matchDetail: MatchDetail;
  propertyLabel?: string;
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'semantic':
      return <CheckCircleIcon sx={{ color: '#4caf50' }} />;
    case 'ontological_validation':
      return <StarIcon sx={{ color: '#ff9800' }} />;
    case 'structural_context':
      return <LinkIcon sx={{ color: '#2196f3' }} />;
    default:
      return <InfoIcon sx={{ color: '#9e9e9e' }} />;
  }
};

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'semantic':
      return '#4caf50';
    case 'ontological_validation':
      return '#ff9800';
    case 'structural_context':
      return '#2196f3';
    default:
      return '#9e9e9e';
  }
};

const formatConfidence = (confidence: number): string => {
  return `${(confidence * 100).toFixed(1)}%`;
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.9) return '#4caf50';
  if (confidence >= 0.8) return '#8bc34a';
  if (confidence >= 0.7) return '#ffc107';
  if (confidence >= 0.6) return '#ff9800';
  return '#f44336';
};

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({
  matchDetail,
  propertyLabel
}) => {
  const [expandedGroup, setExpandedGroup] = useState<string | false>('semantic');

  const handleGroupChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedGroup(isExpanded ? panel : false);
  };

  const propLabel = propertyLabel || matchDetail.matched_property.split('#').pop() || matchDetail.matched_property;

  return (
    <Card elevation={2} sx={{ mb: 2 }}>
      <CardContent>
        {/* Header with overall confidence */}
        <Stack direction="row" spacing={2} alignItems="center" mb={2}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" gutterBottom>
              {matchDetail.column_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              → {propLabel}
            </Typography>
          </Box>

          <Tooltip title={`Confidence: ${formatConfidence(matchDetail.confidence_score)}`}>
            <Chip
              label={formatConfidence(matchDetail.confidence_score)}
              sx={{
                backgroundColor: getConfidenceColor(matchDetail.confidence_score),
                color: 'white',
                fontWeight: 'bold',
                fontSize: '1.1rem'
              }}
            />
          </Tooltip>

          {/* Performance badge */}
          {matchDetail.performance_metrics && (
            <Tooltip title={
              `Execution: ${matchDetail.performance_metrics.execution_time_ms?.toFixed(1)}ms | ` +
              `Speedup: ${matchDetail.performance_metrics.parallel_speedup?.toFixed(1)}x`
            }>
              <Badge
                badgeContent={`${matchDetail.performance_metrics.matchers_fired || 0}`}
                color="primary"
              >
                <SpeedIcon color="action" />
              </Badge>
            </Tooltip>
          )}
        </Stack>

        {/* Reasoning Summary */}
        {matchDetail.reasoning_summary && (
          <Alert
            icon={<PsychologyIcon />}
            severity="info"
            sx={{ mb: 2 }}
          >
            <Typography variant="body2">
              {matchDetail.reasoning_summary}
            </Typography>
          </Alert>
        )}

        {/* Evidence Groups */}
        {matchDetail.evidence_groups && matchDetail.evidence_groups.length > 0 ? (
          <Box sx={{ mt: 2 }}>
            {matchDetail.evidence_groups.map((group) => (
              <Accordion
                key={group.category}
                expanded={expandedGroup === group.category}
                onChange={handleGroupChange(group.category)}
                sx={{ mb: 1 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ width: '100%' }}>
                    {getCategoryIcon(group.category)}
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {group.description}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {group.evidence_items.length} matcher{group.evidence_items.length !== 1 ? 's' : ''}
                        {' · '}
                        Avg: {formatConfidence(group.avg_confidence)}
                      </Typography>
                    </Box>
                    <Chip
                      label={formatConfidence(group.avg_confidence)}
                      size="small"
                      sx={{
                        backgroundColor: getCategoryColor(group.category),
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  </Stack>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1.5}>
                    {group.evidence_items.map((item, idx) => (
                      <Box key={idx}>
                        <Stack direction="row" spacing={2} alignItems="flex-start">
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {item.matcher_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.matched_via}
                            </Typography>
                          </Box>
                          <Chip
                            label={formatConfidence(item.confidence)}
                            size="small"
                            variant="outlined"
                            sx={{
                              borderColor: getConfidenceColor(item.confidence),
                              color: getConfidenceColor(item.confidence)
                            }}
                          />
                        </Stack>
                        <Box sx={{ mt: 0.5 }}>
                          <LinearProgress
                            variant="determinate"
                            value={item.confidence * 100}
                            sx={{
                              height: 4,
                              borderRadius: 2,
                              backgroundColor: 'rgba(0,0,0,0.1)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: getConfidenceColor(item.confidence)
                              }
                            }}
                          />
                        </Box>
                        {idx < group.evidence_items.length - 1 && (
                          <Divider sx={{ mt: 1.5 }} />
                        )}
                      </Box>
                    ))}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        ) : (
          /* Fallback: Show flat evidence list if groups not available */
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Evidence ({matchDetail.evidence.length} matchers)
            </Typography>
            <Stack spacing={1}>
              {matchDetail.evidence.slice(0, 5).map((item, idx) => (
                <Box key={idx}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="body2" sx={{ flexGrow: 1 }}>
                      {item.matcher_name}
                    </Typography>
                    <Chip
                      label={formatConfidence(item.confidence)}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                </Box>
              ))}
              {matchDetail.evidence.length > 5 && (
                <Typography variant="caption" color="text.secondary">
                  ... and {matchDetail.evidence.length - 5} more matchers
                </Typography>
              )}
            </Stack>
          </Box>
        )}

        {/* Alternate Candidates */}
        {matchDetail.alternates && matchDetail.alternates.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Alternate Candidates
            </Typography>
            <Stack spacing={1}>
              {matchDetail.alternates.map((alt, idx) => (
                <Box key={idx}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="body2" sx={{ flexGrow: 1, fontSize: '0.85rem' }}>
                      {alt.property.split('#').pop()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {alt.evidence_count} evidence
                    </Typography>
                    <Chip
                      label={formatConfidence(alt.combined_confidence)}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.75rem' }}
                    />
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Ambiguity Warning */}
        {matchDetail.ambiguity_group_size && matchDetail.ambiguity_group_size > 1 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              {matchDetail.ambiguity_group_size} similar candidates detected. Manual review recommended.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default EvidenceExplorer;

