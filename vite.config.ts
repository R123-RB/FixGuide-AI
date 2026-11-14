import { defineConfig } from 'vite';
import fs from 'fs';
import path from 'path';

export default defineConfig({
  plugins: [
    {
      name: 'serve-static-dir',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith('/static/')) {
            const cleanUrl = req.url.split('?')[0];
            const filePath = path.join(__dirname, cleanUrl);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              if (filePath.endsWith('.css')) res.setHeader('Content-Type', 'text/css');
              if (filePath.endsWith('.js')) res.setHeader('Content-Type', 'application/javascript');
              return fs.createReadStream(filePath).pipe(res);
            }
          }
          next();
        });
      },
    },
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
