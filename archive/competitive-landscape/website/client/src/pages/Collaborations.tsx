import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { collaborations } from "@/data/landscapeData";
import { CheckCircle2, Circle, Filter } from "lucide-react";

export default function Collaborations() {
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [strategicFitFilter, setStrategicFitFilter] = useState<string>("all");

  const filteredCollaborations = collaborations.filter((collab) => {
    if (priorityFilter !== "all" && collab.priority !== priorityFilter) return false;
    if (strategicFitFilter !== "all" && collab.strategicFit !== strategicFitFilter) return false;
    return true;
  });

  const getBadgeVariant = (value: string) => {
    switch (value) {
      case 'high':
      case 'excellent':
        return 'default';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'outline';
    }
  };

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Collaboration Opportunities</h1>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Prioritized strategic partnerships and collaboration opportunities for Web4, with detailed implementation plans and mutual benefits.
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              <CardTitle>Filters</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">
                  Priority
                </label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={priorityFilter === "all" ? "default" : "outline"}
                    onClick={() => setPriorityFilter("all")}
                  >
                    All
                  </Button>
                  <Button
                    size="sm"
                    variant={priorityFilter === "high" ? "default" : "outline"}
                    onClick={() => setPriorityFilter("high")}
                  >
                    High
                  </Button>
                  <Button
                    size="sm"
                    variant={priorityFilter === "medium" ? "default" : "outline"}
                    onClick={() => setPriorityFilter("medium")}
                  >
                    Medium
                  </Button>
                  <Button
                    size="sm"
                    variant={priorityFilter === "low" ? "default" : "outline"}
                    onClick={() => setPriorityFilter("low")}
                  >
                    Low
                  </Button>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">
                  Strategic Fit
                </label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={strategicFitFilter === "all" ? "default" : "outline"}
                    onClick={() => setStrategicFitFilter("all")}
                  >
                    All
                  </Button>
                  <Button
                    size="sm"
                    variant={strategicFitFilter === "excellent" ? "default" : "outline"}
                    onClick={() => setStrategicFitFilter("excellent")}
                  >
                    Excellent
                  </Button>
                  <Button
                    size="sm"
                    variant={strategicFitFilter === "high" ? "default" : "outline"}
                    onClick={() => setStrategicFitFilter("high")}
                  >
                    High
                  </Button>
                  <Button
                    size="sm"
                    variant={strategicFitFilter === "medium" ? "default" : "outline"}
                    onClick={() => setStrategicFitFilter("medium")}
                  >
                    Medium
                  </Button>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              Showing {filteredCollaborations.length} of {collaborations.length} opportunities
            </div>
          </CardContent>
        </Card>

        {/* Collaborations List */}
        <div className="space-y-6">
          {filteredCollaborations.map((collab) => (
            <Card key={collab.id} className="hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <CardTitle className="text-2xl mb-2">{collab.name}</CardTitle>
                    <CardDescription className="text-base">
                      {collab.organization} • {collab.type}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant={getBadgeVariant(collab.priority)}>
                      {collab.priority.toUpperCase()} PRIORITY
                    </Badge>
                    <Badge variant="outline">{collab.timeline}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-muted/50">
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Strategic Fit
                    </div>
                    <Badge variant={getBadgeVariant(collab.strategicFit)}>
                      {collab.strategicFit.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Mutual Benefit
                    </div>
                    <Badge variant={getBadgeVariant(collab.mutualBenefit)}>
                      {collab.mutualBenefit.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Feasibility
                    </div>
                    <Badge variant={getBadgeVariant(collab.feasibility)}>
                      {collab.feasibility.toUpperCase()}
                    </Badge>
                  </div>
                </div>

                {/* Rationale */}
                <div>
                  <h4 className="font-semibold mb-2">Rationale</h4>
                  <p className="text-foreground/90">{collab.rationale}</p>
                </div>

                <Tabs defaultValue="benefits" className="w-full">
                  <TabsList className="grid w-full max-w-md grid-cols-2">
                    <TabsTrigger value="benefits">Benefits</TabsTrigger>
                    <TabsTrigger value="steps">Implementation</TabsTrigger>
                  </TabsList>

                  <TabsContent value="benefits" className="space-y-4 mt-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium mb-3 text-primary">For Web4</h5>
                        <ul className="space-y-2">
                          {collab.benefits.forWeb4.map((benefit, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                              <span className="text-sm text-foreground/90">{benefit}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium mb-3 text-primary">For Partner</h5>
                        <ul className="space-y-2">
                          {collab.benefits.forPartner.map((benefit, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                              <span className="text-sm text-foreground/90">{benefit}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="steps" className="mt-4">
                    <div className="space-y-3">
                      {collab.implementationSteps.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                          <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold flex-shrink-0">
                            {idx + 1}
                          </div>
                          <span className="text-foreground/90">{step}</span>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredCollaborations.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Circle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg text-muted-foreground">
                No collaborations match the selected filters
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
