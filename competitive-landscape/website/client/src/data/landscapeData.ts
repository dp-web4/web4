// Web4 Competitive Landscape Analysis Data

export interface Competitor {
  id: string;
  name: string;
  category: 'direct' | 'indirect' | 'adjacent' | 'collaborator';
  threatLevel: 'high' | 'medium' | 'low' | 'none';
  description: string;
  approach: string;
  url?: string;
}

export interface Collaboration {
  id: string;
  name: string;
  organization: string;
  type: string;
  strategicFit: 'excellent' | 'high' | 'medium' | 'low';
  mutualBenefit: 'very high' | 'high' | 'medium' | 'low';
  feasibility: 'high' | 'medium' | 'low';
  priority: 'high' | 'medium' | 'low';
  timeline: string;
  rationale: string;
  benefits: {
    forWeb4: string[];
    forPartner: string[];
  };
  implementationSteps: string[];
}

export interface Source {
  id: string;
  title: string;
  authors: string;
  publication: string;
  year: number;
  citations?: number;
  url?: string;
  category: 'academic' | 'commercial' | 'standards' | 'market';
  relevance: string;
}

export const competitors: Competitor[] = [
  {
    id: 'auth0',
    name: 'Auth0 for AI Agents',
    category: 'indirect',
    threatLevel: 'high',
    description: 'Centralized OAuth-based authentication and authorization platform for AI agents',
    approach: 'SaaS platform with Token Vault, async authorization, MCP support',
    url: 'https://auth0.com/ai'
  },
  {
    id: 'did',
    name: 'W3C DID Ecosystem',
    category: 'indirect',
    threatLevel: 'medium',
    description: 'Established decentralized identity standard with 103 method specifications',
    approach: 'Standards-based identity layer, 46 conformant implementations',
    url: 'https://www.w3.org/TR/did-core/'
  },
  {
    id: 'microsoft',
    name: 'Microsoft Agent Framework',
    category: 'indirect',
    threatLevel: 'medium',
    description: 'Azure-integrated .NET framework for building intelligent agents',
    approach: 'Platform-based with Azure AI Foundry integration',
  },
  {
    id: 'solid',
    name: 'Solid Project',
    category: 'collaborator',
    threatLevel: 'none',
    description: 'Data pods for user-controlled personal data storage',
    approach: 'Decentralized data storage with application-data separation',
  },
  {
    id: 'ipfs',
    name: 'IPFS',
    category: 'collaborator',
    threatLevel: 'none',
    description: 'Content-addressed, peer-to-peer file system',
    approach: 'Decentralized storage with content addressing',
  },
  {
    id: 'holochain',
    name: 'Holochain',
    category: 'adjacent',
    threatLevel: 'low',
    description: 'Agent-centric distributed computing framework',
    approach: 'DHT-based validation without global consensus',
  },
];

export const collaborations: Collaboration[] = [
  {
    id: 'solid',
    name: 'Solid Project',
    organization: 'MIT CSAIL, Inrupt',
    type: 'Technology Partnership',
    strategicFit: 'excellent',
    mutualBenefit: 'high',
    feasibility: 'medium',
    priority: 'high',
    timeline: '0-6 months',
    rationale: 'Highly complementary - Solid provides data storage, Web4 provides trust layer',
    benefits: {
      forWeb4: [
        'Access to established ecosystem',
        'Tim Berners-Lee\'s reputation',
        'Practical data storage for audit trails'
      ],
      forPartner: [
        'Trust layer for Solid Pods',
        'Economic metering capabilities',
        'Fine-grained authorization'
      ]
    },
    implementationSteps: [
      'Reach out to Solid team',
      'Propose joint technical working group',
      'Develop proof-of-concept integration',
      'Co-author technical paper',
      'Present at W3C TPAC'
    ]
  },
  {
    id: 'w3c-did',
    name: 'W3C DID Ecosystem',
    organization: 'W3C Decentralized Identifier Working Group',
    type: 'Standards Alignment',
    strategicFit: 'excellent',
    mutualBenefit: 'high',
    feasibility: 'high',
    priority: 'high',
    timeline: '0-6 months',
    rationale: 'Standards legitimacy and interoperability with existing DID infrastructure',
    benefits: {
      forWeb4: [
        'Standards legitimacy',
        'Interoperability with DID ecosystem',
        'Access to established implementations'
      ],
      forPartner: [
        'Practical implementation with trust witnessing',
        'Economic metering extension',
        'AI agent authorization use cases'
      ]
    },
    implementationSteps: [
      'Submit Web4 as DID method',
      'Establish W3C Community Group',
      'Engage with DID ecosystem players',
      'Implement DID-compliant identity layer',
      'Contribute to DID Use Cases document'
    ]
  },
  {
    id: 'ipfs',
    name: 'IPFS',
    organization: 'Protocol Labs',
    type: 'Technical Integration',
    strategicFit: 'high',
    mutualBenefit: 'high',
    feasibility: 'high',
    priority: 'high',
    timeline: '0-6 months',
    rationale: 'Content-addressed storage perfect for Web4 audit trails and delegation records',
    benefits: {
      forWeb4: [
        'Robust decentralized storage',
        'Content addressing for immutability',
        'Distributed audit trail storage'
      ],
      forPartner: [
        'Identity and trust layer',
        'Economic model for storage incentives',
        'Authorization framework'
      ]
    },
    implementationSteps: [
      'Implement IPFS storage backend',
      'Develop technical specification',
      'Create reference implementation',
      'Present at IPFS community events',
      'Publish joint case studies'
    ]
  },
  {
    id: 'iot-research',
    name: 'Blockchain IoT Identity Research',
    organization: 'IEEE, Academic Researchers',
    type: 'Research Collaboration',
    strategicFit: 'high',
    mutualBenefit: 'high',
    feasibility: 'high',
    priority: 'high',
    timeline: '0-12 months',
    rationale: 'Academic validation and production-ready implementation of theoretical concepts',
    benefits: {
      forWeb4: [
        'Academic credibility',
        'Research validation',
        'Publication opportunities'
      ],
      forPartner: [
        'Production-ready implementation',
        'Real-world deployment data',
        'Collaboration opportunities'
      ]
    },
    implementationSteps: [
      'Identify key researchers',
      'Propose joint research collaboration',
      'Submit papers to IEEE conferences',
      'Provide implementation for testbeds',
      'Host academic workshops'
    ]
  },
  {
    id: 'energy',
    name: 'Energy Sector Pilots',
    organization: 'DER providers, Battery manufacturers',
    type: 'Commercial Deployment',
    strategicFit: 'high',
    mutualBenefit: 'very high',
    feasibility: 'medium',
    priority: 'high',
    timeline: '6-18 months',
    rationale: 'Strongest technical alignment - P2P energy trading needs exactly what Web4 provides',
    benefits: {
      forWeb4: [
        'Real-world validation',
        'Case study for other domains',
        'Market traction and revenue'
      ],
      forPartner: [
        'Solution for P2P trading',
        'Device identity for batteries',
        'Trust infrastructure for energy markets'
      ]
    },
    implementationSteps: [
      'Identify pilot partners',
      'Develop pilot proposal',
      'Deploy modbatt-CAN in battery systems',
      'Implement P2P trading platform',
      'Publish case study'
    ]
  },
];

export const keyFindings = {
  uniquePosition: 'Web4 is the only initiative integrating identity, trust accumulation through witnessing, economic metering, and authorization into a complete architectural stack.',
  marketTiming: 'EXCELLENT - AI agent authorization market exploding in 2025',
  primaryThreats: [
    'Auth0 for AI Agents - Centralized solution with rapid time-to-market',
    'W3C DID Ecosystem - Established standard with broad adoption',
    'Microsoft Agent Framework - Azure ecosystem advantage'
  ],
  strategicRecommendations: [
    'Target energy sector for initial deployment',
    'Engage with W3C and IETF for standards recognition',
    'Develop SDKs for major AI agent frameworks',
    'Collaborate with Solid Project and IPFS',
    'Publish academic papers for research credibility'
  ]
};

export const domainAlignment = [
  { domain: 'Energy', alignment: 95, description: 'P2P trading, distributed resources' },
  { domain: 'IoT', alignment: 90, description: '75B devices need identity' },
  { domain: 'Healthcare', alignment: 65, description: 'Patient data sovereignty' },
  { domain: 'Finance', alignment: 60, description: 'DeFi and self-custody' },
];

export const timeline = [
  { date: '2013', event: 'Urbit network launch', category: 'parallel' },
  { date: '2014', event: 'IPFS whitepaper published', category: 'parallel' },
  { date: 'Jul 2022', event: 'W3C DID v1.0 ratified', category: 'standards' },
  { date: 'Jul 2025', event: 'TrustTrack preprint published', category: 'academic' },
  { date: 'Aug 2025', event: 'Hashgraph idTrust launch', category: 'commercial' },
  { date: 'Oct 2025', event: 'Microsoft Agent Framework preview', category: 'commercial' },
  { date: 'Nov 2025', event: 'Auth0 for AI Agents preview', category: 'commercial' },
];
