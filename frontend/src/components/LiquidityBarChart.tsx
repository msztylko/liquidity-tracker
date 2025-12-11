import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { format, parseISO } from 'date-fns';
import { LiquidityRecord } from '@/hooks/useLiquidityData';

interface LiquidityBarChartProps {
    data: LiquidityRecord[];
    className?: string;
}

export function LiquidityBarChart({ data, className }: LiquidityBarChartProps) {
    // Show only last 7 days for bar chart to avoid crowding
    const chartData = data.slice(-7);

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>Liquidity Composition (Last 7 Days)</CardTitle>
                <CardDescription>
                    breakdown of Reserve Balances vs RRP
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
                            />
                            <Tooltip
                                cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                                contentStyle={{
                                    backgroundColor: 'hsl(var(--popover))',
                                    borderColor: 'hsl(var(--border))',
                                    borderRadius: 'var(--radius)',
                                    color: 'hsl(var(--foreground))'
                                }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                            <Bar dataKey="reserve_balances" name="Reserve Balances" stackId="a" fill="hsl(var(--chart-4))" radius={[0, 0, 4, 4]} />
                            <Bar dataKey="reverse_repo" name="Reverse Repo" stackId="a" fill="hsl(var(--chart-5))" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}
