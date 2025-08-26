import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Calendar, Users, Clock, Activity, Settings, LogOut, Plus, Mail, CheckCircle, XCircle, Bell, Edit, Trash2, ArrowLeft, BarChart3, TrendingUp, User } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.headers.common['Authorization'] = localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : null;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    setCurrentPage('dashboard');
  };

  if (!user) {
    return <LoginScreen setUser={setUser} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Calendar className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">Sistema Gestione Ferie</h1>
                <p className="text-sm text-slate-600">Benvenuto, {user.username}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
                <div className={`w-2 h-2 rounded-full ${user.role === 'admin' ? 'bg-purple-500' : 'bg-green-500'}`} />
                {user.role === 'admin' ? 'Amministratore' : 'Dipendente'}
              </div>
              <button
                onClick={logout}
                className="flex items-center space-x-2 text-slate-600 hover:text-red-600 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <span>Esci</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {user.role === 'admin' ? (
          <AdminDashboard currentPage={currentPage} setCurrentPage={setCurrentPage} />
        ) : (
          <EmployeeDashboard currentPage={currentPage} setCurrentPage={setCurrentPage} user={user} />
        )}
      </div>
    </div>
  );
}

// Login Screen Component
const LoginScreen = ({ setUser }) => {
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/login`, loginData);
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setUser(user);
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore durante il login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 flex items-center justify-center p-4">
      <div className="bg-white/95 backdrop-blur-md p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 rounded-2xl mx-auto w-fit mb-4">
            <Calendar className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Sistema Ferie</h1>
          <p className="text-slate-600">Accedi al tuo account</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Username</label>
            <input
              type="text"
              value={loginData.username}
              onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              placeholder="Inserisci username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
            <input
              type="password"
              value={loginData.password}
              onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              placeholder="Inserisci password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-6 rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition-all transform hover:scale-[1.02]"
          >
            {loading ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-600">
          <p>Admin predefinito: <strong>admin / admin123</strong></p>
        </div>
      </div>
    </div>
  );
};

// Employee Dashboard Component
const EmployeeDashboard = ({ currentPage, setCurrentPage, user }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingRequest, setEditingRequest] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const response = await axios.get(`${API}/requests`);
      setRequests(response.data);
    } catch (error) {
      console.error('Errore nel caricamento delle richieste:', error);
    }
  };

  const handleEditRequest = (request) => {
    setEditingRequest(request);
    setCurrentPage('edit-request');
  };

  const handleDeleteRequest = async (requestId) => {
    try {
      await axios.delete(`${API}/requests/${requestId}`);
      setShowDeleteConfirm(null);
      loadRequests();
    } catch (error) {
      console.error('Errore nella cancellazione:', error);
      alert('Errore nella cancellazione della richiesta');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', text: 'In attesa', icon: Clock },
      approved: { color: 'bg-green-100 text-green-800 border-green-200', text: 'Approvata', icon: CheckCircle },
      rejected: { color: 'bg-red-100 text-red-800 border-red-200', text: 'Rifiutata', icon: XCircle }
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${config.color}`}>
        <Icon className="h-4 w-4 mr-1" />
        {config.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    return timeString.substring(0, 5); // HH:MM
  };

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setCurrentPage('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'dashboard' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Le mie richieste</span>
          </button>
          
          <button
            onClick={() => setCurrentPage('new-request')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'new-request' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Plus className="h-4 w-4" />
            <span>Nuova richiesta</span>
          </button>
          
          <button
            onClick={() => setCurrentPage('stats')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'stats' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            <span>Le mie statistiche</span>
          </button>
        </div>
      </div>

      {/* Content */}
      {currentPage === 'dashboard' && (
        <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
          <h2 className="text-xl font-semibold text-slate-800 mb-6">Le mie richieste</h2>
          
          {requests.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-16 w-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 text-lg">Nessuna richiesta ancora</p>
              <p className="text-slate-400">Clicca su "Nuova richiesta" per iniziare</p>
            </div>
          ) : (
            <div className="space-y-4">
              {requests.map((request) => (
                <div key={request.id} className="border border-slate-200 rounded-xl p-6 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-slate-800 text-lg capitalize">{request.type}</h3>
                      <p className="text-slate-600">Richiesta del {formatDate(request.created_at)}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(request.status)}
                      {request.status === 'pending' && (
                        <div className="flex space-x-1 ml-2">
                          <button
                            onClick={() => handleEditRequest(request)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Modifica richiesta"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setShowDeleteConfirm(request)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Cancella richiesta"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    {request.type === 'ferie' && (
                      <>
                        <div>
                          <span className="font-medium text-slate-600">Data inizio:</span>
                          <span className="ml-2 text-slate-800">{formatDate(request.start_date)}</span>
                        </div>
                        <div>
                          <span className="font-medium text-slate-600">Data fine:</span>
                          <span className="ml-2 text-slate-800">{formatDate(request.end_date)}</span>
                        </div>
                      </>
                    )}
                    
                    {request.type === 'permesso' && (
                      <>
                        <div>
                          <span className="font-medium text-slate-600">Data:</span>
                          <span className="ml-2 text-slate-800">{formatDate(request.permit_date)}</span>
                        </div>
                        <div>
                          <span className="font-medium text-slate-600">Orario:</span>
                          <span className="ml-2 text-slate-800">
                            {formatTime(request.start_time)} - {formatTime(request.end_time)}
                          </span>
                        </div>
                      </>
                    )}
                    
                    {request.type === 'malattia' && (
                      <>
                        <div>
                          <span className="font-medium text-slate-600">Data inizio:</span>
                          <span className="ml-2 text-slate-800">{formatDate(request.sick_start_date)}</span>
                        </div>
                        <div>
                          <span className="font-medium text-slate-600">Giorni:</span>
                          <span className="ml-2 text-slate-800">{request.sick_days}</span>
                        </div>
                        <div className="md:col-span-2">
                          <span className="font-medium text-slate-600">Protocollo:</span>
                          <span className="ml-2 text-slate-800 font-mono text-xs bg-slate-100 px-2 py-1 rounded">
                            {request.protocol_code}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                  
                  {request.admin_notes && (
                    <div className="mt-4 bg-slate-50 p-4 rounded-lg">
                      <span className="font-medium text-slate-600">Note amministratore:</span>
                      <p className="text-slate-800 mt-1">{request.admin_notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {currentPage === 'new-request' && (
        <NewRequestForm onSuccess={() => {
          setCurrentPage('dashboard');
          loadRequests();
        }} />
      )}

      {currentPage === 'edit-request' && editingRequest && (
        <EditRequestForm 
          request={editingRequest} 
          onSuccess={() => {
            setCurrentPage('dashboard');
            setEditingRequest(null);
            loadRequests();
          }}
          onCancel={() => {
            setCurrentPage('dashboard');
            setEditingRequest(null);
          }}
        />
      )}

      {currentPage === 'stats' && (
        <EmployeeStats />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4 text-slate-800">Conferma Cancellazione</h3>
            <p className="text-slate-600 mb-6">
              Sei sicuro di voler cancellare questa richiesta di {showDeleteConfirm.type}? 
              Questa azione non può essere annullata.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => handleDeleteRequest(showDeleteConfirm.id)}
                className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
              >
                Cancella
              </button>
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 bg-slate-200 text-slate-700 py-2 px-4 rounded-lg hover:bg-slate-300 transition-colors"
              >
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Employee Stats Component
const EmployeeStats = () => {
  const [stats, setStats] = useState(null);
  const [years, setYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadYears();
  }, []);

  useEffect(() => {
    if (selectedYear) {
      loadStats();
    }
  }, [selectedYear]);

  const loadYears = async () => {
    try {
      const response = await axios.get(`${API}/years`);
      setYears(response.data.years);
    } catch (error) {
      console.error('Errore nel caricamento degli anni:', error);
    }
  };

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/stats?year=${selectedYear}`);
      setStats(response.data);
    } catch (error) {
      console.error('Errore nel caricamento delle statistiche:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-slate-800 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
            Le Mie Statistiche
          </h2>
          
          <div className="flex items-center space-x-3">
            <label className="text-sm font-medium text-slate-700">Anno:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="spinner" />
          </div>
        ) : stats ? (
          <div className="space-y-6">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100">Ferie Prese</p>
                    <p className="text-3xl font-bold">{stats.stats.ferie_days}</p>
                    <p className="text-blue-200 text-sm">giorni nel {stats.year}</p>
                  </div>
                  <Calendar className="h-12 w-12 text-blue-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100">Permessi Presi</p>
                    <p className="text-3xl font-bold">{stats.stats.permessi_count}</p>
                    <p className="text-green-200 text-sm">richieste nel {stats.year}</p>
                  </div>
                  <Clock className="h-12 w-12 text-green-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-orange-100">Malattie</p>
                    <p className="text-3xl font-bold">{stats.stats.malattie_days}</p>
                    <p className="text-orange-200 text-sm">giorni nel {stats.year}</p>
                  </div>
                  <Activity className="h-12 w-12 text-orange-200" />
                </div>
              </div>
            </div>

            {/* Summary Card */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Riepilogo Anno {stats.year}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-purple-200">Totale Richieste</p>
                      <p className="text-xl font-bold">{stats.stats.total_requests}</p>
                    </div>
                    <div>
                      <p className="text-purple-200">Giorni Ferie</p>
                      <p className="text-xl font-bold">{stats.stats.ferie_days}</p>
                    </div>
                    <div>
                      <p className="text-purple-200">Permessi</p>
                      <p className="text-xl font-bold">{stats.stats.permessi_count}</p>
                    </div>
                    <div>
                      <p className="text-purple-200">Giorni Malattia</p>
                      <p className="text-xl font-bold">{stats.stats.malattie_days}</p>
                    </div>
                  </div>
                </div>
                <TrendingUp className="h-16 w-16 text-purple-200" />
              </div>
            </div>

            {/* Info Card */}
            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">📊 Informazioni Statistiche</h4>
              <ul className="text-blue-700 text-sm space-y-1">
                <li>• Vengono conteggiate solo le richieste <strong>approvate</strong></li>
                <li>• Le ferie sono calcolate in giorni consecutivi (weekends inclusi)</li>
                <li>• I permessi sono conteggiati come numero di richieste</li>
                <li>• Le malattie sono calcolate in giorni totali</li>
                <li>• I dati sono aggiornati in tempo reale</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <BarChart3 className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">Nessun dato disponibile per l'anno selezionato</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Edit Request Form Component
const EditRequestForm = ({ request, onSuccess, onCancel }) => {
  const [requestType, setRequestType] = useState(request.type);
  const [formData, setFormData] = useState(() => {
    // Initialize form data based on request type
    const data = {};
    
    if (request.type === 'ferie') {
      data.start_date = request.start_date?.split('T')[0] || '';
      data.end_date = request.end_date?.split('T')[0] || '';
    } else if (request.type === 'permesso') {
      data.permit_date = request.permit_date?.split('T')[0] || '';
      data.start_time = request.start_time || '';
      data.end_time = request.end_time || '';
    } else if (request.type === 'malattia') {
      data.sick_start_date = request.sick_start_date?.split('T')[0] || '';
      data.sick_days = request.sick_days || '';
      data.protocol_code = request.protocol_code || '';
    }
    
    return data;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const requestData = { type: requestType, ...formData };
      await axios.put(`${API}/requests/${request.id}`, requestData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore durante la modifica della richiesta');
    } finally {
      setLoading(false);
    }
  };

  const renderEditForm = () => {
    switch (requestType) {
      case 'ferie':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Modifica Richiesta Ferie (max 15 giorni consecutivi)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data inizio</label>
                <input
                  type="date"
                  value={formData.start_date || ''}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data fine</label>
                <input
                  type="date"
                  value={formData.end_date || ''}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>
          </div>
        );
        
      case 'permesso':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Modifica Richiesta Permesso</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Data</label>
              <input
                type="date"
                value={formData.permit_date || ''}
                onChange={(e) => setFormData({ ...formData, permit_date: e.target.value })}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Orario inizio</label>
                <input
                  type="time"
                  value={formData.start_time || ''}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Orario fine</label>
                <input
                  type="time"
                  value={formData.end_time || ''}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>
          </div>
        );
        
      case 'malattia':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Modifica Richiesta Malattia</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data inizio</label>
                <input
                  type="date"
                  value={formData.sick_start_date || ''}
                  onChange={(e) => setFormData({ ...formData, sick_start_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Numero giorni</label>
                <input
                  type="number"
                  min="1"
                  value={formData.sick_days || ''}
                  onChange={(e) => setFormData({ ...formData, sick_days: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Codice protocollo certificato</label>
              <input
                type="text"
                value={formData.protocol_code || ''}
                onChange={(e) => setFormData({ ...formData, protocol_code: e.target.value })}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Inserisci il codice del certificato medico"
                required
              />
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
      <h2 className="text-xl font-semibold text-slate-800 mb-6">Modifica Richiesta</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <p className="text-blue-800 text-sm">
            <strong>Nota:</strong> Puoi modificare solo le richieste in stato "In attesa". 
            Una volta elaborate dall'amministratore, non potranno più essere modificate.
          </p>
        </div>

        {renderEditForm()}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="flex space-x-3 pt-6 border-t border-slate-200">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-6 rounded-lg font-medium hover:from-green-700 hover:to-green-800 disabled:opacity-50 transition-all"
          >
            {loading ? 'Modifica in corso...' : 'Salva Modifiche'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-all"
          >
            Annulla
          </button>
        </div>
      </form>
    </div>
  );
};

// New Request Form Component
const NewRequestForm = ({ onSuccess }) => {
  const [requestType, setRequestType] = useState('');
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const requestData = { type: requestType, ...formData };
      await axios.post(`${API}/requests`, requestData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore durante la creazione della richiesta');
    } finally {
      setLoading(false);
    }
  };

  const renderRequestTypeForm = () => {
    switch (requestType) {
      case 'ferie':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Richiesta Ferie (max 15 giorni consecutivi)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data inizio</label>
                <input
                  type="date"
                  value={formData.start_date || ''}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data fine</label>
                <input
                  type="date"
                  value={formData.end_date || ''}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>
        );
        
      case 'permesso':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Richiesta Permesso</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Data</label>
              <input
                type="date"
                value={formData.permit_date || ''}
                onChange={(e) => setFormData({ ...formData, permit_date: e.target.value })}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Orario inizio</label>
                <input
                  type="time"
                  value={formData.start_time || ''}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Orario fine</label>
                <input
                  type="time"
                  value={formData.end_time || ''}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>
        );
        
      case 'malattia':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Richiesta Malattia</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Data inizio</label>
                <input
                  type="date"
                  value={formData.sick_start_date || ''}
                  onChange={(e) => setFormData({ ...formData, sick_start_date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Numero giorni</label>
                <input
                  type="number"
                  min="1"
                  value={formData.sick_days || ''}
                  onChange={(e) => setFormData({ ...formData, sick_days: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Codice protocollo certificato</label>
              <input
                type="text"
                value={formData.protocol_code || ''}
                onChange={(e) => setFormData({ ...formData, protocol_code: e.target.value })}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Inserisci il codice del certificato medico"
                required
              />
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
      <h2 className="text-xl font-semibold text-slate-800 mb-6">Nuova Richiesta</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">Tipo di richiesta</label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { value: 'ferie', label: 'Ferie', icon: Calendar },
              { value: 'permesso', label: 'Permesso', icon: Clock },
              { value: 'malattia', label: 'Malattia', icon: Activity }
            ].map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  setRequestType(value);
                  setFormData({});
                }}
                className={`p-4 border rounded-xl text-center transition-all hover:shadow-md ${
                  requestType === value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <Icon className="h-6 w-6 mx-auto mb-2" />
                <div className="font-medium">{label}</div>
              </button>
            ))}
          </div>
        </div>

        {requestType && (
          <div className="border-t border-slate-200 pt-6">
            {renderRequestTypeForm()}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {requestType && (
          <div className="flex space-x-3 pt-6 border-t border-slate-200">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-6 rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition-all"
            >
              {loading ? 'Invio in corso...' : 'Invia Richiesta'}
            </button>
            <button
              type="button"
              onClick={() => {
                setRequestType('');
                setFormData({});
                setError('');
              }}
              className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-all"
            >
              Annulla
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

// Admin Dashboard Component
const AdminDashboard = ({ currentPage, setCurrentPage }) => {
  const [stats, setStats] = useState({ pending_ferie: 0, pending_permessi: 0, pending_malattie: 0, total_pending: 0 });
  const [requests, setRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsResponse, requestsResponse, employeesResponse] = await Promise.all([
        axios.get(`${API}/admin/dashboard`),
        axios.get(`${API}/requests`),
        axios.get(`${API}/admin/employees`)
      ]);
      
      setStats(statsResponse.data);
      setRequests(requestsResponse.data);
      setEmployees(employeesResponse.data);
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error);
    }
  };

  const handleRequestAction = async (requestId, action, notes = '') => {
    try {
      await axios.put(`${API}/admin/requests/${requestId}`, {
        request_id: requestId,
        action,
        notes
      });
      
      await loadDashboardData(); // Reload data
    } catch (error) {
      console.error('Errore nell\'azione sulla richiesta:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setCurrentPage('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'dashboard' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Dashboard</span>
          </button>
          
          <button
            onClick={() => setCurrentPage('employees')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'employees' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Dipendenti</span>
          </button>
          
          <button
            onClick={() => setCurrentPage('settings')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              currentPage === 'settings' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>Impostazioni</span>
          </button>
        </div>
      </div>

      {/* Dashboard Stats */}
      {currentPage === 'dashboard' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100">Ferie in attesa</p>
                  <p className="text-3xl font-bold">{stats.pending_ferie}</p>
                </div>
                <Calendar className="h-8 w-8 text-blue-200" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100">Permessi in attesa</p>
                  <p className="text-3xl font-bold">{stats.pending_permessi}</p>
                </div>
                <Clock className="h-8 w-8 text-green-200" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100">Malattie in attesa</p>
                  <p className="text-3xl font-bold">{stats.pending_malattie}</p>
                </div>
                <Activity className="h-8 w-8 text-orange-200" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100">Totale in attesa</p>
                  <p className="text-3xl font-bold">{stats.total_pending}</p>
                </div>
                <Bell className="h-8 w-8 text-purple-200" />
              </div>
            </div>
          </div>

          {/* Requests List */}
          <RequestsList requests={requests} onAction={handleRequestAction} />
        </>
      )}

      {currentPage === 'employees' && (
        <EmployeeManagement employees={employees} onRefresh={loadDashboardData} />
      )}

      {currentPage === 'settings' && (
        <AdminSettings />
      )}
    </div>
  );
};

// Requests List Component
const RequestsList = ({ requests, onAction }) => {
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [adminNotes, setAdminNotes] = useState('');

  const pendingRequests = requests.filter(r => r.status === 'pending');
  const processedRequests = requests.filter(r => r.status !== 'pending');

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    return timeString.substring(0, 5);
  };

  const handleAction = async (request, action) => {
    await onAction(request.id, action, adminNotes);
    setSelectedRequest(null);
    setAdminNotes('');
  };

  return (
    <div className="space-y-6">
      {/* Pending Requests */}
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center">
          <Bell className="h-5 w-5 mr-2 text-orange-500" />
          Richieste in attesa ({pendingRequests.length})
        </h2>
        
        {pendingRequests.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            Nessuna richiesta in attesa
          </div>
        ) : (
          <div className="space-y-4">
            {pendingRequests.map((request) => (
              <div key={request.id} className="border border-slate-200 rounded-xl p-6 hover:shadow-md transition-all">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-slate-800 text-lg capitalize">{request.type}</h3>
                    <p className="text-slate-600">
                      {request.username} ({request.user_email}) - {formatDate(request.created_at)}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setSelectedRequest(request)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Gestisci
                    </button>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {request.type === 'ferie' && (
                    <>
                      <div>
                        <span className="font-medium text-slate-600">Dal:</span>
                        <span className="ml-2">{formatDate(request.start_date)}</span>
                      </div>
                      <div>
                        <span className="font-medium text-slate-600">Al:</span>
                        <span className="ml-2">{formatDate(request.end_date)}</span>
                      </div>
                    </>
                  )}
                  
                  {request.type === 'permesso' && (
                    <>
                      <div>
                        <span className="font-medium text-slate-600">Data:</span>
                        <span className="ml-2">{formatDate(request.permit_date)}</span>
                      </div>
                      <div>
                        <span className="font-medium text-slate-600">Orario:</span>
                        <span className="ml-2">{formatTime(request.start_time)} - {formatTime(request.end_time)}</span>
                      </div>
                    </>
                  )}
                  
                  {request.type === 'malattia' && (
                    <>
                      <div>
                        <span className="font-medium text-slate-600">Inizio:</span>
                        <span className="ml-2">{formatDate(request.sick_start_date)}</span>
                      </div>
                      <div>
                        <span className="font-medium text-slate-600">Giorni:</span>
                        <span className="ml-2">{request.sick_days}</span>
                      </div>
                      <div className="md:col-span-2">
                        <span className="font-medium text-slate-600">Protocollo:</span>
                        <span className="ml-2 font-mono text-xs bg-slate-100 px-2 py-1 rounded">{request.protocol_code}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Request Action Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              Gestisci richiesta {selectedRequest.type} - {selectedRequest.username}
            </h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Note (opzionale)
              </label>
              <textarea
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                rows="3"
                placeholder="Aggiungi note..."
              />
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => handleAction(selectedRequest, 'approve')}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
              >
                Approva
              </button>
              <button
                onClick={() => handleAction(selectedRequest, 'reject')}
                className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700"
              >
                Rifiuta
              </button>
              <button
                onClick={() => {
                  setSelectedRequest(null);
                  setAdminNotes('');
                }}
                className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Processed Requests */}
      {processedRequests.length > 0 && (
        <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
          <h2 className="text-xl font-semibold text-slate-800 mb-6">
            Richieste elaborate ({processedRequests.length})
          </h2>
          
          <div className="space-y-3">
            {processedRequests.slice(0, 10).map((request) => (
              <div key={request.id} className="border border-slate-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium capitalize">{request.type}</span>
                    <span className="text-slate-600 ml-2">- {request.username}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-sm ${
                      request.status === 'approved' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {request.status === 'approved' ? 'Approvata' : 'Rifiutata'}
                    </span>
                    <span className="text-slate-500 text-sm">{formatDate(request.updated_at || request.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Employee Management Component
const EmployeeManagement = ({ employees, onRefresh }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API}/admin/employees`, newEmployee);
      setNewEmployee({ username: '', email: '', password: '' });
      setShowCreateForm(false);
      onRefresh();
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore nella creazione del dipendente');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-slate-800">Gestione Dipendenti</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Nuovo Dipendente</span>
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-6 border border-slate-200 rounded-xl p-6 bg-slate-50">
          <h3 className="text-lg font-semibold mb-4">Crea Nuovo Dipendente</h3>
          <form onSubmit={handleCreateEmployee} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
                <input
                  type="text"
                  value={newEmployee.username}
                  onChange={(e) => setNewEmployee({ ...newEmployee, username: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  value={newEmployee.email}
                  onChange={(e) => setNewEmployee({ ...newEmployee, email: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  value={newEmployee.password}
                  onChange={(e) => setNewEmployee({ ...newEmployee, password: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Creazione...' : 'Crea Dipendente'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setError('');
                  setNewEmployee({ username: '', email: '', password: '' });
                }}
                className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-3">
        {employees.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            Nessun dipendente ancora creato
          </div>
        ) : (
          employees.map((employee) => (
            <div key={employee.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-all">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-slate-800">{employee.username}</h3>
                  <p className="text-slate-600 text-sm">{employee.email}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-block w-2 h-2 rounded-full ${employee.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="ml-2 text-sm text-slate-600">
                    {employee.is_active ? 'Attivo' : 'Inattivo'}
                  </span>
                  <div className="text-xs text-slate-500 mt-1">
                    Creato: {new Date(employee.created_at).toLocaleDateString('it-IT')}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Admin Settings Component
const AdminSettings = () => {
  const [settings, setSettings] = useState({ email: '' });
  const [passwordData, setPasswordData] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleEmailUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      await axios.put(`${API}/admin/settings`, settings);
      setMessage('Email aggiornata con successo');
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore nell\'aggiornamento');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('Le password non corrispondono');
      return;
    }

    setLoading(true);
    setMessage('');
    setError('');

    try {
      await axios.put(`${API}/change-password`, {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      setMessage('Password cambiata con successo');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      setError(error.response?.data?.detail || 'Errore nel cambio password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Email Configuration */}
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center">
          <Mail className="h-5 w-5 mr-2" />
          Configurazione Email
        </h2>
        
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">Configurazione SMTP Gmail richiesta</h3>
          <p className="text-blue-700 text-sm mb-3">
            Per abilitare l'invio automatico delle email, configura le seguenti variabili d'ambiente nel file backend/.env:
          </p>
          <div className="bg-white p-3 rounded border font-mono text-sm">
            <div>ADMIN_EMAIL=tua-email@gmail.com</div>
            <div>ADMIN_APP_PASSWORD=tua-app-password-gmail</div>
          </div>
          <p className="text-blue-600 text-xs mt-2">
            Ricorda di riavviare il backend dopo aver modificato le variabili d'ambiente.
          </p>
        </div>

        <form onSubmit={handleEmailUpdate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Email amministratore (per ricevere notifiche)
            </label>
            <input
              type="email"
              value={settings.email}
              onChange={(e) => setSettings({ ...settings, email: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="admin@company.com"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Aggiornamento...' : 'Aggiorna Email'}
          </button>
        </form>
      </div>

      {/* Password Change */}
      <div className="bg-white/80 backdrop-blur-md rounded-xl p-6 shadow-sm border border-slate-200/50">
        <h2 className="text-xl font-semibold text-slate-800 mb-6">Cambia Password</h2>
        
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Password corrente</label>
            <input
              type="password"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Nuova password</label>
            <input
              type="password"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Conferma nuova password</label>
            <input
              type="password"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Cambiando...' : 'Cambia Password'}
          </button>
        </form>
      </div>

      {/* Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {message}
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
};

export default App;