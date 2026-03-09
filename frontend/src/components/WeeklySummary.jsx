import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Calendar, TrendingUp } from 'lucide-react';

export function WeeklySummary({ weeklyData }) {
  if (!weeklyData || weeklyData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Weekly Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            No data yet. Start tracking!
          </p>
        </CardContent>
      </Card>
    );
  }

  const today = new Date().toISOString().split('T')[0];
  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Weekly Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {weeklyData.map((day) => {
            const date = new Date(day.date + 'T00:00:00');
            const dayName = daysOfWeek[date.getDay()];
            const isToday = day.date === today;

            return (
              <div
                key={day.date}
                className={`
                  p-4 rounded-lg border transition-colors
                  ${isToday 
                    ? 'bg-primary/5 border-primary' 
                    : 'bg-card hover:bg-accent/50 border-border'
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold">
                        {dayName}
                      </p>
                      {isToday && (
                        <Badge variant="default" className="text-xs">Today</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{day.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">
                      {day.total_calories}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {day.entry_count} meal{day.entry_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
