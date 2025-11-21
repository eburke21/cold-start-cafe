import {
  Toaster as ChakraToaster,
  Toast,
} from "@chakra-ui/react";
import { toaster } from "../utils/toaster";

/**
 * Render this component once at the app root to enable toast notifications.
 * Use `toaster.create(...)` anywhere to show a toast.
 */
export function Toaster() {
  return (
    <ChakraToaster toaster={toaster}>
      {(toast) => (
        <Toast.Root>
          <Toast.Title>{toast.title}</Toast.Title>
          {toast.description && (
            <Toast.Description>{toast.description}</Toast.Description>
          )}
          <Toast.CloseTrigger />
        </Toast.Root>
      )}
    </ChakraToaster>
  );
}
