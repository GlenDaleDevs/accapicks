import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toastVariants } from "../utils/animations";
import { subscribe, dismissToast } from "../utils/toast";

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const unsubscribe = subscribe(setToasts);
    return unsubscribe;
  }, []);

  return (
    <div className="toast-container">
      <AnimatePresence mode="sync">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            className={`toast toast-${toast.type}`}
            variants={toastVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            layout
          >
            <span className="toast-message">{toast.message}</span>
            <button
              className="toast-dismiss"
              onClick={() => dismissToast(toast.id)}
              aria-label="Dismiss"
            >
              &#10005;
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
