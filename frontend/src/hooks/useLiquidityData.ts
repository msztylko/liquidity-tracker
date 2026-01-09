import { useState, useEffect } from 'react';

export interface LiquidityRecord {
    id: number;
    date: string;
    total_assets: number;
    reverse_repo: number;
    tga: number;
    reserve_balances: number;
    discount_window: number;
    net_liquidity: number;
}

export function useLiquidityData() {
    const [data, setData] = useState<LiquidityRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                setLoading(true);
                // Use relative URL to leverage Vite proxy
                const response = await fetch('/api/liquidity');
                if (!response.ok) {
                    throw new Error(`Error fetching data: ${response.statusText}`);
                }
                const result = await response.json();
                setData(result);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }

        fetchData();
    }, []);

    return { data, loading, error };
}
