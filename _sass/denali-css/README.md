# Denali CSS Library

[![npm](https://img.shields.io/npm/v/denali-css?color=red)](https://www.npmjs.com/package/denali-css)
[![Build Status][status-image]][status-url]
![jsDelivr hits (GitHub)](https://img.shields.io/jsdelivr/gh/hm/denali-design/denali-css)
[![slack](https://img.shields.io/badge/slack-Denali-3570f4.svg)](https://denali-design.slack.com/app_redirect?channel=general)
[![GitHub](https://img.shields.io/github/license/denali-design/denali-css)](https://github.com/denali-design/denali-css/blob/master/LICENSE.md)

## Table of contents
 
- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Browser support](#browser-support)
- [Versioning](#versioning)
- [Contribute](#contribute)
- [License](#license)

---

## Background

The Denali System Language was created by the Platforms and Technology Design team at Verizon Media as a scalable method for designing and developing visually consistent and functional internal products. Denali’s CSS framework allows developers to implement the Denali System Language in their projects. The framework is lightweight and flexible. It supports theming through custom variables which means the visual appearance of Denali’s components can be easily adapted to fit the visual style of any brand. Additionally, components are framework independent allowing you to take what you need and leave the rest.

You can view the Denali’s entire component library complete with corresponding code snippets and documentation on the [getting started page](https://denali.design/docs/2/guides/get-started).

## Install

#### Prerequisites

You will need the following installed to run the site:

1. [Node](https://nodejs.org/en/)
2. [NPM](https://www.npmjs.com/)
3. [Ruby](https://www.ruby-lang.org/)
4. [Sass](http://compass-style.org/)
5. [Gulp](https://gulpjs.com/)

> Note: This guide assumes you have the prerequisites installed locally and will not go over install instructions for them. Refer to their websites for guidance if necessary.

#### Quick install

###### NPM

To add Denali CSS into your project we offer a node package.

```
npm install denali-css
```

After installation, you can import the CSS file into your project.

```
import 'denali-css/css/denali.css'
```

###### CDN

```
https://cdn.jsdelivr.net/npm/denali-css/css/denali.css
```

#### Generating SASS

Clone or download this repository.

```
denali-system-language/denali-css.git
```

Use any command line tool and navigate to where you downloaded the repository.

```
cd path-to-folder/denali-css
```

Use NPM to install packages.

```
npm install
```

#### Usage

To spin up local server to view demo files use the command below. This will also watch the SCSS files for any changes and will output a CSS file in the css folder. After you should be prompted with a success message with the localhost url available to view.

```
gulp serve
```

## Browser Support
Learn more about the browsers and devices we support [here](https://denali.design/browsers).
- **Chrome** on Android, Windows, macOS, and Linux
- **Firefox** on Windows, macOS, and Linux
- **Safari** on iOS and macOS

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the tags on this [repository](https://github.com/denali-design/denali-css/tags).

## Contribute

To start contributing to Denali, have a look at our guidelines, as well as pointers on where to start making changes, in our [contributing guide](https://github.com/denali-design/denali-css/blob/master/CONTRIBUTE.md).

## Maintainers

- **Jay Torres** | _Dir Product Design for Core Platforms_ (torresr@verizonmedia.com)
- **Chris Esler** | _Principle Software Dev Engineer_ (cesler@verizonmedia.com)
- **Chas Turansky** | _Product Designer & Front-End Dev_ (cturansky@verizonmedia.com)
- **Jazmin Orozco** | _Product Designer_ (jorozco@verizonmedia.com)
- **Marco Sandoval** | _Product Designer_ (msandoval@verizonmedia.com)

## License

Code licensed under the MIT license. See [LICENSE file](https://github.com/denali-design/denali-css/blob/master/LICENSE.md) for terms.

[status-image]: https://cd.screwdriver.cd/pipelines/3067/badge
[status-url]: https://cd.screwdriver.cd/pipelines/3067
