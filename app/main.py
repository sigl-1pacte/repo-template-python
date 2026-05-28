from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="my-service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>my-service</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: #0f0f13;
      color: #ececec;
      font-family: system-ui, sans-serif;
    }

    .logo {
      width: 80px;
      height: 80px;
      margin-bottom: 2rem;
      animation: spin 8s linear infinite;
      filter: drop-shadow(0 0 18px #387eb855);
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }

    h1 {
      font-size: 2.4rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #646cff, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }

    p {
      color: #888;
      font-size: 1rem;
      margin-bottom: 2.5rem;
    }

    .cards {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      justify-content: center;
    }

    .card {
      background: #1a1a2e;
      border: 1px solid #2a2a40;
      border-radius: 12px;
      padding: 1.2rem 1.6rem;
      width: 180px;
      text-align: center;
      transition: border-color .25s, box-shadow .25s;
      text-decoration: none;
      color: inherit;
    }

    .card:hover {
      border-color: #646cff;
      box-shadow: 0 0 20px #646cff33;
    }

    .card span { font-size: 1.6rem; display: block; margin-bottom: .4rem; }
    .card p    { font-size: .85rem; color: #aaa; margin: 0; }
  </style>
</head>
<body>
  <svg class="logo" viewBox="0 0 111.959 115.096" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="pyA" x1="12.959" x2="79.498" y1="0" y2="63.25" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#387EB8"/>
        <stop offset="1" stop-color="#366994"/>
      </linearGradient>
      <linearGradient id="pyB" x1="32.098" x2="98.638" y1="51.845" y2="115.096" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#FFE052"/>
        <stop offset="1" stop-color="#FFC331"/>
      </linearGradient>
    </defs>
    <path fill="url(#pyA)" d="M54.918.019C26.369.019 28.146 12.26 28.146 12.26l.033 12.682h27.24v3.808H17.58S0 26.57 0 55.395c0 28.825 15.926 27.8 15.926 27.8h9.512V70.302S24.893 54.376 41.067 54.376h26.915s15.376.249 15.376-14.874V15.17C83.358.019 54.918.019 54.918.019zM40.283 8.73a4.967 4.967 0 0 1 4.965 4.967 4.967 4.967 0 0 1-4.965 4.965 4.967 4.967 0 0 1-4.965-4.965A4.967 4.967 0 0 1 40.283 8.73z"/>
    <path fill="url(#pyB)" d="M55.857 115.077c28.549 0 26.772-12.241 26.772-12.241l-.033-12.682H55.356v-3.808h37.839s17.58 1.98 17.58-26.845c0-28.825-15.926-27.8-15.926-27.8h-9.512v12.893s.545 15.926-15.629 15.926H43.793s-15.376-.249-15.376 14.874v24.332c0 15.151 28.44 15.151 28.44 15.151zm14.635-8.711a4.967 4.967 0 0 1-4.965-4.967 4.967 4.967 0 0 1 4.965-4.965 4.967 4.967 0 0 1 4.965 4.965 4.967 4.967 0 0 1-4.965 4.967z"/>
  </svg>

  <h1>my-service</h1>
  <p>Your Python service is running.</p>

  <div class="cards">
    <a class="card" href="/docs">
      <span>📖</span>
      <p>API docs</p>
    </a>
    <a class="card" href="/redoc">
      <span>📄</span>
      <p>ReDoc</p>
    </a>
    <a class="card" href="/health">
      <span>💚</span>
      <p>Health</p>
    </a>
  </div>
</body>
</html>"""
