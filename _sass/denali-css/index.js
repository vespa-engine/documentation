/**
 * Copyright 2020, Oath Inc.
 * Licensed under the terms of the MIT license. See LICENSE file in project root for terms
 */

'use strict';

const fs = require('fs');
const path = require('path');

module.exports = {
    getFilePath(name) {
        return path.resolve(__dirname, name || '');
    }
};
