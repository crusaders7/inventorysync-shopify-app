module.exports = {
  middleware: {
    '*': (req, res, next) => {
      res.removeHeader('X-Frame-Options');
      res.removeHeader('Content-Security-Policy');
      res.setHeader('Content-Security-Policy', "default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors * https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;");
      res.setHeader('Access-Control-Allow-Origin', '*');
      next();
    }
  }
};
