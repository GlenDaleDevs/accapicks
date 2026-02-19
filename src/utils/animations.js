// Central animation variants for Framer Motion
// Import these everywhere — never define variants inline

export const pageVariants = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2, ease: "easeIn" } },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

export const staggerItem = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export const leaderboardRowVariants = {
  initial: { opacity: 0, x: -12 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

export const pickSlotVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: "easeOut" } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: "easeIn" } },
};

export const toastVariants = {
  initial: { opacity: 0, x: 80 },
  animate: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 400, damping: 30 } },
  exit: { opacity: 0, x: 80, transition: { duration: 0.2, ease: "easeIn" } },
};

export const CARD_HOVER = { y: -3, scale: 1.01, transition: { duration: 0.2 } };
export const CARD_TAP = { scale: 0.98, transition: { duration: 0.1 } };
