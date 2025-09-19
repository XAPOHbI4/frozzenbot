/**
 * Telegram WebApp utilities
 */

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: any;
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: any;
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  headerColor: string;
  backgroundColor: string;
  isClosingConfirmationEnabled: boolean;

  // Methods
  ready(): void;
  expand(): void;
  close(): void;
  showAlert(message: string, callback?: () => void): void;
  showConfirm(message: string, callback: (confirmed: boolean) => void): void;
  showPopup(params: any, callback?: (buttonId: string) => void): void;
  showScanQrPopup(params: any, callback?: (data: string) => void): void;
  closeScanQrPopup(): void;
  readTextFromClipboard(callback?: (data: string) => void): void;
  openLink(url: string, options?: { try_instant_view?: boolean }): void;
  openTelegramLink(url: string): void;
  openInvoice(url: string, callback?: (status: string) => void): void;
  setHeaderColor(color: string): void;
  setBackgroundColor(color: string): void;
  enableClosingConfirmation(): void;
  disableClosingConfirmation(): void;
  hapticFeedback: {
    impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
    notificationOccurred(type: 'error' | 'success' | 'warning'): void;
    selectionChanged(): void;
  };

  // Events
  onEvent(eventType: string, callback: Function): void;
  offEvent(eventType: string, callback: Function): void;
  sendData(data: string): void;

  // MainButton
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;
    isProgressVisible: boolean;
    setText(text: string): void;
    onClick(callback: () => void): void;
    offClick(callback: () => void): void;
    show(): void;
    hide(): void;
    enable(): void;
    disable(): void;
    showProgress(leaveActive?: boolean): void;
    hideProgress(): void;
    setParams(params: any): void;
  };

  // BackButton
  BackButton: {
    isVisible: boolean;
    onClick(callback: () => void): void;
    offClick(callback: () => void): void;
    show(): void;
    hide(): void;
  };
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

/**
 * Initialize Telegram WebApp
 */
export const initTelegramWebApp = (): TelegramWebApp | null => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    return tg;
  }
  return null;
};

/**
 * Check if running inside Telegram WebApp
 */
export const isTelegramWebApp = (): boolean => {
  return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
};

/**
 * Get Telegram user data from WebApp
 */
export const getTelegramUser = () => {
  if (!isTelegramWebApp()) return null;

  const tg = window.Telegram!.WebApp;
  return tg.initDataUnsafe?.user || null;
};

/**
 * Show Telegram alert
 */
export const showTelegramAlert = (message: string, callback?: () => void): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.showAlert(message, callback);
  } else {
    alert(message);
    callback?.();
  }
};

/**
 * Show Telegram confirm dialog
 */
export const showTelegramConfirm = (
  message: string,
  callback: (confirmed: boolean) => void
): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.showConfirm(message, callback);
  } else {
    const confirmed = confirm(message);
    callback(confirmed);
  }
};

/**
 * Close Telegram WebApp
 */
export const closeTelegramWebApp = (): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.close();
  }
};

/**
 * Expand Telegram WebApp
 */
export const expandTelegramWebApp = (): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.expand();
  }
};

/**
 * Set Telegram WebApp header color
 */
export const setTelegramHeaderColor = (color: string): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.setHeaderColor(color);
  }
};

/**
 * Set Telegram WebApp background color
 */
export const setTelegramBackgroundColor = (color: string): void => {
  if (isTelegramWebApp()) {
    window.Telegram!.WebApp.setBackgroundColor(color);
  }
};

/**
 * Haptic feedback
 */
export const telegramHapticFeedback = {
  impact: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.hapticFeedback.impactOccurred(style);
    }
  },

  notification: (type: 'error' | 'success' | 'warning') => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.hapticFeedback.notificationOccurred(type);
    }
  },

  selection: () => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.hapticFeedback.selectionChanged();
    }
  },
};

/**
 * Main Button utilities
 */
export const telegramMainButton = {
  show: (text: string, callback: () => void) => {
    if (isTelegramWebApp()) {
      const mainButton = window.Telegram!.WebApp.MainButton;
      mainButton.setText(text);
      mainButton.onClick(callback);
      mainButton.show();
    }
  },

  hide: () => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.MainButton.hide();
    }
  },

  setProgress: (show: boolean) => {
    if (isTelegramWebApp()) {
      const mainButton = window.Telegram!.WebApp.MainButton;
      if (show) {
        mainButton.showProgress();
      } else {
        mainButton.hideProgress();
      }
    }
  },

  enable: () => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.MainButton.enable();
    }
  },

  disable: () => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.MainButton.disable();
    }
  },
};

/**
 * Back Button utilities
 */
export const telegramBackButton = {
  show: (callback: () => void) => {
    if (isTelegramWebApp()) {
      const backButton = window.Telegram!.WebApp.BackButton;
      backButton.onClick(callback);
      backButton.show();
    }
  },

  hide: () => {
    if (isTelegramWebApp()) {
      window.Telegram!.WebApp.BackButton.hide();
    }
  },
};

/**
 * Theme utilities
 */
export const getTelegramTheme = () => {
  if (isTelegramWebApp()) {
    const tg = window.Telegram!.WebApp;
    return {
      colorScheme: tg.colorScheme,
      themeParams: tg.themeParams,
      headerColor: tg.headerColor,
      backgroundColor: tg.backgroundColor,
    };
  }
  return null;
};

/**
 * Viewport utilities
 */
export const getTelegramViewport = () => {
  if (isTelegramWebApp()) {
    const tg = window.Telegram!.WebApp;
    return {
      height: tg.viewportHeight,
      stableHeight: tg.viewportStableHeight,
      isExpanded: tg.isExpanded,
    };
  }
  return null;
};

/**
 * Initialize WebApp with optimal settings
 */
export const setupTelegramWebApp = () => {
  const tg = initTelegramWebApp();
  if (!tg) return null;

  // Expand WebApp for better UX
  tg.expand();

  // Set colors for better integration
  if (tg.colorScheme === 'dark') {
    tg.setHeaderColor('#1f2937');
    tg.setBackgroundColor('#111827');
  } else {
    tg.setHeaderColor('#ffffff');
    tg.setBackgroundColor('#ffffff');
  }

  // Enable closing confirmation for important actions
  tg.enableClosingConfirmation();

  return tg;
};

export default {
  init: initTelegramWebApp,
  isTelegramWebApp,
  getTelegramUser,
  showAlert: showTelegramAlert,
  showConfirm: showTelegramConfirm,
  close: closeTelegramWebApp,
  expand: expandTelegramWebApp,
  haptic: telegramHapticFeedback,
  mainButton: telegramMainButton,
  backButton: telegramBackButton,
  theme: getTelegramTheme,
  viewport: getTelegramViewport,
  setup: setupTelegramWebApp,
};