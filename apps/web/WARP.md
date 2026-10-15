# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

VIZION_UI is an AI-powered frontend for generating Manim-based animations from natural language descriptions. Users describe ideas in plain text, and the system generates animated videos through a FastAPI backend.

## Development Commands

### Backend Dependency
**IMPORTANT**: This frontend requires the FastAPI backend running on `http://localhost:8000`.
The app will not function properly without the backend. All API calls are hardcoded to this URL.

### Start Development Server
```bash
npm run dev
```
Runs on `http://localhost:8080` (configured in vite.config.ts)

### Build
```bash
npm run build          # Production build
npm run build:dev      # Development build
```

### Lint
```bash
npm run lint
```
Note: `@typescript-eslint/no-unused-vars` is disabled in eslint.config.js

### Preview Production Build
```bash
npm run preview
```

### Adding shadcn/ui Components
```bash
npx shadcn@latest add <component-name>
```
Configuration is in `components.json`. Components use Radix UI primitives with Tailwind styling.

## Architecture

### Core Application Flow

The app follows a **chat-driven video generation flow**:

1. **Authentication**: Firebase Auth with JWT tokens stored in localStorage (`token`, `uid`)
2. **Chat Interface**: User enters natural language prompts
3. **Backend Communication**: Prompts sent to FastAPI backend at `http://localhost:8000`
4. **Video Generation**: Backend generates Manim animation and returns video URL
5. **Display**: Video appears in split-panel view alongside chat

### State Management Pattern

The main state lives in `Index.tsx` and flows down through components:
- **Chat State**: `messages`, `chats`, `selectedChatId`
- **Video State**: `videoState` (idle/generating/ready/error), `videoSrc`, `videoMetadata`
- **UI State**: `expanded` (controls split-panel layout)

**Split-Panel Behavior**:
- Initially: Chat takes full width (`expanded = false`)
- On first message or chat selection: Layout transitions over 500ms (configured in Tailwind) to 50/50 split
- Chat panel gets `w-1/2` and video panel animates in with `animate-fade-in`
- When starting new chat: Resets to full-width chat view

### Key Data Flow

```
User Input → Index.tsx → API (src/lib/api/chats.ts) → Backend → Video URL → VideoPanel
                ↓
         Chat Messages → ChatPanel → ChatContainer/ChatMessage
```

### Backend Integration

All API calls go through `src/lib/api/chats.ts`:
- `fetchUserChats(userId)` - Get user's chat history
- `fetchChatMessages(userId, chatId)` - Load messages for a chat
- `sendUserPrompt(userId, chatId, prompt)` - Send new prompt and get video
- `fetchVideoFromLatestCode(userId, chatId)` - Regenerate video from existing code

Backend runs on `http://localhost:8000` (FastAPI).

### Authentication Flow

JWT-based auth with token expiry checking:
- Login/Signup pages handle Firebase authentication
- Protected routes check token validity via `isTokenExpired()` function in `App.tsx`
- Expired tokens auto-redirect to `/login`
- Auth functions in `src/lib/auth.ts`

### Component Structure

- **Pages**: `Index` (main app), `LoginPage`, `SignupPage`, `Profile`, `NotFound`
- **Core Components**:
  - `Sidebar`: Chat history and navigation
  - `Header`: Top navigation bar
  - `ChatPanel`: Message display and input (composed of ChatContainer, ChatMessage, ChatInput)
  - `VideoPanel`: Video player and loading states (VideoPlayer, VideoLoading)
- **UI Components**: shadcn/ui components in `src/components/ui/` (Radix UI primitives)

### Styling

- **Tailwind CSS** with custom theme configuration in `tailwind.config.ts`
- **Theme System**: Light/dark mode via `ThemeProvider` (next-themes)
- **Design Tokens**: HSL-based color system with CSS variables (--primary, --secondary, etc.)
- **Custom Animations**: fade-in, pulse-slow, gradient-x, spin-slow defined in Tailwind config

### TypeScript Configuration

- **Path Alias**: `@/` maps to `./src/`
- **Relaxed Type Checking**: `noImplicitAny: false`, `strictNullChecks: false`
- Uses project references (tsconfig.app.json for app, tsconfig.node.json for Vite config)
- Type errors from optional properties are often acceptable given the relaxed config

### Development Tools

- **Vite Plugin**: Uses `@vitejs/plugin-react-swc` for fast refresh with SWC compiler
- **Development Mode**: Includes `lovable-tagger` plugin (component tagging, dev-mode only)
- **React Query**: `@tanstack/react-query` configured with default QueryClient (no custom options)
- **Toast Notifications**: Sonner library (`sonner`) for toast notifications, positioned top-right

### Chat Session Management

- New chats created with UUID when user sends first message (uses `uuid` package: `uuidv4()`)
- Chat titles truncated to 30 chars for display
- Messages include timestamp and sender type (user/ai)
- AI responses use randomized filler text for better UX (two pools: "generating" and "done")
- Message IDs use `crypto.randomUUID()` when loading from backend, `uuidv4()` when creating new

### Error Handling

- All API calls use try/catch with console.error logging
- Video generation errors set `videoState` to "error" and display "❌ Failed to generate video" message
- Token expiry automatically clears localStorage and redirects to `/login`
- No formal error boundaries - errors are handled at the component level

## Project Structure

```
src/
├── pages/          # Route components (Index, Login, Signup, Profile)
├── components/
│   ├── chat/       # Chat UI (ChatPanel, ChatMessage, ChatInput, ChatContainer)
│   ├── video/      # Video display (VideoPanel, VideoPlayer, VideoLoading)
│   ├── sidebar/    # Navigation sidebar (Sidebar, ChatList, Logo)
│   ├── header/     # Top header
│   ├── profile/    # User profile components
│   ├── theme/      # Theme provider
│   └── ui/         # shadcn/ui components (Radix UI wrappers)
├── lib/
│   ├── api/        # Backend API functions (chats.ts, payments.ts)
│   ├── auth.ts     # Firebase authentication
│   └── utils.ts    # Utility functions (cn for class merging)
├── hooks/          # Custom React hooks (use-toast, use-mobile)
├── types/          # TypeScript types (ChatMessage, VideoState, etc.)
├── constants/      # App constants
└── utils/          # Helper functions (createUserMessage, createAiMessage)
```

## Important Implementation Notes

### When Working with Video Generation
- Always append cache-busting query param to video URLs: `${videoUrl}?t=${Date.now()}`
- Video state must transition: idle → generating → ready (or error)
- Display loading state in VideoPanel while `videoState === "generating"`

### When Working with Authentication
- Check token expiry before making authenticated requests
- Clear localStorage on logout or token expiry
- ProtectedRoute wrapper handles route guarding in App.tsx

### When Adding API Endpoints
- Add new functions to `src/lib/api/` files
- Base URL is hardcoded as `http://localhost:8000` in chats.ts and auth.ts
- All API functions are async and return `res.json()` directly (no error checking in API layer)
- Error handling happens in the calling component (Index.tsx, LoginPage.tsx, etc.)
- POST requests require `Content-Type: application/json` header

### When Styling Components
- Use existing design tokens from theme (primary, secondary, muted, etc.)
- Prefer Tailwind utility classes over custom CSS
- Use existing animations from tailwind.config.ts
- shadcn/ui components already follow theme system

### When Working with Chat Messages
- Use `createUserMessage()` and `createAiMessage()` from utils
- Messages require: id (UUID), sender ("user" | "ai"), text, timestamp
- Randomized AI responses improve perceived intelligence

### Routing and Navigation
- Uses React Router v6 (`react-router-dom`)
- Protected routes wrapped with `ProtectedRoute` component in App.tsx
- JWT token validation happens on every protected route render
- Available routes: `/` (Index), `/login`, `/signup`, `/profile`, `*` (NotFound)

### Testing
- No test framework is currently configured
- No test files exist in the repository
