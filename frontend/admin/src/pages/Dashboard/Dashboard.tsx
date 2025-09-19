import React from 'react';
import { useQuery } from 'react-query';
import {
  ShoppingBagIcon,
  CurrencyDollarIcon,
  ClipboardDocumentListIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { DashboardStats } from '../../types';
import * as dashboardService from '../../services/dashboard';

const Dashboard: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>(
    'dashboard-stats',
    dashboardService.getDashboardStats,
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow h-32"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
              <p className="mt-2 text-sm text-red-700">
                Unable to load dashboard statistics. Please try again later.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Revenue',
      value: stats ? `$${stats.total_revenue.toFixed(2)}` : '$0.00',
      change: stats ? `$${stats.revenue_today.toFixed(2)} today` : '$0.00 today',
      icon: CurrencyDollarIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Total Orders',
      value: stats?.total_orders?.toString() || '0',
      change: stats ? `${stats.orders_today} today` : '0 today',
      icon: ClipboardDocumentListIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Pending Orders',
      value: stats?.pending_orders?.toString() || '0',
      change: 'Needs attention',
      icon: ClipboardDocumentListIcon,
      color: 'bg-yellow-500',
    },
    {
      name: 'Total Products',
      value: stats?.total_products?.toString() || '0',
      change: stats ? `${stats.low_stock_products} low stock` : '0 low stock',
      icon: ShoppingBagIcon,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your FrozenBot store performance
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-3 rounded-md ${stat.color}`}>
                    <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                    <dd className="text-lg font-medium text-gray-900">{stat.value}</dd>
                  </dl>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-sm text-gray-600">{stat.change}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Stats */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Performance Overview
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">This Week</span>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {stats?.orders_this_week || 0} orders
                  </div>
                  <div className="text-sm text-gray-500">
                    ${stats?.revenue_this_week?.toFixed(2) || '0.00'}
                  </div>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">This Month</span>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {stats?.orders_this_month || 0} orders
                  </div>
                  <div className="text-sm text-gray-500">
                    ${stats?.revenue_this_month?.toFixed(2) || '0.00'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Quick Actions
            </h3>
            <div className="space-y-3">
              <a
                href="/products/new"
                className="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded-md hover:bg-blue-700 transition duration-150 ease-in-out"
              >
                Add New Product
              </a>
              <a
                href="/orders"
                className="block w-full bg-gray-600 text-white text-center py-2 px-4 rounded-md hover:bg-gray-700 transition duration-150 ease-in-out"
              >
                View Pending Orders
              </a>
              <a
                href="/categories"
                className="block w-full bg-green-600 text-white text-center py-2 px-4 rounded-md hover:bg-green-700 transition duration-150 ease-in-out"
              >
                Manage Categories
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {stats && stats.low_stock_products > 0 && (
        <div className="mt-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Low Stock Alert</h3>
                <p className="mt-2 text-sm text-yellow-700">
                  You have {stats.low_stock_products} product(s) with low stock.
                  <a href="/products" className="font-medium underline ml-1">
                    View products
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;