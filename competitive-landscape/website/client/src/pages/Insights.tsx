import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { timeline, domainAlignment } from "@/data/landscapeData";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts';

export default function Insights() {
  const timelineData = timeline.map((item, idx) => ({
    ...item,
    index: idx,
    year: item.date.includes('2025') ? parseInt(item.date.split(' ')[1] || '2025') : parseInt(item.date),
  }));

  const radarData = domainAlignment.map(d => ({
    domain: d.domain,
    alignment: d.alignment,
  }));

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Strategic Insights</h1>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Data-driven insights and visualizations from the competitive landscape analysis.
          </p>
        </div>

        <div className="grid gap-6">
          {/* Domain Alignment */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Domain Alignment Analysis</CardTitle>
                <CardDescription>
                  Technical fit assessment across target sectors
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={domainAlignment}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 10%)" />
                    <XAxis 
                      dataKey="domain" 
                      stroke="oklch(0.705 0.015 286.067)"
                      style={{ fontSize: '12px' }}
                    />
                    <YAxis 
                      stroke="oklch(0.705 0.015 286.067)"
                      style={{ fontSize: '12px' }}
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'oklch(0.21 0.006 285.885)',
                        border: '1px solid oklch(1 0 0 / 10%)',
                        borderRadius: '8px',
                        color: 'oklch(0.85 0.005 65)'
                      }}
                    />
                    <Bar dataKey="alignment" fill="oklch(0.65 0.22 250)" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Domain Radar Chart</CardTitle>
                <CardDescription>
                  Multi-dimensional alignment view
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="oklch(1 0 0 / 10%)" />
                    <PolarAngleAxis 
                      dataKey="domain" 
                      stroke="oklch(0.705 0.015 286.067)"
                      style={{ fontSize: '12px' }}
                    />
                    <PolarRadiusAxis 
                      angle={90} 
                      domain={[0, 100]}
                      stroke="oklch(0.705 0.015 286.067)"
                      style={{ fontSize: '12px' }}
                    />
                    <Radar 
                      name="Alignment" 
                      dataKey="alignment" 
                      stroke="oklch(0.65 0.22 250)" 
                      fill="oklch(0.65 0.22 250)" 
                      fillOpacity={0.6} 
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Market Timeline</CardTitle>
              <CardDescription>
                Key developments in the competitive landscape (2013-2025)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 10%)" />
                  <XAxis 
                    dataKey="date" 
                    stroke="oklch(0.705 0.015 286.067)"
                    style={{ fontSize: '11px' }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis hide />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'oklch(0.21 0.006 285.885)',
                      border: '1px solid oklch(1 0 0 / 10%)',
                      borderRadius: '8px',
                      color: 'oklch(0.85 0.005 65)'
                    }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-card border border-border rounded-lg p-3">
                            <p className="font-semibold">{data.date}</p>
                            <p className="text-sm text-muted-foreground">{data.event}</p>
                            <p className="text-xs text-primary mt-1 capitalize">{data.category}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="index" 
                    stroke="oklch(0.65 0.22 250)" 
                    strokeWidth={2}
                    dot={{ fill: 'oklch(0.65 0.22 250)', r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="mt-6 space-y-2">
                {timeline.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                    <div className="w-20 flex-shrink-0 text-sm font-medium text-primary">
                      {item.date}
                    </div>
                    <div className="flex-1">
                      <p className="text-foreground/90">{item.event}</p>
                      <p className="text-xs text-muted-foreground mt-1 capitalize">{item.category}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Key Insights Cards */}
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Strongest Alignment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary mb-2">Energy Sector</div>
                <p className="text-sm text-muted-foreground">
                  95% technical alignment with P2P energy trading and distributed resource management
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Market Acceleration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary mb-2">2025</div>
                <p className="text-sm text-muted-foreground">
                  Multiple major players entering AI agent authorization space, validating market demand
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Collaboration Potential</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary mb-2">5 High Priority</div>
                <p className="text-sm text-muted-foreground">
                  Strategic partnerships identified with excellent mutual benefit and feasibility
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
