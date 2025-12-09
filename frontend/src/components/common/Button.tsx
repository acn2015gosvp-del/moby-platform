/**
 * 버튼 컴포넌트
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: 'bg-primary text-background-main hover:brightness-110',
    secondary: 'bg-secondary text-white hover:brightness-110',
    danger: 'bg-danger text-white hover:brightness-110',
    outline: 'border border-primary text-primary bg-transparent hover:bg-primary hover:text-background-main',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  const disabledClasses = 'bg-gray-600 text-gray-400 cursor-not-allowed opacity-60'

  return (
    <button
      type={props.type || 'button'}
      disabled={disabled}
      className={`
        rounded font-medium 
        transition-all duration-200 
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary
        ${disabled ? disabledClasses : variantClasses[variant]} 
        ${sizeClasses[size]} 
        ${className}
      `.trim().replace(/\s+/g, ' ')}
      {...props}
    >
      {children}
    </button>
  )
}

export default Button

