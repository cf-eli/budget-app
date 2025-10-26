import js from '@eslint/js'
import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import pluginQuasar from '@quasar/app-vite/eslint'
import vueTsEslintConfig from '@vue/eslint-config-typescript'
import prettierSkipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser' // Import the parser explicitly
import vueParser from 'vue-eslint-parser' // Import the Vue parser

export default [
  // Ignore auto-generated files and node_modules
  {
    ignores: [
      'node_modules/**',
      'src/api/**/*.gen.ts',
      'src/api/client.gen.ts',
      'src/api/core/**/*.gen.ts',
      'dist/**',
      '.quasar/**',
    ],
  },

  // Base configuration for JavaScript
  js.configs.recommended,
  ...pluginQuasar.configs.recommended(),
  ...pluginVue.configs['flat/essential'],

  // TypeScript-specific configuration
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser, // Use @typescript-eslint/parser directly
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: new URL('.', import.meta.url).pathname,
        sourceType: 'module',
        extraFileExtensions: ['.vue'], // Include this for TypeScript files referencing .vue
      },
      globals: {
        ...globals.node,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
    },
  },

  // Vue-specific configuration
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser, // Use vue-eslint-parser
      parserOptions: {
        parser: tsParser, // Forward TypeScript parser for script blocks
        project: './tsconfig.json',
        tsconfigRootDir: new URL('.', import.meta.url).pathname,
        sourceType: 'module',
        extraFileExtensions: ['.vue'], // Add support for .vue files
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      'vue/no-unused-vars': 'error',
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
    },
  },

  // PWA-specific service worker configuration
  {
    files: ['src-pwa/custom-service-worker.ts'],
    languageOptions: {
      globals: {
        ...globals.serviceworker,
      },
    },
  },

  // Prettier integration
  prettierSkipFormatting,
]
