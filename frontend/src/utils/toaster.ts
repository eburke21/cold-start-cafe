import { createToaster } from "@chakra-ui/react";

/** Shared toaster instance. Import and call `toaster.create(...)` anywhere. */
export const toaster = createToaster({
  placement: "bottom-end",
  pauseOnPageIdle: true,
});
