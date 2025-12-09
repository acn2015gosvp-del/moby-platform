/**
 * 로딩 컴포넌트
 */

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

function Loading({ size = 'md', message }: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div
        className={`${sizeClasses[size]} border-4 border-primary/20 border-t-primary rounded-full animate-spin`}
      ></div>
      {message && (
        <p className="mt-4 text-sm text-text-secondary">{message}</p>
      )}
    </div>
  )
}

export default Loading

