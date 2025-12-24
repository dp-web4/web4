import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "wouter";
import { ArrowRight, Target, TrendingUp, Users, Zap } from "lucide-react";
import { keyFindings, domainAlignment } from "@/data/landscapeData";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent" />
        <div className="container relative py-20 md:py-32">
          <div className="max-w-3xl">
            <Badge className="mb-4" variant="secondary">
              Competitive Analysis • November 2025
            </Badge>
            <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
              Web4 Competitive Landscape Analysis
            </h1>
            <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
              Comprehensive analysis of the competitive and collaborative landscape for Web4's trust-native internet architecture, featuring interactive visualizations and strategic insights.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/landscape">
                <a>
                  <Button size="lg" className="gap-2">
                    Explore Landscape <ArrowRight className="h-4 w-4" />
                  </Button>
                </a>
              </Link>
              <Link href="/collaborations">
                <a>
                  <Button size="lg" variant="outline" className="gap-2">
                    View Collaborations
                  </Button>
                </a>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Key Findings */}
      <section className="py-16 bg-card/30">
        <div className="container">
          <h2 className="text-3xl font-bold mb-8">Key Findings</h2>
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl mb-2">Unique Position</CardTitle>
                    <CardDescription>Market Differentiation</CardDescription>
                  </div>
                  <Target className="h-8 w-8 text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-foreground/90">{keyFindings.uniquePosition}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl mb-2">Market Timing</CardTitle>
                    <CardDescription>Opportunity Assessment</CardDescription>
                  </div>
                  <TrendingUp className="h-8 w-8 text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <Badge className="mb-3" variant="default">EXCELLENT</Badge>
                <p className="text-foreground/90">{keyFindings.marketTiming}</p>
              </CardContent>
            </Card>
          </div>

          {/* Primary Threats */}
          <Card className="mb-8">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl mb-2">Primary Competitive Threats</CardTitle>
                  <CardDescription>Key competitors to monitor</CardDescription>
                </div>
                <Zap className="h-8 w-8 text-destructive" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {keyFindings.primaryThreats.map((threat, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                    <div className="w-6 h-6 rounded-full bg-destructive/20 text-destructive flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {index + 1}
                    </div>
                    <p className="text-foreground/90">{threat}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Strategic Recommendations */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl mb-2">Strategic Recommendations</CardTitle>
                  <CardDescription>Prioritized action items</CardDescription>
                </div>
                <Users className="h-8 w-8 text-primary" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {keyFindings.strategicRecommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {index + 1}
                    </div>
                    <p className="text-foreground/90">{rec}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Domain Alignment */}
      <section className="py-16">
        <div className="container">
          <h2 className="text-3xl font-bold mb-8">Target Domain Alignment</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {domainAlignment.map((domain) => (
              <Card key={domain.domain} className="relative overflow-hidden">
                <div 
                  className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 hover:opacity-100 transition-opacity"
                  style={{ opacity: domain.alignment / 200 }}
                />
                <CardHeader className="relative">
                  <CardTitle className="text-lg">{domain.domain}</CardTitle>
                  <CardDescription>{domain.description}</CardDescription>
                </CardHeader>
                <CardContent className="relative">
                  <div className="flex items-end gap-2 mb-2">
                    <span className="text-4xl font-bold text-primary">{domain.alignment}</span>
                    <span className="text-muted-foreground mb-1">%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${domain.alignment}%` }}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-card/30">
        <div className="container text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Explore?</h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Dive into interactive visualizations, explore collaboration opportunities, and discover strategic insights.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href="/landscape">
              <a>
                <Button size="lg" className="gap-2">
                  Interactive Landscape <ArrowRight className="h-4 w-4" />
                </Button>
              </a>
            </Link>
            <Link href="/insights">
              <a>
                <Button size="lg" variant="outline">
                  View All Insights
                </Button>
              </a>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
