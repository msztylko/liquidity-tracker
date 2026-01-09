import type { VercelRequest, VercelResponse } from '@vercel/node';
import db from '../database/db';

export default function handler(req: VercelRequest, res: VercelResponse) {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    try {
        // Get query params
        const { startDate, endDate } = req.query;

        let query = 'SELECT * FROM liquidity_data ORDER BY date ASC';
        const params: any[] = [];

        if (startDate || endDate) {
            if (startDate && endDate) {
                query = 'SELECT * FROM liquidity_data WHERE date BETWEEN ? AND ? ORDER BY date ASC';
                params.push(startDate, endDate);
            } else if (startDate) {
                query = 'SELECT * FROM liquidity_data WHERE date >= ? ORDER BY date ASC';
                params.push(startDate);
            } else if (endDate) {
                query = 'SELECT * FROM liquidity_data WHERE date <= ? ORDER BY date ASC';
                params.push(endDate);
            }
        }

        const data = db.prepare(query).all(...params);
        res.status(200).json(data);
    } catch (error: any) {
        console.error('Database error:', error);
        res.status(500).json({ error: 'Internal Server Error', details: error.message });
    }
}
