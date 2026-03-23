module.exports = {
  '*.{js,jsx,ts,tsx}': [
    'prettier --write',
    'eslint --fix',
    'eslint',
  ],
  '*.{css,scss,less,md,json,yml,yaml}': [
    'prettier --write',
  ],
};

