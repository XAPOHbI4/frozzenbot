/**
 * Category Filter Component
 * Allows users to filter products by category
 */

import React, { memo } from 'react';
import { Category } from '../../types';
import { telegramHapticFeedback } from '../../utils/telegram';
import './CategoryFilter.css';

interface CategoryFilterProps {
  categories: Category[];
  selectedCategoryId: number | null;
  onCategorySelect: (categoryId: number | null) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const CategoryFilter: React.FC<CategoryFilterProps> = memo(({
  categories,
  selectedCategoryId,
  onCategorySelect,
  loading = false,
  disabled = false,
}) => {
  const handleCategoryClick = (categoryId: number | null) => {
    if (disabled || loading) return;

    onCategorySelect(categoryId);
    telegramHapticFeedback.selection();
  };

  const activeCategoriesCount = categories.filter(cat => cat.is_active).length;

  if (loading && categories.length === 0) {
    return (
      <div className="category-filter category-filter--loading">
        <div className="category-filter__loading">
          <div className="category-loading-skeleton">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="category-skeleton-item" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`category-filter ${disabled ? 'category-filter--disabled' : ''}`}>
      <div className="category-filter__container">
        {/* All Categories Button */}
        <button
          onClick={() => handleCategoryClick(null)}
          disabled={disabled || loading}
          className={`category-filter__item ${
            selectedCategoryId === null ? 'category-filter__item--active' : ''
          }`}
          aria-label="Показать все товары"
        >
          <div className="category-item__content">
            <span className="category-item__icon">🏪</span>
            <span className="category-item__name">Все товары</span>
          </div>
          {selectedCategoryId === null && (
            <div className="category-item__indicator" />
          )}
        </button>

        {/* Category Buttons */}
        {categories
          .filter(category => category.is_active)
          .sort((a, b) => a.sort_order - b.sort_order)
          .map(category => (
            <button
              key={category.id}
              onClick={() => handleCategoryClick(category.id)}
              disabled={disabled || loading}
              className={`category-filter__item ${
                selectedCategoryId === category.id ? 'category-filter__item--active' : ''
              }`}
              aria-label={`Показать товары категории ${category.name}`}
            >
              <div className="category-item__content">
                {/* Category Icon or Image */}
                {category.image_url ? (
                  <img
                    src={category.image_url}
                    alt={category.name}
                    className="category-item__image"
                    loading="lazy"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                ) : (
                  <span className="category-item__icon">📦</span>
                )}

                <span className="category-item__name" title={category.name}>
                  {category.name}
                </span>

                {/* Products Count Badge */}
                {category.products_count > 0 && (
                  <span className="category-item__count">
                    {category.products_count}
                  </span>
                )}
              </div>

              {/* Active Indicator */}
              {selectedCategoryId === category.id && (
                <div className="category-item__indicator" />
              )}
            </button>
          ))}

        {/* No Categories State */}
        {activeCategoriesCount === 0 && !loading && (
          <div className="category-filter__empty">
            <span className="empty-icon">📂</span>
            <span className="empty-text">Категории не найдены</span>
          </div>
        )}
      </div>

      {/* Loading Overlay */}
      {loading && categories.length > 0 && (
        <div className="category-filter__loading-overlay">
          <div className="loading-spinner-small" />
        </div>
      )}
    </div>
  );
});

CategoryFilter.displayName = 'CategoryFilter';

export default CategoryFilter;