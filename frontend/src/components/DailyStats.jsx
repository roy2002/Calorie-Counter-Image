import { Card, CardContent } from './ui/card';
import { Flame, Utensils } from 'lucide-react';

export function DailyStats({ totalCalories, entryCount }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="bg-gradient-to-br from-orange-50 to-red-50 border-orange-200">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-orange-100">
              <Flame className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">Today's Calories</p>
              <p className="text-3xl font-bold text-orange-600">{totalCalories}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-blue-100">
              <Utensils className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">Meals Today</p>
              <p className="text-3xl font-bold text-blue-600">{entryCount}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
