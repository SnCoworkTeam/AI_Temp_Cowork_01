module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'next/core-web-vitals',
    'prettier', // 必须放在最后，用于关闭和Prettier冲突的规则
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    // TypeScript规则
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-empty-function': 'warn',

    // React规则
    'react-hooks/exhaustive-deps': 'warn',
    'react/no-unescaped-entities': 'off',
    'react/react-in-jsx-scope': 'off', // Next.js不需要

    // 通用规则
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
  },
  ignorePatterns: ['dist', 'node_modules', '.next', 'out', 'build'],
};

