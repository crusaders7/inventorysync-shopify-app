#!/usr/bin/env node

const { clearCacheFromCLI } = require('../frontend/src/utils/clearCache');

(async () => {
  try {
    const result = await clearCacheFromCLI();
    if (result.success) {
      console.log(result.message);
    } else {
      console.error('Cache clearing failed:', result.error);
    }
  } catch (error) {
    console.error('An unexpected error occurred:', error);
  }
})();

