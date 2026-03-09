import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Target, Pencil, Check, X } from 'lucide-react';

export function CalorieTarget({ target, onTargetChange, totalCalories }) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState(target.toString());

  const remaining = target - totalCalories;
  const isPositive = remaining >= 0;

  const handleSave = () => {
    const newTarget = parseInt(inputValue);
    if (!isNaN(newTarget) && newTarget > 0) {
      onTargetChange(newTarget);
      setIsEditing(false);
    } else {
      alert('Please enter a valid positive number');
    }
  };

  const handleCancel = () => {
    setInputValue(target.toString());
    setIsEditing(false);
  };

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-600" />
            <span>Daily Target</span>
          </div>
          {!isEditing && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsEditing(true)}
              className="h-8 w-8"
            >
              <Pencil className="h-4 w-4" />
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Target Calories */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground font-medium">Target:</span>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-24 px-3 py-1 text-right border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                autoFocus
              />
              <Button size="icon" variant="ghost" onClick={handleSave} className="h-8 w-8">
                <Check className="h-4 w-4 text-green-600" />
              </Button>
              <Button size="icon" variant="ghost" onClick={handleCancel} className="h-8 w-8">
                <X className="h-4 w-4 text-red-600" />
              </Button>
            </div>
          ) : (
            <Badge variant="secondary" className="text-base font-semibold">
              {target} cal
            </Badge>
          )}
        </div>

        {/* Remaining Calories */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground font-medium">Remaining:</span>
          <Badge
            className={`text-base font-bold ${
              isPositive
                ? 'bg-green-100 text-green-700 border-green-300 hover:bg-green-100'
                : 'bg-red-100 text-red-700 border-red-300 hover:bg-red-100'
            }`}
            variant="outline"
          >
            {isPositive ? '+' : ''}{remaining} cal
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Progress</span>
            <span className="text-xs font-medium">
              {Math.round((totalCalories / target) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                isPositive ? 'bg-gradient-to-r from-green-400 to-green-600' : 'bg-gradient-to-r from-red-400 to-red-600'
              }`}
              style={{ width: `${Math.min((totalCalories / target) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Status Message */}
        <div className="pt-2">
          {isPositive ? (
            <p className="text-xs text-green-700 text-center font-medium">
              🎉 You have {remaining} calories left for today!
            </p>
          ) : (
            <p className="text-xs text-red-700 text-center font-medium">
              ⚠️ You've exceeded your target by {Math.abs(remaining)} calories
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
