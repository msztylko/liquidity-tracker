# Federal Reserve Liquidity Tracker

A modern React dashboard for tracking Federal Reserve liquidity indicators.

## Features

- **Real-time Visualization**: Interactive charts for Net Liquidity, Total Assets, RRP, and TGA.
- **Detailed Metrics**: Breakdown of liquidity components.
- **Historical Analysis**: Data table with 30-day history.
- **Premium UI**: Glassmorphism design with dark mode and smooth animations.

## Tech Stack

- **Frontend**: Vite + React + TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui
- **Charts**: Recharts
- **Database**: SQLite (better-sqlite3)
- **Deployment**: Vercel (Support for Serverless Functions)

## Project Structure

```
├── frontend/
│   ├── api/               # Serverless function for API
│   ├── database/          # Database, migrations, and seeds
│   ├── src/               # React application source
│   ├── public/            # Static assets
│   ├── index.html         # Entry HTML
│   ├── package.json       # Project dependencies
│   └── vite.config.ts     # Vite configuration
└── README.md
```

## API Documentation

### `GET /api/liquidity`

Fetches liquidity data from the database.

**Query Parameters:**
- `startDate` (optional): Filter data on or after this date (YYYY-MM-DD)
- `endDate` (optional): Filter data on or before this date (YYYY-MM-DD)

**Response:**
Array of objects containing: `date`, `total_assets`, `reverse_repo`, `tga`, `reserve_balances`, `discount_window`, `net_liquidity`.

## Getting Started

### Prerequisites

- Node.js (v18+)
- npm

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

### Local Development

1. Run database migrations:
   ```bash
   npm run migrate
   ```

2. Seed database with dummy data:
   ```bash
   npm run seed
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The app will be available at [http://localhost:5173](http://localhost:5173).
The API will be available at [http://localhost:5173/api/liquidity](http://localhost:5173/api/liquidity).

## Deployment

This project is configured for deployment on Vercel.

1. Push to GitHub
2. Import project in Vercel
3. Ensure the `api` function is recognized.
4. **Important**: Since SQLite is file-based, it works in Vercel Serverless ONLY for read-only if you commit the DB, or if you use a cloud database (like Turso or Neon) for production.
   - *Current Configuration*: Uses a local SQLite file. This works for the demo (if committed) but data won't persist across redeploys or be writable in standard Vercel environment.
   - The dummy data generation happens locally. Ensure `liquidity.db` is not gitignored if you want to deploy with data, or run the seeder in a build step (but Vercel build is static).
   - *Recommendation*: For this demo, commit the `liquidity.db` file (remove it from .gitignore if present, or use a generated one).
   - Currently `liquidity.db` is NOT in .gitignore (only standard python stuff was there).

## License

MIT
