import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/card';
import { Button } from './components/ui/button';
import { ImageUpload } from './components/ImageUpload';
import { DailyStats } from './components/DailyStats';
import { WeeklySummary } from './components/WeeklySummary';
import { ResultDisplay } from './components/ResultDisplay';
import { EditSection } from './components/EditSection';
import { LoadingSpinner } from './components/LoadingSpinner';
import { CalorieTarget } from './components/CalorieTarget';
import { TodayEntries } from './components/TodayEntries';
import { Utensils, Trash2, Menu, X } from 'lucide-react';

const API_URL = 'https://calorie-counter-image.onrender.com/';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showEdit, setShowEdit] = useState(false);
  const [dailyStats, setDailyStats] = useState({ total_calories: 0, entry_count: 0 });
  const [weeklyData, setWeeklyData] = useState([]);
  const [todayEntries, setTodayEntries] = useState([]);
  const [currentEntryId, setCurrentEntryId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [targetCalories, setTargetCalories] = useState(() => {
    // Load target from localStorage, default to 2000
    const saved = localStorage.getItem('calorieTarget');
    return saved ? parseInt(saved) : 2000;
  });

  // Save target to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('calorieTarget', targetCalories.toString());
  }, [targetCalories]);

  // Load daily stats and weekly summary on mount
  useEffect(() => {
    loadDailyStats();
    loadWeeklySummary();
    loadTodayEntries();
  }, []);

  const loadDailyStats = async () => {
    try {
      const response = await fetch(`${API_URL}/daily-total`);
      const data = await response.json();
      if (data.success && data.data) {
        setDailyStats({
          total_calories: data.data.total_calories || 0,
          entry_count: data.data.entry_count || 0
        });
      }
    } catch (error) {
      console.error('Error loading daily stats:', error);
    }
  };

  const loadWeeklySummary = async () => {
    try {
      const response = await fetch(`${API_URL}/weekly-summary`);
      const data = await response.json();
      if (data.success && data.data) {
        setWeeklyData(data.data);
      }
    } catch (error) {
      console.error('Error loading weekly summary:', error);
    }
  };

  const loadTodayEntries = async () => {
    try {
      const response = await fetch(`${API_URL}/entries`);
      const data = await response.json();
      if (data.success && data.data) {
        setTodayEntries(data.data);
      }
    } catch (error) {
      console.error('Error loading today entries:', error);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);

    setLoading(true);
    setResult(null);
    setShowEdit(false);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      setLoading(false);

      if (data.success) {
        setResult(data);
        setCurrentEntryId(data.entry_id);
        setDailyStats({
          total_calories: data.daily_total,
          entry_count: data.entry_count
        });
        loadWeeklySummary();
        loadTodayEntries();
      } else {
        setResult({ success: false, error: data.error || 'Unknown error occurred' });
      }
    } catch (error) {
      setLoading(false);
      setResult({ success: false, error: error.message });
    }
  };

  const handleReanalyze = async (correctedItems) => {
    if (!currentEntryId) {
      alert('Error: No entry ID found. Please analyze an image first.');
      return;
    }

    setLoading(true);
    setShowEdit(false);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/reanalyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          corrected_items: correctedItems,
          entry_id: currentEntryId
        })
      });

      const data = await response.json();
      setLoading(false);

      if (data.success) {
        const correctedResult = {
          ...data,
          analysis: '✅ Corrected Analysis:\n\n' + data.analysis + 
                   '\n\n💡 Tip: The meal count stayed the same - we updated your previous entry!'
        };
        setResult(correctedResult);
        setCurrentEntryId(data.entry_id);
        setDailyStats({
          total_calories: data.daily_total,
          entry_count: data.entry_count
        });
        loadWeeklySummary();
        loadTodayEntries();
      } else {
        setResult({ success: false, error: data.error || 'Unknown error occurred' });
      }
    } catch (error) {
      setLoading(false);
      setResult({ success: false, error: error.message });
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setShowEdit(false);
    setCurrentEntryId(null);
  };

  const handleClearData = async () => {
    if (!confirm('⚠️ Are you sure you want to clear ALL data? This cannot be undone!')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/clear-data`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ All data cleared successfully!');
        handleReset();
        loadDailyStats();
        loadWeeklySummary();
        loadTodayEntries();
      } else {
        alert('❌ Error: ' + (data.error || 'Failed to clear data'));
      }
    } catch (error) {
      alert('❌ Error: ' + error.message);
    }
  };

  const handleEntryDeleted = () => {
    // Refresh all data after an entry is deleted
    loadDailyStats();
    loadWeeklySummary();
    loadTodayEntries();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Utensils className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Calorie Tracker</h1>
                <p className="text-sm text-muted-foreground">AI-Powered Food Analysis</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Daily Stats */}
            <DailyStats 
              totalCalories={dailyStats.total_calories}
              entryCount={dailyStats.entry_count}
            />

            {/* Calorie Target */}
            <CalorieTarget
              target={targetCalories}
              onTargetChange={setTargetCalories}
              totalCalories={dailyStats.total_calories}
            />

            {/* Today's Entries */}
            <TodayEntries 
              entries={todayEntries}
              onEntryDeleted={handleEntryDeleted}
            />

            {/* Upload Section */}
            {!selectedFile && !loading && !result && (
              <ImageUpload 
                onImageSelect={setSelectedFile}
                selectedFile={selectedFile}
              />
            )}

            {/* Preview and Analyze */}
            {selectedFile && !loading && !result && (
              <>
                <ImageUpload 
                  onImageSelect={setSelectedFile}
                  selectedFile={selectedFile}
                />
                <div className="flex gap-3">
                  <Button onClick={handleAnalyze} className="flex-1" size="lg">
                    Analyze Image
                  </Button>
                  <Button onClick={handleReset} variant="outline" size="lg">
                    Cancel
                  </Button>
                </div>
              </>
            )}

            {/* Loading - Keep image preview visible */}
            {loading && (
              <>
                <ImageUpload 
                  onImageSelect={setSelectedFile}
                  selectedFile={selectedFile}
                />
                <LoadingSpinner />
              </>
            )}

            {/* Results - Keep image preview visible */}
            {result && !showEdit && (
              <>
                <ImageUpload 
                  onImageSelect={setSelectedFile}
                  selectedFile={selectedFile}
                />
                <ResultDisplay 
                  result={result}
                  onEdit={() => setShowEdit(true)}
                  onReset={handleReset}
                />
              </>
            )}

            {/* Edit Section - Keep image preview visible */}
            {showEdit && (
              <>
                <ImageUpload 
                  onImageSelect={setSelectedFile}
                  selectedFile={selectedFile}
                />
                <EditSection
                  onReanalyze={handleReanalyze}
                  onCancel={() => setShowEdit(false)}
                />
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className={`
            lg:block space-y-6
            ${sidebarOpen ? 'block' : 'hidden'}
          `}>
            <WeeklySummary weeklyData={weeklyData} />

            {/* Clear Data Card */}
            <Card className="border-red-200 bg-red-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <Trash2 className="w-5 h-5" />
                  Danger Zone
                </CardTitle>
                <CardDescription>
                  Clear all tracked data permanently
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  onClick={handleClearData}
                  variant="destructive"
                  className="w-full"
                >
                  Clear All Data
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
