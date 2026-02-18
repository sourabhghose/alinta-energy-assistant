# Frontend Deployment Guide

## Overview

The Alinta Energy Assistant includes a modern React + TypeScript frontend with a clean chat interface matching Alinta Energy branding.

## Frontend Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite 5
- **Styling**: Custom CSS (Alinta Energy brand colors)
- **UI Components**: Custom-built chat interface

## Components

### Core Components

1. **ChatInterface** (`src/components/ChatInterface.tsx`)
   - Main chat container
   - Manages conversation state
   - Handles API communication
   - Error handling and loading states

2. **MessageList** (`src/components/MessageList.tsx`)
   - Displays conversation history
   - Renders user and assistant messages
   - Shows source citations

3. **InputBox** (`src/components/InputBox.tsx`)
   - Text input for user questions
   - Send button and keyboard shortcuts
   - Character limit handling

4. **SourceCard** (`src/components/SourceCard.tsx`)
   - Displays source citations
   - Clickable links to original content
   - Source metadata display

5. **StarterQuestions** (`src/components/StarterQuestions.tsx`)
   - Pre-defined example questions
   - Quick-start for new users
   - Category-based question suggestions

## Building the Frontend

### Prerequisites

- Node.js 18+
- npm or yarn

### Build Steps

```bash
# Navigate to frontend directory
cd app/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

This creates an optimized production build in `app/dist/` with:
- `index.html` - Main HTML file
- `assets/` - Bundled JS and CSS files

### Build Output

```
app/dist/
├── index.html              # Entry point (470 bytes)
└── assets/
    ├── index-[hash].js     # Bundled JavaScript (~148 KB)
    └── index-[hash].css    # Styles (~7 KB)
```

## Deployment to Databricks Apps

### Upload to Workspace

```bash
# Upload index.html
databricks workspace import --file app/dist/index.html \
  --format RAW /Workspace/Users/{user}/apps/alinta-energy-assistant/dist/index.html

# Upload assets folder
databricks workspace import --file app/dist/assets/index-[hash].js \
  --format RAW /Workspace/Users/{user}/apps/alinta-energy-assistant/dist/assets/index-[hash].js

databricks workspace import --file app/dist/assets/index-[hash].css \
  --format RAW /Workspace/Users/{user}/apps/alinta-energy-assistant/dist/assets/index-[hash].css
```

### Deploy App

```bash
databricks apps deploy alinta-energy-assistant \
  --source-code-path /Workspace/Users/{user}/apps/alinta-energy-assistant
```

The FastAPI backend automatically serves the frontend:
- Root path `/` → Serves `index.html`
- Static assets → Served from `/assets/`
- API endpoints → Remain at `/api/*`

## Features

### Chat Interface

- **Real-time messaging**: Instant responses from RAG pipeline
- **Conversation history**: Maintains context across multiple turns
- **Loading states**: Visual feedback during processing
- **Error handling**: User-friendly error messages

### Source Citations

- Every answer includes clickable source links
- Shows original content titles and URLs
- Allows users to verify information

### Starter Questions

Example questions help users get started:
- "What electricity plans are available in Western Australia?"
- "How do I pay my bill online?"
- "What is a solar feed-in tariff?"
- "How can I get help with paying my energy bill?"

### Branding

Alinta Energy brand colors:
- Primary Blue: `#0072BC`
- Dark Blue: `#003C71`
- Light Blue: `#E6F2F9`
- Orange Accent: `#FF6B35`

## Development

### Local Development

```bash
cd app/frontend

# Start development server
npm run dev
```

Access at: `http://localhost:5173`

The dev server proxies API requests to `http://localhost:8000` (local backend).

### Hot Module Replacement (HMR)

Vite provides instant hot reload during development:
- Edit any `.tsx` or `.css` file
- Changes appear immediately without full page reload

## Configuration

### Vite Config (`vite.config.ts`)

```typescript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../dist',      // Output to app/dist
    emptyOutDir: true,      // Clean before build
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Proxy API to backend
        changeOrigin: true,
      }
    }
  }
})
```

### TypeScript Config

- Strict type checking enabled
- JSX transform: React 18
- Module resolution: Node

## API Integration

### Request Format

```typescript
POST /api/chat
Content-Type: application/json

{
  "question": "What electricity plans are available?",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "top_k": 3
}
```

### Response Format

```typescript
{
  "answer": "Alinta Energy offers several plans...",
  "sources": [
    {
      "title": "Electricity Plans",
      "url": "https://www.alintaenergy.com.au/plans"
    }
  ],
  "metadata": {
    "retrieved_chunks": 3,
    "tokens_used": 456
  }
}
```

## Current Deployment

✅ **Live Application**
- **URL**: https://alinta-energy-assistant-2556758628403379.aws.databricksapps.com
- **Status**: Running
- **Authentication**: Databricks OAuth (required)

### Accessing the App

1. Navigate to the app URL in your browser
2. Log in via Databricks authentication
3. Start chatting with the AI assistant!

### Features Available

- ✅ Real-time chat interface
- ✅ RAG-powered responses
- ✅ Source citations
- ✅ Conversation history
- ✅ Starter questions
- ✅ Error handling
- ✅ Mobile-responsive design

## Troubleshooting

### Build Issues

**Issue**: `npm run build` fails
- **Solution**: Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

**Issue**: TypeScript errors
- **Solution**: Check `tsconfig.json` and ensure all dependencies are installed

### Deployment Issues

**Issue**: Frontend not loading after deployment
- **Solution**: Verify dist folder was uploaded correctly to workspace
- Check that `app.py` is serving static files from the correct path

**Issue**: API calls failing
- **Solution**: Check CORS configuration in backend
- Verify API endpoints are accessible

### Runtime Issues

**Issue**: 404 errors on refresh
- **Solution**: Ensure FastAPI serves `index.html` for all non-API routes (SPA routing)

**Issue**: Slow initial load
- **Solution**: This is normal - Vite bundles are optimized but may take a moment to parse
- Consider code splitting for larger apps

## Next Steps

### Enhancements

1. **Add conversation export**: Allow users to download chat history
2. **Implement dark mode**: Toggle between light/dark themes
3. **Add voice input**: Speech-to-text for questions
4. **Multi-language support**: Translate interface to other languages
5. **Progressive Web App**: Add PWA manifest for mobile installation

### Optimization

1. **Code splitting**: Split large components into separate bundles
2. **Lazy loading**: Load components on-demand
3. **Image optimization**: Add image loading optimizations
4. **Caching**: Implement service worker for offline support

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Databricks Apps Guide](https://docs.databricks.com/en/dev-tools/databricks-apps/)
