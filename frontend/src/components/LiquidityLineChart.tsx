import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { format, parseISO } from 'date-fns';
import { LiquidityRecord } from '@/hooks/useLiquidityData';

interface LiquidityLineChartProps {
    data: LiquidityRecord[];
    className?: string;
}

export function LiquidityLineChart({ data, className }: LiquidityLineChartProps) {
    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>Net Liquidity Trends</CardTitle>
                <CardDescription>
                    Tracking Net Liquidity vs TGA and Reverse Repo (Last 30 Days)
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorTga" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="hsl(var(--chart-2))" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="hsl(var(--chart-2))" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" vertical={false} />
                            <XAxis
                                dataKey="date"
                                tickFormatter={(str) => format(parseISO(str), 'MMM d')}
                                className="text-muted-foreground text-xs"
                                tickMargin={10}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                className="text-muted-foreground text-xs"
                                axisLine={false}
                                tickLine={false}
                                tickFormatter={(value) => `$${value / 1000}T`}
                                domain={['auto', 'auto']}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'hsl(var(--popover))',
                                    borderColor: 'hsl(var(--border))',
                                    borderRadius: 'var(--radius)',
                                    color: 'hsl(var(--foreground))'
                                }}
                                labelFormatter={(label) => format(parseISO(label), 'MMM d, yyyy')}
                                formatter={(value: number) => [`$${value.toFixed(2)}B`, '']}
                            />
                            <Area
                                type="monotone"
                                dataKey="net_liquidity"
                                name="Net Liquidity"
                                stroke="hsl(var(--primary))"
                                fillOpacity={1}
                                fill="url(#colorNet)"
                                strokeWidth={2}
                            />
                            <Area
                                type="monotone"
                                dataKey="tga"
                                name="TGA"
                                stroke="hsl(var(--chart-2))"
                                fillOpacity={1}
                                fill="url(#colorTga)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}
