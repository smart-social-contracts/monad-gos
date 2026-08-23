import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve } from 'node:path';
import { writeFileSync, mkdirSync } from 'node:fs';

/**
 * Frontend env (optional unless noted):
 * - VITE_MONAD_GOS_CANISTER_ID — backend canister
 * - VITE_IC_HOST — replica / IC gateway (default http://127.0.0.1:4943)
 * - VITE_MONAD_GOS_MOCK — mock data when true
 * - VITE_MONAD_MCP_URL — Monad MCP server base URL (default http://127.0.0.1:5002)
 * - VITE_MONAD_PRINCIPAL — Monad author principal for thread UI
 */

const BUILD_ID = Date.now().toString();

const distHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <title>Monad GOS</title>
    <link rel="stylesheet" href="./monad-gos-frontend.css?v=${BUILD_ID}" />
  </head>
  <body>
    <div id="monad-gos-root"></div>
    <script type="module" src="./index.js?v=${BUILD_ID}"></script>
  </body>
</html>
`;

const assetsJson = `[
  {
    "match": "**/*",
    "headers": {
      "Cache-Control": "no-cache, must-revalidate"
    }
  }
]
`;

export default defineConfig({
	plugins: [
		svelte({ emitCss: false }),
		{
			name: 'emit-index-html',
			closeBundle() {
				mkdirSync(resolve(__dirname, 'dist'), { recursive: true });
				writeFileSync(resolve(__dirname, 'dist/index.html'), distHtml);
				writeFileSync(resolve(__dirname, 'dist/.ic-assets.json5'), assetsJson);
			},
		},
	],
	base: './',
	build: {
		lib: {
			entry: resolve(__dirname, 'src/index.ts'),
			name: 'MonadGosFrontend',
			formats: ['es'],
			fileName: () => 'index.js',
		},
		rollupOptions: {
			output: {
				inlineDynamicImports: true,
			},
		},
		cssCodeSplit: false,
		minify: 'esbuild',
		sourcemap: false,
		target: 'es2020',
		emptyOutDir: true,
		outDir: 'dist',
	},
});
