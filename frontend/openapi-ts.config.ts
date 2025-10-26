import { defineConfig } from '@hey-api/openapi-ts'
import dotenv from 'dotenv'

dotenv.config()
export default defineConfig({
  input: process.env.VITE_GATEWAY_URL + '/openapi.json',
  output: 'src/api',
  parser: {
    filters: {
      tags: {
        include: ['Finance'],
      },
    },
  },
})
