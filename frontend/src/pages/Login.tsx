/**
 * 로그인 페이지
 */

import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { extractErrorMessage } from '@/utils/errorHandler'
import MobyLogo from '@/components/common/MobyLogo'

const Login: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login(formData)
      navigate('/')
    } catch (err: any) {
      const errorMessage = extractErrorMessage(
        err,
        '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.'
      )
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background-main py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* 로그인 카드 */}
        <div className="bg-background-surface border border-border rounded-2xl p-8 shadow-xl">
          {/* 로고 영역 */}
          <div className="text-center mb-0">
            <div className="flex justify-center">
              <MobyLogo
                width={200}
                height={303}
                fill="currentColor"
                className="text-primary"
              />
            </div>
          </div>

          {/* 제목 */}
          <h1 className="text-5xl font-bold text-primary text-center mb-8 -mt-10">
            MOBY
          </h1>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-lg bg-danger/10 border border-danger p-4">
                <div className="text-sm text-danger">{error}</div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-text-secondary mb-2">
                  아이디
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="appearance-none relative block w-full px-4 h-12 border border-border bg-background-main text-text-primary placeholder-text-secondary rounded-lg focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="아이디를 입력하세요"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
                  비밀번호
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="appearance-none relative block w-full px-4 h-12 border border-border bg-background-main text-text-primary placeholder-text-secondary rounded-lg focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  placeholder="비밀번호를 입력하세요"
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-lg text-background-main bg-primary hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {isLoading ? '로그인 중...' : '로그인'}
              </button>
            </div>

            <div className="text-center">
              <p className="text-sm text-text-secondary">
                계정이 없으신가요?{' '}
                <Link
                  to="/register"
                  className="font-medium text-primary hover:brightness-110 transition-colors"
                >
                  회원가입
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Login

