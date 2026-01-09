import fs from 'fs';
import path from 'path';
import db from './db';

const MIGRATIONS_DIR = path.join(process.cwd(), 'database', 'migrations');

function runMigrations() {
    console.log('Running migrations...');

    // Ensure migrations table exists (handled in 001 but good practice to handle bootstrap if needed, 
    // actually 001 creates it, but we can't check it if it doesn't exist. 
    // So we might need a bootstrap or just assume files handle it. 
    // For safety, let's just read files and apply if not recorded.)

    // We need to check if migrations table exists first, if not, we must run 001.
    // Actually, let's just force run the first one if table doesn't exist?
    // Better: The first migration CREATEs the table. So we can just try to query it.

    let appliedMigrations = new Set<string>();

    try {
        const rows = db.prepare('SELECT name FROM migrations').all() as { name: string }[];
        rows.forEach(row => appliedMigrations.add(row.name));
    } catch (error: any) {
        if (!error.message.includes('no such table')) {
            throw error;
        }
        // Table doesn't exist, so no migrations applied
    }

    const files = fs.readdirSync(MIGRATIONS_DIR).sort();

    for (const file of files) {
        if (file.endsWith('.sql') && !appliedMigrations.has(file)) {
            console.log(`Applying migration: ${file}`);
            const sql = fs.readFileSync(path.join(MIGRATIONS_DIR, file), 'utf-8');

            const transaction = db.transaction(() => {
                db.exec(sql);
                // Only insert into migrations if the table exists (which it should after 001)
                // If 001 creates the table, we need to be careful.
                // If sql contains creation of migrations table, then we are good.
                // My 001 schema creates it.
                db.prepare('INSERT INTO migrations (name) VALUES (?)').run(file);
            });

            transaction();
        }
    }

    console.log('Migrations complete.');
}

runMigrations();
