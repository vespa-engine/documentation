const assert = require('assert');
const denali = require('../index.js');
const fs = require('fs');

describe('index', function() {
  describe('getFilePath', function() {
    it('should return a file path', function() {
      assert.match(denali.getFilePath(), /\/denali-css$/);
      assert.match(denali.getFilePath(''), /\/denali-css$/);
      assert.match(denali.getFilePath('./'), /\/denali-css$/);
      assert.match(denali.getFilePath('css/'), /\/denali-css\/css$/);
      assert.match(denali.getFilePath('css/denali.css'), /denali-css\/css\/denali.css$/);
      assert.match(denali.getFilePath('scss/components/button.scss'), /denali-css\/scss\/components\/button.scss$/);

      const path = denali.getFilePath('scss/components/button.scss');
      assert.match(fs.readFileSync(path, 'utf8'), /@mixin button-default {/);
    });
  });
});
