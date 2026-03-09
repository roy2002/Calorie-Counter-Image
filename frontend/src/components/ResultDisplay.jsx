import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CheckCircle, AlertCircle, Pencil } from 'lucide-react';

export function ResultDisplay({ result, onEdit, onReset }) {
  if (!result) return null;

  const isSuccess = result.success;
  const Icon = isSuccess ? CheckCircle : AlertCircle;

  return (
    <Card className={isSuccess ? 'border-green-200 bg-green-50/50' : 'border-red-200 bg-red-50/50'}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className={`w-5 h-5 ${isSuccess ? 'text-green-600' : 'text-red-600'}`} />
          {isSuccess ? 'Analysis Complete' : 'Error'}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {result.analysis || result.error}
        </div>
        
        {isSuccess && (
          <>
            <div className="border-t pt-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">This Meal:</span>
                <Badge variant="default" className="text-base font-semibold">
                  🍽️ {result.calories} cal
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Today's Total:</span>
                <Badge variant="secondary" className="text-base font-semibold">
                  📊 {result.daily_total} cal
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Meals Today:</span>
                <Badge variant="outline" className="text-base">
                  📝 {result.entry_count}
                </Badge>
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <Button onClick={onEdit} variant="outline" className="flex-1">
                <Pencil className="mr-2 h-4 w-4" />
                Edit / Correct
              </Button>
              <Button onClick={onReset} variant="default" className="flex-1">
                Analyze Another
              </Button>
            </div>
          </>
        )}

        {!isSuccess && (
          <div className="pt-4">
            <Button onClick={onReset} variant="default" className="w-full">
              Try Again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
