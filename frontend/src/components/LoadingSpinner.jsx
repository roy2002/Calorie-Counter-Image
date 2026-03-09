import { Card, CardContent } from './ui/card';
import { Loader2 } from 'lucide-react';

export function LoadingSpinner() {
  return (
    <Card>
      <CardContent className="p-12">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
          <div className="text-center">
            <p className="text-lg font-medium">Analyzing your food...</p>
            <p className="text-sm text-muted-foreground mt-1">
              This may take a few seconds
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
