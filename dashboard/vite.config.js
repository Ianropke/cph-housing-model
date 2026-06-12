import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { exec } from 'child_process'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'api-server',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url === '/api/update') {
            exec('python3 ../scripts/daily_pipeline.py', (err, stdout, stderr) => {
              res.setHeader('Content-Type', 'application/json');
              if (err) {
                res.statusCode = 500;
                res.end(JSON.stringify({ error: err.message, stderr }));
              } else {
                res.end(JSON.stringify({ message: 'Pipeline updated successfully', stdout }));
              }
            });
          } else if (req.url === '/api/backtest') {
            const cmd = 'PYTHONPATH=../server python3 -c "import sys; sys.path.insert(0, \'../server\'); from cph_housing_server import run_historical_backtest; import json; print(json.dumps(run_historical_backtest(2007, 2024)))"';
            exec(cmd, (err, stdout, stderr) => {
              res.setHeader('Content-Type', 'application/json');
              if (err) {
                res.statusCode = 500;
                res.end(JSON.stringify({ error: err.message, stderr }));
              } else {
                res.end(stdout);
              }
            });
          } else if (req.url === '/api/status') {
            exec('../manage.sh status', (err, stdout, stderr) => {
              res.setHeader('Content-Type', 'application/json');
              if (err) {
                res.statusCode = 500;
                res.end(JSON.stringify({ error: err.message, stderr }));
              } else {
                res.end(JSON.stringify({ status: stdout }));
              }
            });
          } else {
            next();
          }
        });
      }
    }
  ],
})
