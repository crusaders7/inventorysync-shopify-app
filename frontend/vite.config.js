import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import compression from 'vite-plugin-compression'
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      react(),
      // Bundle size visualization
      isProduction && visualizer({
        filename: './dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
      // Gzip compression
      isProduction && compression({
        algorithm: 'gzip',
        ext: '.gz',
      }),
      // Brotli compression
      isProduction && compression({
        algorithm: 'brotliCompress',
        ext: '.br',
      }),
      // Image optimization
      ViteImageOptimizer({
        jpg: {
          quality: 80,
        },
        png: {
          quality: 80,
        },
        webp: {
          quality: 80,
        },
      }),
    ].filter(Boolean),
    
    server: {
      host: 'localhost',
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      },
      headers: {
        'Content-Security-Policy': "default-src * 'unsafe-inline' 'unsafe-eval'; connect-src * 'unsafe-inline'; frame-ancestors * https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;",
        'Access-Control-Allow-Origin': '*'
      }
    },
    
    build: {
      // Output directory
      outDir: 'dist',
      
      // Enable source maps in production for debugging
      sourcemap: isProduction ? 'hidden' : true,
      
      // Chunk size warnings
      chunkSizeWarningLimit: 1000,
      
      // Minification
      minify: isProduction ? 'terser' : false,
      
      // Terser options
      terserOptions: {
        compress: {
          drop_console: isProduction,
          drop_debugger: isProduction,
        },
      },
      
      // Rollup options
      rollupOptions: {
        output: {
          // Manual chunks for better caching
          manualChunks: {
            // Vendor chunk
            vendor: ['react', 'react-dom', 'react-router-dom'],
            // Polaris UI chunk
            polaris: ['@shopify/polaris'],
            // Utilities chunk
            utils: ['axios', 'date-fns', 'lodash'],
          },
          // Asset file naming
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return `assets/images/[name]-[hash][extname]`
            } else if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
              return `assets/fonts/[name]-[hash][extname]`
            }
            return `assets/[name]-[hash][extname]`
          },
          // Chunk file naming
          chunkFileNames: 'assets/js/[name]-[hash].js',
          // Entry file naming
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },
    },
    
    // Optimization
    optimizeDeps: {
      include: ['react', 'react-dom', '@shopify/polaris'],
    },
    
    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
  }
})
