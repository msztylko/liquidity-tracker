import { subDays, format } from 'date-fns';
import db from './db';

function seed() {
    console.log('Seeding database...');

    // Clear existing data
    db.prepare('DELETE FROM liquidity_data').run();

    const insert = db.prepare(`
    INSERT INTO liquidity_data (
      date, total_assets, reverse_repo, tga, reserve_balances, discount_window, net_liquidity
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

    const transaction = db.transaction(() => {
        // Generate 30 days of data
        for (let i = 30; i >= 0; i--) {
            const date = format(subDays(new Date(), i), 'yyyy-MM-dd');

            // Base values (in billions) approx realistic for 2024
            // Total Assets: ~7200
            // RRP: ~400-500
            // TGA: ~700-800
            // Reserves: ~3000-3200
            // Discount Window: ~5-10

            // Add some random fluctuation
            const total_assets = 7200 + (Math.random() * 50 - 25) + (i * 2); // Slow uptrend
            const reverse_repo = 450 + (Math.random() * 100 - 50);
            const tga = 750 + (Math.random() * 200 - 100); // Volatile
            const discount_window = 7 + (Math.random() * 5 - 2);

            // Balance sheet identity roughly: Assets = Liabilities + Capital
            // Liabilities include RRP, TGA, Reserves, Currency in Circulation
            // We'll just generate Reserves as ensuring equation balances or just independent?
            // User asked for dummy data, let's make it look correlated but simple.

            // Net Liquidity = Total Assets - TGA - RRP (Simplified Fed Liquidity formula often used by traders)
            const net_liquidity = total_assets - tga - reverse_repo;

            // Reserve balances usually loosely correlated to Net Liquidity but strict formula is complex.
            const reserve_balances = net_liquidity - 2300; // Subtract currency in circulation proxy

            insert.run(
                date,
                parseFloat(total_assets.toFixed(2)),
                parseFloat(reverse_repo.toFixed(2)),
                parseFloat(tga.toFixed(2)),
                parseFloat(reserve_balances.toFixed(2)),
                parseFloat(discount_window.toFixed(2)),
                parseFloat(net_liquidity.toFixed(2))
            );
        }
    });

    transaction();
    console.log('Seeding complete.');
}

seed();
