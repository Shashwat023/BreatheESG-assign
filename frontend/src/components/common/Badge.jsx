import React from 'react';
import clsx from 'clsx';

const variants = {
  success: 'bg-success-50 text-success-600 border border-success-200',
  warning: 'bg-warning-50 text-warning-600 border border-warning-200',
  danger: 'bg-danger-50 text-danger-600 border border-danger-200',
  info: 'bg-primary-50 text-primary-600 border border-primary-200',
  neutral: 'bg-gray-100 text-gray-700 border border-gray-200',
};

export default function Badge({ children, variant = 'neutral', className }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
