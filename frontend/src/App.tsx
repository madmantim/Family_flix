import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserSelect } from './pages/UserSelect';
import { SwipeScreen } from './pages/SwipeScreen';
import { Watchlist } from './pages/Watchlist';
import { MovieNight } from './pages/MovieNight';
import { History } from './pages/History';
import { useCurrentMember } from './hooks/useCurrentMember';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { memberId } = useCurrentMember();
  if (!memberId) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<UserSelect />} />
          <Route
            path="/swipe"
            element={
              <ProtectedRoute>
                <SwipeScreen />
              </ProtectedRoute>
            }
          />
          <Route
            path="/watchlist"
            element={
              <ProtectedRoute>
                <Watchlist />
              </ProtectedRoute>
            }
          />
          <Route
            path="/movie-night"
            element={
              <ProtectedRoute>
                <MovieNight />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
