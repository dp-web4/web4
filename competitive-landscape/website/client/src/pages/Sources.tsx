import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, ExternalLink, BookOpen, Building2, FileText, TrendingUp } from "lucide-react";

// Sample sources data - in a real app this would come from the analysis
const sources = [
  {
    id: '1',
    title: 'From Cloud-Native to Trust-Native: A Protocol for Verifiable Multi-Agent Systems',
    authors: 'Muyang Li',
    publication: 'arXiv:2507.22077',
    year: 2025,
    category: 'academic',
    relevance: 'Parallel work on trust-native systems for AI agents',
    url: 'https://arxiv.org/abs/2507.22077'
  },
  {
    id: '2',
    title: 'Decentralized Identifiers (DIDs) v1.0',
    authors: 'Sporny, Guy, Sabadello, Reed',
    publication: 'W3C Recommendation',
    year: 2022,
    category: 'standards',
    relevance: 'Official W3C standard for decentralized identity',
    url: 'https://www.w3.org/TR/did-core/'
  },
  {
    id: '3',
    title: 'Auth0 for AI Agents',
    authors: 'Okta',
    publication: 'Product Launch',
    year: 2025,
    category: 'commercial',
    relevance: 'Direct competitor in AI agent authorization',
    url: 'https://auth0.com/ai'
  },
  {
    id: '4',
    title: 'Blockchain-enabled Peer-to-Peer energy trading',
    authors: 'Wongthongtham et al.',
    publication: 'Computers & Industrial Engineering',
    year: 2021,
    citations: 178,
    category: 'academic',
    relevance: 'P2P energy trading with blockchain',
  },
  {
    id: '5',
    title: 'Microsoft Agent Framework Preview',
    authors: 'Microsoft',
    publication: 'Product Announcement',
    year: 2025,
    category: 'commercial',
    relevance: 'Azure-integrated agent development platform',
  },
  {
    id: '6',
    title: 'IPFS - Content Addressed, Versioned, P2P File System',
    authors: 'Juan Benet',
    publication: 'arXiv:1407.3561',
    year: 2014,
    citations: 2653,
    category: 'academic',
    relevance: 'Decentralized storage, potential integration',
  },
];

export default function Sources() {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  const filteredSources = sources.filter((source) => {
    const matchesSearch = 
      source.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.authors.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.relevance.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = categoryFilter === "all" || source.category === categoryFilter;
    
    return matchesSearch && matchesCategory;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'academic': return <BookOpen className="h-4 w-4" />;
      case 'commercial': return <Building2 className="h-4 w-4" />;
      case 'standards': return <FileText className="h-4 w-4" />;
      case 'market': return <TrendingUp className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'academic': return 'default';
      case 'commercial': return 'secondary';
      case 'standards': return 'outline';
      case 'market': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Source Database</h1>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Comprehensive reference database of all sources cited in the competitive landscape analysis.
          </p>
        </div>

        {/* Search and Filters */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Search & Filter</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, author, or relevance..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant={categoryFilter === "all" ? "default" : "outline"}
                onClick={() => setCategoryFilter("all")}
              >
                All Sources
              </Button>
              <Button
                size="sm"
                variant={categoryFilter === "academic" ? "default" : "outline"}
                onClick={() => setCategoryFilter("academic")}
                className="gap-2"
              >
                <BookOpen className="h-4 w-4" />
                Academic
              </Button>
              <Button
                size="sm"
                variant={categoryFilter === "commercial" ? "default" : "outline"}
                onClick={() => setCategoryFilter("commercial")}
                className="gap-2"
              >
                <Building2 className="h-4 w-4" />
                Commercial
              </Button>
              <Button
                size="sm"
                variant={categoryFilter === "standards" ? "default" : "outline"}
                onClick={() => setCategoryFilter("standards")}
                className="gap-2"
              >
                <FileText className="h-4 w-4" />
                Standards
              </Button>
              <Button
                size="sm"
                variant={categoryFilter === "market" ? "default" : "outline"}
                onClick={() => setCategoryFilter("market")}
                className="gap-2"
              >
                <TrendingUp className="h-4 w-4" />
                Market Research
              </Button>
            </div>

            <div className="text-sm text-muted-foreground">
              Showing {filteredSources.length} of {sources.length} sources
            </div>
          </CardContent>
        </Card>

        {/* Sources List */}
        <div className="space-y-4">
          {filteredSources.map((source) => (
            <Card key={source.id} className="hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-start gap-3 mb-2">
                      {getCategoryIcon(source.category)}
                      <CardTitle className="text-lg leading-tight">{source.title}</CardTitle>
                    </div>
                    <CardDescription className="text-base">
                      {source.authors} • {source.publication} ({source.year})
                      {source.citations && ` • ${source.citations} citations`}
                    </CardDescription>
                  </div>
                  <div className="flex flex-col gap-2 items-end">
                    <Badge variant={getCategoryColor(source.category)}>
                      {source.category.toUpperCase()}
                    </Badge>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:text-primary/80 transition-colors"
                      >
                        <Button size="sm" variant="ghost" className="gap-2">
                          <ExternalLink className="h-4 w-4" />
                          View Source
                        </Button>
                      </a>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="p-3 rounded-lg bg-muted/30">
                  <span className="text-sm font-medium text-muted-foreground">Relevance: </span>
                  <span className="text-sm text-foreground/90">{source.relevance}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredSources.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg text-muted-foreground">
                No sources match your search criteria
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
