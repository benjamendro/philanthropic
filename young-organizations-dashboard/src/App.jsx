import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { ChevronDown, ChevronUp, MapPin, Search } from 'lucide-react';
import rawData from './processed_data.json';

const CATEGORIES = [
  "מנהיגות צעירה",
  "חינוך והשכלה",
  "התיישבות וציונות",
  "תעסוקה ויזמות"
];

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ec4899'];

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [expandedCategory, setExpandedCategory] = useState(null);

  // Extract all unique locations
  const allLocations = useMemo(() => {
    const locSet = new Set();
    rawData.forEach(item => {
      (item.locations || []).forEach(loc => {
        if (loc) locSet.add(loc);
      });
    });
    return Array.from(locSet).sort();
  }, []);

  // Filter data based on search and location
  const filteredData = useMemo(() => {
    return rawData.filter(item => {
      const matchesSearch = item['שם הארגון']?.includes(searchTerm) || 
                            item['תיאור/פרויקטים']?.includes(searchTerm);
      const matchesLocation = selectedLocation === '' || 
                              (item.locations || []).includes(selectedLocation);
      return matchesSearch && matchesLocation;
    });
  }, [searchTerm, selectedLocation]);

  // Aggregate data for the chart
  const chartData = useMemo(() => {
    return CATEGORIES.map(category => {
      const count = filteredData.filter(item => item[category] === true).length;
      return { name: category, count };
    });
  }, [filteredData]);

  const toggleCategory = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  return (
    <div className="container">
      <header className="glass-panel">
        <h1>מרכז ידע: ארגוני צעירים</h1>
        <p>דאשבורד אינטראקטיבי לנתוני ארגוני צעירים וקרנות</p>
      </header>

      <div className="glass-panel filters-grid">
        <div className="input-group">
          <label><Search size={16} style={{display: 'inline', verticalAlign: 'middle', marginLeft: '4px'}}/> חפש ארגון</label>
          <input 
            type="text" 
            placeholder="חיפוש חופשי בשם או תיאור..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label><MapPin size={16} style={{display: 'inline', verticalAlign: 'middle', marginLeft: '4px'}}/> סנן לפי אזור תכנון / מיקום</label>
          <select 
            value={selectedLocation} 
            onChange={(e) => setSelectedLocation(e.target.value)}
          >
            <option value="">הצג הכל</option>
            {allLocations.map(loc => (
              <option key={loc} value={loc}>{loc}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="glass-panel">
        <h2 style={{marginBottom: '1rem', textAlign: 'center'}}>התפלגות ארגונים לפי תחומי פעילות</h2>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} tick={{fill: 'var(--text-main)'}} />
              <Tooltip 
                cursor={{fill: 'rgba(0,0,0,0.05)'}} 
                contentStyle={{backgroundColor: 'var(--card-bg)', borderRadius: '8px', border: 'none', color: 'var(--text-main)', backdropFilter: 'blur(10px)'}} 
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h2 style={{marginBottom: '1.5rem', marginTop: '2rem'}}>פירוט ארגונים ({filteredData.length})</h2>
      <div className="cards-grid">
        {CATEGORIES.map((category, idx) => {
          const categoryOrgs = filteredData.filter(item => item[category] === true);
          const isExpanded = expandedCategory === category;
          
          return (
            <div key={category} className="glass-panel category-card">
              <div 
                className="category-header" 
                onClick={() => toggleCategory(category)}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                  <span style={{color: COLORS[idx % COLORS.length]}}>
                    {isExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
                  </span>
                  {category}
                </div>
                <span className="category-count" style={{backgroundColor: COLORS[idx % COLORS.length]}}>
                  {categoryOrgs.length}
                </span>
              </div>
              
              {isExpanded && (
                <div className="organizations-list">
                  {categoryOrgs.length === 0 ? (
                    <div className="empty-state">לא נמצאו ארגונים העונים לסינון בתחום זה</div>
                  ) : (
                    categoryOrgs.map((org, orgIdx) => (
                      <div key={orgIdx} className="org-item">
                        <h3>{org['שם הארגון']} {org['איש קשר'] && <span style={{fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 'normal'}}>({org['איש קשר']})</span>}</h3>
                        
                        <div className="org-meta">
                          {(org.locations || []).slice(0, 3).map((loc, i) => (
                            <span key={i} className="badge"><MapPin size={12}/> {loc}</span>
                          ))}
                          {(org.locations && org.locations.length > 3) && (
                            <span className="badge">+{org.locations.length - 3} עוד</span>
                          )}
                        </div>
                        
                        <p className="org-desc">
                          {org['תיאור/פרויקטים'] || 'אין תיאור זמין'}
                        </p>
                        
                        {org['אוכלוסיית יעד'] && (
                          <p style={{marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)'}}>
                            <strong style={{color: 'var(--text-main)'}}>אוכלוסיית יעד:</strong> {org['אוכלוסיית יעד']}
                          </p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
