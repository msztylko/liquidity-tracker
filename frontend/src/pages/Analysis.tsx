import { useLiquidityData } from "@/hooks/useLiquidityData";
import { LiquidityPieChart } from "@/components/LiquidityPieChart";
import { LiquidityTable } from "@/components/LiquidityTable";
import { Loader2 } from "lucide-react";

export default function Analysis() {
    const { data, loading, error } = useLiquidityData();

    if (loading) return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin" /></div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="space-y-6 animate-in fade-in duration-700">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Market Analysis</h2>
                <p className="text-muted-foreground">
                    Historical data and structural analysis.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-7">
                <LiquidityPieChart data={data} className="col-span-7 md:col-span-3 glass-card" />
                <div className="col-span-7 md:col-span-4 space-y-4">
                    <div className="p-6 rounded-xl border bg-card/50 backdrop-blur-sm">
                        <h3 className="font-semibold text-lg mb-2">Analyst Note</h3>
                        <p className="text-sm text-muted-foreground">
                            Net Liquidity has shown a consistent correlation with equity market performance over the last 30 days.
                            The TGA build-up remains a key headwind to watch, while RRP drain continues to support reserve levels.
                        </p>
                    </div>
                </div>
            </div>

            <LiquidityTable data={data} className="glass-card" />
        </div>
    );
}
