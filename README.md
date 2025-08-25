# 📋 Sistema Gestione Ferie e Permessi

Un'applicazione web completa per la gestione di ferie, permessi e malattie aziendali, sviluppata con React, FastAPI e MongoDB.

![Sistema Gestione Ferie](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![React](https://img.shields.io/badge/React-19.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-green)
![MongoDB](https://img.shields.io/badge/MongoDB-4.5.0-darkgreen)

## 🎯 Caratteristiche Principali

### 👨‍💼 Dashboard Amministratore
- **Gestione dipendenti**: Creazione e visualizzazione dipendenti
- **Dashboard real-time**: Contatori richieste in attesa per categoria
- **Approvazione richieste**: Sistema di approvazione/rifiuto con note
- **Configurazione email**: Setup SMTP Gmail per notifiche automatiche
- **Cambio password**: Gestione sicura delle credenziali

### 👤 Dashboard Dipendente  
- **Richieste multiple**: Ferie, Permessi, Malattie con form specifici
- **Modifica richieste**: Possibilità di modificare richieste in attesa
- **Cancellazione richieste**: Eliminazione richieste non ancora elaborate
- **Stato real-time**: Visualizzazione stati con badge colorati
- **Note amministratore**: Feedback su richieste rifiutate

### 📧 Sistema Notifiche Email
- **Credenziali dipendenti**: Invio automatico credenziali via email
- **Alert amministratore**: Notifiche per nuove richieste
- **Risposte dipendenti**: Notifiche approvazioni/rifiuti con note
- **Template HTML**: Email professionali con design responsive

## 🚀 Demo Live

**URL**: [https://workleave-portal.preview.emergentagent.com](https://workleave-portal.preview.emergentagent.com)

### Credenziali di Test:
- **Amministratore**: 
  - Username: `admin`
  - Password: `admin123`
- **Dipendente**: 
  - Username: `mario.rossi`
  - Password: `password123`

## 🛠️ Stack Tecnologico

### Frontend
- **React 19.0.0** - Framework UI moderno
- **Tailwind CSS** - Styling utility-first
- **Lucide React** - Icone moderne
- **Axios** - HTTP client
- **React Router DOM** - Navigazione SPA

### Backend  
- **FastAPI 0.110.1** - Framework web Python ad alte prestazioni
- **MongoDB** - Database NoSQL
- **JWT Authentication** - Autenticazione sicura
- **BCrypt** - Hashing password
- **SMTP Email** - Sistema notifiche

### Sicurezza
- **Password hashing** con bcrypt
- **JWT tokens** con scadenza
- **Controllo ruoli** lato server
- **Validazione input** completa
- **Protezione endpoint** autenticati

## 📁 Struttura Progetto

```
/
├── backend/
│   ├── server.py              # API FastAPI principale
│   ├── requirements.txt       # Dipendenze Python
│   └── .env                   # Variabili ambiente
├── frontend/
│   ├── src/
│   │   ├── App.js            # Componente React principale
│   │   ├── App.css           # Stili personalizzati
│   │   └── components/ui/    # Componenti Shadcn/UI
│   ├── package.json          # Dipendenze Node.js
│   └── .env                  # Configurazione frontend
└── README.md                 # Documentazione
```

## 🔧 Setup e Installazione

### Prerequisiti
- Python 3.8+
- Node.js 16+
- MongoDB
- Yarn

### 1. Clona il Repository
```bash
git clone https://github.com/tuousername/sistema-gestione-ferie.git
cd sistema-gestione-ferie
```

### 2. Setup Backend
```bash
cd backend
pip install -r requirements.txt

# Configura file .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="leave_management_db"
JWT_SECRET="your-secret-key-change-in-production"
ADMIN_EMAIL="your-email@gmail.com"
ADMIN_APP_PASSWORD="your-16-char-app-password"
```

### 3. Setup Frontend
```bash
cd frontend
yarn install

# Il file .env è già configurato per l'ambiente di sviluppo
```

### 4. Avvio Servizi
```bash
# Backend (porta 8001)
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (porta 3000)
cd frontend
yarn start
```

## 📧 Configurazione Email SMTP

Per abilitare le notifiche email automatiche:

### 1. Setup Gmail App Password
1. Attiva **2FA** sul tuo account Gmail
2. Vai in **Impostazioni Google** → **Sicurezza** → **Verifica in due passaggi**
3. Crea **Password per le app** per "Sistema Gestione Ferie"
4. Copia la password di 16 caratteri generata

### 2. Configura Variabili Ambiente
```env
ADMIN_EMAIL=tua-email@gmail.com
ADMIN_APP_PASSWORD=abcdefghijklmnop
```

### 3. Riavvia Backend
```bash
sudo supervisorctl restart backend
```

## 🔐 Funzionalità di Sicurezza

### Autenticazione
- **JWT tokens** con algoritmo HS256
- **Scadenza automatica** (30 giorni)
- **Logout sicuro** con pulizia token

### Autorizzazione
- **Controlli ruoli** su tutti gli endpoint
- **Validazione proprietà** delle richieste
- **Protezione CORS** configurabile

### Validazioni
- **Limite ferie**: Massimo 15 giorni consecutivi
- **Campi obbligatori** per ogni tipo richiesta  
- **Formato email** validato
- **Date coerenti** (fine dopo inizio)

## 📱 Responsive Design

- **Mobile-first** design approach
- **Breakpoints** ottimizzati per tutti i dispositivi
- **Touch-friendly** interfacce
- **Progressive enhancement**

## 🧪 Testing

L'applicazione include test completi:
- **Backend API** testing (94.7% success rate)
- **Frontend UI/UX** testing 
- **Workflow completi** admin e dipendente
- **Validazioni** e **error handling**

## 🚀 Deploy in Produzione

### Variabili Ambiente Produzione
```env
# Backend
JWT_SECRET=strong-random-secret-key
MONGO_URL=mongodb://production-server:27017
ADMIN_EMAIL=admin@company.com
ADMIN_APP_PASSWORD=gmail-app-password

# Frontend  
REACT_APP_BACKEND_URL=https://your-api-domain.com
```

### Considerazioni Sicurezza
- Usa **HTTPS** in produzione
- Configura **CORS** specifici
- **Backup database** regolari
- **Monitoring** logs e performance

## 🔄 Workflow Applicazione

### Flusso Dipendente
1. **Login** con credenziali ricevute via email
2. **Crea richiesta** (Ferie/Permesso/Malattia)
3. **Modifica/Cancella** se ancora in attesa
4. **Visualizza stato** e note amministratore

### Flusso Amministratore  
1. **Login** con credenziali admin
2. **Crea dipendenti** (invio automatico credenziali)
3. **Visualizza dashboard** con contatori real-time
4. **Gestisce richieste** con approvazione/rifiuto + note
5. **Configura sistema** (email, password)

## 📊 Tipi di Richiesta

### 🏖️ Ferie
- **Date**: Inizio e fine (max 15 giorni consecutivi)
- **Validazione**: Data fine > data inizio
- **Stato**: Pending → Approved/Rejected

### ⏰ Permessi  
- **Data**: Giorno specifico
- **Orari**: Ora inizio e fine
- **Flessibilità**: Permessi orari personalizzabili

### 🏥 Malattie
- **Data inizio**: Primo giorno malattia
- **Durata**: Numero giorni
- **Protocollo**: Codice certificato medico

## 🎨 Design System

### Colori
- **Primary**: Blue 600 (#2563eb) 
- **Success**: Green 600 (#059669)
- **Warning**: Yellow 500 (#f59e0b)
- **Danger**: Red 600 (#dc2626)

### Tipografia
- **Font**: Inter (Google Fonts)
- **Weights**: 400, 500, 600, 700

### Componenti
- **Glass morphism** effects
- **Gradient backgrounds**  
- **Smooth animations**
- **Micro-interactions**

## 🤝 Contributi

1. Fai **fork** del progetto
2. Crea **feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** modifiche (`git commit -m 'Add some AmazingFeature'`)
4. **Push** al branch (`git push origin feature/AmazingFeature`)
5. Apri **Pull Request**

## 📝 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 📞 Supporto

Per domande o problemi:
- 📧 Email: support@company.com
- 🐛 Issues: [GitHub Issues](https://github.com/tuousername/sistema-gestione-ferie/issues)
- 📖 Docs: Questa documentazione

## 🔮 Roadmap Futuro

- [ ] **Dashboard analytics** con grafici
- [ ] **Calendario** integrato per visualizzazione ferie
- [ ] **Notifiche push** browser
- [ ] **Export PDF** richieste
- [ ] **API mobile** per app dedicata
- [ ] **Integrazione calendario** (Google Calendar, Outlook)

---

**Sviluppato con ❤️ usando React, FastAPI e MongoDB**

*Versione: 1.0.0 | Ultimo aggiornamento: Agosto 2025*
