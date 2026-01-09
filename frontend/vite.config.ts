import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import db from "./database/db"

export default defineConfig({
    plugins: [
        react(),
        {
            name: 'configure-server',
            configureServer(server) {
                server.middlewares.use('/api/liquidity', (req, res) => {
                    try {
                        // Parse query params manually since middleware doesn't parse them as express does
                        const url = new URL(req.url || '', `http://${req.headers.host}`);
                        const startDate = url.searchParams.get('startDate');
                        const endDate = url.searchParams.get('endDate');

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
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify(data));
                    } catch (error) {
                        console.error(error);
                        res.statusCode = 500;
                        res.end(JSON.stringify({ error: 'Internal Server Error' }));
                    }
                });
            }
        }
    ],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
})
