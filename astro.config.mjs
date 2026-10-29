import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://quancn12.github.io',
  base: '/Physics_read',
  trailingSlash: 'always',
  build: {
    assets: '_astro'
  }
});
