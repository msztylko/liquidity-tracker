import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LiquidityRecord } from '@/hooks/useLiquidityData';
import { format, parseISO } from "date-fns";

interface LiquidityTableProps {
    data: LiquidityRecord[];
    className?: string;
}

export function LiquidityTable({ data, className }: LiquidityTableProps) {
    // Show descending order (newest first)
    const sortedData = [...data].reverse();

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>Historical Data</CardTitle>
                <CardDescription>
                    Detailed daily liquidity metrics (All values in USD Billions)
                </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
                <div className="w-full overflow-auto max-h-[600px]">
                    <table className="w-full caption-bottom text-sm text-left">
                        <thead className="[&_tr]:border-b sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
                            <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground">Date</th>
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Net Liquidity</th>
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Total Assets</th>
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">RRP</th>
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">TGA</th>
                                <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Reserves</th>
                            </tr>
                        </thead>
                        <tbody className="[&_tr:last-child]:border-0">
                            {sortedData.map((row) => (
                                <tr key={row.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                    <td className="p-4 align-middle font-semibold text-foreground/80">{format(parseISO(row.date), 'MMM d, yyyy')}</td>
                                    <td className="p-4 align-middle text-right text-primary font-bold">${row.net_liquidity}B</td>
                                    <td className="p-4 align-middle text-right">${row.total_assets}B</td>
                                    <td className="p-4 align-middle text-right">${row.reverse_repo}B</td>
                                    <td className="p-4 align-middle text-right">${row.tga}B</td>
                                    <td className="p-4 align-middle text-right">${row.reserve_balances}B</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    );
}
