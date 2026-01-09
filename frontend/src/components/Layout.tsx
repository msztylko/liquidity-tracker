import { useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { LayoutDashboard, BarChart3, PieChart, Info, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Layout() {
    const location = useLocation()
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)

    const navItems = [
        { name: 'Overview', path: '/overview', icon: LayoutDashboard },
        { name: 'Metrics', path: '/metrics', icon: BarChart3 },
        { name: 'Analysis', path: '/analysis', icon: PieChart },
    ]

    return (
        <div className="min-h-screen bg-background text-foreground flex overflow-hidden">
            {/* Sidebar for Desktop */}
            <aside className="hidden md:flex w-64 flex-col border-r bg-card/50 backdrop-blur-xl">
                <div className="p-6 border-b border-border/50">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                            <span className="text-primary-foreground font-bold">L</span>
                        </div>
                        <h1 className="font-bold text-xl tracking-tight">Liquidity<span className="text-primary">Tracker</span></h1>
                    </div>
                </div>
                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = location.pathname === item.path
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                                    isActive
                                        ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                )}
                            >
                                <Icon className={cn("h-5 w-5", isActive ? "text-primary-foreground" : "text-muted-foreground")} />
                                {item.name}
                            </Link>
                        )
                    })}
                </nav>
                <div className="p-4 border-t border-border/50">
                    <div className="rounded-lg bg-muted/50 p-4">
                        <div className="flex items-center gap-2 text-sm font-semibold mb-1">
                            <Info className="h-4 w-4 text-primary" />
                            <span>Fed Data Source</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Data sourced from dummy Federal Reserve liquidity indicators. Updated daily.
                        </p>
                    </div>
                    <div className="mt-4 text-xs text-center text-muted-foreground">
                        v1.0.0
                    </div>
                </div>
            </aside>

            {/* Mobile Header & Sidebar */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="md:hidden flex items-center justify-between p-4 border-b bg-card/50 backdrop-blur-md sticky top-0 z-20">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                            <span className="text-primary-foreground font-bold">L</span>
                        </div>
                        <h1 className="font-bold text-lg">Liquidity<span className="text-primary">Tracker</span></h1>
                    </div>
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded-md hover:bg-muted"
                    >
                        {isSidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                    </button>
                </header>

                {isSidebarOpen && (
                    <div className="md:hidden fixed inset-0 z-10 bg-background/80 backdrop-blur-sm top-16" onClick={() => setIsSidebarOpen(false)}>
                        <nav className="bg-card p-4 space-y-2 shadow-xl border-b" onClick={e => e.stopPropagation()}>
                            {navItems.map((item) => {
                                const Icon = item.icon
                                const isActive = location.pathname === item.path
                                return (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        onClick={() => setIsSidebarOpen(false)}
                                        className={cn(
                                            "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                                            isActive
                                                ? "bg-primary text-primary-foreground"
                                                : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                        )}
                                    >
                                        <Icon className="h-5 w-5" />
                                        {item.name}
                                    </Link>
                                )
                            })}
                        </nav>
                    </div>
                )}

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto p-4 md:p-8 relative">
                    {/* Background Gradient Orbs */}
                    <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
                        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-primary/5 blur-[100px]" />
                        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-blue-500/5 blur-[100px]" />
                    </div>

                    <Outlet />
                </main>
            </div>
        </div>
    )
}
