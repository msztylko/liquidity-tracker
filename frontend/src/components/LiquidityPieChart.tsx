import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LiquidityRecord } from '@/hooks/useLiquidityData';

interface LiquidityPieChartProps {
    data: LiquidityRecord[];
    className?: string;
}

export function LiquidityPieChart({ data, className }: LiquidityPieChartProps) {
    const latest = data[data.length - 1];

    if (!latest) return null;

    const chartData = [
        { name: 'Reserve Balances', value: latest.reserve_balances, color: 'hsl(var(--primary))' },
        { name: 'Reverse Repo (RRP)', value: latest.reverse_repo, color: 'hsl(var(--chart-2))' },
        { name: 'TGA', value: latest.tga, color: 'hsl(var(--chart-5))' },
    ];

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>Current Liability Distribution</CardTitle>
                <CardDescription>
                    Composition of major Fed liabilities as of today
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[350px] w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                innerRadius={80}
                                outerRadius={120}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'hsl(var(--popover))',
                                    borderColor: 'hsl(var(--border))',
                                    borderRadius: 'var(--radius)',
                                    color: 'hsl(var(--foreground))'
                                }}
                                formatter={(value: number) => `$${value.toFixed(2)}B`}
                            />
                            <Legend verticalAlign="bottom" height={36} />
                        </PieChart>
                    </ResponsiveContainer>
                    {/* Centered Total Assets Text */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none pb-8">
                        <div className="text-3xl font-bold tracking-tighter">${(latest.total_assets / 1000).toFixed(1)}T</div>
                        <div className="text-xs text-muted-foreground uppercase tracking-wider">Total Assets</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
