/**
 * Payment Status Component
 */

import React from 'react';
import { PaymentStatusResponse } from '../../services/paymentService';
import { PaymentStatus as PaymentStatusEnum } from '../../types';

interface PaymentStatusProps {
  status: PaymentStatusResponse;
  onRetry?: () => void;
  onViewOrder?: (orderId: number) => void;
  className?: string;
}

export const PaymentStatus: React.FC<PaymentStatusProps> = ({
  status,
  onRetry,
  onViewOrder,
  className = '',
}) => {
  const getStatusColor = (paymentStatus: PaymentStatusEnum) => {
    switch (paymentStatus) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'refunded':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (paymentStatus: PaymentStatusEnum) => {
    switch (paymentStatus) {
      case 'success':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        );
      case 'failed':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/>
          </svg>
        );
      case 'pending':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        );
      default:
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
        );
    }
  };

  const getStatusText = (paymentStatus: PaymentStatusEnum) => {
    switch (paymentStatus) {
      case 'success':
        return 'Платеж успешно обработан';
      case 'failed':
        return 'Ошибка при обработке платежа';
      case 'pending':
        return 'Платеж обрабатывается';
      case 'refunded':
        return 'Платеж возвращен';
      default:
        return 'Неизвестный статус платежа';
    }
  };

  const getStatusDescription = (paymentStatus: PaymentStatusEnum) => {
    switch (paymentStatus) {
      case 'success':
        return 'Ваш заказ подтвержден и передан в обработку. Мы отправим уведомление о готовности.';
      case 'failed':
        return 'Не удалось обработать платеж. Попробуйте еще раз или обратитесь в поддержку.';
      case 'pending':
        return 'Платеж находится в обработке. Это может занять несколько минут.';
      case 'refunded':
        return 'Платеж был возвращен на вашу карту. Средства поступят в течение 3-5 рабочих дней.';
      default:
        return 'Обратитесь в поддержку для получения информации о статусе платежа.';
    }
  };

  const statusColor = getStatusColor(status.status);

  return (
    <div className={`payment-status ${className}`}>
      <div className={`border rounded-lg p-6 ${statusColor}`}>
        {/* Status Header */}
        <div className="flex items-center space-x-3 mb-4">
          {getStatusIcon(status.status)}
          <div>
            <h3 className="text-lg font-semibold">
              {getStatusText(status.status)}
            </h3>
            <p className="text-sm opacity-75">
              Заказ #{status.orderId} • Платеж #{status.paymentId}
            </p>
          </div>
        </div>

        {/* Status Description */}
        <p className="text-sm mb-4 opacity-90">
          {getStatusDescription(status.status)}
        </p>

        {/* Payment Details */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Сумма платежа:</span>
            <span className="font-medium">{status.amount}₽</span>
          </div>
          <div className="flex justify-between">
            <span>Дата создания:</span>
            <span className="font-medium">
              {new Date(status.createdAt).toLocaleString('ru-RU')}
            </span>
          </div>
          {status.telegramChargeId && (
            <div className="flex justify-between">
              <span>ID транзакции:</span>
              <span className="font-mono text-xs">{status.telegramChargeId}</span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {status.status === 'failed' && status.errorMessage && (
          <div className="mt-4 p-3 bg-red-100 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Причина ошибки:</strong> {status.errorMessage}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex space-x-3">
          {status.status === 'failed' && onRetry && (
            <button
              onClick={onRetry}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors duration-200"
            >
              Попробовать еще раз
            </button>
          )}

          {onViewOrder && (
            <button
              onClick={() => onViewOrder(status.orderId)}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors duration-200 ${
                status.status === 'success'
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
              }`}
            >
              Посмотреть заказ
            </button>
          )}
        </div>

        {/* Loading Animation for Pending */}
        {status.status === 'pending' && (
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="w-4 h-4 bg-yellow-500 rounded-full animate-pulse"></div>
            <div className="w-4 h-4 bg-yellow-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-4 h-4 bg-yellow-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="mt-4 text-center text-sm text-gray-600">
        Если у вас есть вопросы, обратитесь в поддержку через бот
      </div>
    </div>
  );
};

export default PaymentStatus;