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
          <EvidenceExplorer
            matchDetail={matchDetail}
            propertyLabel={propertyLabel}
          />
        </Box>
      </Box>
    </Drawer>
  );
};

export default EvidenceDrawer;

