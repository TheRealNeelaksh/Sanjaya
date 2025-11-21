# Project Sanjaya v2.1 - Quick Start Guide

## 🚀 One-Command Launch

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your NGROK token (optional for remote access):
```
NGROK_AUTH_TOKEN=your_token_here
```

### Step 3: Launch Everything

```bash
python scripts/main.py
```

That's it! The master launcher will:
- ✅ Start FastAPI backend
- ✅ Start all 3 Streamlit dashboards
- ✅ Start NGROK tunnel
- ✅ Create default admin account
- ✅ Run health checks
- ✅ Display all URLs

---

## 📱 Access the System

After running `main.py`, you'll see:

```
=======================================
           ACCESS LINKS
=======================================

🌐 Backend API:
   Public:  https://xxxx.ngrok.io
   Local:   http://localhost:8000
   Docs:    https://xxxx.ngrok.io/docs

📱 Dashboards:
   Child:   http://localhost:8501
   Parent:  http://localhost:8502
   Admin:   http://localhost:8503

🔗 Tracking:
   Pattern: https://xxxx.ngrok.io/track/<username>-<session_hash>
```

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`
- ⚠️ **Change this in production!**

---

## 🧪 Test the System

### 1. Register a Child User

**Via Dashboard:**
- Go to http://localhost:8501 (Child Dashboard)
- Click "Register" tab
- Create account with username/password

**Via API:**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "john123",
    "role": "child"
  }'
```

### 2. Register a Parent User

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mom",
    "password": "mom123",
    "role": "parent"
  }'
```

### 3. Link Parent to Child

**Get admin token first:**
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Copy the `access_token` from response.

**Link parent to child:**
```bash
curl -X POST http://localhost:8000/link_child \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "parent_username": "mom",
    "child_username": "john"
  }'
```

### 4. Child Creates Geofence

Login as child, then:

```bash
curl -X POST http://localhost:8000/geofences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer CHILD_TOKEN" \
  -d '{
    "name": "Home",
    "lat": 28.6139,
    "lon": 77.2090,
    "radius_m": 100
  }'
```

### 5. Child Starts Trip

```bash
curl -X POST http://localhost:8000/start_trip \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer CHILD_TOKEN" \
  -d '{
    "mode": "college",
    "start_place": "Home",
    "end_place": "College"
  }'
```

Response will include `tracking_link`.

### 6. Parent Views Child

- Go to http://localhost:8502 (Parent Dashboard)
- Login as `mom` / `mom123`
- See John's location in real-time!

---

## 🔌 Test Offline Sync

### Simulate Tracking with Offline Caching

First, get a JWT token:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"john123"}' \
  | grep -o '"access_token":"[^"]*"' \
  | cut -d'"' -f4)
```

Start the simulator:
```bash
python scripts/sync_client.py $TOKEN --simulate
```

This will:
- Send location updates every 10 seconds
- Cache points when offline
- Auto-sync when back online
- Show battery drain simulation

To manually sync cached points:
```bash
python scripts/sync_client.py $TOKEN --sync
```

---

## 🛠️ Common Tasks

### View All Users
```bash
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### View All Trips
```bash
curl http://localhost:8000/admin/trips \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### View All Geofences
```bash
curl http://localhost:8000/admin/geofences \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Check API Usage
```bash
cat logs/api_usage.json
```

### View Cached Points
```bash
cat logs/cached_points.json
```

---

## 🚨 Troubleshooting

### "NGROK authentication failed"
- Get your auth token from https://dashboard.ngrok.com/
- Add it to `.env` file: `NGROK_AUTH_TOKEN=your_token`
- Or run without NGROK (local only): The system will use localhost URLs

### "Could not fetch users"
- Admin endpoints need authentication
- Login as admin first to get token
- The main.py script does this automatically

### "Module not found"
- Run from project root directory
- Check virtual environment is activated
- Run: `pip install -r requirements.txt`

### Backend won't start
- Check port 8000 is not in use
- Kill existing process: `lsof -ti:8000 | xargs kill -9`
- Check Python version: `python --version` (need 3.8+)

### Dashboards won't load
- Check backend is running on port 8000
- Verify `API_BASE_URL` in dashboard files
- Check Streamlit ports (8501, 8502, 8503) are free

---

## 📊 System Monitoring

The main launcher automatically displays:

- **Total users** by role
- **Active trips** count
- **API usage** statistics
- **Geofence** count
- **All access URLs**

Refresh system status anytime:
```bash
python scripts/main.py
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` in `.env`
- [ ] Change default admin password
- [ ] Set up HTTPS (NGROK provides this)
- [ ] Restrict CORS origins in `backend/app.py`
- [ ] Enable firewall on ports 8000-8503
- [ ] Set up database backups
- [ ] Review user permissions
- [ ] Enable rate limiting

---

## 🎯 Next Steps

1. **Add more users** via dashboards or API
2. **Create geofences** for children
3. **Start real trips** and track them
4. **Test flight tracking** with AviationStack API
5. **Customize dashboards** to your needs
6. **Set up alerts** for geofence events
7. **Monitor API usage** to stay under limits

---

## 📚 More Information

- Full documentation: See `README.md`
- API documentation: http://localhost:8000/docs (when running)
- Environment config: See `.env.example`

---

**Enjoy Project Sanjaya! 🚀**