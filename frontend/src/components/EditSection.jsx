import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Pencil, X } from 'lucide-react';

export function EditSection({ onReanalyze, onCancel }) {
  const [correctedItems, setCorrectedItems] = useState('');

  const handleSubmit = () => {
    if (!correctedItems.trim()) {
      alert('Please enter the corrected food items');
      return;
    }
    onReanalyze(correctedItems);
    setCorrectedItems('');
  };

  return (
    <Card className="border-orange-200 bg-orange-50/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Pencil className="w-5 h-5 text-orange-600" />
          Correct Analysis
        </CardTitle>
        <CardDescription>
          Enter the actual food items to get a more accurate calorie count
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="e.g., 2 slices of pizza, 1 can of coke, side salad"
          value={correctedItems}
          onChange={(e) => setCorrectedItems(e.target.value)}
          rows={4}
          className="resize-none"
        />
        <div className="flex gap-2">
          <Button onClick={handleSubmit} className="flex-1">
            <Pencil className="mr-2 h-4 w-4" />
            Reanalyze
          </Button>
          <Button onClick={onCancel} variant="outline" className="flex-1">
            <X className="mr-2 h-4 w-4" />
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
