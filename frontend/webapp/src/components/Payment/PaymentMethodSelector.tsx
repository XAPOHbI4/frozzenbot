/**
 * Payment Method Selector Component
 */

import React from 'react';
import { PaymentMethod } from '../../services/paymentService';

interface PaymentMethodSelectorProps {
  methods: PaymentMethod[];
  selectedMethod: string;
  onMethodSelect: (methodId: string) => void;
  disabled?: boolean;
  className?: string;
}

export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  methods,
  selectedMethod,
  onMethodSelect,
  disabled = false,
  className = '',
}) => {
  return (
    <div className={`payment-methods ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Способ оплаты
      </h3>

      <div className="space-y-3">
        {methods
          .filter(method => method.enabled)
          .map((method) => (
            <div
              key={method.id}
              className={`payment-method-option ${
                selectedMethod === method.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200'
              } ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-300'
              } border-2 rounded-lg p-4 transition-colors duration-200`}
              onClick={() => !disabled && onMethodSelect(method.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-4 h-4 rounded-full border-2 ${
                      selectedMethod === method.id
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    } flex items-center justify-center`}
                  >
                    {selectedMethod === method.id && (
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    )}
                  </div>
                  <div>
                    <div className="font-medium text-gray-800">{method.name}</div>
                    <div className="text-sm text-gray-600">{method.description}</div>
                  </div>
                </div>

                {method.id === 'telegram' && (
                  <div className="text-blue-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.568 8.16l-1.58 7.44c-.12.537-.432.668-.864.414l-2.4-1.764-1.152 1.116c-.128.128-.24.24-.48.24l.168-2.4 4.32-3.888c.192-.168-.048-.264-.288-.096l-5.328 3.36-2.304-.72c-.504-.156-.504-.504.096-.744l8.928-3.456c.432-.156.792.096.672.576z"/>
                    </svg>
                  </div>
                )}

                {method.id === 'cash' && (
                  <div className="text-green-500">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                      <line x1="1" y1="10" x2="23" y2="10"/>
                    </svg>
                  </div>
                )}
              </div>
            </div>
          ))}
      </div>

      {selectedMethod === 'telegram' && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="text-blue-500 mt-0.5">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div className="text-sm text-blue-700">
              <div className="font-medium">Безопасная оплата</div>
              <div>Платеж будет обработан через защищенную систему Telegram Payments</div>
            </div>
          </div>
        </div>
      )}

      {selectedMethod === 'cash' && (
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="text-amber-500 mt-0.5">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div className="text-sm text-amber-700">
              <div className="font-medium">Оплата при получении</div>
              <div>Подготовьте точную сумму для передачи курьеру</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentMethodSelector;