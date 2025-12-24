// Network graph data for competitive landscape visualization

export interface NetworkNode {
  id: string;
  name: string;
  group: 'web4' | 'competitor' | 'collaborator' | 'domain' | 'standard';
  size?: number;
  color?: string;
}

export interface NetworkLink {
  source: string;
  target: string;
  type: 'competes' | 'collaborates' | 'targets' | 'integrates' | 'threatens';
  strength: number;
}

export const networkNodes: NetworkNode[] = [
  // Web4 Core
  { id: 'web4', name: 'Web4', group: 'web4', size: 30 },
  
  // Competitors
  { id: 'auth0', name: 'Auth0 for AI Agents', group: 'competitor', size: 20 },
  { id: 'did', name: 'W3C DID', group: 'competitor', size: 18 },
  { id: 'microsoft', name: 'Microsoft Agent Framework', group: 'competitor', size: 18 },
  
  // Collaborators
  { id: 'solid', name: 'Solid Project', group: 'collaborator', size: 16 },
  { id: 'ipfs', name: 'IPFS', group: 'collaborator', size: 16 },
  { id: 'holochain', name: 'Holochain', group: 'collaborator', size: 12 },
  { id: 'toip', name: 'Trust Over IP', group: 'collaborator', size: 14 },
  
  // Target Domains
  { id: 'energy', name: 'Energy Sector', group: 'domain', size: 15 },
  { id: 'iot', name: 'IoT Devices', group: 'domain', size: 15 },
  { id: 'healthcare', name: 'Healthcare', group: 'domain', size: 12 },
  { id: 'finance', name: 'Finance', group: 'domain', size: 12 },
  
  // Standards
  { id: 'w3c', name: 'W3C', group: 'standard', size: 14 },
  { id: 'ietf', name: 'IETF', group: 'standard', size: 14 },
];

export const networkLinks: NetworkLink[] = [
  // Competitive relationships
  { source: 'auth0', target: 'web4', type: 'competes', strength: 3 },
  { source: 'did', target: 'web4', type: 'competes', strength: 2 },
  { source: 'microsoft', target: 'web4', type: 'competes', strength: 2 },
  
  // Collaborative relationships
  { source: 'web4', target: 'solid', type: 'collaborates', strength: 4 },
  { source: 'web4', target: 'ipfs', type: 'collaborates', strength: 4 },
  { source: 'web4', target: 'holochain', type: 'collaborates', strength: 2 },
  { source: 'web4', target: 'toip', type: 'collaborates', strength: 3 },
  
  // Domain targets
  { source: 'web4', target: 'energy', type: 'targets', strength: 5 },
  { source: 'web4', target: 'iot', type: 'targets', strength: 5 },
  { source: 'web4', target: 'healthcare', type: 'targets', strength: 3 },
  { source: 'web4', target: 'finance', type: 'targets', strength: 3 },
  
  // Standards relationships
  { source: 'web4', target: 'w3c', type: 'integrates', strength: 3 },
  { source: 'web4', target: 'ietf', type: 'integrates', strength: 3 },
  { source: 'did', target: 'w3c', type: 'integrates', strength: 4 },
  
  // Cross-connections
  { source: 'solid', target: 'w3c', type: 'integrates', strength: 3 },
  { source: 'ipfs', target: 'iot', type: 'targets', strength: 2 },
  { source: 'energy', target: 'iot', type: 'integrates', strength: 3 },
];

export const getNodeColor = (group: NetworkNode['group']): string => {
  switch (group) {
    case 'web4':
      return 'oklch(0.65 0.22 250)'; // Primary blue
    case 'competitor':
      return 'oklch(0.60 0.20 0)'; // Red
    case 'collaborator':
      return 'oklch(0.60 0.18 200)'; // Cyan
    case 'domain':
      return 'oklch(0.65 0.16 150)'; // Green
    case 'standard':
      return 'oklch(0.60 0.14 280)'; // Purple
    default:
      return 'oklch(0.50 0.10 250)';
  }
};

export const getLinkColor = (type: NetworkLink['type']): string => {
  switch (type) {
    case 'competes':
      return 'rgba(239, 68, 68, 0.4)'; // Red with transparency
    case 'collaborates':
      return 'rgba(34, 197, 94, 0.4)'; // Green with transparency
    case 'targets':
      return 'rgba(59, 130, 246, 0.4)'; // Blue with transparency
    case 'integrates':
      return 'rgba(168, 85, 247, 0.4)'; // Purple with transparency
    case 'threatens':
      return 'rgba(249, 115, 22, 0.4)'; // Orange with transparency
    default:
      return 'rgba(156, 163, 175, 0.3)';
  }
};
