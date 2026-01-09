import { useLiquidityData } from "@/hooks/useLiquidityData";
import { LiquidityBarChart } from "@/components/LiquidityBarChart";
import { KPICard } from "@/components/KPICard";
import { Loader2 } from "lucide-react";

export default function Metrics() {
    const { data, loading, error } = useLiquidityData();

    if (loading) return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin" /></div>;
    if (error) return <div>Error: {error}</div>;
    if (!data.length) return <div>No data available</div>;

    const latest = data[data.length - 1];

    return (
        <div className="space-y-6 animate-in fade-in duration-500 slide-in-from-bottom-4">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Detailed Metrics</h2>
                <p className="text-muted-foreground">
                    Deep dive into liquidity components and composition.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <LiquidityBarChart data={data} className="col-span-2 glass-card" />
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <KPICard
                    title="Reserve Balances"
                    value={latest.reserve_balances}
                    prefix="$"
                    suffix="B"
                    className="md:col-span-1"
                />
                <KPICard
                    title="Discount Window"
                    value={latest.discount_window}
                    prefix="$"
                    suffix="B"
                    className="md:col-span-1"
                />
                <KPICard
                    title="Metrics Health"
                    value="Stable"
                    className="md:col-span-1"
                    description="Based on 30-day volatility"
                />
            </div>
        </div>
    );
}
