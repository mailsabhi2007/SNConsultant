/**
 * Advanced Animation System
 * Provides consistent, smooth animations across the application
 */

export const animations = {
  // Fade animations
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
  },

  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  },

  fadeInDown: {
    initial: { opacity: 0, y: -20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  },

  fadeInScale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
  },

  // Slide animations
  slideInRight: {
    initial: { x: 100, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -100, opacity: 0 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  },

  slideInLeft: {
    initial: { x: -100, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: 100, opacity: 0 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  },

  // Scale animations
  scaleIn: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    exit: { scale: 0 },
    transition: { duration: 0.3, ease: [0.34, 1.56, 0.64, 1] } // Bouncy
  },

  scaleInSpring: {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0, opacity: 0 },
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20
    }
  },

  // Stagger children
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1
      }
    }
  },

  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  },

  // Continuous animations
  pulse: {
    animate: {
      scale: [1, 1.05, 1],
      opacity: [1, 0.8, 1]
    },
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },

  float: {
    animate: {
      y: [0, -10, 0]
    },
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },

  shimmer: {
    animate: {
      backgroundPosition: ["200% 0", "-200% 0"]
    },
    transition: {
      duration: 8,
      repeat: Infinity,
      ease: "linear"
    }
  },

  glow: {
    animate: {
      boxShadow: [
        "0 0 20px rgba(59, 130, 246, 0.3)",
        "0 0 40px rgba(59, 130, 246, 0.6)",
        "0 0 20px rgba(59, 130, 246, 0.3)"
      ]
    },
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },

  // Hover animations
  hoverScale: {
    whileHover: {
      scale: 1.05,
      transition: { duration: 0.2 }
    },
    whileTap: { scale: 0.95 }
  },

  hoverLift: {
    whileHover: {
      y: -4,
      boxShadow: "0 10px 30px rgba(0, 0, 0, 0.1)",
      transition: { duration: 0.2 }
    },
    whileTap: { y: 0 }
  },

  hoverGlow: {
    whileHover: {
      boxShadow: "0 0 30px rgba(59, 130, 246, 0.4)",
      transition: { duration: 0.3 }
    }
  },

  // Loading animations
  spinner: {
    animate: { rotate: 360 },
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear"
    }
  },

  dots: (delay: number = 0) => ({
    animate: {
      scale: [1, 1.5, 1],
      opacity: [0.4, 1, 0.4]
    },
    transition: {
      duration: 1.5,
      repeat: Infinity,
      delay
    }
  }),

  wave: (delay: number = 0) => ({
    animate: {
      y: [0, -10, 0]
    },
    transition: {
      duration: 0.6,
      repeat: Infinity,
      delay,
      ease: "easeInOut"
    }
  }),

  // Page transitions
  pageTransition: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
  },

  // Card animations
  cardHover: {
    whileHover: {
      y: -8,
      boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
      transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
    }
  },

  cardTap: {
    whileTap: { scale: 0.98 }
  }
};

/**
 * Easing functions for custom animations
 */
export const easings = {
  easeInOut: [0.4, 0, 0.2, 1],
  easeOut: [0, 0, 0.2, 1],
  easeIn: [0.4, 0, 1, 1],
  bouncy: [0.34, 1.56, 0.64, 1],
  smooth: [0.25, 0.1, 0.25, 1]
};

/**
 * Duration presets
 */
export const durations = {
  fast: 0.15,
  normal: 0.3,
  slow: 0.5,
  verySlow: 0.8
};

/**
 * Stagger presets
 */
export const stagger = {
  fast: 0.05,
  normal: 0.1,
  slow: 0.15
};
