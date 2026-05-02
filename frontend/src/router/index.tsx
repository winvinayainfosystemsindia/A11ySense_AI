import { 
  createRootRoute, 
  createRoute, 
  createRouter, 
  Outlet 
} from '@tanstack/react-router';
import Home from '../pages/Home';
import Audit from '../pages/Audit';

// Create a root route
const rootRoute = createRootRoute({
  component: () => (
    <>
      <Outlet />
      {/* Add DevTools or Global Components here */}
    </>
  ),
});

// Create routes
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Home,
});

const auditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/audit',
  component: Audit,
});

// Create the route tree
const routeTree = rootRoute.addChildren([indexRoute, auditRoute]);

// Create the router
export const router = createRouter({ routeTree });

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
