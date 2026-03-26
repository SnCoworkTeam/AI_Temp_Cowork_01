module.exports = {
  // 前端文件
  '*.{js,jsx,ts,tsx}': [
    'prettier --write',
    'eslint --fix',
    'eslint',
  ],
  '*.{css,scss,less,md,json,yml,yaml}': [
    'prettier --write',
  ],
  // Python文件
  '*.py': [
    'black',
    'isort',
    'ruff check --fix',
  ],
};

