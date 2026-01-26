# Frontend Developer & Agent Guide

This document outlines the architectural standards, coding conventions, and best practices for the **EquityPulse** frontend.

## 1. Code Organization & Architecture

We use **React (Vite)** with **TypeScript** and **Tailwind CSS**.

*   **`src/components/`**: **UI Components**.
    *   *Rule:* Components should be functional. Split large components (like Dashboards) into smaller sub-components (e.g., `AnalysisCard`, `LogViewer`).
    *   *Style:* Co-locate component-specific logic with the component.
*   **`src/api.ts`**: **Data Access Layer**.
    *   *Responsibility:* Centralized Axios instance and API functions.
    *   *Rule:* Components should call functions from `api.ts`, not `axios.get` directly.
*   **`src/assets/`**: Static assets (images, SVGs).
*   **`src/hooks/`** (Recommended): Custom hooks for reusable state logic (e.g., `useAnalysisStatus`).

## 2. SOLID Principles in React

*   **Single Responsibility Principle (SRP):**
    *   **Scope:** Applies to Components AND the functions inside them.
    *   *Bad (Component Level):* A `Dashboard` component that fetches data, formats dates, manages WebSocket connections, and renders the UI.
    *   *Good (Component Level):* A `Dashboard` that calls a `useAnalysisData` hook (for logic) and renders `AnalysisView` (presentation).
    *   *Bad (Function Level):* An `onSubmit` handler that validates form data, transforms it, calls the API, and updates local state error messages all in one block.
    *   *Good (Function Level):* Extract logic into small, pure functions.
        ```typescript
        const handleSubmit = () => {
             if (!isValid(formData)) return; // Small validation helper
             const payload = transformToApiFormat(formData); // Small transformer
             submitData(payload);
        }
        ```
    *   **Small Functions:** Even inside a component file, write small helper functions outside the component definition if they don't depend on props/state.
*   **Open/Closed Principle:**
    *   Components should be open for extension (via props) but closed for modification.
    *   *Example:* A `Button` component that accepts `className` props to extend styles without changing the base component code.

## 3. Writing Reusable Functions & Hooks

### Helper Functions
For pure logic (formatting, calculations), use utility files.

*   *Location:* `src/utils/` (create if needed) or inside `src/lib/`.
*   *Example:*
    ```typescript
    // src/utils/formatters.ts
    export const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };
    ```

### Custom Hooks
For logic involving React state/effects.

*   *Example:*
    ```typescript
    // src/hooks/useFetch.ts
    export function useFetch<T>(url: string) {
        const [data, setData] = useState<T | null>(null);
        // ... useEffect logic ...
        return { data, loading, error };
    }
    ```

## 4. Logging & Debugging

*   **Development:** `console.log` is acceptable for debugging but should be cleaned up before merging.
*   **Production:** Errors should be caught via Error Boundaries or `try/catch` blocks and displayed gracefully to the user (e.g., Toast notifications or Error Cards).
*   **Agent Logs:** We use a specialized `LogViewer` component to show backend agent activity. Do not confuse this with browser console logs.

## 5. Engineering Design Principles

### High-Level Design (HLD)
*   **Component Composition:** Build pages by composing smaller, isolated components.
*   **State Management:**
    *   Use local state (`useState`) for UI-only state (isDropdownOpen).
    *   Use `useEffect` for side effects (fetching data), but prefer libraries like TanStack Query (if we upgrade) or custom hooks to avoid effect spaghetti.
    *   Lift state up only when necessary.
*   **Responsive Design:** Use Tailwind's responsive prefixes (`md:`, `lg:`) to ensure mobile-first compatibility.

### Low-Level Design (LLD)
*   **Typing:** Strict TypeScript usage. Avoid `any`. Define interfaces for Props and API responses.
    ```typescript
    interface UserProfileProps {
        username: string;
        isActive?: boolean; // Optional
    }
    ```
*   **Styling:** Use `clsx` or `tailwind-merge` for dynamic class names.
    ```typescript
    <div className={clsx("p-4", isActive ? "bg-blue-500" : "bg-gray-200")}>
    ```

## 6. What Developers/Architects Do Here
*   **UX Consistency:** Ensure all buttons, inputs, and cards follow the design system (Tailwind classes).
*   **Performance:** Avoid unnecessary re-renders. Use `useMemo` and `useCallback` for expensive operations only when profiling shows a need.
*   **Code Reviews:** Check for prop drilling (passing data through too many layers) -> suggest Context API.
