import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Trash2, Clock } from 'lucide-react';

export function TodayEntries({ entries, onEntryDeleted, authToken }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (entryId) => {
    if (!confirm('Are you sure you want to delete this entry?')) {
      return;
    }

    setDeletingId(entryId);
    try {
      const response = await fetch(`https://calorie-counter-image.onrender.com/delete-entry/${entryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      const data = await response.json();

      if (data.success) {
        onEntryDeleted();
      } else {
        alert('❌ Error: ' + (data.error || 'Failed to delete entry'));
      }
    } catch (error) {
      alert('❌ Error: ' + error.message);
    } finally {
      setDeletingId(null);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  if (!entries || entries.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Today's Entries
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-4">
            No entries yet today. Start tracking!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Today's Entries ({entries.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="default" className="font-semibold">
                      {entry.total_calories} cal
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(entry.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap line-clamp-3">
                    {entry.analysis}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-destructive hover:text-destructive hover:bg-destructive/10 flex-shrink-0"
                  onClick={() => handleDelete(entry.id)}
                  disabled={deletingId === entry.id}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
