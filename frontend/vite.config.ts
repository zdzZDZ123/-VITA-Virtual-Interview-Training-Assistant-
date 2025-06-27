import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import viteCompression from 'vite-plugin-compression'
import { visualizer } from 'rollup-plugin-visualizer'
import Icons from 'unplugin-icons/vite'
// import vitePluginImp from 'vite-plugin-imp'  // 暂时不使用

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    
    // 按需加载UI组件库（当前未使用，已注释）
    // vitePluginImp({
    //   libList: [
    //     {
    //       libName: '@mui/material',
    //       style: (name) => `@mui/material/${name}/style/index.js`,
    //     },
    //     {
    //       libName: 'antd',
    //       style: (name) => `antd/es/${name}/style`,
    //     },
    //   ],
    // }),
    
    // 按需加载图标
    Icons({
      compiler: 'jsx',
      jsx: 'react',
      autoInstall: true,
    }),
    
    // Gzip压缩
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240, // 10kb以上才压缩
      algorithm: 'gzip',
      ext: '.gz',
      deleteOriginFile: false,
    }),
    
    // Brotli压缩
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240,
      algorithm: 'brotliCompress',
      ext: '.br',
      deleteOriginFile: false,
    }),
    
    // Bundle分析器（仅在分析模式下启用）
    process.env.ANALYZE && visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ].filter(Boolean),
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  build: {
    // 启用CSS代码分割
    cssCodeSplit: true,
    
    // 构建输出目录
    outDir: 'dist',
    
    // 启用源码映射（生产环境建议关闭）
    sourcemap: false,
    
    // 启用压缩
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    
    // 警告大小限制
    chunkSizeWarningLimit: 1000,
    
    rollupOptions: {
      output: {
        // 手动代码分割策略
        manualChunks: {
          // React相关
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          
          // Three.js相关
          'three-vendor': ['three', '@react-three/fiber', '@react-three/drei'],
          
          // 工具库
          'utils-vendor': ['axios', 'zustand'],
        },
        
        // 基于内容的哈希命名
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk';
          return `js/[name]-${facadeModuleId}-[hash].js`;
        },
        
        // 入口文件命名
        entryFileNames: 'js/[name]-[hash].js',
        
        // 资源文件命名
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || 'unknown';
          const info = name.split('.');
          const ext = info[info.length - 1];
          
          if (/\.(png|jpe?g|gif|svg|ico|webp)$/.test(name)) {
            return `images/[name]-[hash].${ext}`;
          }
          
          if (/\.(woff2?|eot|ttf|otf)$/.test(name)) {
            return `fonts/[name]-[hash].${ext}`;
          }
          
          if (/\.css$/.test(name)) {
            return `css/[name]-[hash].${ext}`;
          }
          
          return `assets/[name]-[hash].${ext}`;
        },
      },
    },
  },
  
  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'three',
      '@react-three/fiber',
      '@react-three/drei',
    ],
    exclude: ['@vite/client', '@vite/env'],
  },
  
  server: {
    port: 5174,
    proxy: {
      '/session': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/speech': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    }
  }
})
