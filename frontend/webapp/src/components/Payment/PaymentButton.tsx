/**
 * Payment Button Component
 */

import React from 'react';
import { PaymentService } from '../../services/paymentService';

interface PaymentButtonProps {
  amount: number;
  paymentMethod: string;
  loading: boolean;
  disabled?: boolean;
  onPayment: () => void;
  className?: string;
}

export const PaymentButton: React.FC<PaymentButtonProps> = ({
  amount,
  paymentMethod,
  loading,
  disabled = false,
  onPayment,
  className = '',
}) => {
  const isMinOrderMet = amount >= 1500;
  const buttonDisabled = disabled || loading || !isMinOrderMet;

  const getButtonText = () => {
    if (loading) {
      return paymentMethod === 'telegram' ? 'Обработка платежа...' : 'Создание заказа...';
    }

    if (!isMinOrderMet) {
      const shortage = 1500 - amount;
      return `Добавьте товары на ${PaymentService.formatAmount(shortage)}`;
    }

    if (paymentMethod === 'telegram') {
      return `Оплатить ${PaymentService.formatAmount(amount)}`;
    }

    return `Оформить заказ на ${PaymentService.formatAmount(amount)}`;
  };

  const getButtonStyle = () => {
    if (buttonDisabled) {
      return 'bg-gray-300 cursor-not-allowed text-gray-500';
    }

    if (paymentMethod === 'telegram') {
      return 'bg-blue-500 hover:bg-blue-600 text-white';
    }

    return 'bg-green-500 hover:bg-green-600 text-white';
  };

  return (
    <div className={`payment-button-container ${className}`}>
      <button
        onClick={onPayment}
        disabled={buttonDisabled}
        className={`w-full py-4 px-6 rounded-lg font-semibold text-lg transition-colors duration-200 flex items-center justify-center space-x-2 ${getButtonStyle()}`}
      >
        {loading && (
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}

        {paymentMethod === 'telegram' && !loading && (
          <div className="text-white">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.568 8.16l-1.58 7.44c-.12.537-.432.668-.864.414l-2.4-1.764-1.152 1.116c-.128.128-.24.24-.48.24l.168-2.4 4.32-3.888c.192-.168-.048-.264-.288-.096l-5.328 3.36-2.304-.72c-.504-.156-.504-.504.096-.744l8.928-3.456c.432-.156.792.096.672.576z"/>
            </svg>
          </div>
        )}

        {paymentMethod === 'cash' && !loading && (
          <div className="text-white">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3h18v18H3z"/>
              <path d="m3 12 18 0"/>
              <path d="M12 3v18"/>
            </svg>
          </div>
        )}

        <span>{getButtonText()}</span>
      </button>

      {/* Additional Info */}
      {isMinOrderMet && (
        <div className="mt-3 text-center">
          {paymentMethod === 'telegram' && (
            <p className="text-sm text-gray-600">
              После нажатия откроется защищенное окно Telegram для ввода данных карты
            </p>
          )}

          {paymentMethod === 'cash' && (
            <p className="text-sm text-gray-600">
              Заказ будет создан и отправлен в обработку. Оплата при получении
            </p>
          )}
        </div>
      )}

      {/* Security Badge for Telegram Payments */}
      {paymentMethod === 'telegram' && isMinOrderMet && (
        <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-gray-500">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM9 6c0-1.66 1.34-3 3-3s3 1.34 3 3v2H9V6z"/>
          </svg>
          <span>Платежи защищены 256-битным шифрованием SSL</span>
        </div>
      )}
    </div>
  );
};

export default PaymentButton;