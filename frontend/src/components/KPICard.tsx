import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface KPICardProps {
    title: string
    value: string | number
    change?: number
    prefix?: string
    suffix?: string
    description?: string
    className?: string
}

export function KPICard({
    title,
    value,
    change,
    prefix = "",
    suffix = "",
    description,
    className
}: KPICardProps) {
    const isPositive = change && change > 0
    const isNegative = change && change < 0

    return (
        <Card className={cn("glass-card overflow-hidden transition-all hover:shadow-lg", className)}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                {change !== undefined && (
                    <div className={cn(
                        "flex items-center text-xs font-bold px-2 py-1 rounded-full",
                        isPositive ? "text-emerald-500 bg-emerald-500/10" :
                            isNegative ? "text-rose-500 bg-rose-500/10" : "text-gray-500 bg-gray-500/10"
                    )}>
                        {isPositive ? <ArrowUpIcon className="h-3 w-3 mr-1" /> :
                            isNegative ? <ArrowDownIcon className="h-3 w-3 mr-1" /> :
                                <MinusIcon className="h-3 w-3 mr-1" />}
                        {Math.abs(change).toFixed(2)}%
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold tracking-tight">
                    {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
                </div>
                {description && (
                    <p className="text-xs text-muted-foreground mt-1">
                        {description}
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
