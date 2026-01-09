import { useLiquidityData } from "@/hooks/useLiquidityData";
import { KPICard } from "@/components/KPICard";
import { LiquidityLineChart } from "@/components/LiquidityLineChart";
import { Loader2 } from "lucide-react";

export default function Overview() {
    const { data, loading, error } = useLiquidityData();

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return <div className="text-destructive">Error: {error}</div>;
    }

    const latest = data[data.length - 1];
    const previous = data[data.length - 2];

    // Helper to calculate change
    const calcChange = (curr: number, prev: number) => ((curr - prev) / prev) * 100;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Market Overview</h2>
                <p className="text-muted-foreground">
                    Real-time tracking of Federal Reserve liquidity dynamics.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KPICard
                    title="Net Liquidity"
                    value={latest.net_liquidity}
                    prefix="$"
                    suffix="B"
                    change={calcChange(latest.net_liquidity, previous.net_liquidity)}
                    description="Total Assets - TGA - RRP"
                />
                <KPICard
                    title="Total Assets"
                    value={latest.total_assets}
                    prefix="$"
                    suffix="B"
                    change={calcChange(latest.total_assets, previous.total_assets)}
                    description="Fed Balance Sheet Size"
                />
                <KPICard
                    title="Reverse Repo"
                    value={latest.reverse_repo}
                    prefix="$"
                    suffix="B"
                    change={calcChange(latest.reverse_repo, previous.reverse_repo)}
                    description="Overnight RRP Operations"
                />
                <KPICard
                    title="TGA"
                    value={latest.tga}
                    prefix="$"
                    suffix="B"
                    change={calcChange(latest.tga, previous.tga)}
                    description="Treasury General Account"
                />
            </div>

            <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-7">
                <LiquidityLineChart className="col-span-7 glass-card" data={data} />
            </div>
        </div>
    );
}
