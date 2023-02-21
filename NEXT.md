---
version: 2.0
status: BETA
---

# Next

> Provides informations about the next coming version

This version provides general improvements over the whole project, brining more stability and ease of use.

## New

- Docs Localization: You can now choose a language for the automatic documentation generation (please contribute to add your language!)
  - It already comes with the English, Japanese and French translations
- A new logging system, which is way more stable
- A new string formatting system
- A new server configuration system
- Switch to a local variables based system (more stable)
- Using [`rich`](https://github.com/Textualize/rich) to output things to the console, which improves the UI a lot
- Adding a CLI to easily run Nasse apps

## Fixes

- Fixing a problem with CORS headers
- Fixing a problem with request verifications
- Fixing an issue with `UserSent` validation

## Updates

- Only log exceptions when wanted
- Better compatibility
- Other little improvements
- Improved code quality
- Improved in-code docs
- Type-hinting code more
- Making a fully custom NasseJSONEncoder with more flexibility (example: encoding default types)

Everything is detailed in the [`README.md`](./README.md) file

A comparison from the previous release can be found here [`v1.1...v2.0`](https://github.com/Animenosekai/nasse/compare/v1.1...v2.0)

A comparison from the current branch can be found here [`v2.0...main`](https://github.com/Animenosekai/nasse/compare/v2.0...main)

> 🍡 Animenosekai
