import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { competitors } from "@/data/landscapeData";
import NetworkGraph from "@/components/NetworkGraph";
import { ExternalLink } from "lucide-react";

export default function Landscape() {
  const getThreatBadgeVariant = (level: string) => {
    switch (level) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'direct': return 'Direct Competitor';
      case 'indirect': return 'Indirect Competitor';
      case 'adjacent': return 'Adjacent Innovator';
      case 'collaborator': return 'Potential Collaborator';
      default: return category;
    }
  };

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Competitive Landscape</h1>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Interactive visualization of Web4's competitive positioning, showing relationships with competitors, collaborators, and target domains.
          </p>
        </div>

        <Tabs defaultValue="network" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="network">Network View</TabsTrigger>
            <TabsTrigger value="list">List View</TabsTrigger>
          </TabsList>

          <TabsContent value="network" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Interactive Network Graph</CardTitle>
                <CardDescription>
                  Explore the competitive landscape through an interactive force-directed graph. 
                  Drag nodes to rearrange, zoom to explore, and hover for details.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="w-full h-[600px] bg-card rounded-lg border border-border overflow-hidden">
                  <NetworkGraph />
                </div>
                <div className="mt-4 flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'oklch(0.65 0.22 250)' }} />
                    <span className="text-muted-foreground">Web4</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'oklch(0.60 0.20 0)' }} />
                    <span className="text-muted-foreground">Competitors</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'oklch(0.60 0.18 200)' }} />
                    <span className="text-muted-foreground">Collaborators</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'oklch(0.65 0.16 150)' }} />
                    <span className="text-muted-foreground">Target Domains</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'oklch(0.60 0.14 280)' }} />
                    <span className="text-muted-foreground">Standards Bodies</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="list" className="space-y-6">
            <div className="grid gap-6">
              {competitors.map((competitor) => (
                <Card key={competitor.id} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <CardTitle className="text-xl">{competitor.name}</CardTitle>
                          {competitor.url && (
                            <a 
                              href={competitor.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-primary hover:text-primary/80 transition-colors"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                        </div>
                        <CardDescription>{competitor.description}</CardDescription>
                      </div>
                      <div className="flex flex-col gap-2 items-end">
                        <Badge variant="outline">
                          {getCategoryLabel(competitor.category)}
                        </Badge>
                        {competitor.threatLevel !== 'none' && (
                          <Badge variant={getThreatBadgeVariant(competitor.threatLevel)}>
                            {competitor.threatLevel.toUpperCase()} THREAT
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div>
                        <span className="text-sm font-medium text-muted-foreground">Approach:</span>
                        <p className="text-foreground/90 mt-1">{competitor.approach}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
