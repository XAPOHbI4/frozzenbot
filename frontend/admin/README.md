# FrozenBot Admin Panel

A modern React + TypeScript admin panel for managing the FrozenBot frozen food delivery service.

## Features

- ✅ **Dashboard** - Overview with statistics and key metrics
- ✅ **Product Management** - Full CRUD operations for products
- ✅ **Order Management** - View orders, update status, track delivery
- ✅ **Category Management** - Organize products by categories
- ✅ **Authentication** - Secure login system
- ✅ **Responsive Design** - Works on desktop and mobile devices
- ✅ **Real-time Updates** - Live order status tracking
- ✅ **Error Handling** - Comprehensive error management

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query** - Server state management
- **React Hook Form** - Form validation and handling
- **Heroicons** - Beautiful SVG icons
- **Axios** - HTTP client with interceptors
- **React Hot Toast** - Toast notifications

## Project Structure

```
src/
├── components/
│   ├── Layout/
│   │   └── Layout.tsx          # Main layout with navigation
│   └── UI/
│       └── LoadingSpinner.tsx  # Reusable UI components
├── contexts/
│   └── AuthContext.tsx         # Authentication context
├── pages/
│   ├── Dashboard/
│   │   └── Dashboard.tsx       # Dashboard with statistics
│   ├── Login/
│   │   └── Login.tsx           # Login form
│   ├── Products/
│   │   ├── Products.tsx        # Product list page
│   │   └── ProductForm.tsx     # Add/edit product form
│   ├── Orders/
│   │   ├── Orders.tsx          # Orders list page
│   │   └── OrderView.tsx       # Single order view
│   └── Categories/
│       └── Categories.tsx      # Categories management
├── services/
│   ├── api.ts                  # Axios instance with interceptors
│   ├── auth.ts                 # Authentication services
│   ├── dashboard.ts            # Dashboard statistics
│   ├── products.ts             # Product CRUD operations
│   ├── orders.ts               # Order management
│   └── categories.ts           # Category operations
├── types/
│   └── index.ts                # TypeScript type definitions
├── App.tsx                     # Main app component with routing
├── main.tsx                    # App entry point
└── index.css                   # Global styles with Tailwind
```

## API Integration

The admin panel connects to the backend API at `http://localhost:8000` with the following endpoints:

### Authentication
- `POST /auth/login` - Admin login

### Products
- `GET /products` - List products
- `GET /products/{id}` - Get single product
- `POST /products` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

### Categories
- `GET /categories` - List categories
- `POST /categories` - Create category
- `PUT /categories/{id}` - Update category
- `DELETE /categories/{id}` - Delete category

### Orders
- `GET /orders` - List orders
- `GET /orders/{id}` - Get single order
- `PUT /orders/{id}/status` - Update order status

### Dashboard
- `GET /admin/dashboard/stats` - Dashboard statistics

## Setup Instructions

1. **Install Dependencies**
   ```bash
   cd frontend/admin
   npm install
   ```

2. **Environment Setup**
   - Ensure backend is running on `http://localhost:8000`
   - API proxy is configured in `vite.config.ts`

3. **Development Server**
   ```bash
   npm run dev
   ```
   The admin panel will be available at `http://localhost:3000`

4. **Build for Production**
   ```bash
   npm run build
   ```

## Authentication

The admin panel requires admin-level access. Login with admin credentials:
- The authentication system stores JWT tokens in localStorage
- Protected routes automatically redirect to login if not authenticated
- API requests include Bearer token in Authorization header

## Key Features

### Dashboard
- Real-time statistics (revenue, orders, products)
- Quick action buttons
- Low stock alerts
- Performance metrics by period

### Product Management
- Add/edit products with image upload
- Category assignment
- Stock quantity tracking
- Availability toggle
- Price management

### Order Management
- View all orders with filtering
- Update order status (pending → confirmed → preparing → ready → delivering → delivered)
- Customer information display
- Order timeline tracking
- Status change notifications

### Category Management
- Create/edit categories
- Active/inactive status toggle
- Product organization
- Category descriptions

## Error Handling

- Comprehensive error boundaries
- Toast notifications for user feedback
- Network error handling with retry
- Form validation with helpful messages
- 401 handling with automatic logout

## Responsive Design

- Mobile-first approach
- Collapsible sidebar navigation
- Touch-friendly interface
- Responsive tables and forms
- Optimized for all screen sizes

## Development Notes

- TypeScript strict mode enabled
- ESLint configuration for code quality
- Hot reload for fast development
- React Query for efficient data fetching
- Tailwind for consistent styling

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Ensure backend is running on port 8000
   - Check CORS settings on backend
   - Verify proxy configuration in vite.config.ts

2. **Authentication Issues**
   - Clear localStorage and try logging in again
   - Check if user has admin privileges
   - Verify JWT token validity

3. **Build Issues**
   - Delete node_modules and reinstall
   - Check for TypeScript errors
   - Ensure all dependencies are up to date

### Performance Tips

- Images are lazy-loaded
- API responses are cached with React Query
- Bundle size optimized with Vite
- Gzip compression recommended for production

## Contributing

1. Follow TypeScript strict mode
2. Use Tailwind CSS for styling
3. Add proper error handling
4. Include loading states
5. Write descriptive commit messages
6. Test on different screen sizes

## License

This project is part of the FrozenBot delivery service.